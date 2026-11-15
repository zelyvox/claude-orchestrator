---
name: claude-orchestrator
description: "Delegation policy for a Claude Pro plan only (not Max, no Fable): Opus 5.5 runs the main loop and owns architecture, specs, briefs, integration and review; Sonnet 5.5 sub-agents gather context and carry simple bounded work; Opus 5.5 sub-agents only for hard lanes that must run in parallel or would flood the main context, and for fresh-eyes reviews; Haiku 5.5 only for very large data cleanup. Load whenever spawning sub-agents (Agent tool or Workflow agent() calls) or planning any delegation."
---

# Orchestration & delegation policy (Pro plan, Opus in the main loop)

A routing policy for one $20 Claude **Pro** plan: **Opus 5.5 in the main
loop**, **Sonnet 5.5** as the default delegate, **Opus 5.5** sub-agents for
the rare hard lane and for fresh-eyes reviews, **Haiku 5.5** only for very
large data cleanup. Fable is not available on Pro.

Every model draws from the same small pool, and Opus burns it much faster,
so Opus is the scarce tier.

Core law: **Opus tokens buy judgment, not throughput.** The main loop does
the work it can carry itself; everything mechanical goes down a tier.

## The hard rules

1. **Always set `model` explicitly** (`"sonnet"`, `"opus"` or `"haiku"`) on
   every Agent call and every Workflow `agent()` call; `meta.phases` entries
   carry the same model for display. An omitted model inherits the main loop
   and silently fans out Opus. The Workflow reference says to omit it by
   default; under this policy, don't.
2. **Hands-on while limits are healthy.** The main loop does small and
   medium work itself; delegation has its own overhead (brief, spawn,
   review). Delegate only work that is parallelizable, large and mechanical,
   or would flood the main context. Do not open a sub-agent by reflex.
3. **The main loop keeps the big picture.** Architecture, specs,
   contract-sensitive design, subtle state machines, integration, conflict
   resolution, final synthesis, judgment calls and acceptance stay in the
   main loop.
4. **The main loop writes the brief.** Every sub-agent gets a brief written
   by the main loop; how tight it is depends on the tier and the work. See
   "The brief is the ceiling".

## Choosing the delegate

The routing axis is **difficulty**, not only recon versus execution.

- **Sonnet, the default for bounded work**: exploration, codebase mapping,
  research sweeps, verification passes, templated changes, clones of an
  existing pattern, features that ride an existing pipeline end to end.
- **Main loop (Opus)**: everything in rule 3, plus hard execution:
  multi-file implementation, real debugging, correctness-sensitive paths,
  security-critical strengthen-never-relax changes. On Pro this is done in
  the main loop by default, not delegated.
- **Opus sub-agent, sparingly**: a hard lane only when it must run in
  parallel with other work or would flood the main context, and the
  fresh-eyes review of risky work (see Review). State the reason in the
  plan. Opus chooses the route inside its lane; it does not redesign the
  architecture or the contract the main loop set.
- **Haiku (`model: "haiku"`, effort `medium`), only for very large data
  cleanup**: thousands of rows or files to normalize, deduplicate, classify
  or extract. Not for small or medium lanes: measured on 2026-10-12, no
  gain over Sonnet on two small tasks and much slower on the second; the
  ~50k-token spawn cost per sub-agent eats a cheap model's advantage on
  small work. No `low` effort: Haiku stops early at `low` with a long
  brief. Bulk use is not measured yet: run `claude-limit` before and after
  the first runs and note the cost.

Rule of thumb: **context gathering and simple execution → Sonnet; hard
execution, judgment, spec-writing and review → the main loop; Opus
sub-agent only when the hard lane cannot wait in line.**

When unsure between two tiers, take the cheaper one and verify the result;
escalate one tier on failure rather than starting high.

## The brief is the ceiling

A delegated lane is never better than its brief. Once the decision to
delegate is made, spend main-loop tokens on the brief, not on doing the lane
yourself. Every brief states:

- the goal and what "done" looks like,
- the files or places to start from,
- the constraints that must hold and what is out of scope,
- what to return, in what shape,
- for any lane that edits files: "run a check that actually exercises the
  change (test, build, the file on disk); if you could not run one, say
  which and why". A low-effort lane may otherwise report done unverified.

How tight to write depends on who reads it and what the work is:

- **Sonnet** (the usual reader): name the files or area, list the steps in
  order when order matters, give the output format and what not to touch.
  One task per agent. When something is unclear or does not match the
  brief, stop and report instead of improvising.
