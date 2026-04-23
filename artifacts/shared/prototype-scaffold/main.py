from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse


PROJECT_ROOT = Path(__file__).resolve().parent
DEMO_DATA_PATH = PROJECT_ROOT / "demo_data.json"


def load_demo_data() -> dict:
    return json.loads(DEMO_DATA_PATH.read_text(encoding="utf-8"))


app = FastAPI(title="__PROJECT_TITLE__")


@app.get("/", response_class=HTMLResponse)
async def home() -> HTMLResponse:
    data = load_demo_data()
    items = "".join(
        f"<li><a href='/items/{item['id']}'>{item['label']}</a> - {item['status']}</li>"
        for item in data["items"]
    )
    return HTMLResponse(
        f"""
        <!doctype html>
        <html lang='en'>
        <head>
          <meta charset='utf-8'>
          <meta name='viewport' content='width=device-width, initial-scale=1'>
          <title>{data['project_title']}</title>
        </head>
        <body>
          <main>
            <h1>{data['project_title']}</h1>
            <p>Replace this scaffold homepage with the product-specific happy path.</p>
            <ul>{items}</ul>
          </main>
        </body>
        </html>
        """
    )


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    load_demo_data()
    return {"status": "ok"}


@app.get("/items/{item_id}")
async def item_detail(item_id: str) -> dict:
    data = load_demo_data()
    for item in data["items"]:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")