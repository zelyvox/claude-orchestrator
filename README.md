# Claude Orchestrator

[![Tests](https://github.com/zelyvox/claude-orchestrator/actions/workflows/tests.yml/badge.svg)](https://github.com/zelyvox/claude-orchestrator/actions/workflows/tests.yml)

Skills for running Claude Code on a single Claude subscription without wasting
it. **Opus 5.5** in the main loop keeps judgment, specs and review;
**Sonnet 5.5** sub-agents gather context and carry simple execution. On a Max
plan, **Fable 5.1** takes the main loop and Opus moves down to the hard lanes
and reviews.

| Skill | Plan | What it does |
|---|---|---|
| [claude-orchestrator](skills/claude-orchestrator/SKILL.md) | Pro ($20) | Delegation policy for Opus + Sonnet: who gets which work. |
| [claude-orchestrator-max](skills/claude-orchestrator-max/SKILL.md) | Max ($100) | Fable 5.1 in the main loop owns architecture, specs, briefs and acceptance; Opus 5.5 sub-agents carry the hard lanes and fresh-eyes reviews; Sonnet 5.5 gathers context and does simple bounded work. Effort per lane, and a budget rule for the Fable weekly window. |
| [lider](skills/lider/SKILL.md) | Max ($100) | Turkish-language policy. Leader mode: the main-loop leader (Fable 5.1, or Opus/Sonnet when limits run low) does no work itself: it writes no files, runs no commands and reads no raw material; it writes briefs, hands the work to Sonnet/Opus lanes and accepts on their reports alone. A layer on top of claude-orchestrator-max. The ladder (basamak) picks the leader model from claude-limit at session start: Fable → Opus → Sonnet. |
| [claude-limit](skills/claude-limit/SKILL.md) | any | Colored screen of the 5-hour and 7-day usage windows, plus model-scoped weekly windows such as Fable on Max, and what to do at each level. |

Each policy is one Markdown file and loads only when sub-agents are spawned;
the rest of the time only its one-line description is in context.

## Install

Install the policy for your plan, plus `claude-limit`.

Pro:

```bash
cp -r skills/claude-orchestrator skills/claude-limit ~/.claude/skills/
```

Max:

```bash
cp -r skills/claude-orchestrator-max skills/lider skills/claude-limit ~/.claude/skills/
```

PowerShell: `Copy-Item -Recurse -Force skills/<policy>, skills/claude-limit ~/.claude/skills/`
(Max: `Copy-Item -Recurse -Force skills/claude-orchestrator-max, skills/lider, skills/claude-limit ~/.claude/skills/`)

If you switch between a Pro and a Max account, install both policies. Each
description names its plan, and the Max policy checks the plan through
`claude-limit` and hands over to the Pro one when it is not on Max.

`claude-limit` needs Python 3.11+ (standard library only).

## Does it work? What we measured (Pro policy)

Short answer: **when Claude Code delegates work to sub-agents, this skill
roughly halved the cost of the same job, with the same quality.** It does not
make Claude delegate more often.

Why it matters: a sub-agent spawned without a `model` inherits the main
model. With Opus in the main loop, every sub-agent is silently Opus too.

All runs: `claude -p --model opus` on a Pro plan, October 2026. "Without
skill" runs used `--disable-slash-commands`, so no skills were loaded.

### Test 3: big job with delegation (the main result)

A monorepo with 4 services (~4,400 lines, 89 modules) and **80 planted bugs**
(40 security, 40 logic). The prompt asked Claude to audit and fix everything,
with one sub-agent per service. It did not name a model. Grading used 80 bug
tests and 73 behaviour tests that the agents never saw.

| | Without skill | With skill |
|---|---|---|
| Sub-agents ran on | 4 × Opus | 4 × Sonnet |
| Cost (API-equivalent) | $5.97 | **$3.16 (−47%)** |
| Opus output tokens | 150k | 18k |
| 5-hour limit used | +40 points | +23 points |
| 7-day limit used | +3 points | +2 points |
| Wall time | 9m 12s | 6m 08s |
| Bugs fixed | 79 / 80 | 79 / 80 |
| Behaviour tests | 73 / 73 | 73 / 73 |

Each side missed one bug, a different one each.

Keep in mind:
- **One run per side.** The gap is large, but this is not a statistical study.
- The two runs used **two different Pro accounts**, so the limit percentages
  are a rough comparison. The cost figure is measured per run and does not
  depend on the account; trust it more.
- One behaviour test was too strict (it rejected a valid file-signature check
  that both sides added). It was fixed and both runs were re-graded the same
  way.

### Test 1: does the skill change the model? (small job)

6 small modules, the prompt asks for one sub-agent per module, 3 runs per side.

| | Without skill | With skill |
|---|---|---|
| Sub-agent calls with `model` set | 0 / 18 | 18 / 18 |
| Sub-agents actually ran on | Opus (18) | Sonnet (18) |

No clear limit saving here: the job was too small, and each Sonnet sub-agent
pays its own start-up cost.

### Test 2: does the skill make Claude delegate? (natural job)

A 19-module package with 20 planted security bugs. The prompt only said
"audit and fix", nothing about sub-agents. 3 runs per side.

- Opus did the whole job itself in all 6 runs. No sub-agents, so the skill
  never loaded.
- Both sides fixed 20 / 20 bugs; limit use was within noise.

**Takeaway:** the saving comes when work is actually delegated (Test 3). Ask
for sub-agents on large, parallel work. On small and medium jobs Opus works
alone, which is also what the skill recommends.

## Tests

```bash
python3 -m unittest discover -s tests -v   # Windows: py -3 -m unittest discover -s tests -v
```

Offline: no real token, no real endpoint.

## License

[MIT](LICENSE)
