# Research Eval Harness

The APD research eval harness is a deterministic, fixture-only way to compare harness changes without depending on live web results or a live local model.

## Overview

The first version uses:

- YAML case files under `evals/research/cases/`
- fixture HTML or text pages under `evals/research/fixtures/pages/`
- deterministic/static search discovery inputs when a case needs pre-synthesis retrieval behavior
- a simulated APD component-execution path in `apd/evals/research_runner.py`
- JSON results written to `evals/research/results/`

The runner assembles APD-style draft packages from fixture sources and simulated phase batches, validates them with the existing APD draft validator, imports them into a temporary SQLite database, and then scores the output with deterministic rubric checks.

## Running Evals

Run the fixture-only harness with:

```bash
uv run python scripts/run_research_evals.py --fixture-only
```

The command prints a short per-case table plus aggregate totals and writes a timestamped JSON file to `evals/research/results/`.

Use `--model-label` and `--harness-label` when you want to compare two mocked or partially mocked configurations while keeping the same deterministic fixtures.

## Case Schema

Each YAML case should include these top-level fields:

- `id`
- `title`
- `brief`
- `fixture_sources`
- `relevant_source_ids`
- `irrelevant_source_ids`
- `expected_claim_traits`
- `expected_theme_traits`
- `expected_candidate_traits`
- `forbidden_claim_patterns`
- `rubric_metadata`
- `simulated_execution`

`brief` should provide at least `title` and `research_question`.

Each `fixture_sources` entry should provide:

- `id`
- `path`
- `url`
- optional `title`
- optional `source_type`
- optional `excerpt_type`
- optional `relevant`

`simulated_execution.phase_batches` should mirror the APD component-batch format already used by grounded execution:

- `candidate_batch`
- `claim_theme_batch`
- `validation_gate_batch`

Each batch should contain `schema_version`, `batch_id`, and `events`. Event payloads should use the same typed event schema as `apd/services/research_components.py`.

## Scoring

Each case result includes deterministic metrics intended to stay stable across repeated runs:

- `import_success`
- `schema_validation_success`
- `valid_source_links`
- `unknown_source_reference_count`
- `unsupported_claim_count`
- `expected_claim_trait_coverage`
- `expected_theme_trait_coverage`
- `expected_candidate_trait_coverage`
- `forbidden_claim_hit_count`
- `retry_count`
- `attempts_by_phase`
- `runtime_seconds`

The runner also emits `score_summary.overall_score`, which is a simple average of normalized checks and trait-coverage values. It is intentionally basic. The goal is not perfect semantic judgment; the goal is a stable comparison signal that later scorecard work can aggregate.

Interpretation guidance:

- high trait coverage with zero forbidden hits means the simulated output stayed close to the expected wedge
- non-zero `unknown_source_reference_count` means evidence links pointed at sources or excerpts that were not present in the fixture packet
- non-zero `unsupported_claim_count` means claims were emitted without a supporting `supports` evidence link to a known fixture source
- higher `retry_count` means the case is modeling a harness path that needed one or more repair attempts

## Adding Cases

To add a new eval case:

1. Add one YAML file under `evals/research/cases/`.
2. Add one or more HTML or text fixtures under `evals/research/fixtures/pages/`.
3. Reference those fixture files from `fixture_sources`.
4. Define expected claim, theme, and candidate traits as plain keywords or short phrases.
5. Define any forbidden claim patterns you want to catch.
6. Add simulated component batches under `simulated_execution.phase_batches`.
7. Run `uv run python scripts/run_research_evals.py --fixture-only` and confirm the new case appears in the summary and output JSON.

Keep cases narrow. The goal is not to model the whole internet. The goal is to exercise one repeatable research situation with explicit evidence, bait sources, and expected output traits.

The eval harness should remain runnable without live web, live model calls, paid search providers, or hosted APIs. Static search fixtures are the intended way to test the discovery layer in CI.