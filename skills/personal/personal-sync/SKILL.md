---
name: personal-sync
description: Run a unified personal planning loop across weekly review, daily-note preparation, reflection, morning briefing, and progress checks using calendar, tasks, Obsidian, inbox, goals, projects, and bounded supporting data. Use when the user invokes /personal-sync, asks to plan or refresh a week or day, review recent progress, prepare a briefing, reflect on daily patterns, or check whether priorities are moving.
---

# Personal Sync

Keep human planning surfaces calm while maintaining richer, auditable agent context.

## Quick start

1. Read `~/.config/agent-skills/personal-sync.json`.
2. If it is missing, run `python3 scripts/onboard.py`.
3. Resolve the requested mode; default to `weekly` for `/personal-sync` with no mode.
4. Read the shared references required below, then the selected mode reference.
5. Use the Obsidian CLI for vault writes and normal reads. A deterministic read-only helper may use a configured file path when documented. Resolve dates through the configured Planning Notes CLI before touching planning notes.

## Modes

- `weekly`: read [mode-weekly.md](references/mode-weekly.md).
- `refresh`: read [mode-refresh.md](references/mode-refresh.md).
- `daily`: read [mode-daily.md](references/mode-daily.md).
- `reflect`: read [mode-reflect.md](references/mode-reflect.md).
- `brief`: read [mode-brief.md](references/mode-brief.md).
- `progress`: read [mode-progress.md](references/mode-progress.md).

Legacy aliases map as follows: `/daily-note` → `daily`, `/daily-dream` → `reflect`, `/morning-briefing` → `brief`, and `/progress-check` → `progress`.

## Required shared references

Before any write, read:

- [source-model.md](references/source-model.md)
- [surfaces.md](references/surfaces.md)
- [task-model.md](references/task-model.md)
- [events-and-logs.md](references/events-and-logs.md)

For weekly or daily planning, also read [capacity-model.md](references/capacity-model.md).

## Invariants

- Human daily notes contain only Scripture Memory, non-obvious Calendar Notes, and Todos.
- Human weekly notes contain choices, not agent reasoning or source dumps.
- Detailed evidence, Dream material, nudges, coverage, warnings, and rationale live under the configured agent-context paths.
- Canonical task state remains in its source system. Planning notes are work surfaces.
- Calendar events are context, not completable tasks.
- Attended planning asks unresolved questions one at a time, always with a recommended answer.
- Scheduled runs may refresh managed context and high-confidence factual state, but never invent goals, silently reprioritize approved outcomes, or reschedule commitments.
- Preserve human edits. If a safe merge is uncertain, leave the surface unchanged, log the warning, and request a decision.
- Degrade by source; do not pretend missing coverage is complete.

## Output

Return a compact summary of the mode, dates, surfaces changed, decisions requested, and unavailable sources. In preview or quiet scheduled modes, do not write. In Axon send modes, publish the specified compact event and keep the operator response brief.
