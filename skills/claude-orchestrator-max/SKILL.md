---
name: claude-orchestrator-max
description: "Delegation policy for a Claude Max plan only (not Pro): Fable 5.1 is the scarce judgment tier (the operator's design partner in the main loop, or a read-only consultant Opus calls as a sub-agent), Opus 5.5 plans, builds and reviews, Sonnet 5.5 sub-agents do the bounded work. Load whenever spawning sub-agents (Agent tool or Workflow agent() calls), planning delegation, or switching the main-loop model. If the plan is unknown, load this one rather than claude-orchestrator: its first step checks the plan and hands off to claude-orchestrator when not on Max."
---

# Orchestration & delegation policy (Max plan, Fable for judgment)

A routing policy for one Claude **Max** plan with three roles: **Fable 5.1**
for judgment, as the operator's design partner in the main loop or as a
read-only consultant Opus calls; **Opus 5.5** to plan, build and review;
**Sonnet 5.5** as the default delegate for bounded work.

Core law: **judgment on Fable, building on Opus, bounded work on Sonnet.**
Fable's tokens buy decisions at the points where a wrong call is expensive,
never throughput.

## Two modes

The operator picks the main-loop model with `/model`; the session keeps its
context across the switch.

**Design mode (main loop: Fable).** The operator and Fable work out the
architecture together: options, risks, the decision. Fable then writes the
plan to a file: the task list, a model stamped on every task, acceptance
criteria. Fable reads little in this mode; when the terrain is unknown, a
Sonnet sweep maps it and Fable reads the map. No build work here beyond
trivial edits. "When to consult Fable" does not apply: the consultant is
already in the loop. Every turn draws on the Fable 7-day window, so when the
file-heavy part starts, Fable says so and the operator switches to Opus.

**Build mode (main loop: Opus).** Opus takes the plan, delegates to Sonnet,
carries the hard lanes itself or with an Opus sub-agent, and reviews. A
design question the plan did not foresee goes to Fable through the
consultation triggers below, or the operator switches back to Fable for a
conversation. Both draw on the same window.

The rules below apply in both modes.

## Check the plan first

Run the `claude-limit` skill once per session, before the first delegation.
Its header shows the plan.

- `plan: max` → this policy applies.
- Anything else (e.g. after switching to a Pro account) → stop using this
  skill and follow `claude-orchestrator`. Fable is not available there.

## The pools

- **Opus and Sonnet** share the plan's 5-hour and 7-day windows. Opus burns
  them much faster.
- **Fable** has its own weekly window (`Fable 7-day` in `claude-limit`) and
  also counts toward the all-model 7-day window, up to the share the line
  shows (`may use up to N% of 7-day`).

## The hard rules

1. **Always set `model` explicitly** (`"sonnet"`, `"opus"` or `"fable"`) on
   every Agent call and every Workflow `agent()` call; `meta.phases` entries
   carry the same model for display. An omitted model inherits the main loop
   and silently fans out Opus, or Fable in design mode. The Workflow
   reference says to omit it by default; under this policy, don't.
2. **Hands-on while limits are healthy.** The main loop does small and medium
   work itself. Delegate work that is parallelizable, large and mechanical, or
   would flood the main context.
3. **Opus sub-agents are allowed, not reflexive.** Max has room for them, so
   use one for a hard, bounded lane Sonnet can't carry (security-critical
   change, correctness-sensitive path, fresh-eyes review of risky work) and
   state the reason in the plan.
4. **Fable is a consultant, never a worker.** It reads and answers. It does
   not edit files, commit, run long jobs, or review routine diffs.
5. **The main loop owns the decision.** Architecture, specs, integration,
   final synthesis, review and acceptance stay in the main loop, including
   after a Fable consultation.

## Choosing the delegate

- **Sonnet**: exploration, codebase mapping, research sweeps, verification
  passes, templated changes, clones of an existing pattern, features that ride
  an existing pipeline.
- **Opus sub-agent**: the hard bounded lane from rule 3, and the fresh-eyes
  review of risky work.
- **Main loop**: everything in rule 5, plus hard execution that needs the
  whole picture.
- **Fable**: design mode, or the consultation triggers below.
- **Haiku**: not used. Three tiers keep routing auditable; a Sonnet lane at
  low effort covers the mechanical end.

## The brief is the ceiling

