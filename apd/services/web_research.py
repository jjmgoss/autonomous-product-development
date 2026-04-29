from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass
import html
import ipaddress
import json
import re
from urllib import error, parse, request

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apd.domain.models import EvidenceExcerpt, ResearchBrief, Run, RunPhase, Source
from apd.services.research_execution_ollama import (
    _build_generate_payload,
    _ollama_generate,
    _unload_ollama_model,
    extract_json_object_from_model_output,
    get_ollama_execution_config,
)

SCHEMA_VERSION = "1.0"
MAX_PROPOSED_QUERIES = 5
MAX_FETCH_URLS = 5
FETCH_TIMEOUT_SECONDS = 10
MAX_RESPONSE_BYTES = 1_000_000
MAX_EXTRACTED_TEXT_CHARS = 12_000
MAX_EXCERPT_TEXT_CHARS = 8_000
MAX_GROUNDED_PACKET_SOURCES = 5
MAX_GROUNDED_PACKET_EXCERPTS = 10
MAX_GROUNDED_PACKET_EXCERPT_CHARS = 1500
MAX_GROUNDED_PACKET_TOTAL_CHARS = 10000
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


def run_web_research_for_brief(db: Session, brief: ResearchBrief) -> dict[str, object]:
    config, missing = get_ollama_execution_config(db)
    started_at = _iso_now()
    if config is None:
        return {
            "success": False,
            "status": "config_missing",
            "started_at": started_at,
            "finished_at": started_at,
            "errors": [f"Missing required env: {value}" for value in missing],
            "warnings": [],
            "proposed_query_count": 0,
            "proposed_url_count": 0,
            "fetched_source_count": 0,
            "skipped_urls": [],
            "sources": [],
        }

    prompt = build_web_research_target_prompt(brief)
    payload = _build_generate_payload(config, prompt, during_execution=True)
    try:
        response_data, call_error = _ollama_generate(config, payload)
        if call_error:
            finished_at = _iso_now()
            return {
                "success": False,
                "status": "provider_error",
                "started_at": started_at,
                "finished_at": finished_at,
                "errors": [call_error],
                "warnings": [],
                "proposed_query_count": 0,
                "proposed_url_count": 0,
                "fetched_source_count": 0,
                "skipped_urls": [],
                "sources": [],
            }

        raw_output = str(response_data.get("response") or "")
        if not raw_output.strip():
            finished_at = _iso_now()
            return {
                "success": False,
                "status": "parse_failed",
                "started_at": started_at,
                "finished_at": finished_at,
                "errors": ["provider_error: empty_ollama_response"],
                "warnings": [],
                "proposed_query_count": 0,
                "proposed_url_count": 0,
                "fetched_source_count": 0,
                "skipped_urls": [],
                "sources": [],
            }

        targets, parse_error = parse_web_research_targets(raw_output)
        if parse_error or targets is None:
            finished_at = _iso_now()
            return {
                "success": False,
                "status": "parse_failed",
                "started_at": started_at,
                "finished_at": finished_at,
                "errors": [parse_error or "parse_failed: invalid_web_targets"],
                "warnings": [],
                "proposed_query_count": 0,
                "proposed_url_count": 0,
                "fetched_source_count": 0,
                "skipped_urls": [],
                "sources": [],
            }

        queries = list(targets.get("queries") or [])
        url_targets = list(targets.get("urls") or [])
        capped_queries = queries[:MAX_PROPOSED_QUERIES]
        capped_url_targets = url_targets[:MAX_FETCH_URLS]
        run = _get_or_create_web_research_run(db, brief)
        skipped_urls: list[dict[str, str]] = []
        source_summaries: list[dict[str, object]] = []
        fetched_source_count = 0
        seen_urls: set[str] = set()

        for url_target in capped_url_targets:
            raw_url = str(url_target.get("url") or "").strip()
            rationale = str(url_target.get("rationale") or "").strip()
            normalized_url, validation_error = validate_public_url(raw_url)
            if validation_error or normalized_url is None:
                skipped_urls.append({"url": raw_url, "reason": validation_error or "invalid_url"})
                continue
            if normalized_url in seen_urls:
                skipped_urls.append({"url": normalized_url, "reason": "duplicate_in_request"})
                continue
            seen_urls.add(normalized_url)

            existing_source = db.scalar(
                select(Source).where(Source.run_id == run.id, Source.url == normalized_url)
            )
            if existing_source is not None:
                skipped_urls.append({"url": normalized_url, "reason": "duplicate_existing_source"})
                continue

            fetch_result = fetch_public_url(normalized_url)
            if not fetch_result.get("success"):
                skipped_urls.append({"url": normalized_url, "reason": str(fetch_result.get("error") or "fetch_failed")})
                continue

            content_type = str(fetch_result.get("content_type") or "")
            title, extracted_text, extraction_error = extract_title_and_text(
                fetch_result.get("body") or b"",
                content_type,
            )

            source = Source(
                run_id=run.id,
                title=title,
                source_type="public_web",
                url=normalized_url,
                origin=parse.urlparse(normalized_url).hostname,
                captured_at=datetime.now(timezone.utc),
                summary=(extracted_text[:400] if extracted_text else None),
                metadata_json={
                    "brief_id": brief.id,
                    "fetched_by": "apd_web_research",
                    "fetched_at": _iso_now(),
                    "rationale": rationale,
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
                    metadata_json={"brief_id": brief.id, "fetched_by": "apd_web_research"},
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
                }
            )

        run.source_count = db.scalar(select(func.count()).select_from(Source).where(Source.run_id == run.id)) or 0
        db.add(run)
        finished_at = _iso_now()

        status = "completed" if fetched_source_count > 0 else "no_valid_urls"
        warnings: list[str] = []
        if len(queries) > MAX_PROPOSED_QUERIES:
            warnings.append(f"capped_queries_at_{MAX_PROPOSED_QUERIES}")
        if len(url_targets) > MAX_FETCH_URLS:
            warnings.append(f"capped_urls_at_{MAX_FETCH_URLS}")
        result = {
            "success": fetched_source_count > 0,
            "status": status,
            "started_at": started_at,
            "finished_at": finished_at,
            "errors": [],
            "warnings": warnings,
            "proposed_query_count": len(capped_queries),
            "proposed_url_count": len(capped_url_targets),
            "fetched_source_count": fetched_source_count,
            "skipped_urls": skipped_urls[:10],
            "sources": source_summaries[:10],
            "queries": capped_queries,
            "web_research_run_id": run.id,
        }
        if fetched_source_count == 0:
            result["errors"] = ["No valid public URLs were fetched. Proposed queries were stored for future work."]

        meta = dict(brief.metadata_json or {})
        meta["web_research_run_id"] = run.id
        brief.metadata_json = meta
        db.add(brief)
        db.commit()
        db.refresh(brief)
        return result
    finally:
        _unload_ollama_model(config)
