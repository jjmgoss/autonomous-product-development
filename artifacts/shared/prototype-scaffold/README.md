# __PROJECT_TITLE__

This project was initialized from the shared prototype scaffold.

Prototype class: working demo

## Purpose

Replace this section with one paragraph naming the first buyer, first workflow, first wedge, and prototype success event.

## What Works

- local app entrypoint
- deterministic demo data
- health check route
- one smoke test and one behavior-oriented test

## What Is Stubbed Or Fake

- replace this list with the components that are fixture-backed, mocked, or intentionally omitted

## Known Rough Edges

- replace this list with the rough parts that are acceptable at prototype stage

## Run Locally

```bash
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Then open `http://127.0.0.1:8000`.

## Verify Locally

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Health Check

`GET /healthz`

## Demo Data

Seed data lives in `demo_data.json`.

## Next Milestone

Replace this section with the next smallest step after the current prototype works.