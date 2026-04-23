# Product Skill: Roadmap

## Goal

Break the MVP into milestones and issue-sized slices that preserve learning speed and reviewability.

## When to use

After requirements and design are stable enough to plan real work.

In the active framework, roadmap and backlog updates are part of the default continuation path once discovery produces a go-now recommendation and no hard boundary blocks planning.

## Procedure

1. Define the first meaningful vertical slice.
	- It should exercise one real user flow.
	- It should be runnable or meaningfully testable.
	- It should teach you something about the product thesis.

2. Define later milestones only as far as they remain credible.
	- Keep them narrow.
	- Prefer milestone goals over exhaustive task trees.

3. Decompose milestone work into issue-sized slices.
	- Keep issues small enough to implement and verify cleanly.
	- Separate discovery tasks, build tasks, and hardening tasks when useful.

4. Mark the cut line.
	- What can be removed without breaking the wedge?
	- What is future expansion rather than MVP-critical?

## Planning rules

- The first milestone must not be mostly scaffolding.
- A good slice proves a user-visible path, not just infrastructure readiness.
- If the plan gets big quickly, cut scope before adding more tasks.

## Expected outputs

- `docs/roadmap.md`
- `docs/backlog.md`

## Common failure modes

- planning only scaffolding, not user-visible slices
- overloading the first milestone with future-proofing
- mixing research uncertainty into implementation tasks without calling it out
