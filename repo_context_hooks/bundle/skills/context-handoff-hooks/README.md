# context-handoff-hooks

Reusable skill package for GitHub repositories that need durable agent context across compact cycles.

## Included Files

- `SKILL.md`: usage and triggering rules
- `scripts/install_hooks.py`: installs hook config + runtime scripts into a target repo
- `scripts/repo_specs_memory.py`: syncs/updates `specs/README.md` memory contract
- `scripts/session_context.py`: prints session-start context (docs + next work + issue refs)
- `templates/hooks.json`: hook payload template
- Local telemetry events for `repo-context-hooks measure`

## Install Into a GitHub Repo

From the target repo root:

```bash
python .claude/skills/context-handoff-hooks/scripts/install_hooks.py --repo-root .
```

This command:

1. Creates `.claude/scripts/` if missing.
2. Copies runtime scripts into `.claude/scripts/`.
3. Adds/updates `hooks` in `.claude/settings.json`:
   - `SessionStart`
   - `PreCompact`
   - `PostCompact`
   - `SessionEnd`

## Validate

```bash
python .claude/scripts/repo_specs_memory.py session-start
python .claude/scripts/repo_specs_memory.py pre-compact
python .claude/scripts/session_context.py session-start
repo-context-hooks measure
```

## Notes

- Keep `README.md` user-facing.
- Keep `specs/README.md` engineering-facing.
- Keep `Open Issues and Next Work` current for best handoffs.
- Use `repo-context-hooks measure` to prove whether hooks emitted evidence.

## Companion Skills

- `skills/session-start-context-loader/SKILL.md`
- `skills/precompact-checkpoint/SKILL.md`
- `skills/postcompact-context-reload/SKILL.md`
