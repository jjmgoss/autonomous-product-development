from __future__ import annotations

from collections.abc import Mapping, Sequence
import re
from typing import Any
from urllib import parse
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from apd.domain.models import ResearchTraceEvent


MAX_TRACE_MESSAGE_CHARS = 400
MAX_TRACE_STRING_CHARS = 280
MAX_TRACE_DICT_ITEMS = 16
MAX_TRACE_LIST_ITEMS = 10
MAX_TRACE_RESULTS = 200
_REDACTED = "[redacted]"
_TRUNCATED = "[truncated]"
_WINDOWS_PATH_RE = re.compile(r"^[A-Za-z]:\\")
_UNIX_PATH_PREFIXES = ("/Users/", "/home/", "/var/", "/tmp/")
_SENSITIVE_KEY_FRAGMENTS = (
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "credential",
    "password",
    "secret",
    "session",
    "token",
)
_PATH_KEY_FRAGMENTS = ("path", "file")


def create_trace_correlation_id(*, brief_id: int | None = None) -> str:
    prefix = f"brief-{brief_id}" if brief_id is not None else "trace"
    return f"{prefix}-{uuid4().hex}"


def append_research_trace_event(
    db: Session,
    *,
    event_type: str,
    brief_id: int | None = None,
    run_id: int | None = None,
    correlation_id: str | None = None,
    phase: str | None = None,
    message: str | None = None,
    payload: Mapping[str, Any] | None = None,
) -> ResearchTraceEvent:
    event = ResearchTraceEvent(
        brief_id=brief_id,
        run_id=run_id,
        correlation_id=(correlation_id or "").strip() or None,
        phase=(phase or "").strip() or None,
        event_type=(event_type or "").strip(),
        message=_sanitize_message(message),
        payload_json=sanitize_trace_payload(payload) if payload is not None else None,
    )
    db.add(event)
    db.flush()
    return event


def list_research_trace_events(
    db: Session,
    *,
    brief_id: int | None = None,
    run_id: int | None = None,
    correlation_id: str | None = None,
    limit: int = MAX_TRACE_RESULTS,
) -> list[ResearchTraceEvent]:
    bounded_limit = max(1, min(limit, MAX_TRACE_RESULTS))
    stmt = select(ResearchTraceEvent)
    if brief_id is not None:
        stmt = stmt.where(ResearchTraceEvent.brief_id == brief_id)
    if run_id is not None:
        stmt = stmt.where(ResearchTraceEvent.run_id == run_id)
    if correlation_id:
        stmt = stmt.where(ResearchTraceEvent.correlation_id == correlation_id)
    stmt = stmt.order_by(ResearchTraceEvent.created_at.asc(), ResearchTraceEvent.id.asc()).limit(bounded_limit)
    return list(db.scalars(stmt))


def attach_run_to_trace_events(
    db: Session,
    *,
    correlation_id: str,
    run_id: int,
) -> int:
    if not correlation_id:
        return 0

    events = list(
        db.scalars(
            select(ResearchTraceEvent).where(
                ResearchTraceEvent.correlation_id == correlation_id,
                ResearchTraceEvent.run_id.is_(None),
            )
        )
    )
    for event in events:
        event.run_id = run_id
        db.add(event)
    db.flush()
    return len(events)


def sanitize_trace_payload(payload: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if payload is None:
        return None
    sanitized = _sanitize_value(dict(payload), key=None, depth=0)
    if isinstance(sanitized, dict):
        return sanitized
    return {"value": sanitized}


def _sanitize_message(message: str | None) -> str | None:
    if not message:
        return None
    collapsed = " ".join(str(message).split())
    if len(collapsed) <= MAX_TRACE_MESSAGE_CHARS:
        return collapsed
    return collapsed[: MAX_TRACE_MESSAGE_CHARS - 3].rstrip() + "..."


def _sanitize_value(value: Any, *, key: str | None, depth: int) -> Any:
    lower_key = (key or "").strip().lower()
    if depth >= 4:
        return _TRUNCATED

    if any(fragment in lower_key for fragment in _SENSITIVE_KEY_FRAGMENTS):
        return _REDACTED

    if value is None or isinstance(value, (bool, int, float)):
        return value

    if isinstance(value, Mapping):
        items = list(value.items())
        sanitized: dict[str, Any] = {}
        for child_key, child_value in items[:MAX_TRACE_DICT_ITEMS]:
            sanitized[str(child_key)] = _sanitize_value(child_value, key=str(child_key), depth=depth + 1)
        if len(items) > MAX_TRACE_DICT_ITEMS:
            sanitized["_truncated_items"] = len(items) - MAX_TRACE_DICT_ITEMS
        return sanitized

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        items = list(value)
        sanitized_items = [
            _sanitize_value(item, key=key, depth=depth + 1)
            for item in items[:MAX_TRACE_LIST_ITEMS]
        ]
        if len(items) > MAX_TRACE_LIST_ITEMS:
            sanitized_items.append(f"[{len(items) - MAX_TRACE_LIST_ITEMS} more items omitted]")
        return sanitized_items

    if isinstance(value, bytes):
        return f"[{len(value)} bytes omitted]"

    text = str(value).strip()
    if not text:
        return text

    if "url" in lower_key:
        return _sanitize_url(text)

    if any(fragment in lower_key for fragment in _PATH_KEY_FRAGMENTS) or _looks_like_local_path(text):
        return _REDACTED

    if len(text) <= MAX_TRACE_STRING_CHARS:
        return text
    return text[: MAX_TRACE_STRING_CHARS - 3].rstrip() + "..."


def _sanitize_url(value: str) -> str:
    try:
        parsed_url = parse.urlsplit(value)
    except Exception:
        return _REDACTED

    scheme = (parsed_url.scheme or "").lower()
    if scheme not in {"http", "https"}:
        return f"{scheme}://{_REDACTED}" if scheme else _REDACTED

    hostname = parsed_url.hostname or ""
    if not hostname:
        return _REDACTED

    netloc = hostname
    if parsed_url.port:
        default_port = 80 if scheme == "http" else 443
        if parsed_url.port != default_port:
            netloc = f"{hostname}:{parsed_url.port}"

    path = parsed_url.path or "/"
    safe_url = parse.urlunsplit((scheme, netloc, path, "", ""))
    if len(safe_url) <= MAX_TRACE_STRING_CHARS:
        return safe_url
    return safe_url[: MAX_TRACE_STRING_CHARS - 3].rstrip() + "..."


def _looks_like_local_path(value: str) -> bool:
    if _WINDOWS_PATH_RE.match(value):
        return True
    return value.startswith(_UNIX_PATH_PREFIXES)