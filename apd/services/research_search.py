from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import os
import re
from pathlib import Path
from typing import Protocol

from apd.domain.models import ResearchBrief


MAX_SEARCH_QUERIES = 5
DEFAULT_RESULTS_PER_QUERY = 5
_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "there",
    "these",
    "this",
    "to",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}
_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9\-]{1,}")


@dataclass(frozen=True)
class SearchQuery:
    query: str
    rationale: str


@dataclass(frozen=True)
class SearchResult:
    query: str
    title: str
    url: str
    snippet: str | None
    provider: str
    rank: int
    metadata_json: dict[str, object] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class SearchProvider(Protocol):
    provider_name: str

    def search(
        self,
        queries: list[SearchQuery],
        *,
        max_results_per_query: int = DEFAULT_RESULTS_PER_QUERY,
    ) -> list[SearchResult]: ...


@dataclass(frozen=True)
class EmptySearchProvider:
    provider_name: str = "none"

    def search(
        self,
        queries: list[SearchQuery],
        *,
        max_results_per_query: int = DEFAULT_RESULTS_PER_QUERY,
    ) -> list[SearchResult]:
        return []


class StaticSearchProvider:
    def __init__(
        self,
        fixtures_by_query: dict[str, list[SearchResult | dict[str, object]]],
        *,
        provider_name: str = "static",
    ) -> None:
        self.provider_name = provider_name
        normalized: dict[str, list[SearchResult]] = {}
        for query, rows in fixtures_by_query.items():
            query_key = _normalize_query_key(query)
            normalized[query_key] = [
                _coerce_search_result(row, query=str(query), provider_name=provider_name, rank=index + 1)
                for index, row in enumerate(rows)
            ]
        self._fixtures_by_query = normalized

    def search(
        self,
        queries: list[SearchQuery],
        *,
        max_results_per_query: int = DEFAULT_RESULTS_PER_QUERY,
    ) -> list[SearchResult]:
        results: list[SearchResult] = []
        for query in queries:
            for result in self._fixtures_by_query.get(_normalize_query_key(query.query), [])[: max(0, max_results_per_query)]:
                results.append(
                    SearchResult(
                        query=query.query,
                        title=result.title,
                        url=result.url,
                        snippet=result.snippet,
                        provider=self.provider_name,
                        rank=result.rank,
                        metadata_json=dict(result.metadata_json or {}),
                    )
                )
        return results


def generate_search_queries_for_brief(
    brief: ResearchBrief,
    *,
    max_queries: int = MAX_SEARCH_QUERIES,
) -> list[SearchQuery]:
    topic = _brief_topic_text(brief)
    aspect_templates = [
        ("forum complaints", "Look for first-person pain and workaround discussions."),
        ("reddit pain", "Look for user language describing repeated frustration."),
        ("github issues", "Look for explicit bugs, feature gaps, and maintainer responses."),
        ("docs limitations", "Look for product docs that reveal constraints or workflow friction."),
        ("reviews alternatives", "Look for substitute comparisons and negative reviews."),
    ]
    queries: list[SearchQuery] = []
    seen: set[str] = set()
    for suffix, rationale in aspect_templates:
        query = " ".join(part for part in (topic, suffix) if part).strip()
        if not query:
            continue
        normalized = _normalize_query_key(query)
        if normalized in seen:
            continue
        seen.add(normalized)
        queries.append(SearchQuery(query=query, rationale=rationale))
        if len(queries) >= max(1, max_queries):
            break
    return queries


def get_configured_search_provider() -> SearchProvider:
    provider = (os.getenv("APD_RESEARCH_SEARCH_PROVIDER") or "").strip().lower()
    if provider in {"", "none", "disabled"}:
        return EmptySearchProvider()
    if provider == "static":
        fixture_path = (os.getenv("APD_RESEARCH_STATIC_SEARCH_RESULTS_PATH") or "").strip()
        if not fixture_path:
            return EmptySearchProvider()
        return load_static_search_provider(Path(fixture_path))
    return EmptySearchProvider(provider_name=provider or "unknown")


def load_static_search_provider(path: str | Path) -> StaticSearchProvider:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Static search fixture must be a JSON object keyed by query.")
    fixtures: dict[str, list[SearchResult | dict[str, object]]] = {}
    for query, rows in data.items():
        if not isinstance(rows, list):
            raise ValueError("Static search fixture rows must be lists.")
        fixtures[str(query)] = rows
    return StaticSearchProvider(fixtures, provider_name="static")


def search_results_to_dicts(results: list[SearchResult]) -> list[dict[str, object]]:
    return [result.as_dict() for result in results]


def _brief_topic_text(brief: ResearchBrief) -> str:
    raw = " ".join(
        part.strip()
        for part in [brief.title, brief.research_question, brief.constraints or ""]
        if part and part.strip()
    )
    tokens: list[str] = []
    seen: set[str] = set()
    for token in _TOKEN_RE.findall(raw.lower()):
        if token in _STOP_WORDS:
            continue
        if token in seen:
            continue
        seen.add(token)
        tokens.append(token)
        if len(tokens) >= 8:
            break
    return " ".join(tokens)


def _coerce_search_result(
    value: SearchResult | dict[str, object],
    *,
    query: str,
    provider_name: str,
    rank: int,
) -> SearchResult:
    if isinstance(value, SearchResult):
        return SearchResult(
            query=query,
            title=value.title,
            url=value.url,
            snippet=value.snippet,
            provider=provider_name,
            rank=value.rank or rank,
            metadata_json=dict(value.metadata_json or {}),
        )
    title = str(value.get("title") or "").strip()
    url = str(value.get("url") or "").strip()
    if not title or not url:
        raise ValueError("Static search result entries require title and url.")
    snippet = str(value.get("snippet") or "").strip() or None
    metadata_json = value.get("metadata_json")
    if not isinstance(metadata_json, dict):
        metadata_json = {}
    return SearchResult(
        query=query,
        title=title,
        url=url,
        snippet=snippet,
        provider=str(value.get("provider") or provider_name),
        rank=int(value.get("rank") or rank),
        metadata_json=dict(metadata_json),
    )


def _normalize_query_key(query: str) -> str:
    return " ".join(str(query or "").split()).strip().lower()