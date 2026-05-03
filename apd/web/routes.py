from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from apd.app.db import SessionLocal
from apd.domain.models import DecisionValue, ReviewStatus, ReviewTargetType
from apd.web.mutations import (
    add_review_note,
    update_candidate_review_status,
    update_claim_review_status,
    update_run_decision,
)
from apd.services.report_export import export_run_markdown_report
from apd.services.research_brief_service import (
    create_brief,
    get_brief,
    list_briefs,
)
from apd.services.research_brief_ideation import generate_brief_idea_with_ollama, get_brief_ideation_themes
from apd.services.sample_research_briefs import get_sample_research_briefs
from apd.services.model_execution_settings import get_model_execution_settings, save_model_execution_settings
from apd.services.research_search import resolve_configured_search_provider
from apd.services.research_execution_ollama import (
    execute_research_brief_ollama_components,
    execute_research_brief_ollama_components_grounded,
    execute_research_brief_ollama,
    get_ollama_execution_config,
)
from apd.services.research_execution_stub import execute_research_brief_stub
from apd.services.research_trace import create_trace_correlation_id, list_research_trace_events
from apd.services.web_research import get_grounding_source_packet_for_brief, run_web_research_for_brief
from apd.web.queries import get_recent_runs, get_run_detail

_TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

router = APIRouter()


def _get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _save_last_execution(db: Session, brief, execution_data: dict) -> None:
    meta = dict(brief.metadata_json or {})
    meta["last_execution"] = dict(execution_data)
    brief.metadata_json = meta
    db.add(brief)
    db.commit()
    db.refresh(brief)


def _prefixed_messages(prefix: str, values: list[str] | None) -> list[str]:
    return [f"{prefix}: {value}" for value in (values or [])[:5]]


def _web_discovery_phase_data(result: dict) -> dict:
    return {
        "status": result.get("status"),
        "started_at": result.get("started_at"),
        "finished_at": result.get("finished_at"),
        "search_provider": result.get("search_provider"),
        "search_provider_setup_required": result.get("search_provider_setup_required"),
        "proposed_query_count": result.get("proposed_query_count", 0),
        "proposed_url_count": result.get("proposed_url_count", 0),
        "candidate_result_count": result.get("candidate_result_count", result.get("proposed_url_count", 0)),
        "fetched_source_count": result.get("fetched_source_count", 0),
        "triage_counts": dict(result.get("triage_counts") or {}),
        "discovery_summary": dict(result.get("discovery_summary") or {}),
        "weak_discovery_warning": result.get("weak_discovery_warning"),
        "queries": list(result.get("queries") or [])[:10],
        "candidate_results": list(result.get("candidate_results") or [])[:10],
        "candidate_decisions": list(result.get("candidate_decisions") or [])[:10],
        "sources": list(result.get("sources") or [])[:10],
        "skipped_urls": list(result.get("skipped_urls") or [])[:10],
        "errors": [str(value) for value in (result.get("errors") or [])][:5],
        "warnings": [str(value) for value in (result.get("warnings") or [])][:5],
        "capture_run_id": result.get("web_research_run_id"),
    }


def _component_execution_phase_data(result: dict) -> dict:
    return {
        "status": result.get("status"),
        "started_at": result.get("started_at"),
        "finished_at": result.get("finished_at"),
        "run_id": result.get("run_id"),
        "last_phase": result.get("last_phase"),
        "attempts_by_phase": dict(result.get("attempts_by_phase") or {}),
        "errors": [str(value) for value in (result.get("errors") or [])][:5],
        "warnings": [str(value) for value in (result.get("warnings") or [])][:5],
        "grounding_status": result.get("grounding_status"),
        "grounding_errors": [str(value) for value in (result.get("grounding_errors") or [])][:5],
        "grounding_source_count": result.get("grounding_source_count"),
        "grounding_excerpt_count": result.get("grounding_excerpt_count"),
    }


