---
name: claude-limit
description: Show the Claude subscription usage windows (5-hour, 7-day, model-scoped weekly windows such as Fable on Max, plus any extra window the plan has) on one colored screen, live where possible. Use when the user asks "limit", "quota", "how much usage is left", or before a large delegation under an orchestrator skill.
---

# Claude Limit

Run the script that ships next to this file (adjust the path if the skill is installed
elsewhere):

```bash
python3 ~/.claude/skills/claude-limit/scripts/claude_limit.py --color always
```

On Windows use the Python launcher, not `python`:

```bash
py -3 ~/.claude/skills/claude-limit/scripts/claude_limit.py --color always
```

A bare `python` on Windows often resolves to the Microsoft Store app-execution alias,
which prints "Python was not found" and exits with code 49 even when Python is installed.

Show the output verbatim before summarising it — do not paraphrase or round the numbers.
In your reply, copy the lines without the color escape codes.

A window marked stale, expired or unknown is **unknown, not empty**. Don't treat its
percentage as current, and don't treat a missing reading as room to spend.

## Acting on it

Opus 5.5 and Sonnet 5.5 share one pool with two walls (model-scoped windows: see below). Each window has its own wall, and
the reset time matters as much as the percentage:

| Reading | Do |
|---|---|
| Both windows clear | Work normally. Don't hedge or narrate the number. |
| A window within ~5 points of full | Narrow the work: fewer parallel sub-agents, Sonnet over Opus, sequential. Say the number once. |
| 5-hour window at the wall **and resets within ~30 min** | Wait for the reset. Don't start a long run that will be cut in half. |
| 5-hour window at the wall, reset further off | Stop. Tell the user which work is waiting and when the window resets. |
| Weekly window at the wall | It won't come back for days. Delegate nothing, keep only essential work in the main loop, and ask. |
| A window unknown | Delegate nothing. Report what is known and ask. |

The fullest *valid* window is binding — a 12% 5-hour window next to an exhausted weekly
window means the pool is exhausted. Keep a few percent in reserve for whatever must run at
the end of a session (review, handoff notes): a job that dies mid-flight costs more than one
that never started.

### Model-scoped windows

Some plans add a weekly window for one model, e.g. `Fable 7-day` on Max. It binds **only that
model**: at its wall, stop routing work to that model and carry on with the others. Usage of
that model still counts toward the all-model 7-day window too. When the source reports it,
the line shows how much of the 7-day pool the model may use at most
(`may use up to 50% of 7-day`). A plan without such a window simply has no line for it —
that is not an unknown reading.

## Sources, in order

- **Live:** `https://api.anthropic.com/api/oauth/usage`, authenticated with the OAuth token in
  `~/.claude/.credentials.json`. The token is never printed, logged or written anywhere, and
  redirects are not followed. An expired token skips this source.
- **ravenline snapshot:** `~/.claude/ravenline-limits.json`, written by the ravenline statusline
  from Claude Code's statusline `rate_limits` field. Used only when younger than 45 minutes.
  All-zero values count as unreadable, not as an empty pool.
- Nothing else. The `~/.claude.json` usage cache is not used: it only refreshes on an
  interactive `/usage` and can be hours stale.

`--json` prints the same result in machine-readable form. Exit code is 1 when no window is known.

## Limits

- The live endpoint is undocumented. If Anthropic changes it, the script falls back or reports
  unknown; the offline tests cannot detect such a change.
- These are percentages of rolling subscription windows, not token counts.
- Model-scoped windows come only from the live endpoint; the ravenline snapshot carries the
  5-hour and 7-day windows only.

Decision table adapted from the `limit` skill in
[avenoxai/avenoxskills](https://github.com/avenoxai/avenoxskills) (MIT).
