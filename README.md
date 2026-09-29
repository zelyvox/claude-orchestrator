# Claude Orchestrator

[![Tests](https://github.com/zelyvox/claude-orchestrator/actions/workflows/tests.yml/badge.svg)](https://github.com/zelyvox/claude-orchestrator/actions/workflows/tests.yml)

Skills for running Claude Code on a single $20 Claude Pro plan with two models:
**Opus 5.5** in the main loop keeps judgment, specs and review;
**Sonnet 5.5** sub-agents gather context and carry simple execution.

| Skill | What it does |
|---|---|
| [claude-orchestrator](skills/claude-orchestrator/SKILL.md) | Delegation policy: who gets which work. One Markdown file. Loads whenever sub-agents are spawned. |
| [claude-limit](skills/claude-limit/SKILL.md) | Colored screen of the 5-hour and 7-day usage windows, plus what to do at each level. |

## Install

```bash
cp -r skills/claude-orchestrator skills/claude-limit ~/.claude/skills/
```

```powershell
Copy-Item -Recurse -Force skills/claude-orchestrator, skills/claude-limit ~/.claude/skills/
```

`claude-limit` needs Python 3.11+ (standard library only).

## Tests

```bash
python -m unittest discover -s tests -v
```

Offline: no real token, no real endpoint.

## License

[MIT](LICENSE)
