from __future__ import annotations

import json
from io import BytesIO

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import pytest

from apd.app.db import Base
from apd.services.model_execution_settings import save_model_execution_settings
from apd.services.research_brief_service import create_brief
from apd.services.research_search import (
    BraveSearchProvider,
    EmptySearchProvider,
    SearchResult,
    SearchQuery,
    StaticSearchProvider,
    generate_search_queries_for_brief,
    load_static_search_provider,
    resolve_configured_search_provider,
)
from apd.services.research_source_triage import guess_source_type, triage_search_result


@pytest.fixture()
def db_session(tmp_path):
    db_path = tmp_path / "test_research_search.db"
    engine = create_engine(
        f"sqlite+pysqlite:///{db_path}",
        future=True,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with Session() as session:
        yield session


def test_generate_search_queries_for_brief_returns_bounded_queries(db_session):
    brief = create_brief(
        db_session,
        title="Customer support handoff pain",
        research_question="What evidence shows support teams lose time during ticket handoff?",
        constraints="Focus on public user complaints, docs, and issue trackers.",
    )

    queries = generate_search_queries_for_brief(brief)

    assert len(queries) == 5
    assert all(query.query for query in queries)
    assert queries[0].query.endswith("forum complaints")
    assert "customer support handoff pain" in queries[0].query
    assert queries[-1].query.endswith("reviews alternatives")


def test_static_search_provider_returns_deterministic_results_for_exact_queries():
    provider = StaticSearchProvider(
        {
            "customer support handoff pain forum complaints": [
                {
                    "title": "Forum thread",
                    "url": "https://example.com/forum-thread",
                    "snippet": "Agents lose context during escalations.",
                    "metadata_json": {"kind": "forum"},
                }
            ]
        },
        provider_name="static-fixture",
    )

    results = provider.search(
        [SearchQuery(query="customer support handoff pain forum complaints", rationale="pain")]
    )

    assert len(results) == 1
    assert results[0].provider == "static-fixture"
    assert results[0].query == "customer support handoff pain forum complaints"
    assert results[0].metadata_json["kind"] == "forum"


def test_empty_search_provider_returns_no_results():
    results = EmptySearchProvider().search([SearchQuery(query="abc", rationale="x")])
    assert results == []


def test_load_static_search_provider_reads_json_fixture(tmp_path):
    fixture_path = tmp_path / "search-fixture.json"
    fixture_path.write_text(
        json.dumps(
            {
                "customer support handoff pain github issues": [
                    {
                        "title": "GitHub issue",
                        "url": "https://github.com/org/repo/issues/1",
                        "snippet": "Context disappears between queues.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    provider = load_static_search_provider(fixture_path)
    results = provider.search([SearchQuery(query="customer support handoff pain github issues", rationale="issues")])

    assert len(results) == 1
    assert results[0].title == "GitHub issue"
    assert results[0].rank == 1


def test_triage_search_result_keeps_github_issues_for_pain_briefs(db_session):
    brief = create_brief(
        db_session,
        title="On-call handoff pain",
        research_question="What user pain shows up in incident handoff workflows?",
    )
    result = SearchResult(
        query="on-call handoff pain github issues",
        title="Incident handoff loses context",
        url="https://github.com/org/repo/issues/42",
        snippet="Users report manual triage and missing context during escalation.",
        provider="static",
        rank=1,
        metadata_json={},
    )

    decision = triage_search_result(brief, result)

    assert guess_source_type(result) == "github_issue"
    assert decision.decision == "keep"
    assert "first-hand" in decision.reason.lower() or "issue" in decision.reason.lower()


def test_triage_search_result_discards_vendor_marketing_for_pain_briefs(db_session):
    brief = create_brief(
        db_session,
        title="CRM workflow pain",
        research_question="What public complaints show up around CRM workflow friction?",
    )
    result = SearchResult(
        query="crm workflow pain pricing",
        title="CRM Pricing and Features",
        url="https://vendor.example.com/pricing",
        snippet="Book a demo for the best all-in-one CRM platform.",
        provider="static",
        rank=1,
        metadata_json={},
    )

    decision = triage_search_result(brief, result)

    assert decision.source_type == "vendor_marketing"
    assert decision.decision == "discard"
    assert "weak evidence" in decision.reason.lower()


def test_resolve_configured_search_provider_uses_saved_brave_settings(db_session, monkeypatch):
    save_model_execution_settings(
        db_session,
        {
            "provider": "ollama",
            "ollama_base_url": "http://localhost:11434",
            "ollama_model": "llama3",
            "research_search_provider": "brave",
            "brave_search_base_url": "https://api.search.brave.com/res/v1/web/search",
        },
    )
    monkeypatch.setenv("APD_BRAVE_SEARCH_API_KEY", "brave-test-key")

    resolution = resolve_configured_search_provider(db_session)

    assert resolution.provider_name == "brave"
    assert resolution.is_live_provider is True
    assert resolution.is_configured is True
    assert isinstance(resolution.provider, BraveSearchProvider)


def test_resolve_configured_search_provider_reports_missing_brave_key(db_session, monkeypatch):
    save_model_execution_settings(
        db_session,
        {
            "research_search_provider": "brave",
            "brave_search_base_url": "https://api.search.brave.com/res/v1/web/search",
        },
    )
    monkeypatch.delenv("APD_BRAVE_SEARCH_API_KEY", raising=False)

    resolution = resolve_configured_search_provider(db_session)

    assert resolution.provider_name == "brave"
    assert resolution.is_configured is False
    assert "APD_BRAVE_SEARCH_API_KEY" in str(resolution.setup_required_message)


def test_brave_search_provider_parses_response(monkeypatch):
    class _FakeResponse(BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    payload = {
        "web": {
            "results": [
                {
                    "title": "Forum thread",
                    "url": "https://example.com/thread",
                    "description": "Users describe painful manual work.",
                    "family_friendly": True,
                    "language": "en",
                }
            ]
        }
    }

    monkeypatch.setattr(
        "apd.services.research_search.request.urlopen",
        lambda req, timeout=0: _FakeResponse(json.dumps(payload).encode("utf-8")),
    )

    provider = BraveSearchProvider(api_key="test-key")
    results = provider.search([SearchQuery(query="manual work pain forum complaints", rationale="pain")])

    assert len(results) == 1
    assert results[0].provider == "brave"
    assert results[0].title == "Forum thread"