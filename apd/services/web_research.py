from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass
from collections import Counter
import html
import ipaddress
import json
import re
from urllib import error, parse, request

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apd.domain.models import EvidenceExcerpt, ResearchBrief, Run, RunPhase, Source
from apd.services.research_execution_ollama import extract_json_object_from_model_output
from apd.services.research_search import (
    DEFAULT_RESULTS_PER_QUERY,
    SearchProvider,
    generate_search_queries_for_brief,
    get_configured_search_provider,
    search_results_to_dicts,
)
from apd.services.research_skills import (
    render_research_skill_context_for_phase,
    resolve_research_skills_for_phase,
)
from apd.services.research_source_triage import triage_search_results
from apd.services.research_trace import append_research_trace_event, create_trace_correlation_id

SCHEMA_VERSION = "1.0"
MAX_PROPOSED_QUERIES = 5
MAX_FETCH_URLS = 5
MAX_SEARCH_RESULTS_PER_QUERY = DEFAULT_RESULTS_PER_QUERY
FETCH_TIMEOUT_SECONDS = 10
MAX_RESPONSE_BYTES = 1_000_000
MAX_EXTRACTED_TEXT_CHARS = 12_000
MAX_EXCERPT_TEXT_CHARS = 8_000
MAX_GROUNDED_PACKET_SOURCES = 5
MAX_GROUNDED_PACKET_EXCERPTS = 10
MAX_GROUNDED_PACKET_EXCERPT_CHARS = 1500
MAX_GROUNDED_PACKET_TOTAL_CHARS = 10000
WEB_DISCOVERY_SKILL_CONTEXT_CHARS = 4200
WEB_USER_AGENT = "APD local research prototype/1.0"

_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", flags=re.IGNORECASE | re.DOTALL)
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", flags=re.IGNORECASE | re.DOTALL)
_WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class GroundingSourcePacket:
    sources: list[dict[str, object]]
    evidence_excerpts: list[dict[str, object]]
    total_chars: int

    @property
    def source_ids(self) -> set[str]:
        return {str(item["id"]) for item in self.sources}

    @property
    def excerpt_ids(self) -> set[str]:
        return {str(item["id"]) for item in self.evidence_excerpts}


def _grounding_source_external_id(source_id: int) -> str:
    return f"captured-source-{source_id}"


def _grounding_excerpt_external_id(excerpt_id: int) -> str:
    return f"captured-excerpt-{excerpt_id}"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_web_research_limits() -> dict[str, int]:
    return {
        "max_queries": MAX_PROPOSED_QUERIES,
        "max_urls": MAX_FETCH_URLS,
        "timeout_seconds": FETCH_TIMEOUT_SECONDS,
        "max_response_bytes": MAX_RESPONSE_BYTES,
        "max_extracted_text_chars": MAX_EXTRACTED_TEXT_CHARS,
    }


def build_web_research_target_prompt(brief: ResearchBrief) -> str:
    skill_context = render_research_skill_context_for_phase(
        "web_discovery",
        max_chars=WEB_DISCOVERY_SKILL_CONTEXT_CHARS,
    )
    parts = [
        "You are helping APD plan a controlled web research loop.",
        "Return only JSON.",
        "Do not browse or fetch anything yourself.",
        "Do not invent citations, source text, or claims of completed research.",
        "Propose a small list of public web research targets for APD to validate and fetch.",
        "Include optional queries for future search integration, but APD will only fetch explicit validated URLs in this prototype.",
        f"Cap yourself to at most {MAX_PROPOSED_QUERIES} queries and {MAX_FETCH_URLS} URLs.",
        "Only include public http/https URLs likely relevant to the product investigation.",
        "Do not include localhost, private hosts, file URLs, or authenticated sources.",
    ]
    if skill_context:
        parts.extend(["", skill_context])
    parts.extend(
        [
            "",
            "Return JSON with this shape:",
            "{",
            '  "schema_version": "1.0",',
            '  "queries": [{"query": "string", "rationale": "string"}],',
            '  "urls": [{"url": "https://example.com", "rationale": "string"}]',
            "}",
            "",
            "Research brief:",
            f"Title: {brief.title}",
            f"Research question: {brief.research_question}",
        ]
    )
    if brief.constraints:
        parts.append(f"Constraints: {brief.constraints}")
    if brief.desired_depth:
        parts.append(f"Desired depth: {brief.desired_depth}")
    if brief.expected_outputs:
        parts.append(f"Expected outputs: {brief.expected_outputs}")
    if brief.notes:
        parts.append(f"Notes: {brief.notes}")
    return "\n".join(parts)


