from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
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
    generate_agent_prompt,
    get_brief,
    list_briefs,
)
from apd.services.research_execution_ollama import (
    execute_research_brief_ollama,
    get_ollama_execution_config,
)
from apd.services.research_execution_stub import execute_research_brief_stub
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
    meta = brief.metadata_json or {}
    meta["last_execution"] = execution_data
    brief.metadata_json = meta
    db.add(brief)
    db.commit()
    db.refresh(brief)


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
def briefs_new(request: Request):
    return templates.TemplateResponse(
        request,
        "brief_new.html",
        {},
    )


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
    prompt = generate_agent_prompt(brief)
    ollama_config, missing_ollama_env = get_ollama_execution_config()
    return templates.TemplateResponse(
        request,
        "brief_detail.html",
        {
            "brief": brief,
            "agent_prompt": prompt,
            "ollama_ready": ollama_config is not None,
            "missing_ollama_env": missing_ollama_env,
            "ollama_model": ollama_config.model if ollama_config else None,
        },
    )


@router.post("/briefs/{brief_id}/start-research", response_class=RedirectResponse)
def start_research(brief_id: int, db: Session = Depends(_get_db)):
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


@router.post("/briefs/{brief_id}/start-research-ollama", response_class=RedirectResponse)
def start_research_ollama(brief_id: int, db: Session = Depends(_get_db)):
    brief = get_brief(db, brief_id)
    if brief is None:
        raise HTTPException(status_code=404, detail="Research brief not found")

    config, missing_env = get_ollama_execution_config()
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
        },
    )

    result = execute_research_brief_ollama(db, brief)
    _save_last_execution(db, brief, result)

    if result.get("success") and result.get("run_id"):
        return RedirectResponse(url=f"/runs/{result.get('run_id')}", status_code=303)

    return RedirectResponse(url=f"/briefs/{brief.id}", status_code=303)

