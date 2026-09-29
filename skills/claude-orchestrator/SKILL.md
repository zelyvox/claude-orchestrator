---
name: claude-orchestrator
description: "Delegation policy for a single Claude Pro subscription where the main loop runs on Opus 5.5 (the scarce tier) and Sonnet 5.5 sub-agents do the bounded work. The main loop owns architecture, judgment and review; Sonnet gathers context and carries simple execution. Load whenever spawning sub-agents (Agent tool) or planning any delegation."
---

# Orchestration & delegation policy (Opus + Sonnet, one Pro plan)

A routing policy for one $20 Claude plan: **Opus 5.5 in the main loop** and
**Sonnet 5.5 as the only delegate tier**. Both draw from the same usage pool;
Opus burns it much faster, so it is the scarce tier.

Core law: **Opus must not do pleb work, and must not be spawned as a sub-agent
by reflex.** Its tokens buy judgment, not throughput.

## The hard rules

1. **Opus as sub-agent: sparingly, never aggressively.** Set `model: "sonnet"`
   explicitly on every Agent call — never omit-and-inherit, or you silently fan
   out Opus. A rare judgment-heavy delegated task may use Opus, only when Sonnet
   genuinely can't carry it, and the reason is stated in the plan.
2. **Hands-on while limits are healthy.** Prefer the main loop doing small and
   medium work itself over reflexive delegation — delegation has its own
   overhead (brief + review). Delegate work that is parallelizable, large and
   mechanical, or would flood the main context. Check usage (`/usage`, or the
   `claude-limit` skill when installed) before a large delegation.
3. **No mid-tiers.** Two models: Opus 5.5 and Sonnet 5.5. More tiers make
   routing decisions unauditable.
4. **The main loop keeps the big picture.** Architecture, specs,
   contract-sensitive design, subtle state machines, integration and conflict
   resolution, final synthesis, review and acceptance — all in the main loop.

## Choosing the delegate

- **Sonnet — context gathering and simple execution.** Exploration, codebase
  mapping, research sweeps, verification passes, and light execution: templated
  changes, clones of an existing pattern, features that ride an existing
  pipeline end-to-end.
- **Opus (main loop) — hard or precision work.** Security-critical
  strengthen-never-relax changes, correctness-sensitive paths, core seams,
  the largest surfaces. Done in the main loop, not delegated by default.

Rule of thumb: **context gathering and simple execution → Sonnet; hard
execution, judgment, spec-writing and review → the main loop.** A Sonnet lane
is bounded by the quality of its brief — invest tokens in the brief.

## Review

- The main loop reviews every delegated result before accepting it.
- Risky work (security, data, external integrations) gets an extra review by a
  fresh Opus sub-agent that did not carry the implementation context.
- No second-opinion lanes: on a genuinely hard call with real ambiguity, ask
  the operator.

When planning, stamp the model per task (`Sonnet → inventory · Sonnet ×2 → A, B
· main loop → integration`) so spawning is mechanical and no routing decision
happens at spawn time.

## Exceptions

- If the operator explicitly names a model for a scoped task, honor it for that
  task only, then return to this policy.
- The operator can override any of this per session; absent that, this policy
  stands.
