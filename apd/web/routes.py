from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from apd.app.db import SessionLocal
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
        {"run": detail["run"], "detail": detail},
    )
