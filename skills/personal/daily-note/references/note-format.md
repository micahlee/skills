# Daily Note Format

Daily-note generation should leave the note Micah interacts with simple, readable, and editable. The daily note is the work surface; machine ownership, task refs, scoring, event IDs, and refresh audit data belong in sidecar state and run logs.

## Human-Facing Shape

Recommended top-level task/context shape:

```markdown
## Commitments
- On Call, through 2026-06-01 9:00 AM.

## Focus Tasks
### Must
- [ ] BUY: Carrie flowers ([[Tasks/Recurring#^task-buy-carrie-flowers|src]])

### Should
- [ ] Schedule music teams ([src](https://3.basecamp.com/...))

### Could

## Routines
- [ ] Clean one surface ([[Tasks/Recurring#^clean-one-surface|src]])

## Needs Decision
- [ ] Decide whether the overdue budget review should happen today, be scheduled, snoozed, or dropped ([[Tasks/Recurring#^review-budget|src]])

## Agent Queue
- [ ] Add file-watch reconcile events ([[01 - PERSONAL/01 - PROJECTS/Axon/Backlog Designs/file-watch-reconcile-events|design]])

## Context
Dinner, weather, Planning Center, Basecamp, and user-relevant warnings.
```

Do not emit HTML comments such as `<!-- daily-note:focus:start -->` or inline hidden refs such as `<!-- task-ref: ... -->` in newly rendered daily notes.

## Sidecar State

Write machine metadata to a per-note sidecar, defaulting to:

```text
Tasks/Daily Note State/YYYY-MM-DD.json
```

Recommended shape:

```json
{
  "schema_version": 1,
  "processing_date": "2026-05-29",
  "daily_note_path": "Daily Notes/2026/05/2026-05-29.md",
  "generated_at": "2026-05-29T07:10:00-04:00",
  "sections": {
    "Focus Tasks": {
      "previous_generated_markdown": "### Must\n- [ ] ...\n",
      "content_fingerprint": "sha256:..."
    }
  },
  "rendered_tasks": [
    {
      "task_ref": "obsidian:Tasks/Recurring.md#^task-buy-carrie-flowers",
      "completion_strategy": "advance_recurrence",
      "source_type": "obsidian",
      "source_uri": "Tasks/Recurring.md#^task-buy-carrie-flowers",
      "source_link": "[[Tasks/Recurring#^task-buy-carrie-flowers|src]]",
      "section": "Focus Tasks > Must",
      "rendered_text": "BUY: Carrie flowers",
      "line_fingerprint": "sha256:...",
      "completed": false
    }
  ],
  "warnings": []
}
```

The global registry still tracks task history across days. The sidecar tracks what was rendered into one daily note and how to reconcile that visible checkbox later.

## Refresh Rules

Prefer a sidecar-assisted three-way merge for generated sections:

1. Read the current daily note and the previous sidecar.
2. For each generated section, compare the current section body with `previous_generated_markdown`.
3. Preserve human additions, edits, and no-ref checkboxes when they do not conflict.
4. Replace stale generated lines using the new selection.
5. Write the clean note plus an updated sidecar.

Use heading boundaries for standard sections (`## Commitments`, `## Focus Tasks`, `## Routines`, `## Needs Decision`, `## Agent Queue`, `## Context`). If the section is missing, insert it in the standard order. If a section has substantial human edits that cannot be merged confidently, leave it unchanged, write a warning to the run log, and publish a decision event when useful.

## Checkbox Format

Generated checkboxes are plain Markdown with optional visible source links:

```markdown
- [ ] BUY: Carrie flowers ([[Tasks/Recurring#^task-buy-carrie-flowers|src]])
- [ ] BASECAMP: Schedule music teams ([src](https://3.basecamp.com/...))
- [ ] Choose the next concrete action for "Improve async agent work" ([[Tasks/Backlog#^task-improve-async-agent-work|src]])
```

Do not make the whole task text a link. Do not append hidden comments.

## Legacy Migration

Existing daily notes may contain old machine markers and inline `task-ref` comments. Treat them as read-only reconciliation hints:

- parse legacy `task-ref` comments when sidecar data is missing
- strip legacy comments only when explicitly cleaning or refreshing the note
- do not add new legacy markers

## Preserve Stable Personal Sections

Carry forward non-task personal sections from the previous day unless the user explicitly changed the structure. Never copy raw Templater syntax into the note.

## Context Content

Context is for information that shapes the day but is not itself Micah-actionable work:

- calendar commitments and time blocks
- weather
- dinner from Plan to Eat, with recipe links in the form `https://app.plantoeat.com/recipes/{id}` when available
- Planning Center summary
- Basecamp/external task summary
- user-relevant warnings that materially change trust in the plan

Keep technical processing summaries in the run log unless Micah needs to see them to interpret the note.
