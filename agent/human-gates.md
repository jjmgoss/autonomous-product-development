# Hard Boundaries

Use this file to identify the few actions that actually require human approval.

## Default policy

Continue by default through research, opportunity selection, validation, requirements, design, planning, local implementation, and local verification.

Generated artifacts remain useful for asynchronous human inspection, but they do not create an automatic pause.

## Approval is required for these boundary types

### Boundary 1: Destructive or hard-to-reverse actions

Require approval before:

- deleting or overwriting important user data
- destructive repo or environment actions outside the current safe working flow
- irreversible migrations or bulk data rewrites

### Boundary 2: Deployment or public exposure

Require approval before:

- deploying to a real environment
- exposing an app, API, dataset, or credentials externally
- enabling outbound automation that could affect real users or systems

### Boundary 3: External publishing or communication

Require approval before:

- publishing content publicly
- sending emails, messages, or other outbound communications
- creating external tickets, issues, pull requests, or boards when those actions are externally consequential

### Boundary 4: Financial, legal, or credential-sensitive actions

Require approval before:

- spending money or creating paid accounts
- entering secrets or credentials into external systems
- taking actions that materially change legal, privacy, or compliance exposure

## Discovery milestone policy

Checkpoint 1 is a status marker and async review surface.
Do not pause there by default.

If the discovery package is complete and the winning candidate earns a go-now recommendation, continue into the next non-risky stage unless `ACTIVE_RUN.md` explicitly ends the run at discovery.

## Escalation rule

If an action is internal, reversible, and quiet, continue.
If an action is external, noisy, destructive, costly, or hard to reverse, treat it as a hard boundary and ask for approval.
