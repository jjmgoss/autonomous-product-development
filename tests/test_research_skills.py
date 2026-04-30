from __future__ import annotations

from apd.domain.models import ResearchBrief
from apd.services.research_brief_service import (
    generate_ollama_component_phase_prompt,
    generate_ollama_component_repair_prompt,
)
from apd.services.research_skills import (
    load_research_skill_manifest,
    render_research_skill_context,
    resolve_research_skills_for_phase,
)
from apd.services.web_research import build_web_research_target_prompt


def _brief() -> ResearchBrief:
    return ResearchBrief(
        title="Self-hosting operations pain",
        research_question=(
            "Investigate product opportunities for solo developers who self-host "
            "small apps and struggle with deployment, monitoring, backups, and maintenance."
        ),
    )


def test_load_research_skill_manifest_reads_initial_skill_tree():
    specs = load_research_skill_manifest()
    ids = [spec.id for spec in specs]

    assert "research_protocol" in ids
    assert "search_strategy" in ids
    assert "candidate_generation" in ids
    assert all(spec.max_prompt_budget_chars > 0 for spec in specs)


def test_resolve_research_skills_for_web_discovery_and_component_aliases():
    web_skill_ids = resolve_research_skills_for_phase("web_discovery", max_skills=None)
    assert web_skill_ids[:3] == [
        "research_protocol",
        "search_strategy",
        "url_target_selection",
    ]

    claim_theme_skill_ids = resolve_research_skills_for_phase("claim_theme_batch", max_skills=None)
    assert "research_protocol" in claim_theme_skill_ids
    assert "claim_grounding" in claim_theme_skill_ids
    assert "theme_synthesis" in claim_theme_skill_ids

    validation_skill_ids = resolve_research_skills_for_phase("validation_gate_batch", max_skills=None)
    assert "validation_gate_design" in validation_skill_ids


def test_render_research_skill_context_is_bounded_and_operational():
    context = render_research_skill_context(["search_strategy"], max_chars=1300)

    assert len(context) <= 1300
    assert "Research skill: search_strategy" in context
    assert "## Procedure" in context
    assert "## Output contract" in context
    assert "## Quality checks" in context


def test_web_discovery_prompt_includes_selected_research_skills():
    prompt = build_web_research_target_prompt(_brief())

    assert "Selected APD research skills" in prompt
    assert "Research skill: search_strategy" in prompt
    assert "Research skill: url_target_selection" in prompt
    assert "Return JSON with this shape" in prompt


def test_component_phase_prompts_include_relevant_skill_context():
    brief = _brief()

    candidate_prompt = generate_ollama_component_phase_prompt(brief, "candidate_batch")
    assert "Research skill: candidate_generation" in candidate_prompt
    assert "Phase: candidate_batch" in candidate_prompt

    claim_theme_prompt = generate_ollama_component_phase_prompt(brief, "claim_theme_batch")
    assert "Research skill: claim_grounding" in claim_theme_prompt
    assert "Research skill: theme_synthesis" in claim_theme_prompt
    assert "Phase: claim_theme_batch" in claim_theme_prompt

    validation_prompt = generate_ollama_component_phase_prompt(
        brief,
        "validation_gate_batch",
        candidate_ids=["cand-1"],
    )
    assert "Research skill: validation_gate_design" in validation_prompt
    assert "Existing candidate IDs: cand-1" in validation_prompt


def test_repair_prompt_includes_phase_skill_context_and_validation_errors():
    prompt = generate_ollama_component_repair_prompt(
        _brief(),
        phase_name="claim_theme_batch",
        validation_errors=["event #1 missing external_id"],
        invalid_batch_data={"schema_version": "1.0", "events": []},
    )

    assert "Research skill: claim_grounding" in prompt
    assert "Research skill: theme_synthesis" in prompt
    assert "event #1 missing external_id" in prompt
    assert "Return only the corrected ResearchComponentBatch JSON object." in prompt
