---
name: create-monthly-worship-plan
description: Create the monthly worship team planning todo list in Basecamp. Creates a todolist with predefined tasks, assignees, and due dates. Triggers on phrases like "create the [month] team planning list", "set up team planning for [month]", "create monthly worship plan for [month]".
---

# Create Monthly Worship Team Planning List

Creates the `{Month} Team Planning ({Leader})` todolist in the configured worship ministry Basecamp project.

## Context

- **Project ID**: `<basecamp_project_id>`
- **Account ID**: `<basecamp_account_id>`
- **Todoset ID**: `<basecamp_todoset_id>`
- **Core class assignee ID**: `<core_class_assignee_id>` when those tasks always belong to a fixed person

### Known Leaders

| Name | Basecamp ID | First Name (for list title) |
|------|-------------|----------------------------|
| `<leader name>` | `<basecamp_person_id>` | `<first name>` |
| `<leader name>` | `<basecamp_person_id>` | `<first name>` |

If the leader is someone else, look up their ID:
```bash
basecamp people list --in <basecamp_project_id> --json
```

---

## Workflow

### Step 1 — Gather Inputs and Check for Duplicates

Ask for (or extract from context):
- **Target month**: the month being planned for (e.g., "August 2026")
- **Leader**: who is leading that month (their first name goes in the list title)

Then verify a list for that month doesn't already exist:

```bash
basecamp todolists list --in <basecamp_project_id> --json
```

If a todolist already exists with that month's name, stop and tell the user. Also note the **current count** of todolists (call it `existing_count`) — you'll need it for positioning in Step 6.

### Step 2 — Compute Due Dates

Given target month **M**:
- **early_date**: 1st of (M − 2). If Saturday, use +2 days (Monday). If Sunday, use +1 day (Monday). Weekdays stay as-is.
- **mid_date**: 1st of (M − 1). Same weekend adjustment.
- **late_date**: 15th of (M − 1). Same weekend adjustment.
- **future_month**: M + 4, including year (e.g., September 2026 → January 2027, not just "January")

**Example** — Target = July 2026:
- early_date = May 1, 2026 (Friday ✓ — no adjustment, Friday is a weekday)
- mid_date = June 1, 2026 (Monday ✓)
- late_date = June 15, 2026 (Monday ✓)
- future_month = November 2026

**Example** — Target = September 2026:
- early_date = July 1, 2026 (Wednesday ✓)
- mid_date = August 1, 2026 (Saturday → August 3, 2026)
- late_date = August 15, 2026 (Saturday → August 17, 2026)
- future_month = January 2027

**Example** — Target = October 2026:
- early_date = August 1, 2026 (Saturday → August 3, 2026)
- mid_date = September 1, 2026 (Tuesday ✓)
- late_date = September 15, 2026 (Tuesday ✓)
- future_month = February 2027

### Step 3 — Show Plan for Confirmation

Before creating anything, display the full plan and ask the user to confirm:

```
Todolist: "{Month} Team Planning ({Leader})"

1. Schedule worship leaders → {Leader}, due {early_date}
   Note: Also assign "Call to Worship" service responsibility.
2. (If needed) Create Family Meeting service in PCO → {Leader}, due {early_date}
3. (If needed) Create Core Class service in PCO → {FixedAssignee}, due {early_date}
4. Schedule music teams → {Leader}, due {mid_date}
5. Populate songs & Lord's Supper in Planning Center → {Leader}, due {late_date}
   Note: Ensure songs have all of the details set and practice materials available.
6. (If needed) Publish sign-up sheet for open band spots → {Leader}, due {late_date}
7. Create team planning list for {future_month} → {Leader}, due {mid_date}
8. (If needed) Schedule Family Meeting music team → {Leader}, due {mid_date}
9. (If needed) Schedule Core Class music team → {FixedAssignee}, due {mid_date}
```

### Step 4 — Create the Todolist

```bash
basecamp todolists create --name "{Month} Team Planning ({LeaderFirstName})" --in <basecamp_project_id> --json
```

Note the returned todolist **ID** for use in the next steps.

### Step 5 — Create All 9 Todos

Use `basecamp api post` for **all todos** with `"notify": false` to suppress Basecamp notifications. Descriptions for todos 1 and 5 are included at creation time. Run sequentially.

**Todo 1 — Schedule worship leaders** (with description)
```bash
basecamp api post "https://3.basecampapi.com/<basecamp_account_id>/buckets/<basecamp_project_id>/todolists/<todolist_id>/todos.json" \
  --data '{"content": "Schedule worship leaders", "due_on": "<early_date>", "assignee_ids": [<leader_id>], "notify": false, "description": "<div>Also assign \"Call to Worship\" service responsibility.</div>"}' \
  --json
```

**Todo 2 — (If needed) Create Family Meeting service in PCO**
```bash
basecamp api post "https://3.basecampapi.com/<basecamp_account_id>/buckets/<basecamp_project_id>/todolists/<todolist_id>/todos.json" \
  --data '{"content": "(If needed) Create Family Meeting service in PCO", "due_on": "<early_date>", "assignee_ids": [<leader_id>], "notify": false}' \
  --json
```

