# Daily Note Task Reconciliation

Reconciliation runs before today's task selection. The goal is to clean canonical state first so completed work is not reintroduced as fresh unchecked work.

## Order

1. Read the registry and current/recent daily notes.
2. Load per-note sidecars for current/recent daily notes and identify system-owned rendered checkboxes from sidecar `rendered_tasks`.
3. Parse legacy same-line `task-ref` comments only when a sidecar is missing or incomplete.
4. Reconcile checked instances to their canonical source.
5. Advance recurring source tasks when applicable.
6. Promote clear unresolved manual tasks.
7. Emit decision events for unclear manual tasks or stuck sourced tasks.
8. Update registry state.
9. Select and render today's bounded clean sections from canonical state.

## Completion Sync

Completion behavior depends on `completion_strategy`:

- `sync_back`: mark the canonical source task complete.
- `advance_recurrence`: keep the recurring source task unchecked and advance its due date.
- `external_complete`: call the external source's completion API or CLI when semantics are clear.
- `external_link_only`: record completion locally only if useful; do not mutate the external source.
- `no_sync`: update registry only.

Do not rewrite historical daily notes just to add completion dates.

## Clean-Note Matching

For current clean notes, match visible checkbox lines to sidecar entries using the most stable available data:

- exact line fingerprint from the last render
- visible source link plus section path
- legacy inline `task-ref` when present

Do not depend on task text alone unless the task is human-owned and no source mutation will happen.

## Recurring Tasks

Recurring task completion advances the source due date instead of leaving the source task overdue.

Policy:

- Fixed schedule by default.
- Advance from the scheduled due date, not the actual completion date.
- Skip missed occurrences and advance until the next due date is after the processing date.
- Keep the recurring source task unchecked.
- Record `last_completed`, `completion_count`, old due date, and new due date in the registry/run log.

Example: a weekly task due 2026-05-01 completed on 2026-05-29 advances to the next future weekly occurrence, not 2026-05-08.

Only use an after-completion policy when the source task explicitly says to do so.

## Manual Task Promotion

Unchecked no-ref daily tasks should have a path into the trusted system.

High-confidence promotion examples:

- obvious household task -> configured backlog/home section
- obvious project task -> matching active project board or backlog
- obvious purchase -> shopping list or backlog
- obvious agent/repo task -> matching project backlog if the project match is strong

If destination confidence is low, do not guess. Publish `obsidian.task.decision_requested` with reason `manual_task_needs_routing`.

Promote before rendering today's note. Yesterday remains unchanged; today may show the new sourced task if it wins selection.

## Source Writes

Use Obsidian CLI writes for vault mutations. When mutating canonical task files:

- Build edits in memory first.
- Validate each source task still exists exactly once.
- Add stable block IDs only when missing and needed.
- Snapshot every canonical file that will be changed.
- Apply all planned edits carefully.
- Record changed files and warnings in the run log.

Do not use broad text replacement. Task text can be rewritten in daily rendering, but source mutation must use TaskRef or exact source location.

Daily note refreshes should use heading-bounded sections plus sidecar snapshots. If a section cannot be refreshed without risking human edits, leave it as-is and log the warning instead of adding machine comments back into the note.

## Failure Policy

Hard fail when:

- the target daily note cannot be read or written
- the registry cannot be read or safely initialized
- a planned canonical mutation has ambiguous source identity
- source parsing cannot distinguish the task that would be changed

Soft fail when:

- an external source is unavailable
- one source task cannot be reconciled but others can proceed safely
- the event outbox cannot be written and note generation itself is still safe

Soft failures must appear in the run log and daily-note processing summary.
