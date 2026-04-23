# Roadmap

Run ID: 20260422-investigate-internal-recruiting-operations-r1
Product: Hiring Loop Coordinator

## Milestone Overview

- Milestone 1: Blocked loop visibility and reminder engine
- Milestone 2: Decision packet generation and recruiter review workflow
- Milestone 3: ATS integration hardening and pilot team fit

## First Vertical Slice

Build one runnable flow:
- import one candidate loop manually or from a simple adapter
- assign two evaluators and one due time
- miss one deadline
- trigger reminder and escalation
- produce a recruiter-readable decision packet

## Milestone Goals And Acceptance Checks

### Milestone 1
- goal: show recruiters which loops are blocked and automate the first reminder
- acceptance check: one stalled candidate loop appears in the queue and sends a reminder automatically

### Milestone 2
- goal: reduce recruiter recap work with a generated decision packet
- acceptance check: the packet can be reviewed and used to move a candidate to the next decision step

### Milestone 3
- goal: prove the workflow works with a real hiring stack and not only with manual fixtures
- acceptance check: one pilot team can use the flow against live or semi-live ATS data without manual engineering for each candidate

## Dependencies And Unresolved Risks

- ATS access model for the first pilot
- reminder channel choice and deliverability
- whether decision packets feel trustworthy enough without deep customization

## Cut-Line Options

- If ATS integration is too heavy, keep milestone 1 on manual import plus internal queue.
- If summary generation is noisy, keep milestone 2 focused on state visibility and missing-input detection.
- If escalation policy becomes too organization-specific, support one default policy first.

## Later Improvements Only If Still Credible

- richer ATS integrations
- hiring-manager dashboards
- configurable workflow templates by role family
- offer-stage approval routing if buyers keep asking for it
