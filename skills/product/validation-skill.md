# Product Skill: Validation

## Goal

Decide whether the selected opportunity deserves implementation now, later, or not at all.

## When to use

After opportunity selection and before requirements or implementation.

## Procedure

1. State the thesis clearly.
   - User: who exactly has the problem?
   - Workflow: what recurring job are they trying to complete?
   - Pain: what is costly, risky, or frustrating?
   - Wedge: what narrow product would improve that workflow?

2. Build an evidence ledger.
   - Record the strongest evidence for the idea.
   - Record the strongest evidence against the idea.
   - Cite saved evidence IDs rather than unattributed summaries.
   - Separate source facts from your interpretation.

3. Judge evidence quality.
   - Weak: trend chatter, generic praise, broad category interest.
   - Moderate: repeated complaints, workaround descriptions, reviews, issue threads.
   - Stronger: explicit switching pain, budget-linked frustration, direct user requests, evidence that teams already spend time or money on the problem.

4. Analyze substitutes and incumbents honestly.
   - What do users use today?
   - Is the current answer already good enough?
   - Would your wedge create a meaningful improvement or just a nicer interface?

5. Test commercial plausibility.
   - Why would anyone pay?
   - What budget, cost, risk, or time-saving story exists?
   - What pricing shapes are plausible for the wedge?
   - Does the product create recurring value or only one-off curiosity?

6. Test operational fit.
   - Can the product be delivered digitally?
   - Can it be operated mostly virtually?
   - Can a solo operator with agents plausibly maintain support, operations, and iteration?
   - Does the MVP depend on trust, compliance, or service work that the framework should avoid?

7. Define the smallest falsification step.
   - Prefer the smallest experiment that could disprove the thesis.
   - This can be a prototype, offer test, landing-page test, workflow simulation, or deeper user/problem validation.

8. Make an explicit call.
   - Go now
   - Continue validation before building
   - No-go

## Go criteria

Default toward go only when most of these are true:

- the user and workflow are specific
- the pain is recurring and meaningful
- the substitutes are meaningfully insufficient for a target niche
- willingness to pay is plausible rather than hand-waved
- the wedge is narrow and testable
- the product can be built and run mostly virtually
- the support and operational burden look realistic for a solo operator with agents

## No-go triggers

- the problem is interesting but weakly painful
- existing tools look good enough for most users
- the monetization path is vague
- the product depends on heavy manual services, compliance, or enterprise sales too early
- the MVP would require a platform-sized build to be useful
- the evidence is thin and the agent is filling gaps with optimism

## Expected outputs

- `artifacts/runs/<run-id>/review-package/validation.md` during the discovery run
- a validation argument whose key claims point back to saved evidence IDs
- an explicit go, continue-validation, or no-go decision

If the run is still at Gate 1, the validation artifact should also explain why the winning candidate beat the runner-up and what evidence would overturn that decision.

## Common failure modes

- skipping the negative case because the idea feels buildable
- treating repeated discussion as willingness to pay
- ignoring substitutes because they look unglamorous
- forcing a go decision because implementation feels more concrete than research
