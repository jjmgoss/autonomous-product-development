# Design

Run ID: 20260422-investigate-internal-recruiting-operations-r1
Product: Hiring Loop Coordinator

## Architecture Overview

The simplest credible architecture is a small web application plus background job runner.

- Web app: recruiter-facing queue, candidate loop detail, and decision packet view
- Background worker: reminder scheduling, escalation checks, and summary generation
- Integration layer: pull or receive ATS candidate-loop metadata and send email or Slack reminders
- Database: store candidate loops, evaluation tasks, reminders, and audit events

## Stack Choices And Rationale

- Python backend with FastAPI: fast to build, easy to script, friendly for agent-led implementation
- SQLite for the first local prototype, upgradeable to Postgres later
- Lightweight job scheduler or queue for reminder jobs
- Minimal HTML server-rendered UI before investing in heavier frontend complexity

## Data Model

- Job: role, department, owner, current status
- Candidate: candidate identity, role, stage, external ATS reference
- InterviewLoop: stage window, due dates, overall status
- EvaluationTask: assigned evaluator, due time, completion state, escalation target
- DecisionPacket: generated summary, recommendation draft, last updated time
- AuditEvent: reminder sent, escalation fired, packet viewed, status changed

## Major Flows

### Post-interview setup
- Candidate enters an interview-complete state
- Required evaluators and deadlines are attached
- Recruiter sees the loop as active

### Reminder and escalation flow
- If a due time passes without feedback, send a reminder
- If the loop remains blocked after the reminder window, escalate to the configured owner
- Update the recruiter queue automatically

### Decision packet flow
- Once enough inputs exist, generate a summary packet
- Show completed inputs, missing inputs, and current blocker
- Allow recruiter review before sharing internally

## Interfaces

- ATS import adapter: candidate, job, stage, interviewer assignments
- Notification adapter: email first, optional Slack second
- UI contract: list blocked loops, open loop details, open decision packet

## Deployment Assumptions

- First prototype runs locally or in a small hosted environment for one pilot team
- No public candidate-facing surface is required in milestone 1

## Security And Privacy Considerations

- Candidate data and interview notes must be access-controlled by role
- Generated summaries should avoid exposing unnecessary sensitive information
- Audit events should be preserved for accountability

## Test Strategy

- Unit tests for reminder timing, escalation rules, and packet generation
- Integration tests for ATS import and reminder dispatch
- End-to-end test for one stalled loop becoming visible, reminded, escalated, and summarized
