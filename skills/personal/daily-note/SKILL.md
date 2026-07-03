---
name: daily-note
description: Create or populate a personal daily note from recurring tasks, carryovers, project notes, and calendar-aware meal context. Use when building tomorrow's daily note or refreshing today's task list.
---

# Daily Note Creation

Create or refresh the user's daily note from canonical task sources, calendar context, recurring routines, and external task systems. Treat the daily note as a work surface, not the task source of truth.

## Onboarding

Run `python3 scripts/onboard.py` from this skill directory to collect the vault path, daily note path pattern, task-note locations, projects folder, optional external task command, and boundaries. The script writes `~/.config/agent-skills/daily-note.json`. Read that file before assuming any vault layout or private task source.

**IMPORTANT:** Always use the `obsidian` CLI to read and write vault files — never use direct filesystem reads/writes (`cat`, `Write` tool, etc.). This avoids conflicts with Obsidian's live sync and cache.

In Codex, Obsidian CLI commands must be run outside the filesystem sandbox if the sandboxed command reports `The CLI is unable to find Obsidian. Please make sure Obsidian is running and try again.` The CLI talks to the already-running Obsidian app through `~/.obsidian-cli.sock`; sandboxed commands may be unable to use that socket even when Obsidian is open. Retry the same `obsidian ...` command with escalation rather than falling back to direct vault file edits or launching Obsidian.

Prefer Obsidian-native commands such as:

- `obsidian vault`
- `obsidian daily:path`
- `obsidian daily:read`
- `obsidian read path="Daily Notes/YYYY/MM/YYYY-MM-DD.md"`
- `obsidian create path="Daily Notes/YYYY/MM/YYYY-MM-DD.md" content="..." overwrite`
- `obsidian append path="Daily Notes/YYYY/MM/YYYY-MM-DD.md" content="..."`

When multiple vaults are present, pass `vault="Micah's Vault"` explicitly.

## Planning Note Resolution

Before reading, creating, appending, or replacing the target daily/planning note, resolve the target date through the configured Planning Notes command.

Use the configured `planning_note_cli` from `~/.config/agent-skills/daily-note.json` when present:

```bash
node "$planning_note_cli" ensure YYYY-MM-DD --vault "$vault_path"
```

Parse the returned JSON and use `block.path` as the target note path for all subsequent `obsidian read`, `obsidian create`, and `obsidian append` operations. Do not derive the target path directly from `daily_note_pattern` when planning-note resolution is configured.

For dates on or after the planning-note effective date, `ensure` creates the canonical planning note, compatibility stubs for non-anchor dates, and `Tasks/Planning Blocks.json` as needed. For legacy dates, use the returned `block.path` but do not expect `ensure` to create or persist a planning block.

**IMPORTANT:** Never copy raw Templater syntax (`<%*`, `tp.`, etc.) into the daily note. Always render actual content.

---

## Required References

Read these references before changing tasks or rendering task sections:

- [references/task-model.md](references/task-model.md) for task identity, source links, source ownership, and manual task handling.
- [references/reconciliation.md](references/reconciliation.md) for the run order, completion sync, recurring task advancement, manual task promotion, and failure policy.
- [references/selection.md](references/selection.md) for task caps, scoring, routines, stuck-task escalation, and agent candidates.
- [references/events-and-logs.md](references/events-and-logs.md) for the event outbox, run logs, daily-note sidecars, snapshots, and Axon event contracts.
- [references/note-format.md](references/note-format.md) for clean human-facing daily-note sections and sidecar metadata.

## Core Pipeline

Run daily-note task processing in this order:

1. Load config, resolve/ensure the target planning note path, load the daily-note task registry and per-note sidecar, and read the current target note if it exists.
2. Reconcile completed sourced daily-note task instances from the sidecar back to canonical sources, with legacy inline `task-ref` comments as a migration fallback only.
3. Advance completed recurring source tasks to the next future due date using fixed-schedule recurrence.
4. Promote unresolved manual daily-note tasks into canonical Obsidian task sources when confidence is high.
5. Publish decision-requested events for unresolved, stuck, vague, or repeatedly skipped tasks.
6. Update the task registry skip/completion/decision state.
7. Select bounded Commitments, Focus Tasks, Routines, Needs Decision items, Agent Queue candidates, and Context.
8. Render clean, human-facing daily-note sections without HTML ownership markers or hidden inline task metadata; preserve human-written content and no-ref human tasks.
9. Write the per-note sidecar, event outbox, run log, and snapshots for changed canonical files.

## Operating Rules

- Prefer deterministic scripts or structured parsing for task refs, recurrence advancement, registry updates, and event IDs. Do not rely on task text when sidecar metadata or legacy `task-ref` data exists.
- Keep daily notes clean. Do not emit `<!-- daily-note:... -->` markers or hidden same-line `task-ref` comments in newly rendered notes.
- Every generated checkbox should include a visible source link when there is a useful source. Store its `task_ref`, completion strategy, rendered text, source link, section, and line/fingerprint in the per-note sidecar.
- Daily note task sections are capped work surfaces, not backlog dumps.
- In the scheduled Axon morning workflow, Telegram delivery is not the daily-note final response. Let `/morning-briefing send` publish the `personal.morning-briefing` domain event with `payload.message`; Axon routes that compact event to Telegram through a subscriber workflow.
- Calendar commitments and meal/weather/context are not Focus Tasks.
- Repeated unchecked appearances are treated as skip signals and eventually become decision requests.
- Do not delete or clean up historical daily-note task instances.
- If a subsystem fails, degrade by subsystem when safe and record the warning in the run log. Mention it in the daily note only when the warning materially changes how Micah should trust or use the day plan.
