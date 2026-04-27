from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from apd.web.routes import router as web_router

_STATIC_DIR = Path(__file__).parent.parent / "web" / "static"

app = FastAPI(title="APD Local App")
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
app.include_router(web_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