def _get_last_execution_trace_events(db: Session, brief) -> list:
    execution = (brief.metadata_json or {}).get("last_execution") or {}
    correlation_id = str(execution.get("trace_correlation_id") or "").strip()
    if not correlation_id:
        return []
    return list_research_trace_events(
        db,
        brief_id=brief.id,
        correlation_id=correlation_id,
        limit=120,
    )


def _build_web_assisted_execution_result(
    *,
    model: str,
    started_at: str,
    web_discovery_result: dict,
    component_result: dict,
    trace_correlation_id: str | None = None,
) -> dict:
    errors = _prefixed_messages("web_discovery", web_discovery_result.get("errors"))
    errors.extend(_prefixed_messages("component_execution", component_result.get("errors")))

    warnings = _prefixed_messages("web_discovery", web_discovery_result.get("warnings"))
    warnings.extend(_prefixed_messages("component_execution", component_result.get("warnings")))

    result = {
        "success": bool(component_result.get("success")),
        "provider": "ollama-components",
        "model": model,
        "mode": "web_assisted_component_execution",
        "status": component_result.get("status"),
        "started_at": started_at,
        "finished_at": _iso_now(),
        "errors": errors[:5],
        "warnings": warnings[:5],
        "run_id": component_result.get("run_id"),
        "web_discovery": _web_discovery_phase_data(web_discovery_result),
        "component_execution": _component_execution_phase_data(component_result),
        "source_grounding_status": component_result.get("grounding_status") or "unknown",
        "source_grounding_deferred_issue": 63,
        "source_grounding_note": (
            "APD used captured sources as grounding context and validated source/excerpt IDs, "
            "but this does not prove grounded claims are true. Human review is still required."
        ),
    }
    if trace_correlation_id:
        result["trace_correlation_id"] = trace_correlation_id
    return result


def _build_component_execution_skipped_result(reason: str) -> dict:
    return {
        "success": False,
        "status": "skipped",
        "started_at": _iso_now(),
        "finished_at": _iso_now(),
        "errors": [],
        "warnings": [reason],
        "run_id": None,
        "last_phase": None,
        "attempts_by_phase": {},
        "grounding_status": "not_started",
        "grounding_errors": [],
        "grounding_source_count": 0,
        "grounding_excerpt_count": 0,
    }


@router.get("/", response_class=RedirectResponse, include_in_schema=False)
def index():
    return RedirectResponse(url="/runs")


@router.get("/runs", response_class=HTMLResponse)
def recent_runs(request: Request, db: Session = Depends(_get_db)):
    runs = get_recent_runs(db)
    return templates.TemplateResponse(
        request,
        "runs_list.html",
        {"runs": runs},
    )


