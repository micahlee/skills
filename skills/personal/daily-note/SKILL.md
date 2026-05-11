---
name: daily-note
description: Create or populate a personal daily note from recurring tasks, carryovers, project notes, and calendar-aware meal context. Use when building tomorrow's daily note or refreshing today's task list.
---

# Daily Note Creation

Vault path: configure this for the user's note system, for example `~/vault/Daily Notes/YYYY/MM/YYYY-MM-DD.md`.

**IMPORTANT:** Always use the `obsidian` CLI to read and write vault files — never use direct filesystem reads/writes (`cat`, `Write` tool, etc.). This avoids conflicts with Obsidian's live sync and cache.

**IMPORTANT:** Never copy raw Templater syntax (`<%*`, `tp.`, etc.) into the daily note. Always render actual content.

---

## Task Population Rules

### 1. Carryovers
- Copy unchecked `[ ]` tasks from previous day's note
- SKIP tasks that are date-specific (e.g. "drop off at 8:30am", "call X at 2pm", "appointment today")
- SKIP tasks that are clearly no longer relevant
- SKIP checked `[x]` tasks

### 2. Recurring Tasks — PARSE CADENCE ANNOTATIONS
Read the configured recurring-tasks note, such as `Tasks/Recurring.md`. For each task, evaluate its `cadence:` tag against the target date:

| Cadence | Rule |
|---|---|
| `daily` | Always include |
| `weekly:Mon` / `weekly:Wed` / etc. | Include only on that day of week |
| `biweekly:Fri` | Every other Friday — check last occurrence to determine if this week |
| `monthly:1st` | Include on the 1st of the month |
| `monthly:19th` | Include on the 19th of the month |
| `monthly:20th` | Include on the 20th of the month |
| `quarterly` | Every 3 months — use notes field for next date |
| `semiannual` | Every 6 months — use notes field for next date |
| `annual:Apr-1` | Include on that date each year |
| `bimonthly` | Every 2 months — use notes field for pattern |

For `biweekly`, `quarterly`, `semiannual`, `annual`, and `bimonthly`, always check the `notes:` field for the specific next date before including.

Do NOT include recurring tasks whose next date hasn't arrived yet.

### 3. Backlog
- Read the configured backlog note, such as `Tasks/Backlog.md`
- Surface 1-2 p1 items not yet in the daily note
- Surface relevant p2 items if timely (upcoming deadlines, seasonal tasks)
- Keep it to 1-2 items max — don't flood

### 4. Projects
- Scan the configured projects folder for active projects
- Pull in next actionable task from any project where relevant
- Keep it to 1 item unless something is urgent

### 5. Optional External Tasks
- If the user has a task CLI such as Basecamp, Google Tasks, or another project tool configured, pull only tasks assigned to the user that are overdue or due within the next 7 days.
- Add external tasks with due dates noted and keep the list short. Do not dump an entire project into the daily note.

---

## Task Ordering
- Personal before Church (within each priority section)
- Must → Should → Could priority order
- Within each section: unchecked above checked (heartbeat maintains this)

## Priority Mapping from Recurring.md
- `p1` → Must
- `p2` → Should
- `p3` / `p4` → Could

## Other Rules
- Carry forward stable personal sections from the previous day unless the user explicitly updates them.
- Respect the user's configured boundaries for work, personal, household, and faith/community tasks.
- Date-specific tasks (appointments, pickups) go in Must with time noted
- Dinner task: check Plan to Eat planner for what's scheduled; link to recipe URL `https://app.plantoeat.com/recipes/{id}`
