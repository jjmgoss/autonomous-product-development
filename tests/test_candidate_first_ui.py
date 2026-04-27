from __future__ import annotations


def test_candidates_render_before_sources(client):
    resp = client.get("/runs/1")
    assert resp.status_code == 200
    body = resp.text
    # Find section headings and assert candidates appears earlier than sources
    idx_cand = body.find("Candidates")
    idx_sources = body.find("Sources")
    assert idx_cand != -1 and idx_sources != -1
    assert idx_cand < idx_sources


def test_candidate_card_includes_title_and_linked_gate(client):
    resp = client.get("/runs/1")
    assert resp.status_code == 200
    body = resp.text
    # Fixture candidate title should appear
    assert "Release Guardrails Assistant" in body
    # The gate linked to that candidate in fixtures should appear
    assert "Confirm willingness to pay" in body