**Todo 3 — (If needed) Create Core Class service in PCO** *(fixed assignee when configured — notify: false)*
```bash
basecamp api post "https://3.basecampapi.com/<basecamp_account_id>/buckets/<basecamp_project_id>/todolists/<todolist_id>/todos.json" \
  --data '{"content": "(If needed) Create Core Class service in PCO", "due_on": "<early_date>", "assignee_ids": [<core_class_assignee_id>], "notify": false}' \
  --json
```

**Todo 4 — Schedule music teams**
```bash
basecamp api post "https://3.basecampapi.com/<basecamp_account_id>/buckets/<basecamp_project_id>/todolists/<todolist_id>/todos.json" \
  --data '{"content": "Schedule music teams", "due_on": "<mid_date>", "assignee_ids": [<leader_id>], "notify": false}' \
  --json
```

**Todo 5 — Populate songs & Lord's Supper in Planning Center** (with description)
```bash
basecamp api post "https://3.basecampapi.com/<basecamp_account_id>/buckets/<basecamp_project_id>/todolists/<todolist_id>/todos.json" \
  --data '{"content": "Populate songs & Lord'\''s Supper in Planning Center", "due_on": "<late_date>", "assignee_ids": [<leader_id>], "notify": false, "description": "<div>Ensure songs have all of the details set and practice materials available.</div>"}' \
  --json
```

**Todo 6 — (If needed) Publish sign-up sheet for open band spots**
```bash
basecamp api post "https://3.basecampapi.com/<basecamp_account_id>/buckets/<basecamp_project_id>/todolists/<todolist_id>/todos.json" \
  --data '{"content": "(If needed) Publish sign-up sheet for open band spots", "due_on": "<late_date>", "assignee_ids": [<leader_id>], "notify": false}' \
  --json
```

**Todo 7 — Create team planning list for {future_month}**
```bash
basecamp api post "https://3.basecampapi.com/<basecamp_account_id>/buckets/<basecamp_project_id>/todolists/<todolist_id>/todos.json" \
  --data '{"content": "Create team planning list for {future_month}", "due_on": "<mid_date>", "assignee_ids": [<leader_id>], "notify": false}' \
  --json
```

**Todo 8 — (If needed) Schedule Family Meeting music team**
```bash
basecamp api post "https://3.basecampapi.com/<basecamp_account_id>/buckets/<basecamp_project_id>/todolists/<todolist_id>/todos.json" \
  --data '{"content": "(If needed) Schedule Family Meeting music team", "due_on": "<mid_date>", "assignee_ids": [<leader_id>], "notify": false}' \
  --json
```

**Todo 9 — (If needed) Schedule Core Class music team** *(fixed assignee when configured — notify: false)*
```bash
basecamp api post "https://3.basecampapi.com/<basecamp_account_id>/buckets/<basecamp_project_id>/todolists/<todolist_id>/todos.json" \
  --data '{"content": "(If needed) Schedule Core Class music team", "due_on": "<mid_date>", "assignee_ids": [<core_class_assignee_id>], "notify": false}' \
  --json
```

### Step 6 — Reposition the Todolist

New todolists are created at position 1 (top). Move it to the correct chronological position using the `existing_count + 1` value you noted in Step 1 (that's where the new month belongs at the end of the existing list):

```bash
basecamp api put "https://3.basecamp.com/<basecamp_account_id>/buckets/<basecamp_project_id>/todosets/todolists/<todolist_id>/position?position=<existing_count+1>" --data '{}' --json
```

Note: this endpoint uses `3.basecamp.com` (web UI), not `3.basecampapi.com`.

### Step 7 — Verify

Confirm the list is in the right spot and share the URL with the user:

```
https://3.basecamp.com/<basecamp_account_id>/buckets/<basecamp_project_id>/todolists/<todolist_id>
```

---

## Todo Summary Table

| # | Task | Assignee | Due |
|---|------|----------|-----|
| 1 | Schedule worship leaders | Leader | early_date |
| 2 | (If needed) Create Family Meeting service in PCO | Leader | early_date |
| 3 | (If needed) Create Core Class service in PCO | Fixed assignee | early_date |
| 4 | Schedule music teams | Leader | mid_date |
| 5 | Populate songs & Lord's Supper in Planning Center | Leader | late_date |
| 6 | (If needed) Publish sign-up sheet for open band spots | Leader | late_date |
| 7 | Create team planning list for {M+4} | Leader | mid_date |
| 8 | (If needed) Schedule Family Meeting music team | Leader | mid_date |
| 9 | (If needed) Schedule Core Class music team | Fixed assignee | mid_date |

## Notes

- Configure whether a fixed assignee always handles core class tasks (todos 3 and 9), regardless of who leads that month.
- **future_month** = target month + 4 (e.g., August → December, September → January of next year).
- **Date adjustment**: if the 1st or 15th falls on Saturday, use Monday (+2 days); if Sunday, use Monday (+1 day).
- If there is an alternating leader pattern, infer it from recent lists or ask the user to confirm it before creating the next list.
