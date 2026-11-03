---
name: claude-orchestrator-max
description: "Delegation policy for a Claude Max plan only (not Pro): Fable 5.1 runs the main loop and owns architecture, specs, briefs, integration and review; Opus 5.5 sub-agents carry the hard, precision lanes and fresh-eyes reviews; Sonnet 5.5 sub-agents gather context and carry simple bounded work. Fable is never spawned as a sub-agent. Load whenever spawning sub-agents (Agent tool or Workflow agent() calls) or planning any delegation. If the plan is unknown, load this one rather than claude-orchestrator: its first step checks the plan and hands off to claude-orchestrator when not on Max."
---

# Orchestration & delegation policy (Max plan, Fable in the main loop)

A routing policy for one Claude **Max** plan with one scarce main-loop model
and two delegate tiers: **Fable 5.1 in the main loop**, **Opus 5.5** for
hard lanes and reviews, **Sonnet 5.5** for context gathering and simple
execution.

Core law: **the scarce model is never spawned as a sub-agent and never does
throughput work.** Fable's tokens buy judgment: architecture, specs, briefs,
integration, synthesis, acceptance. Everything mechanical goes down a tier.

## Check the plan first

Run the `claude-limit` skill once per session, before the first delegation.
Its header shows the plan.

- `plan: max` → this policy applies.
- Anything else (e.g. after switching to a Pro account) → stop using this
  skill and follow `claude-orchestrator`. Fable is not available there.

## The pools

- **Fable** has its own weekly window (`Fable 7-day` in `claude-limit`) and
  also counts toward the all-model 7-day window, up to the share the line
  shows (`may use up to N% of 7-day`). Every main-loop turn draws on it.
- **Opus and Sonnet** share the plan's 5-hour and 7-day windows. Opus burns
  them much faster.

## The hard rules

1. **Never spawn Fable.** No Agent call or Workflow `agent()` with
   `model: "fable"`; the main loop is the only Fable. The one exception is
   the operator naming Fable for a scoped task.
2. **Always set `model` explicitly** (`"sonnet"` or `"opus"`) on every Agent
   call and every Workflow `agent()` call; `meta.phases` entries carry the
   same model for display. An omitted model inherits the main loop and
   silently fans out Fable. The Workflow reference says to omit it by
   default; under this policy, don't.
3. **Hands-on while limits are healthy.** The main loop does small and
   medium work itself; delegation has its own overhead. Delegate work that is
   parallelizable, large and mechanical, or would flood the main context.
4. **The main loop keeps the big picture.** Architecture, specs,
   contract-sensitive design, subtle state machines, integration, conflict
   resolution, final synthesis, judgment calls and acceptance stay in the
   main loop.
5. **The main loop writes the brief.** Sub-agents receive a spec written by
   Fable, not a goal to interpret. See "The brief is the ceiling".

## Choosing the delegate

The routing axis is **difficulty**, not only recon versus execution.

- **Sonnet, the default for bounded work**: exploration, codebase mapping,
  research sweeps, verification passes, templated changes, clones of an
  existing pattern, features that ride an existing pipeline end to end.
  Sonnet copes with a looser brief when the deliverable is understanding,
  not a diff.
- **Opus, for the hard and precision lanes**: correctness-sensitive paths,
  security-critical strengthen-never-relax changes, the largest surfaces,
  migrations and refactors against a complete spec, and the fresh-eyes
  review of risky work. Opus is a strong instruction follower: give it a
  complete, explicit spec and it executes it precisely. It is not a second
  main loop; it does not redesign.
- **Main loop (Fable)**: everything in rule 4, plus hard execution that
  needs the whole picture.
- **Haiku**: not used. Two delegate tiers keep routing auditable; a Sonnet
  lane at low effort covers the mechanical end.

Rule of thumb: **context gathering and simple execution → Sonnet; hard
execution against a spec → Opus; judgment, spec-writing and synthesis → the
main loop.**

## The brief is the ceiling

A delegated lane is never better than its brief. Once the decision to
delegate is made, spend main-loop tokens on the brief, not on doing the lane
yourself. Every brief states:

- the goal and what "done" looks like,
- the files or places to start from,
- the constraints that must hold and what is out of scope,
- what to return, in what shape.

An Opus lane gets the complete spec: exact files, exact contract, exact
acceptance checks, and what not to touch. When a lane comes back wrong: fix
the brief, then raise the effort, then raise the model, in that order.

## Effort

The Agent tool and Workflow `agent()` set reasoning effort only when a skill
or the operator asks for it; this policy is that instruction.

- Sonnet mechanical lanes (inventory, sweeps, templated changes): `low`;
  `medium` when the lane has to make small judgment calls.
- Opus hard lanes: `high`.
- Opus fresh-eyes review of risky work: `high`, regardless of the size of
  the diff.

## Review

- The main loop reviews every delegated result before accepting it; it does
  not accept a lane's own claim of success.
- Risky work (security, data, external integrations) gets an extra review by
  a fresh Opus sub-agent that did not carry the implementation context,
  before the main loop's acceptance.

## Budget

- Run `claude-limit` once per session; re-run it before a large fan-out.
- The 5-hour and 7-day rules in `claude-limit` apply to every model.
- `Fable 7-day` comes only from the live endpoint. If it is unknown, say so
  to the operator; don't guess.
- At 75% of `Fable 7-day`, tell the operator and keep main-loop reading
  light (Sonnet maps, Fable reads the map). At 90%, stop and tell the
  operator; the fallback is `/model opus`, after which the same delegation
  rules apply with Opus as the main loop and Fable out of the stack until
  the window resets. Never switch silently.

## Planning

When planning, stamp the model and effort on every task so spawning is
mechanical and no routing decision happens at spawn time:

`Sonnet low → inventory · Sonnet medium ×2 → A, B · Opus high → auth lane · Opus high → fresh-eyes review · main loop → spec, integration, acceptance`

## Exceptions

- If the operator names a model for a scoped task, honor it for that task
  only, then return to this policy.
- The operator can override any of this per session; absent that, this
  policy stands.
