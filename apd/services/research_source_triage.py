from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from urllib import parse

from apd.domain.models import ResearchBrief
from apd.services.research_search import SearchResult


_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9\-]{1,}")
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
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}
_PAIN_KEYWORDS = {
    "annoying",
    "bug",
    "complaint",
    "complaints",
    "confusing",
    "delay",
    "difficult",
    "friction",
    "issue",
    "issues",
    "limitation",
    "limitations",
    "manual",
    "pain",
    "problem",
    "problems",
    "slow",
    "stuck",
    "toil",
    "workaround",
}
_BAIT_PATTERNS = (
    "top 10",
    "top ten",
    "best tools",
    "trends",
    "ultimate guide",
    "hot takes",
    "must-have",
    "top startups",
)


@dataclass(frozen=True)
class SearchDecisionRecord:
    query: str
    title: str
    url: str
    snippet: str | None
    provider: str
    rank: int
    decision: str
    reason: str
    source_type: str
    fetched: bool = False
    rejection_error: str | None = None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def triage_search_results(brief: ResearchBrief, results: list[SearchResult]) -> list[SearchDecisionRecord]:
    return [triage_search_result(brief, result) for result in results]


def triage_search_result(brief: ResearchBrief, result: SearchResult) -> SearchDecisionRecord:
    source_type = guess_source_type(result)
    content_text = " ".join(part for part in [result.title, result.snippet or "", result.url] if part).lower()
    brief_terms = _brief_terms(brief)
    overlap = bool(brief_terms.intersection(_tokenize(content_text)))
    contains_pain = any(keyword in content_text for keyword in _PAIN_KEYWORDS)
    pain_oriented = _brief_is_pain_oriented(brief)

    if _looks_like_bait(content_text) and not overlap:
        return SearchDecisionRecord(
            query=result.query,
            title=result.title,
            url=result.url,
            snippet=result.snippet,
            provider=result.provider,
            rank=result.rank,
            decision="bait",
            reason="Low-overlap trend/listicle content is unlikely to help grounded product research.",
            source_type=source_type,
        )

    if source_type == "vendor_marketing":
        decision = "discard" if pain_oriented else "uncertain"
        reason = (
            "Vendor marketing and homepages are weak evidence for user pain."
            if pain_oriented
            else "Vendor marketing may matter later, but it is weak primary evidence."
        )
        return SearchDecisionRecord(
            query=result.query,
            title=result.title,
            url=result.url,
            snippet=result.snippet,
            provider=result.provider,
            rank=result.rank,
            decision=decision,
            reason=reason,
            source_type=source_type,
        )

    if source_type in {"forum_thread", "reddit_thread", "hn_discussion", "github_issue", "github_discussion", "review_page"}:
        return SearchDecisionRecord(
            query=result.query,
            title=result.title,
            url=result.url,
            snippet=result.snippet,
            provider=result.provider,
            rank=result.rank,
            decision="keep",
            reason="Likely first-hand discussion, issue reporting, or substitute evidence.",
            source_type=source_type,
        )

    if source_type == "documentation":
        decision = "keep" if overlap and contains_pain else "uncertain"
        reason = (
            "Documentation appears to describe limitations or workflow friction."
            if decision == "keep"
            else "Documentation may be relevant, but the result does not clearly show limitations yet."
        )
        return SearchDecisionRecord(
            query=result.query,
            title=result.title,
            url=result.url,
            snippet=result.snippet,
            provider=result.provider,
            rank=result.rank,
            decision=decision,
            reason=reason,
            source_type=source_type,
        )

    if overlap and contains_pain:
        return SearchDecisionRecord(
            query=result.query,
            title=result.title,
            url=result.url,
            snippet=result.snippet,
            provider=result.provider,
            rank=result.rank,
            decision="keep",
            reason="The result matches the brief and contains explicit pain or workaround language.",
            source_type=source_type,
        )

    if not overlap:
        return SearchDecisionRecord(
            query=result.query,
            title=result.title,
            url=result.url,
            snippet=result.snippet,
            provider=result.provider,
            rank=result.rank,
            decision="discard",
            reason="The result does not appear closely related to the brief topic.",
            source_type=source_type,
        )

    return SearchDecisionRecord(
        query=result.query,
        title=result.title,
        url=result.url,
        snippet=result.snippet,
        provider=result.provider,
        rank=result.rank,
        decision="uncertain",
        reason="The result may be relevant, but it is not strong enough to fetch in v1.",
        source_type=source_type,
    )


def guess_source_type(result: SearchResult) -> str:
    parsed_url = parse.urlsplit(result.url)
    hostname = (parsed_url.hostname or "").lower()
    path = (parsed_url.path or "").lower()
    content_text = " ".join(part for part in [hostname, path, result.title.lower(), (result.snippet or "").lower()])

    if "github.com" in hostname and "/issues/" in path:
        return "github_issue"
    if "github.com" in hostname and "/discussions/" in path:
        return "github_discussion"
    if "reddit.com" in hostname:
        return "reddit_thread"
    if "news.ycombinator.com" in hostname:
        return "hn_discussion"
    if any(token in hostname for token in ("forum", "community")) or any(token in path for token in ("/forum", "/t/", "/thread")):
        return "forum_thread"
    if hostname.startswith("docs.") or "/docs/" in path or "documentation" in content_text:
        return "documentation"
    if any(token in content_text for token in ("pricing", "request demo", "book demo", "signup", "sign up", "features")):
        return "vendor_marketing"
    if any(token in hostname for token in ("g2.com", "capterra.com", "trustpilot.com")) or "review" in content_text:
        return "review_page"
    if "/blog/" in path or " blog " in f" {content_text} ":
        return "blog_post"
    return "public_web"


def _brief_terms(brief: ResearchBrief) -> set[str]:
    raw = " ".join(part for part in [brief.title, brief.research_question, brief.constraints or ""] if part)
    return _tokenize(raw)


def _brief_is_pain_oriented(brief: ResearchBrief) -> bool:
    combined = " ".join(part for part in [brief.title, brief.research_question, brief.constraints or ""] if part).lower()
    return any(token in combined for token in _PAIN_KEYWORDS.union({"user", "workflow", "complaint", "complaints"}))


def _looks_like_bait(content_text: str) -> bool:
    return any(pattern in content_text for pattern in _BAIT_PATTERNS)


def _tokenize(text: str) -> set[str]:
    return {token for token in _TOKEN_RE.findall(text.lower()) if token not in _STOP_WORDS}