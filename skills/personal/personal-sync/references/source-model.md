# Source Model

Personal Sync uses bounded evidence and an explicit authority hierarchy.

## Windows

- Weekly look-back: the previous 7 calendar days, ending yesterday.
- Primary planning window: the next 7 days, starting today unless a week/date is specified.
- Horizon: the following 7 days, for a total 14-day look-forward.
- Daily/brief/progress: the requested local date in the configured timezone.

## Always read when relevant

- the last approved human and agent weekly notes
- resolved planning notes in the look-back and primary windows
- configured authoritative goal/current-season notes
- canonical recurring/backlog tasks and per-note task state
- active project notes with recent activity, deadlines, or explicit goal links
- Obsidian Inbox status, including ambiguous/failed items
- calendar events across the 14-day look-forward
- assigned Basecamp work due or overdue in the window
- relevant Axon task, decision, warning, reflection, and nudge events

## Scheduled source adapters

Scheduled runs must prefer `scheduled_calendar_command` and
`scheduled_external_tasks_command` when configured. These commands should read
deployment-owned Axon projections or another credential source that is known to
work without an interactive shell. Direct provider commands remain useful for
attended runs and as an explicitly logged fallback, but scheduled automation
must not assume that an interactive login or shell environment is available.

If a scheduled adapter is absent, stale, unauthorized, or unavailable, mark
that source degraded and continue with the remaining evidence. Never convert an
empty result from a failed adapter into authoritative “no events” or “no tasks.”

Daily reflection and prior agent context are always evidence for weekly mode, but their detail stays agent-facing.

## Default when available and cheap

- Gmail metadata, senders, subjects, and thread-level actionable summaries
- health/fitness/food summaries
- Planning Center responsibilities
- meal, weather, travel, and household logistics

## Drill down only when triggered

- full email bodies
- finance and transaction detail
- shopping/order detail
- health raw metrics
- deep project trees or linked documents

Drill down only when a configured goal, recent strong signal, explicit task, or upcoming event makes the detail relevant. Follow at most 1–3 central linked notes per major signal.

## Authority rules

- Configured goal/current-season notes are authoritative goals.
- Approved weekly outcomes are authoritative for the current week.
- Project activity is evidence, not proof of priority.
- Tasks are owned by canonical source systems.
- Family Calendar is authoritative for non-work planning blocks when configured.
- Scheduled runs preserve the last approved interpretation when evidence is ambiguous.

## Privacy and coverage

Use private data to reason, but summarize it at the right altitude. Do not copy full email, prayer, journal, health, or finance detail into events or human weekly notes.

Record `read`, `unavailable`, `stale`, and `triggered_detail` sources in the agent note and run log, including which configured adapter was attempted. Mention a missing source to the user only when it materially changes trust in the plan.
