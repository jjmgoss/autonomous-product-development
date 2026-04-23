# Requirements

Run ID: 20260422-investigate-internal-recruiting-operations-r1
Product: Hiring Loop Coordinator

## User Stories

- As a recruiter, I want every interview loop to show the missing evaluator or decision owner so I know who is blocking progress.
- As a recruiter, I want reminders and escalations to happen automatically when feedback is overdue so I spend less time chasing manually.
- As a hiring manager, I want one packet that summarizes interview input and current status so I can make a faster decision.
- As a people ops lead, I want deadline and audit visibility so I can see which roles are slipping and why.

## Functional Requirements

- The system shall ingest or receive candidate, job, and interview-stage metadata from an existing hiring workflow.
- The system shall allow each candidate loop to define required evaluators, due times, and escalation rules.
- The system shall send reminders when required feedback is overdue.
- The system shall escalate to the next owner when a decision SLA is missed.
- The system shall generate a candidate decision packet containing stage, pending inputs, completed evaluations, and a concise summary.
- The system shall show a recruiter-facing queue of blocked or overdue candidate loops.
- The system shall store an audit trail of reminders, escalations, and state changes.

## Non-Functional Requirements

- The first version should work for a small hiring team without dedicated recruiting ops support.
- The reminder and status model should be understandable without custom workflow consulting.
- Generated summaries must be inspectable and editable by a human before they are treated as final.

## Constraints

- Do not replace the ATS.
- Keep the first integration surface narrow.
- Optimize for one team and one hiring pattern rather than many buyer archetypes.

## Acceptance Criteria

- A recruiter can identify the current blocker for any pilot candidate loop in one screen.
- A missed feedback deadline triggers a reminder automatically.
- A recruiter can open a candidate decision packet without manually assembling notes from multiple tools.
- Pilot users can run the workflow without custom engineering for every job opening.

## Non-Goals

- Candidate sourcing
- Full interview scheduling
- Offer generation and onboarding
- General recruiting analytics dashboards

## Edge Cases That Matter For The MVP

- One interviewer never submits feedback.
- The hiring manager wants to wait for one missing interview before deciding.
- A candidate moves stages while one reminder is already queued.
- A role changes ownership while multiple candidate loops are active.