@router.get("/runs/{run_id}", response_class=HTMLResponse)
def run_detail(run_id: int, request: Request, db: Session = Depends(_get_db)):
    detail = get_run_detail(db, run_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return templates.TemplateResponse(
        request,
        "run_detail.html",
        {
            "run": detail["run"],
            "detail": detail,
            "review_statuses": [s.value for s in ReviewStatus],
            "decision_values": [d.value for d in DecisionValue],
        },
    )


# --- Review status updates ---

@router.post("/runs/{run_id}/claims/{claim_id}/review", response_class=RedirectResponse)
def update_claim_review(
    run_id: int,
    claim_id: int,
    review_status: str = Form(...),
    note: str = Form(""),
    db: Session = Depends(_get_db),
):
    try:
        status = ReviewStatus(review_status)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid review status: {review_status}")
    result = update_claim_review_status(db, run_id, claim_id, status, note_text=note or None)
    if result is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    return RedirectResponse(url=f"/runs/{run_id}#claims", status_code=303)


@router.post("/runs/{run_id}/candidates/{candidate_id}/review", response_class=RedirectResponse)
def update_candidate_review(
    run_id: int,
    candidate_id: int,
    review_status: str = Form(...),
    note: str = Form(""),
    db: Session = Depends(_get_db),
):
    try:
        status = ReviewStatus(review_status)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid review status: {review_status}")
    result = update_candidate_review_status(db, run_id, candidate_id, status, note_text=note or None)
    if result is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return RedirectResponse(url=f"/runs/{run_id}#candidates", status_code=303)


# --- Standalone review note endpoints ---

@router.post("/runs/{run_id}/claims/{claim_id}/notes", response_class=RedirectResponse)
def add_claim_note(
    run_id: int,
    claim_id: int,
    note: str = Form(...),
    db: Session = Depends(_get_db),
):
    if not note.strip():
        raise HTTPException(status_code=422, detail="Note text required")
    result = add_review_note(db, run_id, ReviewTargetType.CLAIM, claim_id, note)
    if result is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return RedirectResponse(url=f"/runs/{run_id}#claims", status_code=303)


@router.post("/runs/{run_id}/candidates/{candidate_id}/notes", response_class=RedirectResponse)
def add_candidate_note(
    run_id: int,
    candidate_id: int,
    note: str = Form(...),
    db: Session = Depends(_get_db),
):
    if not note.strip():
        raise HTTPException(status_code=422, detail="Note text required")
    result = add_review_note(db, run_id, ReviewTargetType.CANDIDATE, candidate_id, note)
    if result is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return RedirectResponse(url=f"/runs/{run_id}#candidates", status_code=303)


# --- Run decision update ---

@router.post("/runs/{run_id}/decision", response_class=RedirectResponse)
def update_decision(
    run_id: int,
    decision: str = Form(...),
    rationale: str = Form(""),
    db: Session = Depends(_get_db),
):
    try:
        decision_value = DecisionValue(decision)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid decision: {decision}")
    result = update_run_decision(db, run_id, decision_value, rationale=rationale or None)
    if result is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return RedirectResponse(url=f"/runs/{run_id}", status_code=303)


# --- Run markdown export ---

@router.post("/runs/{run_id}/export-report", response_class=RedirectResponse)
def export_report(run_id: int, db: Session = Depends(_get_db)):
    result = export_run_markdown_report(db, run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return RedirectResponse(url=f"/runs/{run_id}#artifacts", status_code=303)


# ── Research briefs ────────────────────────────────────────────────────────────


@router.get("/briefs", response_class=HTMLResponse)
def briefs_list(request: Request, db: Session = Depends(_get_db)):
    briefs = list_briefs(db)
    return templates.TemplateResponse(
        request,
        "briefs_list.html",
        {"briefs": briefs},
    )


@router.get("/briefs/new", response_class=HTMLResponse)
def briefs_new(request: Request, db: Session = Depends(_get_db)):
    ollama_config, missing_ollama_env = get_ollama_execution_config(db)
    return templates.TemplateResponse(
        request,
        "brief_new.html",
        {
            "sample_briefs": get_sample_research_briefs(),
            "ideation_themes": get_brief_ideation_themes(),
            "ideation_enabled": ollama_config is not None,
            "ideation_disabled_reason": (
                "Configure local Ollama model settings to enable fresh idea generation."
                if ollama_config is None
                else None
            ),
            "ideation_model": ollama_config.model if ollama_config else None,
            "missing_ollama_env": missing_ollama_env,
        },
    )


@router.post("/briefs/ideate")
async def briefs_ideate(request: Request, db: Session = Depends(_get_db)):
    payload = await request.json()
    selected_themes = payload.get("selected_themes") if isinstance(payload, dict) else None
    if selected_themes is not None and not isinstance(selected_themes, list):
        return JSONResponse(
            {"success": False, "error": "Invalid ideation request payload."},
            status_code=422,
        )

    idea, ideation_error = generate_brief_idea_with_ollama(
        db,
        [str(value) for value in selected_themes] if selected_themes is not None else None,
    )
    if ideation_error:
        status_code = 503 if "not configured" in ideation_error.lower() else 400
        return JSONResponse({"success": False, "error": ideation_error}, status_code=status_code)

    return JSONResponse({"success": True, **idea})


@router.post("/briefs", response_class=RedirectResponse)
def briefs_create(
    title: str = Form(...),
    research_question: str = Form(...),
    constraints: str = Form(""),
    desired_depth: str = Form(""),
    expected_outputs: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(_get_db),
):
    if not title.strip() or not research_question.strip():
        raise HTTPException(status_code=422, detail="Title and research question are required")
    brief = create_brief(
        db,
        title=title,
        research_question=research_question,
        constraints=constraints or None,
        desired_depth=desired_depth or None,
        expected_outputs=expected_outputs or None,
        notes=notes or None,
    )
    return RedirectResponse(url=f"/briefs/{brief.id}", status_code=303)


@router.get("/briefs/{brief_id}", response_class=HTMLResponse)
def brief_detail(brief_id: int, request: Request, db: Session = Depends(_get_db)):
    brief = get_brief(db, brief_id)
    if brief is None:
        raise HTTPException(status_code=404, detail="Research brief not found")
    ollama_config, missing_ollama_env = get_ollama_execution_config(db)
    search_provider_resolution = resolve_configured_search_provider(db)
    grounding_packet = get_grounding_source_packet_for_brief(db, brief)
    trace_events = _get_last_execution_trace_events(db, brief)
    return templates.TemplateResponse(
        request,
        "brief_detail.html",
        {
            "brief": brief,
            "ollama_ready": ollama_config is not None,
            "missing_ollama_env": missing_ollama_env,
            "ollama_model": ollama_config.model if ollama_config else None,
            "search_provider_ready": search_provider_resolution.is_live_provider and search_provider_resolution.is_configured,
            "search_provider_name": search_provider_resolution.provider_name,
            "search_provider_setup_message": search_provider_resolution.setup_required_message,
            "grounded_source_count": len(grounding_packet.sources),
            "grounded_excerpt_count": len(grounding_packet.evidence_excerpts),
            "trace_events": trace_events,
        },
    )


@router.get("/settings/model-execution", response_class=HTMLResponse)
def settings_model_execution(request: Request, db: Session = Depends(_get_db)):
    settings = get_model_execution_settings(db)
    return templates.TemplateResponse(
        request,
        "settings_model_execution.html",
        {"settings": settings},
    )


@router.post("/settings/model-execution", response_class=RedirectResponse)
def settings_model_execution_save(
    provider: str = Form("ollama"),
    ollama_base_url: str = Form(""),
    ollama_model: str = Form(""),
    ollama_timeout_seconds: int = Form(120),
    ollama_keep_alive: str = Form("0"),
    component_repair_attempts: int = Form(1),
    research_search_provider: str = Form("none"),
    brave_search_base_url: str = Form("https://api.search.brave.com/res/v1/web/search"),
    enabled: str = Form("on"),
    db: Session = Depends(_get_db),
):
    data = {
        "provider": provider,
        "ollama_base_url": ollama_base_url or None,
        "ollama_model": ollama_model or None,
        "ollama_timeout_seconds": ollama_timeout_seconds,
        "ollama_keep_alive": int(ollama_keep_alive) if str(ollama_keep_alive).isdigit() else ollama_keep_alive,
        "component_repair_attempts": min(max(int(component_repair_attempts), 0), 3),
        "research_search_provider": research_search_provider,
        "brave_search_base_url": brave_search_base_url or None,
        "enabled": bool(enabled),
    }
    save_model_execution_settings(db, data)
    return RedirectResponse(url="/settings/model-execution", status_code=303)


@router.post("/briefs/{brief_id}/start-research", response_class=RedirectResponse)
def start_research(brief_id: int, db: Session = Depends(_get_db)):
    return start_research_ollama_components(brief_id, db)


@router.post("/briefs/{brief_id}/start-research-stub", response_class=RedirectResponse)
def start_research_stub(brief_id: int, db: Session = Depends(_get_db)):
    brief = get_brief(db, brief_id)
    if brief is None:
        raise HTTPException(status_code=404, detail="Research brief not found")

    _save_last_execution(
        db,
        brief,
        {
            "provider": "stub",
            "status": "running",
            "started_at": _iso_now(),
            "errors": [],
            "warnings": [],
            "run_id": None,
        },
    )

    result = execute_research_brief_stub(db, brief)
    _save_last_execution(
        db,
        brief,
        {
            "provider": "stub",
            "status": "imported" if result.get("success") else "failed",
            "started_at": (brief.metadata_json or {}).get("last_execution", {}).get("started_at") or _iso_now(),
            "finished_at": _iso_now(),
            "errors": [str(e) for e in (result.get("errors") or [])][:5],
            "warnings": [str(w) for w in (result.get("warnings") or [])][:5],
            "run_id": result.get("run_id"),
        },
    )

    if result.get("success") and result.get("run_id"):
        return RedirectResponse(url=f"/runs/{result.get('run_id')}", status_code=303)

    # On failure, return to brief detail so the UI can show last_execution with errors
    return RedirectResponse(url=f"/briefs/{brief.id}", status_code=303)


@router.post("/briefs/{brief_id}/research-web", response_class=RedirectResponse)
def research_web_sources(brief_id: int, db: Session = Depends(_get_db)):
    brief = get_brief(db, brief_id)
    if brief is None:
        raise HTTPException(status_code=404, detail="Research brief not found")

    trace_correlation_id = create_trace_correlation_id(brief_id=brief.id)
    result = run_web_research_for_brief(db, brief, trace_correlation_id=trace_correlation_id)
    config, _ = get_ollama_execution_config(db)
    _save_last_execution(
        db,
        brief,
        {
            "success": bool(result.get("success")),
            "provider": "ollama-web-discovery",
            "model": config.model if config is not None else None,
            "mode": "web_discovery_phase",
            "status": result.get("status"),
            "started_at": result.get("started_at") or _iso_now(),
            "finished_at": result.get("finished_at") or _iso_now(),
            "errors": _prefixed_messages("web_discovery", result.get("errors"))[:5],
            "warnings": _prefixed_messages("web_discovery", result.get("warnings"))[:5],
            "run_id": None,
            "trace_correlation_id": result.get("trace_correlation_id") or trace_correlation_id,
            "web_discovery": _web_discovery_phase_data(result),
            "source_grounding_status": "not_started",
            "source_grounding_deferred_issue": 63,
            "source_grounding_note": (
                "Web discovery captured sources for later grounded component execution. "
                "APD validates source and excerpt IDs during grounded execution, but does not verify truth."
            ),
        },
    )
    return RedirectResponse(url=f"/briefs/{brief.id}", status_code=303)


@router.post("/briefs/{brief_id}/start-grounded-research-ollama-components", response_class=RedirectResponse)
def start_research_ollama_components_grounded(brief_id: int, db: Session = Depends(_get_db)):
    brief = get_brief(db, brief_id)
    if brief is None:
        raise HTTPException(status_code=404, detail="Research brief not found")

    config, missing_env = get_ollama_execution_config(db)
    if config is None:
        _save_last_execution(
            db,
            brief,
            {
                "provider": "ollama-components-grounded",
                "status": "config_missing",
                "started_at": _iso_now(),
                "finished_at": _iso_now(),
                "errors": [f"Missing required env: {value}" for value in missing_env],
                "warnings": [],
                "run_id": None,
                "source_grounding_status": "config_missing",
            },
        )
        return RedirectResponse(url=f"/briefs/{brief.id}", status_code=303)

    started_at = _iso_now()
    trace_correlation_id = create_trace_correlation_id(brief_id=brief.id)
    _save_last_execution(
        db,
        brief,
        {
            "provider": "ollama-components-grounded",
            "model": config.model,
            "status": "running",
            "started_at": started_at,
            "errors": [],
            "warnings": [],
            "run_id": None,
            "mode": "grounded_component_execution",
            "trace_correlation_id": trace_correlation_id,
            "component_execution": {"status": "pending"},
            "source_grounding_status": "running",
        },
    )

    result = execute_research_brief_ollama_components_grounded(
        db,
        brief,
        trace_correlation_id=trace_correlation_id,
    )
    _save_last_execution(db, brief, result)

    if result.get("success") and result.get("run_id"):
        return RedirectResponse(url=f"/runs/{result.get('run_id')}", status_code=303)
    return RedirectResponse(url=f"/briefs/{brief.id}", status_code=303)


@router.post("/briefs/{brief_id}/start-research-ollama", response_class=RedirectResponse)
def start_research_ollama(brief_id: int, db: Session = Depends(_get_db)):
    brief = get_brief(db, brief_id)
    if brief is None:
        raise HTTPException(status_code=404, detail="Research brief not found")

    config, missing_env = get_ollama_execution_config(db)
    if config is None:
        _save_last_execution(
            db,
            brief,
            {
                "provider": "ollama",
                "status": "config_missing",
                "started_at": _iso_now(),
                "finished_at": _iso_now(),
                "errors": [f"Missing required env: {value}" for value in missing_env],
                "warnings": [],
                "run_id": None,
            },
        )
        return RedirectResponse(url=f"/briefs/{brief.id}", status_code=303)

    trace_correlation_id = create_trace_correlation_id(brief_id=brief.id)
    _save_last_execution(
        db,
        brief,
        {
            "provider": "ollama",
            "model": config.model,
            "status": "running",
            "started_at": _iso_now(),
            "errors": [],
            "warnings": [],
            "run_id": None,
            "trace_correlation_id": trace_correlation_id,
        },
    )

    result = execute_research_brief_ollama(db, brief, trace_correlation_id=trace_correlation_id)
    _save_last_execution(db, brief, result)

    if result.get("success") and result.get("run_id"):
        return RedirectResponse(url=f"/runs/{result.get('run_id')}", status_code=303)

    return RedirectResponse(url=f"/briefs/{brief.id}", status_code=303)


@router.post("/briefs/{brief_id}/start-research-ollama-components", response_class=RedirectResponse)
def start_research_ollama_components(brief_id: int, db: Session = Depends(_get_db)):
    brief = get_brief(db, brief_id)
    if brief is None:
        raise HTTPException(status_code=404, detail="Research brief not found")

    config, missing_env = get_ollama_execution_config(db)
    if config is None:
        _save_last_execution(
            db,
            brief,
            {
                "provider": "ollama-components",
                "status": "config_missing",
                "started_at": _iso_now(),
                "finished_at": _iso_now(),
                "errors": [f"Missing required env: {value}" for value in missing_env],
                "warnings": [],
                "run_id": None,
            },
        )
        return RedirectResponse(url=f"/briefs/{brief.id}", status_code=303)

    started_at = _iso_now()
    trace_correlation_id = create_trace_correlation_id(brief_id=brief.id)
    _save_last_execution(
        db,
        brief,
        {
            "provider": "ollama-components",
            "model": config.model,
            "status": "running",
            "started_at": started_at,
            "errors": [],
            "warnings": [],
            "run_id": None,
            "mode": "web_assisted_component_execution",
            "trace_correlation_id": trace_correlation_id,
            "web_discovery": {"status": "pending"},
            "component_execution": {"status": "pending"},
            "source_grounding_status": "pending",
        },
    )

    web_discovery_result = run_web_research_for_brief(
        db,
        brief,
        trace_correlation_id=trace_correlation_id,
    )
    if web_discovery_result.get("success"):
        component_result = execute_research_brief_ollama_components_grounded(
            db,
            brief,
            trace_correlation_id=trace_correlation_id,
        )
    else:
        component_result = _build_component_execution_skipped_result(
            "Skipped grounded synthesis because source discovery did not produce captured sources."
        )
    result = _build_web_assisted_execution_result(
        model=config.model,
        started_at=started_at,
        web_discovery_result=web_discovery_result,
        component_result=component_result,
        trace_correlation_id=trace_correlation_id,
    )
    if not web_discovery_result.get("success"):
        result["status"] = web_discovery_result.get("status")
        result["success"] = False
        result["source_grounding_status"] = "not_started"
    _save_last_execution(db, brief, result)

    if result.get("success") and result.get("run_id"):
        return RedirectResponse(url=f"/runs/{result.get('run_id')}", status_code=303)
    return RedirectResponse(url=f"/briefs/{brief.id}", status_code=303)

