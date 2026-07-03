# Process Inbox Routing Reference

## Inbox States

- `#inbox/ambiguous`: the destination or intent is unclear. Automation skips until the tag is removed.
- `#inbox/failed`: the route is clear, but a required write or integration failed. Include an inline note explaining how to fix or retry. Automation skips until the tag is removed.
- `#inbox/duplicate`: the item appears to already exist in the intended destination. Include an inline pointer to the likely existing entry. Automation skips until the tag is removed.

Only moved items are recorded in the Processing Log. Ambiguous, failed, and duplicate items stay in the Inbox and appear only in the run summary.

## Destination Types

- General Backlog: cross-project actionable items without a clear project match.
- Project Board: project-specific Kanban or checklist note for actionable project work.
- Project Note: project-specific reference or context that is not itself a task.
- Shopping List: store-specific list when the store is explicit or strongly implied.
- Read Later: low-friction holding list for raw links after public inspection confirms that is the right route.
- Reading List: categorized reading idea with enough context for an existing heading or obvious new low-risk section.
- Someday/Maybe: possible future actions with no current commitment.
- Gift Idea: gift for a specific person or occasion.
- People Note: person plus useful context, not a bare name.
- Area Note: existing ongoing area of responsibility or interest.
- Daily Note: date-specific tasks, day-specific context, and journal-like fragments.

Do not route to archived folders or completed-task history. PARA is the organization model, not a destination.

## Confidence Rules

- Automation moves only high-confidence items.
- If the destination note or destination section is unclear, leave the item as `#inbox/ambiguous`.
- New destinations are allowed only when confidence is high and the destination is low risk.
- Low-risk new destinations include obvious store shopping lists, simple resource notes, reading-list sections, missing daily notes, and the missing Processing Log.
- New project folders, project boards, areas, archive structures, and sensitive church/work destinations require interactive approval unless explicitly named.

## Project Routing

Project Board or Project Note routing requires a clear project match: exact or strongly implied project name. Loose topic similarity is not enough.

Actionable items without a project match may go to General Backlog only when the backlog category is clear. Otherwise mark ambiguous.

For project Kanban boards, append new tasks to `Backlog` unless the user approved another column.

## General Backlog Sections

Use the most specific existing section:

- `p1` only when urgency/high priority is clear.
- `p2 - Should Do` for ordinary actionable tasks.
- `p2 - Home Projects` for home repair, maintenance, yard, garage, basement, or house projects.
- `p3 - Eventually` for low-pressure future ideas.

If the backlog file is clear but the section is not, mark ambiguous.

## Shopping

Use a Shopping List only for store-clear shopping items:

- Explicit store: `Buy brake fluid at Lowes`.
- Strongly implied store: `Costco dishwasher pods`.

If the item is something to buy but no store is clear, route it as an actionable task to General Backlog when possible.

## Links

Do not route URLs from domain alone. Inspect enough public page title, metadata, and readable main content to classify the item.

- Links requiring login, unavailable pages, social/app links that cannot be inspected, or unclear content become `#inbox/ambiguous`.
- Bare URLs may go to Read Later only after inspection supports that route.
- A URL plus clear context may route elsewhere, such as Gift Idea, Project Note, or Reading List.

## Date And Calendar Routing

Resolve relative dates using the run date and configured timezone.

- Dated Task: task-like item with a date. Move to the appropriate Daily Note only; do not create a calendar entry.
- Calendar-Worthy Item: appointment, event, reservation, travel, hard deadline, or intentional time block. Move to the Daily Note and create a Google Calendar entry.
- Hard Deadline: due, closes, expires, or must happen by a specific date. Add a Daily Note task and an all-day calendar date marker unless an explicit time is given.

Date-only calendar-worthy items create all-day events. Items with explicit times create timed events. Do not invent times.

Task-like dated items go in the Daily Note Must section. Create a missing Daily Note using the configured daily note pattern and template rules.

## People, Fragments, And Notes

- Bare person names are ambiguous.
- Person plus context goes to People Note.
- Compressed fragments stay ambiguous unless intent is clear.
- Lightly rewrite destination entries to clarify intent/context while preserving meaning.

## Duplicate Detection

Compare the proposed destination entry against the intended destination only, not the whole vault. For sectioned files, compare within the intended section when known.

If a likely duplicate exists, leave the original in the Inbox with `#inbox/duplicate` and an inline pointer to the likely existing entry.

## Processing Log

The Processing Log is prepend-only. For each moved item, record:

```md
## YYYY-MM-DD HH:MM

- Original: <original inbox text>
  Destination: <destination path and section>
  Entry: <final destination entry>
```

For calendar-worthy items, include both destinations:

```md
- Original: <original inbox text>
  Destinations:
    - Daily Note: <path and section>
    - Default Calendar: <all-day/timed date details>
  Entry: <final destination entry>
```

## Run Summary

Automation output should include concise counts:

- moved count and destination breakdown
- ambiguous count
- duplicate count
- failed count