def parse_web_research_targets(raw_output: str) -> tuple[dict[str, object] | None, str | None]:
    parsed, parse_error = extract_json_object_from_model_output(raw_output)
    if parse_error or parsed is None:
        return None, parse_error or "parse_failed: invalid_web_research_targets"
    if not isinstance(parsed, dict):
        return None, "parse_failed: web_research_targets_not_object"

    queries_raw = parsed.get("queries") or []
    urls_raw = parsed.get("urls") or []
    if not isinstance(queries_raw, list):
        return None, "validation_failed: queries_must_be_list"
    if not isinstance(urls_raw, list):
        return None, "validation_failed: urls_must_be_list"

    queries: list[dict[str, str]] = []
    for item in queries_raw:
        if not isinstance(item, dict):
            continue
        query = str(item.get("query") or "").strip()
        rationale = str(item.get("rationale") or "").strip()
        if not query:
            continue
        queries.append({"query": query, "rationale": rationale})

    urls: list[dict[str, str]] = []
    for item in urls_raw:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").strip()
        rationale = str(item.get("rationale") or "").strip()
        if not url:
            continue
        urls.append({"url": url, "rationale": rationale})

    return ({"schema_version": str(parsed.get("schema_version") or SCHEMA_VERSION), "queries": queries, "urls": urls}, None)


def validate_public_url(url: str) -> tuple[str | None, str | None]:
    raw = (url or "").strip()
    if not raw:
        return None, "empty_url"
    try:
        parsed_url = parse.urlparse(raw)
    except Exception:
        return None, "malformed_url"
    if parsed_url.scheme.lower() not in {"http", "https"}:
        return None, "unsupported_scheme"
    if not parsed_url.netloc or not parsed_url.hostname:
        return None, "missing_host"
    if parsed_url.username or parsed_url.password:
        return None, "credentials_not_allowed"

    hostname = parsed_url.hostname.strip().lower()
    if hostname == "localhost" or hostname.endswith(".local"):
        return None, "local_host_not_allowed"

    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        ip = None
    if ip is not None:
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            return None, "private_or_loopback_ip_not_allowed"

    normalized = parse.urlunparse(
        (
            parsed_url.scheme.lower(),
            parsed_url.netloc,
            parsed_url.path or "/",
            parsed_url.params,
            parsed_url.query,
            parsed_url.fragment,
        )
    )
    return normalized, None


def fetch_public_url(url: str, *, timeout_seconds: int = FETCH_TIMEOUT_SECONDS, max_bytes: int = MAX_RESPONSE_BYTES) -> dict[str, object]:
    req = request.Request(url=url, headers={"User-Agent": WEB_USER_AGENT}, method="GET")
    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            status_code = getattr(response, "status", 200)
            content_type = response.headers.get("Content-Type", "")
            raw = response.read(max_bytes + 1)
    except error.HTTPError as exc:
        return {"success": False, "error": f"http_{exc.code}", "status_code": exc.code}
    except error.URLError as exc:
        return {"success": False, "error": f"url_error: {exc.reason}"}
    except TimeoutError:
        return {"success": False, "error": "timeout"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}

    if len(raw) > max_bytes:
        return {"success": False, "error": "response_too_large", "status_code": status_code, "content_type": content_type}

    return {
        "success": True,
        "status_code": status_code,
        "content_type": content_type,
        "body": raw,
    }


def extract_title_and_text(body: bytes, content_type: str) -> tuple[str | None, str | None, str | None]:
    content_type_lower = (content_type or "").lower()
    if "html" in content_type_lower or not content_type_lower:
        decoded = body.decode("utf-8", errors="replace")
        title_match = _TITLE_RE.search(decoded)
        title = html.unescape(title_match.group(1).strip()) if title_match else None
        without_scripts = _SCRIPT_STYLE_RE.sub(" ", decoded)
        without_tags = _TAG_RE.sub(" ", without_scripts)
        text = html.unescape(_WHITESPACE_RE.sub(" ", without_tags)).strip()
        return title, text[:MAX_EXTRACTED_TEXT_CHARS] or None, None
    if content_type_lower.startswith("text/"):
        text = body.decode("utf-8", errors="replace").strip()
        return None, text[:MAX_EXTRACTED_TEXT_CHARS] or None, None
    return None, None, "unsupported_content_type"


