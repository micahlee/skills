---
name: schedule-music-team
description: Schedule the music team on Planning Center for a given month. Checks that all services and music leads exist, checks availability, builds a balanced schedule (max 2 Sundays/person), presents the plan for approval, then executes it. Triggers on phrases like "schedule the music team for [month]", "fill in the band for [month]", or "schedule music for [month]".
---

# Schedule Music Team

CLI: `pco`

## Onboarding

Run `python3 scripts/onboard.py` from this skill directory to collect local Planning Center team IDs and the band roster. The script writes `~/.config/agent-skills/schedule-music-team.json`. Read that file before replacing placeholders such as `<band_team_id>`, `<service_responsibilities_team_id>`, and `<person_id>`.

Before scheduling, load or build the local roster for this church:

| Person ID | Name | Typical Positions |
|-----------|------|-------------------|
| `<person_id>` | `<name>` | Acoustic Guitar, Music Lead, Vocals |
| `<person_id>` | `<name>` | Bass Guitar |
| `<person_id>` | `<name>` | Percussion |
| `<person_id>` | `<name>` | Keys, Vocals, Music Lead |

Required local IDs:

- Band team ID: `<band_team_id>`
- Service Responsibilities / Music Lead team ID: `<service_responsibilities_team_id>`

---

## Workflow

### Step 1 — Get Full Month Overview

Run this single command to get everything at once — plans, Music Leads, current band assignments, blockouts, and appearance counts:

```bash
pco music-month <YYYY-MM>
```

From the output:
- **Verify all Sundays exist.** If any are missing, **stop and tell the user** which dates need plans created before proceeding.
- **Verify each Sunday has a confirmed Music Lead** (status `C`). If any ML is missing or declined (`D`), **stop and tell the user** before proceeding.
- **Note blockouts** (shown as `Out:` lines) — these people are unavailable that Sunday.
- **Note current appearance counts** at the bottom — if scheduling from scratch these will all be 0 or just the ML counts.

---

### Step 4 — Build the Schedule Plan

**Key rules:**

1. **Music Lead always gets three Band positions:** instrument + Vocals + (implicitly) Music Lead in Service Responsibilities. Always add both the ML's instrument AND a Vocals entry to the Band team. Determine their instrument from typical positions. All three positions on the same Sunday count as one appearance.

2. **Max 2 Sundays per person per month.** ML Sundays count toward this limit. This is a goal, not a hard rule — a 5th Sunday may require a 3rd appearance from someone.

3. **Never leave a service with only 1 person.** Minimum: ML + 1 other Band member.

4. **Scheduling logic:**
   - Track each person's appearance count (ML Sunday = 1 appearance, regardless of how many positions they fill that day)
   - Fill in remaining Band slots from the available pool, respecting the 2x limit
   - Prioritize: Percussion when available, Keys when the Music Lead plays guitar, Guitar when the Music Lead plays keys, Vocals as needed
   - When 5 Sundays in the month, someone will likely need a 3rd appearance — choose whoever has the fewest obligations or is most flexible

---

### Step 5 — Present Plan for Approval

Show the full schedule before executing. Format:

```
May 3 — Leader A (ML)
  + Leader A → Acoustic Guitar
  + Musician B → Keys
  + Vocalist C → Vocals

May 10 — Leader D (ML)
  + Leader D → Acoustic Guitar
  ...

Appearance counts:
  Leader A: 2  |  Leader D: 2  |  Musician B: 2  |  ...
```

**Ask the user to confirm before scheduling.** Point out any tradeoffs (someone at 3 Sundays, a thin service, missing percussion, etc.).

---

### Step 6 — Execute

For each person + position, run:
```bash
# Band positions (instruments, vocals)
pco teams schedule <plan_id> <person_id> <band_team_id> "<Position Name>"

# Music Lead's instrument (also Band team, same command)
pco teams schedule <plan_id> <person_id> <band_team_id> "<Position Name>"
```

**Position names** (case-sensitive): `Acoustic Guitar`, `Electric Guitar`, `Bass Guitar`, `Keys`, `Percussion`, `Piano`, `Vocals`, `Worship Leader`

For each Music Lead, always add **both** their instrument AND Vocals to the Band team:
```bash
pco teams schedule <plan_id> <ml_person_id> <band_team_id> "Acoustic Guitar"  # or Keys
pco teams schedule <plan_id> <ml_person_id> <band_team_id> "Vocals"
```

Do **NOT** re-add Music Lead — that's already in Service Responsibilities and was pre-assigned.

Do **NOT** send notifications. All scheduling uses `prepare_notification: true` (queued only). Tell the user notifications are queued and ready to send from PCO.

---

### Step 7 — Verify

After all commands complete, run `teams` for each plan and confirm the Band positions look correct.

---

### Step 8 — Enable Sign-ups

After verifying, enable Band team sign-ups for each plan in the month:

```bash
pco enable-signups <plan_id>
```

Run this for every plan scheduled that month. This allows team members to see and self-schedule on these plans in PCO.

---

## Notes

- Check long-term blockouts and leave notes before planning
- `availability` only checks PCO blockouts — it does not account for someone being a Music Lead on another Sunday (handle that manually in your count)
- ML appearances count toward the 2x limit even though the ML position itself is already scheduled — you're adding their *instrument* position, and their Sunday appearance is what's being tracked
