# Data Model

This file describes the first APD application data model.

The goal is not to design a perfect long-term schema. The goal is to give implementation agents a shared vocabulary and a concrete starting point for the local research cockpit.

## Modeling Principles

APD should model research as structured, reviewable, evidence-linked work.

Prefer explicit relationships over opaque generated reports.

Agent-generated data should be distinguishable from human-reviewed or accepted data.

Large source text and generated reports may live on disk, with database records pointing to file paths.

The database should contain the structured state needed for UI, review, filtering, validation, and export.

## Core Entities

### Run

A product-discovery investigation.

A run starts from a product curiosity, market question, uploaded corpus, or research prompt.

Suggested fields:

- `id`
- `title`
- `intent`
- `summary`
- `mode`
- `phase`
- `decision`
- `recommendation`
- `confidence`
- `created_at`
- `updated_at`
- `completed_at`
- `source_count`
- `claim_count`
- `theme_count`
- `candidate_count`
- `metadata_json`

Relationships:

- has many `Source`
- has many `Claim`
- has many `Theme`
- has many `Candidate`
- has many `ValidationGate`
- has many `ReviewNote`
- has many `Artifact`

### Source

A URL, file, note, transcript, issue, thread, review, or other evidence input.

Suggested fields:

- `id`
- `run_id`
- `title`
- `source_type`
- `url`
- `origin`
- `author_or_org`
- `captured_at`
- `published_at`
- `raw_path`
- `normalized_path`
- `reliability_notes`
- `summary`
- `metadata_json`

Relationships:

- belongs to `Run`
- has many `EvidenceExcerpt`
- has many `EvidenceLink`

### EvidenceExcerpt

A specific excerpt, quote, passage, or observation from a source.

This is the smallest reviewable evidence unit.

Suggested fields:

- `id`
- `run_id`
- `source_id`
- `excerpt_text`
- `location_reference`
- `excerpt_type`
- `created_at`
- `metadata_json`

Example `excerpt_type` values:

- `complaint`
- `workaround`
- `substitute`
- `feature_request`
- `pricing_signal`
- `adoption_signal`
- `counterevidence`
- `context`

Relationships:

- belongs to `Run`
- belongs to `Source`
- has many `EvidenceLink`

### Claim

A specific assertion made by an agent or human.

Claims should be reviewable and evidence-linked.

Suggested fields:

- `id`
- `run_id`
- `statement`
- `claim_type`
- `review_status`
- `confidence`
- `created_by`
- `created_at`
- `updated_at`
- `metadata_json`

Example `claim_type` values:

- `pain`
- `workflow`
- `user_segment`
- `substitute`
- `market_gap`
- `monetization`
- `feasibility`
- `risk`
- `counterevidence`

Example `review_status` values:

- `unreviewed`
- `accepted`
- `weak`
- `disputed`
- `needs_followup`

Relationships:

- belongs to `Run`
- has many `EvidenceLink`
- has many `ReviewNote`
- may link to many `Theme`
- may link to many `Candidate`

### Theme

A cluster of related pain, need, workaround, behavior, or opportunity evidence.

Suggested fields:

- `id`
- `run_id`
- `name`
- `summary`
- `theme_type`
- `severity`
- `frequency`
- `user_segment`
- `workflow`
- `review_status`
- `created_at`
- `updated_at`
- `metadata_json`

Example `theme_type` values:

- `pain_theme`
- `workflow_theme`
- `substitute_theme`
- `market_gap`
- `risk_theme`

Relationships:

- belongs to `Run`
- has many `EvidenceLink`
- has many `ReviewNote`
- may link to many `Claim`
- may link to many `Candidate`

### Candidate

A possible product wedge.

Candidates should be narrow, evidence-linked, and reviewable.

Suggested fields:

- `id`
- `run_id`
- `title`
- `summary`
- `target_user`
- `first_workflow`
- `first_wedge`
- `prototype_success_event`
- `monetization_path`
- `substitutes`
- `risks`
- `why_now`
- `why_it_might_fail`
- `score`
- `rank`
- `review_status`
- `decision`
- `created_at`
- `updated_at`
- `metadata_json`

Example candidate `decision` values:

- `archive`
- `watch`
- `publish`
- `prototype_later`
- `build_approved`

Relationships:

- belongs to `Run`
- has many `EvidenceLink`
- has many `ValidationGate`
- has many `ReviewNote`
- may link to many `Claim`
- may link to many `Theme`
- may have many `Artifact`

### EvidenceLink

A connection between evidence and an interpreted object.

This is the traceability layer.

Suggested fields:

- `id`
- `run_id`
- `source_id`
- `excerpt_id`
- `target_type`
- `target_id`
- `relationship`
- `strength`
- `notes`
- `created_at`
- `metadata_json`

Example `target_type` values:

- `claim`
- `theme`
- `candidate`
- `validation_gate`

Example `relationship` values:

- `supports`
- `weakens`
- `contradicts`
- `context_for`
- `example_of`

Example `strength` values:

- `weak`
- `medium`
- `strong`

Relationships:

- belongs to `Run`
- may belong to `Source`
- may belong to `EvidenceExcerpt`
- points to one target object by `target_type` and `target_id`

### ValidationGate

A required check before a run or candidate can credibly advance phases.

Suggested fields:

- `id`
- `run_id`
- `candidate_id`
- `phase`
- `name`
- `description`
- `status`
- `blocking`
- `evidence_summary`
- `missing_evidence`
- `created_at`
- `updated_at`
- `metadata_json`

Example `status` values:

- `not_started`
- `in_progress`
- `satisfied`
- `weak`
- `failed`
- `waived`

Relationships:

- belongs to `Run`
- may belong to `Candidate`
- has many `EvidenceLink`
- has many `ReviewNote`

### ReviewNote

Human or agent feedback on a run, source, claim, theme, candidate, gate, or artifact.

Suggested fields:

- `id`
- `run_id`
- `target_type`
- `target_id`
- `author`
- `note`
- `status`
- `created_at`
- `resolved_at`
- `metadata_json`

Example `status` values:

- `open`
- `resolved`
- `wont_fix`
- `superseded`

Relationships:

- belongs to `Run`
- points to one target object by `target_type` and `target_id`

### Decision

A durable decision about a run or candidate.

A decision is separate from a current status field so the system can preserve decision history.

Suggested fields:

- `id`
- `run_id`
- `candidate_id`
- `target_type`
- `target_id`
- `decision`
- `rationale`
- `decided_by`
- `decided_at`
- `metadata_json`

Example `decision` values:

- `archive`
- `watch`
- `publish`
- `prototype_later`
- `build_approved`

Relationships:

- belongs to `Run`
- may belong to `Candidate`
- points to one target object by `target_type` and `target_id`

### Artifact

A generated or curated output.

Examples include reports, exports, post outlines, prototype briefs, review packages, and imported legacy Markdown files.

Suggested fields:

- `id`
- `run_id`
- `candidate_id`
- `artifact_type`
- `title`
- `path`
- `url`
- `created_by`
- `created_at`
- `summary`
- `metadata_json`

Example `artifact_type` values:

- `run_report`
- `source_note`
- `discovery_summary`
- `candidate_review`
- `opportunity_scorecard`
- `validation_report`
- `post_outline`
- `prototype_brief`
- `export`
- `legacy_markdown`

Relationships:

- belongs to `Run`
- may belong to `Candidate`

## Many-To-Many Relationships

Implementation may use join tables for these relationships:

- claims to themes
- claims to candidates
- themes to candidates
- artifacts to candidates

If implementation starts simpler, `EvidenceLink` can carry most cross-object traceability at first.

## Status Enums

### Run Phase

Use:

- `vague_notion`
- `evidence_collected`
- `supported_opportunity`
- `vetted_opportunity`
- `prototype_ready`
- `build_approved`

### Review Status

Use:

- `unreviewed`
- `accepted`
- `weak`
- `disputed`
- `needs_followup`

### Decision

Use:

- `archive`
- `watch`
- `publish`
- `prototype_later`
- `build_approved`

### Evidence Relationship

Use:

- `supports`
- `weakens`
- `contradicts`
- `context_for`
- `example_of`

## MVP Simplifications

The first implementation may simplify the model as long as it preserves the core concepts.

Acceptable simplifications:

- store some secondary fields in `metadata_json`
- implement polymorphic links with `target_type` and `target_id`
- use manually assigned phases before automatic phase evaluation exists
- use one fixture seed run instead of full import support
- render artifacts from structured data before building rich export workflows

Avoid these simplifications:

- storing all run data as one giant JSON blob
- skipping evidence links
- treating agent-generated claims as accepted by default
- omitting review status
- making candidates impossible to trace back to sources
- making decisions overwrite history without a durable decision record

## First Fixture Requirements

The first fixture run should include:

- one run
- at least three sources
- at least six evidence excerpts
- at least five claims
- at least two themes
- at least two candidates
- evidence links connecting sources/excerpts to claims and candidates
- at least one weak or disputed claim
- at least one validation gate that is not satisfied
- one run-level decision

The fixture should be deterministic and suitable for tests, local development, and UI screenshots.

## Open Questions

These should be resolved during implementation, not guessed globally up front:

- whether `Decision` should be a separate history table only, or also denormalized onto `Run` and `Candidate`
- whether `EvidenceExcerpt` should be required for every `EvidenceLink`
- whether source files should live under the existing `research-corpus/` structure or a new app-managed data directory
- whether legacy Markdown artifacts should be imported into structured fields or linked as `Artifact` records first
- whether review notes should support threaded replies in the first MVP
- whether generated draft imports need a separate `Draft` entity or can be represented through review status and metadata