def _get_or_create_web_research_run(db: Session, brief: ResearchBrief) -> Run:
    meta = dict(brief.metadata_json or {})
    existing_run_id = meta.get("web_research_run_id")
    if existing_run_id:
        existing_run = db.get(Run, int(existing_run_id))
        if existing_run is not None:
            return existing_run

    run = Run(
        title=f"{brief.title} — Web research capture",
        intent=brief.research_question,
        summary="Controlled APD web research capture for a research brief.",
        mode="web_research_capture",
        phase=RunPhase.EVIDENCE_COLLECTED,
        metadata_json={"brief_id": brief.id, "created_by": "apd_web_research"},
    )
    db.add(run)
    db.flush()

    meta["web_research_run_id"] = run.id
    brief.metadata_json = meta
    db.add(brief)
    db.commit()
    db.refresh(brief)
    return run


def get_grounding_source_packet_for_brief(
    db: Session,
    brief: ResearchBrief,
    *,
    max_sources: int = MAX_GROUNDED_PACKET_SOURCES,
    max_excerpts: int = MAX_GROUNDED_PACKET_EXCERPTS,
    max_excerpt_chars: int = MAX_GROUNDED_PACKET_EXCERPT_CHARS,
    max_total_chars: int = MAX_GROUNDED_PACKET_TOTAL_CHARS,
) -> GroundingSourcePacket:
    meta = dict(brief.metadata_json or {})
    source_rows: list[Source] = []

    web_research_run_id = meta.get("web_research_run_id")
    if web_research_run_id:
        source_rows = list(
            db.scalars(
                select(Source)
                .where(Source.run_id == int(web_research_run_id))
                .order_by(Source.id.asc())
                .limit(max_sources)
            )
        )

    if not source_rows:
        source_rows = list(
            db.scalars(
                select(Source)
                .where(Source.metadata_json["brief_id"].as_integer() == int(brief.id))
                .order_by(Source.id.asc())
                .limit(max_sources)
            )
        )

    selected_sources = source_rows[:max_sources]
    if not selected_sources:
        return GroundingSourcePacket(sources=[], evidence_excerpts=[], total_chars=0)

    source_id_map = {source.id: _grounding_source_external_id(source.id) for source in selected_sources}
    source_packet: list[dict[str, object]] = []
    for source in selected_sources:
        source_packet.append(
            {
                "id": source_id_map[source.id],
                "title": source.title,
                "source_type": source.source_type,
                "url": source.url,
                "origin": source.origin,
                "summary": source.summary,
                "metadata_json": {
                    "grounding_source": True,
                    "captured_source_db_id": source.id,
                    "brief_id": brief.id,
                },
            }
        )

    excerpt_rows = list(
        db.scalars(
            select(EvidenceExcerpt)
            .where(EvidenceExcerpt.source_id.in_([source.id for source in selected_sources]))
            .order_by(EvidenceExcerpt.id.asc())
            .limit(max_excerpts * 2)
        )
    )

    total_chars = 0
    excerpt_packet: list[dict[str, object]] = []
    for excerpt in excerpt_rows:
        if excerpt.source_id not in source_id_map:
            continue
        excerpt_text = (excerpt.excerpt_text or "").strip()[:max_excerpt_chars]
        if not excerpt_text:
            continue
        next_total = total_chars + len(excerpt_text)
        if excerpt_packet and next_total > max_total_chars:
            break
        excerpt_packet.append(
            {
                "id": _grounding_excerpt_external_id(excerpt.id),
                "source_id": source_id_map[excerpt.source_id],
                "excerpt_text": excerpt_text,
                "location_reference": excerpt.location_reference,
                "excerpt_type": excerpt.excerpt_type,
                "metadata_json": {
                    "grounding_source": True,
                    "captured_excerpt_db_id": excerpt.id,
                    "captured_source_db_id": excerpt.source_id,
                    "brief_id": brief.id,
                },
            }
        )
        total_chars = next_total
        if len(excerpt_packet) >= max_excerpts:
            break

    return GroundingSourcePacket(
        sources=source_packet,
        evidence_excerpts=excerpt_packet,
        total_chars=total_chars,
    )


