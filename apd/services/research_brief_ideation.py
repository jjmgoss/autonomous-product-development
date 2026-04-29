from __future__ import annotations

import re

from sqlalchemy.orm import Session

from apd.services.research_execution_ollama import (
    _build_generate_payload,
    _ollama_generate,
    _unload_ollama_model,
    extract_json_object_from_model_output,
    get_ollama_execution_config,
)


_IDEATION_THEMES = [
    "AI-assisted product research",
    "local-first developer tools",
    "self-hosting and maintenance",
    "personal knowledge management",
    "small business operations",
    "household maintenance and repairs",
    "personal finance decision support",
    "car ownership and insurance workflows",
    "data quality and analytics trust",
    "hobbyist project management",
]

_OPTIONAL_FIELDS = ["constraints", "desired_depth", "expected_outputs", "notes"]
_RESEARCH_CLAIM_PATTERN = re.compile(
    r"https?://|www\.|\b(citation|citations|source url|source urls|sources include|based on research|according to research)\b",
    flags=re.IGNORECASE,
)


def get_brief_ideation_themes() -> list[str]:
    return list(_IDEATION_THEMES)


def build_brief_ideation_prompt(selected_themes: list[str]) -> str:
    themes_text = ", ".join(selected_themes)
    return "\n".join(
        [
            "Generate a draft APD research brief form prefill.",
            "Return only JSON.",
            "Generate a product-investigation brief, not generic trivia.",
            "Do not claim to have researched the space yet.",
            "Do not invent sources, URLs, or citations.",
            "Keep the brief suitable for APD's component execution workflow.",
            "The output is only a draft form prefill, not a saved run.",
            "Use these selected themes: " + themes_text + ".",
            "",
            "Required JSON shape:",
            "{",
            '  "title": "string",',
            '  "research_question": "string",',
            '  "constraints": "string",',
            '  "desired_depth": "string",',
            '  "expected_outputs": "string",',
            '  "notes": "string"',
            "}",
            "",
            "Make the idea product-oriented and plausible for APD dogfooding.",
        ]
    )


def parse_generated_brief_idea(raw_model_output: str) -> tuple[dict[str, str] | None, str | None]:
    parsed, parse_error = extract_json_object_from_model_output(raw_model_output)
    if parse_error or parsed is None:
        return None, parse_error or "parse_failed: invalid_brief_idea_output"

    if not isinstance(parsed, dict):
        return None, "parse_failed: brief_idea_not_object"

    result: dict[str, str] = {}
    for field_name in ["title", "research_question", *_OPTIONAL_FIELDS]:
        value = parsed.get(field_name)
        if value is None:
            result[field_name] = ""
            continue
        if isinstance(value, str):
            result[field_name] = value.strip()
            continue
        if isinstance(value, (int, float, bool)):
            result[field_name] = str(value).strip()
            continue
        return None, f"validation_failed: {field_name}_must_be_string"

    if not result["title"]:
        return None, "validation_failed: missing_title"
    if not result["research_question"]:
        return None, "validation_failed: missing_research_question"

    combined = "\n".join(value for value in result.values() if value)
    if _RESEARCH_CLAIM_PATTERN.search(combined):
        return None, "validation_failed: generated_idea_claims_researched_sources"

    return result, None


def generate_brief_idea_with_ollama(
    db: Session,
    selected_themes: list[str],
) -> tuple[dict[str, str] | None, str | None]:
    if not selected_themes:
        return None, "Select at least one theme before generating a brief idea."

    valid_themes = set(_IDEATION_THEMES)
    normalized_themes = [theme.strip() for theme in selected_themes if theme and theme.strip()]
    if not normalized_themes:
        return None, "Select at least one theme before generating a brief idea."
    invalid_themes = [theme for theme in normalized_themes if theme not in valid_themes]
    if invalid_themes:
        return None, "One or more selected ideation themes are invalid."

    config, missing = get_ollama_execution_config(db)
    if config is None:
        return None, "Local Ollama is not configured. Save model execution settings first."

    prompt = build_brief_ideation_prompt(normalized_themes)
    payload = _build_generate_payload(config, prompt, during_execution=True)
    try:
        response_data, call_error = _ollama_generate(config, payload)
        if call_error:
            return None, call_error

        output_text = str(response_data.get("response") or "")
        if not output_text.strip():
            return None, "provider_error: empty_ollama_response"

        return parse_generated_brief_idea(output_text)
    finally:
        _unload_ollama_model(config)