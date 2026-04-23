# Backlog

Run ID: 20260422-investigate-internal-recruiting-operations-r1
Product: Hiring Loop Coordinator

## Active Now

- Define the candidate loop state model and reminder timing rules
- Build the recruiter queue for blocked and overdue loops
- Draft the first decision packet format

## Next Up

- Implement email reminder and escalation delivery
- Add a simple ATS import adapter for one candidate-loop source
- Test whether recruiters trust the packet enough to use it in real decisions

## Blocked By Missing Evidence

- Which ATS the first pilot buyer already uses
- Whether buyers care more about interview feedback chase or offer approvals in the first purchase
- Whether Slack is a must-have channel for the first users

## Deferred

- Candidate-facing communications automation
- Offer approval workflow expansion
- Full interview scheduling features

## Rejected

- Standalone interview scheduling coordinator: too exposed to strong generic substitutes
- Full recruiting operations platform: too broad for the first wedge

## Technical Debt

- Integration abstractions may overcomplicate the first prototype if added too early
- Summary generation should stay inspectable and avoid opaque AI-only decisions

## Future Experiments

- Compare recruiter time saved before and after reminder automation
- Test a decision-packet only workflow with no reminder engine
- Validate whether approval routing becomes the better upsell after the first wedge works