def render_grounding_source_packet(packet: GroundingSourcePacket) -> str:
    if not packet.sources or not packet.evidence_excerpts:
        return "(no captured web source packet available)"

    lines = ["## Captured source packet", "", "Use only these APD-captured sources for factual claims.", ""]
    for source in packet.sources:
        lines.append(f"Source ID: {source['id']}")
        if source.get("title"):
            lines.append(f"Title: {source['title']}")
        if source.get("url"):
            lines.append(f"URL: {source['url']}")
        source_excerpts = [
            excerpt
            for excerpt in packet.evidence_excerpts
            if excerpt.get("source_id") == source["id"]
        ]
        for excerpt in source_excerpts:
            lines.append(f"Excerpt ID: {excerpt['id']}")
            lines.append(f"Excerpt: {excerpt['excerpt_text']}")
        lines.append("")
    return "\n".join(lines).strip()


def run_web_research_for_brief(
    db: Session,
    brief: ResearchBrief,
    *,
    trace_correlation_id: str | None = None,
    search_provider: SearchProvider | None = None,
) -> dict[str, object]:
    started_at = _iso_now()
    trace_correlation_id = trace_correlation_id or create_trace_correlation_id(brief_id=brief.id)
    trace_phase = "web_discovery"
    trace_run_id: int | None = None

    def _trace(
        event_type: str,
        *,
        run_id: int | None = None,
        phase: str | None = None,
        message: str | None = None,
        payload: dict[str, object] | None = None,
    ) -> None:
        append_research_trace_event(
            db,
            brief_id=brief.id,
            run_id=run_id if run_id is not None else trace_run_id,
            correlation_id=trace_correlation_id,
            phase=phase or trace_phase,
            event_type=event_type,
            message=message,
            payload=payload,
        )

    selected_skill_ids = resolve_research_skills_for_phase("web_discovery", max_skills=None)
    _trace(
        "phase_started",
        message="Web discovery started.",
        payload={"mode": "agent_led_source_discovery"},
    )
    if selected_skill_ids:
        _trace(
            "skill_context_selected",
            message="Selected research skills for web discovery.",
            payload={"skill_ids": selected_skill_ids, "skill_count": len(selected_skill_ids)},
        )

    queries = generate_search_queries_for_brief(brief, max_queries=MAX_PROPOSED_QUERIES)
    provider = search_provider or get_configured_search_provider()
    run = _get_or_create_web_research_run(db, brief)
    trace_run_id = run.id

    _trace(
        "search_queries_generated",
        run_id=run.id,
        message="Generated bounded discovery queries.",
        payload={"query_count": len(queries), "queries": [query.query for query in queries]},
    )
    _trace(
        "search_provider_called",
        run_id=run.id,
        message="Calling configured search provider.",
        payload={
            "provider": provider.provider_name,
            "query_count": len(queries),
            "max_results_per_query": MAX_SEARCH_RESULTS_PER_QUERY,
        },
    )

    search_results = provider.search(queries, max_results_per_query=MAX_SEARCH_RESULTS_PER_QUERY)
    for result in search_results:
        _trace(
            "search_result_collected",
            run_id=run.id,
            message="Collected candidate search result.",
            payload=result.as_dict(),
        )

    decision_records = triage_search_results(brief, search_results)
    triage_counts = Counter(record.decision for record in decision_records)
    skipped_urls: list[dict[str, str]] = []
    source_summaries: list[dict[str, object]] = []
    fetched_source_count = 0
    seen_urls: set[str] = set()
    decision_records_with_fetch: list[dict[str, object]] = []
    kept_fetch_slots_used = 0

    for record in decision_records:
        _trace(
            "search_result_triaged",
            run_id=run.id,
            message="Triaged candidate search result.",
            payload=record.as_dict(),
        )
        if record.decision == "keep":
            _trace(
                "search_result_kept",
                run_id=run.id,
                message="Keeping search result for validation and fetch.",
                payload=record.as_dict(),
            )
        else:
            skipped_urls.append({"url": record.url, "reason": record.reason})
            _trace(
                "search_result_rejected",
                run_id=run.id,
                message="Rejected search result before fetch.",
                payload=record.as_dict(),
            )
            decision_records_with_fetch.append(record.as_dict())
            continue

        if kept_fetch_slots_used >= MAX_FETCH_URLS:
            capped_reason = f"capped_urls_at_{MAX_FETCH_URLS}"
            skipped_urls.append({"url": record.url, "reason": capped_reason})
            decision_records_with_fetch.append({**record.as_dict(), "rejection_error": capped_reason})
            _trace(
                "url_rejected",
                run_id=run.id,
                message="Rejected kept result after reaching fetch budget.",
                payload={"url": record.url, "reason": capped_reason},
            )
            continue
        kept_fetch_slots_used += 1

        normalized_url, validation_error = validate_public_url(record.url)
        if validation_error or normalized_url is None:
            skipped_urls.append({"url": record.url, "reason": validation_error or "invalid_url"})
            updated = {**record.as_dict(), "rejection_error": validation_error or "invalid_url"}
            decision_records_with_fetch.append(updated)
            _trace(
                "url_rejected",
                run_id=run.id,
                message="Rejected kept result after URL validation.",
                payload={"url": record.url, "reason": validation_error or "invalid_url"},
            )
            continue

        if normalized_url in seen_urls:
            skipped_urls.append({"url": normalized_url, "reason": "duplicate_in_request"})
            updated = {**record.as_dict(), "rejection_error": "duplicate_in_request"}
            decision_records_with_fetch.append(updated)
            _trace(
                "url_rejected",
                run_id=run.id,
                message="Rejected duplicate kept result.",
                payload={"url": normalized_url, "reason": "duplicate_in_request"},
            )
            continue
        seen_urls.add(normalized_url)

        existing_source = db.scalar(select(Source).where(Source.run_id == run.id, Source.url == normalized_url))
        if existing_source is not None:
            skipped_urls.append({"url": normalized_url, "reason": "duplicate_existing_source"})
            updated = {**record.as_dict(), "rejection_error": "duplicate_existing_source"}
            decision_records_with_fetch.append(updated)
            _trace(
                "url_rejected",
                run_id=run.id,
                message="Rejected already captured source.",
                payload={"url": normalized_url, "reason": "duplicate_existing_source"},
            )
            continue

        _trace(
            "search_source_fetch_started",
            run_id=run.id,
            message="Fetching kept public source.",
            payload={"url": normalized_url, "query": record.query, "provider": record.provider},
        )
        _trace(
            "tool_call_started",
            run_id=run.id,
            message="Fetching public web source.",
            payload={"tool_name": "fetch_public_url", "url": normalized_url},
        )
        fetch_result = fetch_public_url(normalized_url)
        _trace(
            "tool_call_completed",
            run_id=run.id,
            message="Completed public web fetch.",
            payload={
                "tool_name": "fetch_public_url",
                "url": normalized_url,
                "success": bool(fetch_result.get("success")),
                "status_code": fetch_result.get("status_code"),
                "error": fetch_result.get("error"),
            },
        )
        _trace(
            "search_source_fetch_completed",
            run_id=run.id,
            message="Completed kept source fetch.",
            payload={
                "url": normalized_url,
                "success": bool(fetch_result.get("success")),
                "status_code": fetch_result.get("status_code"),
                "error": fetch_result.get("error"),
            },
        )
        if not fetch_result.get("success"):
            fetch_error = str(fetch_result.get("error") or "fetch_failed")
            skipped_urls.append({"url": normalized_url, "reason": fetch_error})
            decision_records_with_fetch.append({**record.as_dict(), "rejection_error": fetch_error})
            continue

        content_type = str(fetch_result.get("content_type") or "")
        title, extracted_text, extraction_error = extract_title_and_text(
            fetch_result.get("body") or b"",
            content_type,
        )

        source = Source(
            run_id=run.id,
            title=title or record.title,
            source_type=record.source_type,
            url=normalized_url,
            origin=parse.urlparse(normalized_url).hostname,
            captured_at=datetime.now(timezone.utc),
            summary=(extracted_text[:400] if extracted_text else (record.snippet or None)),
            metadata_json={
                "brief_id": brief.id,
                "fetched_by": "apd_web_research",
                "fetched_at": _iso_now(),
                "query": record.query,
                "provider": record.provider,
                "rank": record.rank,
                "triage_decision": record.decision,
                "triage_reason": record.reason,
                "source_type_guess": record.source_type,
                "status": "fetched",
                "content_type": content_type,
                "extraction_error": extraction_error,
            },
        )
        db.add(source)
        db.flush()

        excerpt_id = None
        if extracted_text:
            excerpt = EvidenceExcerpt(
                run_id=run.id,
                source_id=source.id,
                excerpt_text=extracted_text[:MAX_EXCERPT_TEXT_CHARS],
                location_reference="fetched_page_text",
                excerpt_type="web_capture",
                metadata_json={
                    "brief_id": brief.id,
                    "fetched_by": "apd_web_research",
                    "query": record.query,
                    "provider": record.provider,
                },
            )
            db.add(excerpt)
            db.flush()
            excerpt_id = excerpt.id

        fetched_source_count += 1
        source_summaries.append(
            {
                "source_id": source.id,
                "excerpt_id": excerpt_id,
                "url": source.url,
                "title": source.title,
                "content_type": content_type,
                "query": record.query,
                "provider": record.provider,
                "decision_reason": record.reason,
            }
        )
        decision_records_with_fetch.append({**record.as_dict(), "fetched": True})
        _trace(
            "source_fetched",
            run_id=run.id,
            message="Fetched and stored public web source.",
            payload={
                "capture_run_id": run.id,
                "source_id": source.id,
                "excerpt_id": excerpt_id,
                "url": source.url,
                "content_type": content_type,
                "extraction_error": extraction_error,
            },
        )

    run.source_count = db.scalar(select(func.count()).select_from(Source).where(Source.run_id == run.id)) or 0
    db.add(run)
    finished_at = _iso_now()

    warnings: list[str] = []
    weak_discovery_warning: str | None = None
    if triage_counts.get("keep", 0) > MAX_FETCH_URLS:
        warnings.append(f"capped_urls_at_{MAX_FETCH_URLS}")
    if fetched_source_count < 2:
        weak_discovery_warning = (
            f"Weak discovery: fetched {fetched_source_count} sources from {len(search_results)} candidates."
        )
        warnings.append(weak_discovery_warning)
        _trace(
            "discovery_weak_warning",
            run_id=run.id,
            message="Discovery completed with weak source coverage.",
            payload={
                "candidate_result_count": len(search_results),
                "kept_count": triage_counts.get("keep", 0),
                "fetched_source_count": fetched_source_count,
            },
        )

    status = "completed" if fetched_source_count > 0 else ("no_search_results" if not search_results else "no_valid_urls")
    summary = {
        "query_count": len(queries),
        "candidate_result_count": len(search_results),
        "kept_count": triage_counts.get("keep", 0),
        "discard_count": triage_counts.get("discard", 0),
        "bait_count": triage_counts.get("bait", 0),
        "uncertain_count": triage_counts.get("uncertain", 0),
        "fetched_source_count": fetched_source_count,
        "skipped_count": len(skipped_urls),
        "weak_discovery_warning": weak_discovery_warning,
    }
    _trace(
        "discovery_completed",
        run_id=run.id,
        message="Structured source discovery completed.",
        payload={"status": status, **summary},
    )
    _trace(
        "phase_completed",
        run_id=run.id,
        message="Web discovery completed.",
        payload={"status": status, "capture_run_id": run.id, **summary},
    )

    result = {
        "success": fetched_source_count > 0,
        "status": status,
        "started_at": started_at,
        "finished_at": finished_at,
        "errors": [],
        "warnings": warnings,
        "search_provider": provider.provider_name,
        "proposed_query_count": len(queries),
        "proposed_url_count": len(search_results),
        "candidate_result_count": len(search_results),
        "fetched_source_count": fetched_source_count,
        "triage_counts": {
            "keep": triage_counts.get("keep", 0),
            "discard": triage_counts.get("discard", 0),
            "bait": triage_counts.get("bait", 0),
            "uncertain": triage_counts.get("uncertain", 0),
        },
        "discovery_summary": summary,
        "weak_discovery_warning": weak_discovery_warning,
        "skipped_urls": skipped_urls[:10],
        "sources": source_summaries[:10],
        "queries": [{"query": query.query, "rationale": query.rationale} for query in queries],
        "candidate_results": search_results_to_dicts(search_results)[:10],
        "candidate_decisions": decision_records_with_fetch[:10],
        "web_research_run_id": run.id,
        "trace_correlation_id": trace_correlation_id,
    }
    if fetched_source_count == 0:
        result["errors"] = [
            "No kept public URLs were fetched. Discovery results and rejection reasons were stored for review."
        ]

    meta = dict(brief.metadata_json or {})
    meta["web_research_run_id"] = run.id
    brief.metadata_json = meta
    db.add(brief)
    db.commit()
    db.refresh(brief)
    return result
