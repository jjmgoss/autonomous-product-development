# Decision Log

Record meaningful decisions.

For each decision, include:

- date or iteration context
- decision statement
- options considered
- chosen option
- why chosen
- reversibility
- remaining uncertainty

## 2026-04-23 - Continuation surface for validation run

- decision statement: Keep the repo's new continuation model as written and exercise `docs/product-brief.md`, `docs/requirements.md`, `docs/design.md`, `docs/roadmap.md`, and `docs/backlog.md` directly during the self-validation run.
- options considered: Validate only the discovery package; validate discovery plus the active planning surface.
- chosen option: Validate discovery plus the active planning surface.
- why chosen: The refactor goal was to strengthen discovery-to-prototype continuation. Skipping the planning docs would avoid the exact behavior the redesign is supposed to prove.
- reversibility: High. The planning docs are lightweight and can be rewritten again if the repo later moves that continuation surface into run-local artifacts.
- remaining uncertainty: Whether `docs/` should remain the living planning surface long term or move into a more run-local planning tree in a later pass.

## 2026-04-23 - Validation-run wedge selection

- decision statement: Recommend the Hiring Loop Coordinator over approval routing and scheduling coordination for the internal recruiting workflow validation run.
- options considered: Hiring Loop Coordinator; Hiring Approval Router; Interview Scheduling Coordinator.
- chosen option: Hiring Loop Coordinator.
- why chosen: Feedback delay and decision-lag pain repeated across the strongest sources and mapped to a narrower, more monetizable workflow than the approval or scheduling alternatives.
- reversibility: High. The candidate map preserves the runner-up and the evidence that could overturn the call.
- remaining uncertainty: Whether small teams will buy a standalone layer rather than expecting this inside the ATS.
