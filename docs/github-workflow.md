# GitHub Workflow

This repository follows an issue-driven, pull-request-first workflow for agent-assisted development.

## Expected Flow

1. Track implementation steps in GitHub Issues.
2. Use one branch per issue or discrete task.
3. Open a pull request for each branch.
4. Use the PR body as the delivery-report surface for what changed, verification, risk, and follow-ups.
5. Run CI and lightweight PR policy checks on pull requests.
6. If checks fail, inspect logs, fix on the same branch, and re-run validation.
7. Require another agent or a human to review the pull request.
8. Merge to `main` only after required checks and review pass.
9. Treat deploy actions as explicit follow-up work, not an automatic part of every PR.

## Required Issue Content

Issues should include:

- explicit ask
- relevant context
- acceptance criteria
- safety constraints
- verification expectations
- deployment impact

## Required Pull Request Content

Pull requests should include:

- a short summary
- linked issue or reference
- what changed
- verification commands and results
- risk or deployment impact
- reviewer focus
- follow-ups

Use `.github/PULL_REQUEST_TEMPLATE.md` to keep these sections consistent.

## Check Handling

- Poll CI and PR policy checks until they finish.
- If a PR-caused check fails, fix it on the same branch and push again.
- If a failure is unrelated or requires unavailable credentials, document that clearly in the PR.

## Review And Merge Posture

- Do not merge without explicit human approval.
- Keep deployment decisions explicit and repository-specific.
- Do not alter branch protection, delete branches, or run deployment workflows without explicit instruction.

Safety notes: Do not write secrets into the repository. Keep repository-local architecture, runtime behavior, and dangerous-command guidance in `AGENTS.md`, not in this shared workflow document.