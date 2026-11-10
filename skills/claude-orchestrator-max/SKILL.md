---
name: claude-orchestrator-max
description: "Delegation policy for a Claude Max plan only (not Pro): Fable runs the main loop and owns architecture, specs, briefs, integration and review; Opus 5.5 sub-agents carry the hard, precision lanes and fresh-eyes reviews; Sonnet 5.5 sub-agents gather context and carry simple bounded work. Fable is never spawned as a sub-agent. Load whenever spawning sub-agents (Agent tool or Workflow agent() calls) or planning any delegation. If the plan is unknown, load this one rather than claude-orchestrator: its first step checks the plan and hands off to claude-orchestrator when not on Max. Does not apply while the lider skill is active: lider is self-contained and replaces it."
---

# Orchestration & delegation policy (Max plan, Fable in the main loop)

A routing policy for one Claude **Max** plan with one scarce main-loop model
and two delegate tiers: **Fable in the main loop**, **Opus 5.5** for
hard lanes and reviews, **Sonnet 5.5** for context gathering and simple
execution.

Core law: **the scarce model is never spawned as a sub-agent and never does
throughput work.** Fable's tokens buy judgment: architecture, specs, briefs,
integration, synthesis, acceptance. Everything mechanical goes down a tier.

If the `lider` skill is active in this session, stop here and follow it
instead: Lider is self-contained and this policy does not apply under it.

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
   the operator naming Fable for a scoped task. The advisor (`/advisor`) is
   not a sub-agent, but it rereads the whole conversation uncached on every
   call and draws on the Fable window: off by default, on only when the
   operator turns it on.
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
5. **The main loop writes the brief.** Every sub-agent gets a brief written
   by Fable; how tight it is depends on the tier and the work. See "The
   brief is the ceiling".

## Choosing the delegate

The routing axis is **difficulty**, not only recon versus execution.

- **Sonnet, the default for bounded work**: exploration, codebase mapping,
  research sweeps, verification passes, templated changes, clones of an
  existing pattern, features that ride an existing pipeline end to end.
  Sonnet copes with a looser brief when the deliverable is understanding,
  not a diff.
- **Opus, for the hard and precision lanes**: multi-file implementation,
  real debugging, research that needs judgment, correctness-sensitive paths,
  security-critical strengthen-never-relax changes, the largest surfaces,
  migrations and refactors, and the fresh-eyes review of risky work. Opus
  chooses the route inside its lane; it does not redesign the architecture
  or the contract the main loop set. It is not a second main loop.
- **Main loop (Fable)**: everything in rule 4, plus hard execution that
  needs the whole picture.
- **Haiku**: not used. Measured on 2026-10-12: no gain over Sonnet on two
  tasks, slower on the second, quota difference not measurable; the
  operator decided to keep two delegate tiers. A Sonnet lane at low effort
  covers the mechanical end.

Rule of thumb: **context gathering and simple execution → Sonnet; hard
execution → Opus; judgment, spec-writing and synthesis → the main loop.**

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

- **Opus, judgment work** (debugging, research, multi-file implementation
  where the route is open): fairly loose. The goal and why it matters, the
  context it cannot discover on its own, the constraints, and what done
  looks like. Leave the route to it; over-specifying costs main-loop tokens
  and removes the judgment the Opus lane is paid for.
- **Opus, contract work** (security, data, migrations, a public interface,
  anything where the shape is already decided): the complete spec. Exact
  files, exact contract, exact acceptance checks, and what not to touch.
- **Sonnet** (a notch tighter): name the files or area, list the steps in
  order when order matters, give the output format and what not to touch.
  One task per agent. When something is unclear or does not match the
  brief, stop and report instead of improvising.

When a lane comes back wrong: fix the brief, then raise the effort, then
raise the model, in that order.

## Effort

The Agent tool and Workflow `agent()` set reasoning effort only when a skill
or the operator asks for it; this policy is that instruction.

- Sonnet mechanical lanes (inventory, sweeps, templated changes): `low`;
  `medium` when the lane has to make small judgment calls.
- Opus hard lanes: `medium`. Independent tests found medium and high equal
  on completion; high's gain is in subtle bugs, which the review catches.
- Opus fresh-eyes review (every Opus lane and any risky work): `high`,
  regardless of the size of the diff.

## Review

- The main loop reviews every delegated result before accepting it; it does
  not accept a lane's own claim of success.
- Every Opus lane that edits files, and any risky work (security, data,
  external integrations), gets an extra review by a fresh Opus sub-agent that did not carry the implementation context,
  before the main loop's acceptance. Give the reviewer the spec and where
  the change is, not the implementer's report: "skip style, report only
  gaps that affect correctness, show the command you ran and its output".
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
  policy (reading and sweeps Sonnet `low`, implementation Opus `medium`,
  verification of risky findings Opus `high`). The Workflow reference says
  to omit the model; under this policy, don't, or every agent is Fable.
- If the script will run more than 10 agents, tell the operator the agent
  count and models in one line first.
- If ultracode is on for the whole session, say so once: every substantive
  task becomes a workflow, effort rises, the large-workflow warning and the
  concurrent sub-agent cap are lifted, and the limits fill sooner.

## Budget

- Run `claude-limit` once per session; re-run it before a large fan-out.
- The 5-hour and 7-day rules in `claude-limit` apply to every model.
- `Fable 7-day` comes only from the live endpoint. If it is unknown, say so
  to the operator; don't guess.
- At 85% of `Fable 7-day`, hand the main loop to Opus: tell the operator
  in one line and ask for `/model opus`, and start no new lane until it
  arrives. The same delegation rules then apply with Opus as the main loop
  and Fable out of the stack until the window resets. Never switch
  silently. The threshold is the operator's standing decision and matches
  the lider skill.

## Planning

When planning, stamp the model and effort on every task so spawning is
mechanical and no routing decision happens at spawn time:

`Sonnet low → inventory · Sonnet medium ×2 → A, B · Opus medium → auth lane · Opus high → fresh-eyes review · main loop → spec, integration, acceptance`

## Exceptions

- If the operator names a model for a scoped task, honor it for that task
  only, then return to this policy.
- The operator can override any of this per session; absent that, this
  policy stands.