- **Opus, judgment work** (debugging, research, implementation where the
  route is open): fairly loose. The goal and why it matters, the context it
  cannot discover on its own, the constraints, and what done looks like.
- **Opus, contract work** (security, data, migrations, a public interface,
  anything where the shape is already decided): the complete spec. Exact
  files, exact contract, exact acceptance checks, and what not to touch.
- **Haiku** (bulk cleanup): one mechanical rule set, stated exactly, with
  two or three input and output examples. Split the data into batches small
  enough that a bad batch is cheap to redo, have each batch write to its own
  output file, and sample every batch before merging. Never ask this tier
  to decide what the rules should be.

When a lane comes back wrong: fix the brief, then raise the effort, then
raise the model, in that order.

When Sonnet is stuck: if the same task is still unsolved after two Sonnet
rounds (brief fixed, effort raised), do not open a third. The main loop
takes that task itself, telling the operator in one line first.

## Effort

The Agent tool and Workflow `agent()` set reasoning effort only when a skill
or the operator asks for it; this policy is that instruction. A sub-agent on
a different model than the main loop does not inherit the session's effort,
so write it on every call.

- Sonnet: `low` for mechanical lanes (inventory, sweeps, templated
  changes); `medium` when the lane has to make small judgment calls. Pick
  per lane.
- Opus sub-agent, hard lane: `medium` by default. `high` for security,
  data and other correctness-critical lanes.
- Opus fresh-eyes review: `high`, regardless of the size of the diff.
- Haiku: `medium`, never `low`.
- The main loop's own effort is the session setting (`/effort`); the main
  loop cannot change it. Expected for Opus: `medium`, `high` for heavy
  planning or hard debugging. `xhigh` and `max` drain the Pro pool fast:
  never suggest them, use them only when the operator sets them, and if the
  session opened at `xhigh` or `max`, say so once in one line at the start.

## Review

- The main loop reviews every delegated result before accepting it; it does
  not accept a lane's own claim of success.
- For a lane that is not risky, the main loop's own review is the whole
  review, Opus sub-agent lanes included. A second Opus pass on every lane
  costs more than the Pro pool can carry.
- Only risky work (security, data, external integrations) gets an extra
  review by a fresh Opus sub-agent that did not carry the implementation
  context, before the main loop's acceptance. Give the reviewer the spec
  and where the change is, not the implementer's report: "skip style,
  report only gaps that affect correctness, show the command you ran and
  its output".
- No second-opinion lanes: on a genuinely hard call with real ambiguity,
  ask the operator.
- Do not park a lane: a sub-agent's cache goes cold after five minutes, so
  a lane left open for hours rewrites its whole context on every resume.
  Have it write its state to a file and finish; start a new lane to resume.

## Workflows and ultracode

- Ultracode stays off as a session setting. When the operator puts
  `ultracode` in a prompt or asks for a workflow, that one task runs as a
  workflow. It fits audits, broad reviews, batch production and
  multi-source research; it does not fit work that needs the operator's
  decision midway, because the script cannot ask.
- Every `agent()` call in the script names `model` and `effort` from this
  policy (reading and sweeps Sonnet `low`, judgment sweeps Sonnet `medium`,
  verification of risky findings Opus `high`). Implementation lanes in a
  workflow are Sonnet unless the plan states why one needs Opus.
- If the script will run more than 5 agents, tell the operator the agent
  count and models in one line first. A Pro pool runs out much sooner than
  a Max one.

## Budget

- Run `claude-limit` once per session, before the first delegation, for
  the limits; re-run it before a large fan-out. Its decision table applies
  to every model. The operator chooses which policy to load; do not use the
  plan line to switch policies.
- There is no model-scoped weekly window on Pro: the 5-hour and 7-day
  windows bind every model alike, and Opus fills them fastest.
- At 70% of the binding window (5-hour or 7-day, whichever is fuller), cut
  Opus first: open no new Opus sub-agent and keep only essential work in
  the main loop. If the main loop itself has to keep going past that, tell
  the operator in one line and ask for `/model sonnet`; never switch
  silently. The `claude-limit` rules for a window near or at its wall still
  apply on top of this.

## Planning

When planning, stamp the model and effort on every task so spawning is
mechanical and no routing decision happens at spawn time:

`Sonnet low → inventory · Sonnet medium ×2 → A, B · main loop → auth change, integration, acceptance · Opus high → fresh-eyes review`

## Exceptions

- If the operator names a model for a scoped task, honor it for that task
  only, then return to this policy.
- The operator can override any of this per session; absent that, this
  policy stands.
