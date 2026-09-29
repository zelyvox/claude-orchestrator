# Claude Orchestrator

A delegation policy skill for Claude Code on a single $20 Claude Pro plan:
**Opus 5.5** runs the main loop and keeps judgment, specs and review;
**Sonnet 5.5** sub-agents gather context and carry simple execution.

It is a policy, not an engine: one Markdown file, no scripts.
See [SKILL.md](skills/claude-orchestrator/SKILL.md).

## Install

```bash
cp -r skills/claude-orchestrator ~/.claude/skills/
```

```powershell
Copy-Item -Recurse -Force skills/claude-orchestrator ~/.claude/skills/
```

The skill loads automatically whenever Claude Code plans a delegation or spawns sub-agents.

## License

[MIT](LICENSE)