A delegated lane is never better than its brief. Once the decision to
delegate is made, spend main-loop tokens on the brief, not on doing the lane
yourself. Every brief states:

- the goal and what "done" looks like,
- the files or places to start from,
- the constraints that must hold and what is out of scope,
- what to return, in what shape.

When a lane comes back wrong: fix the brief, then raise the effort, then
raise the model, in that order.

## Effort

The Agent tool and Workflow `agent()` set reasoning effort only when a skill
or the operator asks for it; this policy is that instruction.

- Sonnet mechanical lanes (inventory, sweeps, templated changes): `low`;
  `medium` when the lane has to make small judgment calls.
- Opus hard lanes and fresh-eyes reviews: `high`.
- Fable consultations: omit, inherit the session default.

## When to consult Fable

Build mode only; in design mode Fable is already in the loop. The operator
may also switch the main loop to Fable with `/model` instead of a sub-agent
consultation; the budget gate applies either way.

Only these three:

1. **A costly, hard-to-reverse design decision** (data model, public API or
   contract, module split, choice of core dependency) where the main loop sees
   at least two credible options and no clear winner.
2. **The main loop is stuck.** Two *different* hypotheses, each tested with
   evidence, have failed (retrying the same fix is one attempt). A Sonnet
   sweep has already mapped the relevant files; Fable gets the map, not the
   search.
3. **A new or changed trust boundary** (authentication, authorization,
   secrets, untrusted input reaching privileged code), before implementation,
   even when one option looks clear. Not: any edit in a security-adjacent file.

The operator saying "ask Fable" (or naming Fable for a question) bypasses the
triggers; the budget gate still applies.

Not for: routine review, exploration, anything a Sonnet sweep can answer,
"just to be sure" on a decision that is already clear, and product decisions
(what the user should experience, which external dependency to add). Those go
to the operator.

## How to consult

- Agent tool, `model: "fable"`. Say in the prompt what it may do: read files,
  grep, `git log`/`git diff`, run tests or a reproduction. And what it may not:
  no file edits, no commits, no installs, no network side effects.
- The brief, in this order:
  1. The question in one sentence.
  2. Constraints that must hold.
  3. The options, stated neutrally. Ask for Fable's own ranking first; give
     the main loop's leaning last, for Fable to attack. A handed-over
     conclusion tends to come back confirmed.
  4. If stuck: the hypotheses tested, how, and what happened (exact errors).
  5. The files to read: a short list of paths, no open-ended sweep. Let Fable
     read the code; don't paste whole files.
  6. The answer wanted: recommendation, reasoning, main risks, what would
     change the answer, claims tagged *verified in code* or *assumed*, and a
     word limit.
- One consultation per decision. A follow-up goes to the same agent
  (SendMessage), not to a new one.
- After the answer: check its factual claims against the code, decide, and
  record the decision and the reason in the plan. If the main loop disagrees
  with Fable, tell the operator both views instead of silently overriding.

## Budget

- Before each consultation, run `claude-limit`. Don't consult if `Fable 7-day`
  is at 90% or more, the all-model 7-day window is at 85% or more, or either
  is unknown. The main loop decides, or asks the operator.
- `Fable 7-day` comes only from the live endpoint. If it is unknown, tell the
  operator that Fable is unavailable and why; don't skip it silently.
- Design mode draws on the same window with every turn. At 90% of
  `Fable 7-day`, Fable stops and tells the operator; it does not switch
  silently.
- The 5-hour and 7-day rules in `claude-limit` apply to every model.
- Expect a few consultations a week. A second consultation in one session
  needs a one-line reason in the plan; before a third, ask the operator.
  Follow-ups through SendMessage count.

## Review

- The main loop reviews every delegated result before accepting it.
- Risky work (security, data, external integrations) gets an extra review by a
  fresh Opus sub-agent that did not carry the implementation context.
- Fable does not review code diffs. Its security role is the design-time
  consultation of trigger 3; review after implementation stays with the fresh
  Opus sub-agent.

## Planning

When planning, stamp the model on every task so spawning is mechanical:

`Sonnet → inventory · Sonnet ×2 → A, B · Opus sub → auth lane · Fable → consult: storage schema · main loop → integration, review`

## Exceptions

- If the operator names a model for a scoped task, honor it for that task
  only, then return to this policy.
- The operator can override any of this per session; absent that, this policy
  stands.
