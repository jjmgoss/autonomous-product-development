from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import os
import re
from pathlib import Path
from typing import Protocol
from urllib import error, parse, request

from apd.domain.models import ResearchBrief


MAX_SEARCH_QUERIES = 5
DEFAULT_RESULTS_PER_QUERY = 5
BRAVE_SEARCH_DEFAULT_BASE_URL = "https://api.search.brave.com/res/v1/web/search"
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
class SearchProviderResolution:
    provider: SearchProvider
    provider_name: str
    is_live_provider: bool
    is_configured: bool
    setup_required_message: str | None = None
    configuration_source: str | None = None


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


class BraveSearchProvider:
    provider_name = "brave"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = BRAVE_SEARCH_DEFAULT_BASE_URL,
        timeout_seconds: int = 15,
    ) -> None:
        self._api_key = api_key.strip()
        self._base_url = base_url.strip() or BRAVE_SEARCH_DEFAULT_BASE_URL
        self._timeout_seconds = max(1, int(timeout_seconds))

    def search(
        self,
        queries: list[SearchQuery],
        *,
        max_results_per_query: int = DEFAULT_RESULTS_PER_QUERY,
    ) -> list[SearchResult]:
        results: list[SearchResult] = []
        for query in queries:
            results.extend(
                self._search_one_query(query, max_results=max_results_per_query)
            )
        return results

    def _search_one_query(self, query: SearchQuery, *, max_results: int) -> list[SearchResult]:
        params = parse.urlencode({
            "q": query.query,
            "count": max(1, max_results),
            "search_lang": "en",
            "safesearch": "moderate",
        })
        req = request.Request(
            url=f"{self._base_url}?{params}",
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": self._api_key,
                "User-Agent": "APD research search/1.0",
            },
            method="GET",
        )
        with request.urlopen(req, timeout=self._timeout_seconds) as response:
            raw = response.read()
        data = json.loads(raw.decode("utf-8"))
        web = data.get("web") if isinstance(data, dict) else None
        raw_results = web.get("results") if isinstance(web, dict) else None
        if not isinstance(raw_results, list):
            return []
        results: list[SearchResult] = []
        for index, item in enumerate(raw_results[: max(1, max_results)], start=1):
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            url = str(item.get("url") or "").strip()
            if not title or not url:
                continue
            snippet = str(item.get("description") or item.get("snippet") or "").strip() or None
            results.append(
                SearchResult(
                    query=query.query,
                    title=title,
                    url=url,
                    snippet=snippet,
                    provider=self.provider_name,
                    rank=index,
                    metadata_json={
                        "family_friendly": item.get("family_friendly"),
                        "language": item.get("language"),
                    },
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


def get_configured_search_provider(db=None) -> SearchProvider:
    return resolve_configured_search_provider(db).provider


def resolve_configured_search_provider(db=None) -> SearchProviderResolution:
    settings = _load_search_settings(db)
    provider = (settings.get("research_search_provider") or "").strip().lower()

    if provider in {"", "none", "disabled"}:
        return SearchProviderResolution(
            provider=EmptySearchProvider(),
            provider_name="none",
            is_live_provider=False,
            is_configured=False,
            setup_required_message=(
                "Search provider setup required: configure a live web search provider before Start Research can discover sources."
            ),
            configuration_source=settings.get("configuration_source"),
        )
    if provider == "static":
        fixture_path = (os.getenv("APD_RESEARCH_STATIC_SEARCH_RESULTS_PATH") or "").strip()
        if not fixture_path:
            return SearchProviderResolution(
                provider=EmptySearchProvider(provider_name="static"),
                provider_name="static",
                is_live_provider=False,
                is_configured=False,
                setup_required_message=(
                    "Static search provider selected but APD_RESEARCH_STATIC_SEARCH_RESULTS_PATH is missing. Static mode is only intended for tests and deterministic local development."
                ),
                configuration_source=settings.get("configuration_source"),
            )
        return SearchProviderResolution(
            provider=load_static_search_provider(Path(fixture_path)),
            provider_name="static",
            is_live_provider=False,
            is_configured=True,
            configuration_source=settings.get("configuration_source"),
        )
    if provider == "brave":
        api_key = (os.getenv("APD_BRAVE_SEARCH_API_KEY") or "").strip()
        if not api_key:
            return SearchProviderResolution(
                provider=EmptySearchProvider(provider_name="brave"),
                provider_name="brave",
                is_live_provider=True,
                is_configured=False,
                setup_required_message=(
                    "Search provider setup required: Brave Search is selected but APD_BRAVE_SEARCH_API_KEY is missing."
                ),
                configuration_source=settings.get("configuration_source"),
            )
        return SearchProviderResolution(
            provider=BraveSearchProvider(
                api_key=api_key,
                base_url=str(settings.get("brave_search_base_url") or BRAVE_SEARCH_DEFAULT_BASE_URL),
            ),
            provider_name="brave",
            is_live_provider=True,
            is_configured=True,
            configuration_source=settings.get("configuration_source"),
        )
    return SearchProviderResolution(
        provider=EmptySearchProvider(provider_name=provider or "unknown"),
        provider_name=provider or "unknown",
        is_live_provider=False,
        is_configured=False,
        setup_required_message=(
            f"Search provider setup required: unsupported provider '{provider or 'unknown'}'."
        ),
        configuration_source=settings.get("configuration_source"),
    )


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


def search_provider_setup_message(db=None) -> str | None:
    resolution = resolve_configured_search_provider(db)
    return resolution.setup_required_message


def is_live_search_provider_configured(db=None) -> bool:
    resolution = resolve_configured_search_provider(db)
    return resolution.is_live_provider and resolution.is_configured


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


def _load_search_settings(db=None) -> dict[str, object]:
    settings: dict[str, object] = {
        "research_search_provider": (os.getenv("APD_RESEARCH_SEARCH_PROVIDER") or "").strip().lower() or "none",
        "brave_search_base_url": (os.getenv("APD_BRAVE_SEARCH_BASE_URL") or "").strip() or BRAVE_SEARCH_DEFAULT_BASE_URL,
        "configuration_source": "environment",
    }
    if db is None:
        return settings
    try:
        from apd.services.model_execution_settings import get_model_execution_settings

        db_settings = get_model_execution_settings(db)
    except Exception:
        return settings
    provider = str(db_settings.get("research_search_provider") or settings["research_search_provider"]).strip().lower()
    base_url = str(db_settings.get("brave_search_base_url") or settings["brave_search_base_url"]).strip()
    if db_settings:
        settings["configuration_source"] = "database"
    settings["research_search_provider"] = provider or "none"
    settings["brave_search_base_url"] = base_url or BRAVE_SEARCH_DEFAULT_BASE_URL
    return settings