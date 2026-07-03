# Daily Note Task Selection

The daily note should show what is realistically useful today. It should not mirror the whole backlog.

## Sections

Use separate surfaces:

- `Commitments`: calendar/time context, not checkboxes.
- `Focus Tasks`: Micah-actionable chosen work.
- `Routines`: recurring chores, habits, and maintenance.
- `Needs Decision`: one or two stuck or unclear items that need judgment.
- `Agent Queue`: conservative agent-doable candidates.
- `Context`: summaries such as dinner, weather, Planning Center, Basecamp, and processing results.

## Focus Task Caps

Hard cap:

- Must: max 3
- Should: max 3
- Could: max 3

`Must` means deadline, commitment, blocker, or explicitly chosen for today. Do not put ordinary reminders in `Must`.

Selection priority:

1. urgent, due, or blocking
2. in-motion recent tasks
3. context-matched backlog or project tasks
4. neglected but still concrete tasks

Prefer continuing plausible in-motion work over rotating randomly through neglected backlog. Repeated skips prevent in-motion tasks from becoming immortal.

Respect source priority first, then day context and source order. When ties remain, keep the user's existing domain preference: personal/household before church/community inside the same priority class unless a deadline or commitment says otherwise.

## Routines

Routines have their own cap and do not count against Focus Tasks.

Default cap:

- due today: max 3
- overdue but not decision-needed: max 2

Sort routines by priority first, then overdue age, then source order. Overdue routines can appear, but the daily note must not become an overdue landfill.

## Skip And Stuck Detection

For now, infer skipped from history and registry:

```text
system-owned task appeared unchecked
+ next daily-note processing sees it still unchecked
= one skip
```

After 2-3 skips, stop treating repetition as a reminder. Mark the task decision-needed and publish a decision-requested event. This applies to routines, backlog tasks, project tasks, and manual tasks after promotion.

Reasons include:

- `repeated_carryover`
- `stuck_recurring`
- `needs_refinement`
- `manual_task_needs_routing`
- `source_ambiguous`

Show only 1-2 decision-needed items in the daily note, but publish decision-requested events for all current stuck items each processing run.

## Agent Candidates

Agent-doable work should not count against Micah's Focus Task cap.

Only classify a task as an agent candidate when it is:

- concrete
- bounded
- source-linked
- likely safe to start
- has enough context to choose a next action

Publish `obsidian.task.agent_candidate` events for agent-doable tasks. Show only 2-3 in the daily note's Agent Queue. Axon decides whether to launch work, ask, queue, or ignore.

Vague tasks such as "Improve async agent work" should become decision/refinement items before becoming agent candidates.

## External Tasks

Pull only external tasks assigned to the user that are overdue or due within the next 7 days. Do not dump an entire external project into the daily note.

External task selection follows the same caps:

- deadline/blocker items may enter Focus Tasks
- agent-doable external items may become Agent Queue candidates
- unclear external tasks become decision/refinement events
