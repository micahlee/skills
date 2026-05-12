---
name: schedule-worship-leaders
description: Schedule worship leaders in Planning Center for a given month. Checks Sunday Morning Worship plans, availability/blockouts, and existing Service Responsibilities assignments; proposes a balanced Music Lead plan; waits for approval; then schedules those assignments in PCO. Triggers on phrases like "schedule worship leaders for July", "assign music leads for next month", "schedule Music Lead", or "fill worship leaders in PCO".
---

# Schedule Worship Leaders

Use this skill to schedule **worship leaders only** for Sunday Morning Worship plans in Planning Center. This is the first step before scheduling the full music team.

CLI: `pco`

## Onboarding

Run `python3 scripts/onboard.py` from this skill directory to collect local Planning Center IDs, the worship leader roster, and the repeating leader rotation. The script writes `~/.config/agent-skills/schedule-worship-leaders.json`. Read that file before replacing placeholders such as `<sunday_worship_service_type_id>`, `<service_responsibilities_team_id>`, and `<person_id>`.

If PCO reports missing credentials, run `pco init` and have the user enter the Planning Center API client ID and secret. The CLI stores them in the macOS Keychain for future commands.

## Local Configuration

Discover or configure these IDs before scheduling:

- Service type: `<sunday_worship_service_type_id>` -- Sunday Morning Worship
- Service Responsibilities / Music Lead team: `<service_responsibilities_team_id>`
- Band team: `<band_team_id>`

## Worship Leader Roster

| Person ID | Name | Typical Music Lead Instrument |
|-----------|------|-------------------------------|
| `<person_id>` | `<name>` | Acoustic Guitar |
| `<person_id>` | `<name>` | Keys |
| `<person_id>` | `<name>` | Keys |
| `<person_id>` | `<name>` | Acoustic Guitar |

## Assignment Rules

For each Sunday:

1. Schedule the worship leader only as `Music Lead` in the Service Responsibilities team.
2. Do **not** schedule `Call to Worship`. That is not the Music Lead's responsibility.
3. Do **not** schedule their Band instrument or Vocals here. That is handled later by the `schedule-music-team` skill.
4. Avoid assigning anyone who is blocked out that Sunday.
5. Use the locally configured repeating worship leader pattern. It is okay if not every leader is scheduled every month.
6. Preserve existing confirmed assignments unless the user explicitly asks to change them.
7. If `Music Lead` is already assigned to a different person, stop and ask before changing anything.
8. Do not send notifications. `pco teams schedule` queues notifications only.
9. If the user provides specific date-to-leader assignments, use those instead of generating a rotation, but still check blockouts and conflicts.

## Workflow

### Step 1 -- Determine the Month

Accept a month from the user, e.g. `July 2026`, `2026-07`, or `next month`. Convert it to `YYYY-MM`.

If the month is ambiguous, ask for clarification before querying PCO.

### Step 2 -- Inspect the Month

Run:

```bash
pco music month <YYYY-MM>
```

Use this output to:

- Verify all Sundays in the target month have plans. If any are missing, stop and tell the user which dates need plans created.
- Note current `Music Lead` assignments and statuses.
- Note `Out:` lines for blockouts.
- Note existing appearance counts.

Also inspect the recent past so the rotation continues from where it actually left off:

```bash
pco music month <previous YYYY-MM>
pco music month <two-months-prior YYYY-MM>  # if needed to find enough recent Music Lead history
```

Look at confirmed `Music Lead` assignments from the past several weeks, newest last, and map them onto the rotation:

```text
Leader A -> Leader B -> Leader C -> Leader A -> Leader B -> Leader D -> repeat
```

Find the most recent confirmed worship leader in that pattern and start the target month with the next expected leader. If recent assignments deviated from the pattern, choose the next assignments that get the sequence back on track with the least disruption.

Then inspect each plan's full team assignments:

```bash
pco teams show <plan_id>
```

Check for existing `Music Lead` assignments. Ignore `Call to Worship`; do not create, change, or validate it as part of this skill.

### Step 3 -- Build a Proposal

Create a month plan that includes only missing worship leader assignments.

Use the repeating pattern when choosing leaders:

```text
Leader A -> Leader B -> Leader C -> Leader A -> Leader B -> Leader D
```

Continue from the recent-past history rather than restarting the pattern at the beginning of each month. Skip a leader only when they are blocked out, already conflicting, or the user specifies a different assignment. When skipping, use the next available leader in the pattern and keep track of who was skipped so future assignments can move the sequence back toward the intended pattern.

Format:

```text
July 5 -- Leader B
  + Leader B -> Music Lead

July 12 -- Leader A
  + Leader A -> Music Lead

Counts:
  Leader A: 1 | Leader B: 1 | Leader C: 1 | Leader D: 1
Rotation:
  Previous: Leader B -> Leader D
  Proposed continuation: Leader A -> Leader B -> Leader C -> Leader A
```

Call out any tradeoffs, such as:

- someone serving twice
- a blocked-out preferred leader
- a date with an existing conflicting assignment
- any skipped rotation slot and how the proposal catches back up

Always show this dry run before scheduling, including plan IDs, skipped rotation slots, blockouts, and any conflicts. Ask for explicit approval before scheduling. Do not proceed from proposal to execution unless the user clearly confirms the dry run or has already given an explicit same-conversation instruction to apply that exact proposal.

### Step 4 -- Execute After Approval

For each approved missing assignment, run:

```bash
pco teams schedule <plan_id> <person_id> <service_responsibilities_team_id> "Music Lead"
```

Only run the command when `Music Lead` is actually missing. Do not duplicate existing assignments.

### Step 5 -- Verify

After scheduling, run:

```bash
pco teams show <plan_id>
```

for every plan touched. Confirm that each service has the intended `Music Lead` assignment.

Tell the user that notifications are queued in PCO and have not been sent.

## Boundaries

- Do not create Basecamp todo lists. That belongs to `create-monthly-worship-plan`.
- Do not schedule Band positions, Vocals, instruments, or enable Band sign-ups. That belongs to `schedule-music-team`.
- Do not schedule songs. That belongs to `schedule-songs`.
