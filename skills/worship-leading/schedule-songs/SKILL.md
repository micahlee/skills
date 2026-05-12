---
name: schedule-songs
description: Schedule worship songs into Planning Center services for a sermon series. Takes a date range, song block (from Google Doc or Basecamp), and sermon series info. Proposes 4 songs per Sunday (adoration opener, 2 flexible, charge/benediction closer) plus a Lord's Supper hymn. Iterates with user, then puts songs into PCO. Triggers on phrases like "schedule songs for [series/month]", "put songs in PCO", "assign songs to services", or "fill in songs for [date range]".
---

# Schedule Songs

CLI: `pco`

## Onboarding

Run `python3 scripts/onboard.py` from this skill directory to collect the local Sunday worship service type ID, song-history window, and document-reading command templates. The script writes `~/.config/agent-skills/schedule-songs.json`. Read that file before replacing placeholders or assuming a service type.

## Song Slot Structure

Each Sunday gets 5 songs placed into pre-existing PCO slots ("Song 1" through "Song 5"):

| Slot | Role | Criteria |
|------|------|----------|
| Song 1 | **Adoration** | Bold, celebratory opener — sets the tone for worship |
| Song 2 | **Flexible** | Any role from the song pool that fits the week's theme |
| Song 3 | **Flexible** | Any role from the song pool that fits the week's theme |
| Song 4 | **Charge / Benediction** | Upbeat or creedal send-off; must have a strong closing chorus |
| Song 5 | **Lord's Supper Hymn** | Slow, contemplative traditional hymn inserted as a new plan item after the "Lord's Supper" item. Search the full PCO library. |

---

## Workflow

### Step 1 — Gather Inputs

Ask the user for:
- **Date range**: which Sundays to schedule (e.g., "April 12 – May 17")
- **Song block source**: Google Doc link OR Basecamp message board post
- **Sermon series info**: per-Sunday passage + title + main idea (if not already in the song block)

---

### Step 2 — Read the Song Block

**From Google Doc:**
```bash
gws doc read <doc_id>
```

**From Basecamp:**
```bash
basecamp message read <message_id>
```

The song block contains a ranked pool of songs with roles, tiers, and recency tags. Extract:
- Song title, author, tempo, roles, tier, recency
- Note which songs are Adoration, Charge/Benediction roles

---

### Step 3 — Fetch PCO Plans

```bash
pco plans --count 10
```

Match each Sunday in the date range to a plan ID. If any Sunday is missing a plan, stop and tell the user.

For each plan, check what's currently in the song slots:
```bash
pco plan-items <plan_id>
```

---

### Step 4 — Check Song Recency

```bash
pco song-history --weeks 20
```

Use this to avoid scheduling songs used in the past 4 weeks and to flag recently overused songs.

---

### Step 5 — Propose Songs

For each Sunday, select:
- **Song 1**: Pick a Tier 1 or 2 Adoration song from the pool. Prefer `[fresh]` tags. Avoid songs used in the past 4 weeks.
- **Song 2**: Any pool song that fits the week's sermon theme. Can be Confession, Assurance, or Thanksgiving role.
- **Song 3**: Same as Song 2, complementing Song 2's role for variety.
- **Song 4**: Pick a song with a Charge/Benediction role from the pool. Must have a strong, singable closing chorus.
- **Song 5 (Hymn)**: Choose a slow, contemplative traditional hymn from PCO's full song library that connects to the sermon text or theme. Search by theme if needed:
  ```bash
  pco songs --query "<keyword>"
  ```

**Avoid repeating** the same song on back-to-back Sundays. Spread Tier 1 songs across the series — don't front-load them.

**Before finalizing the proposal**, verify every song is in PCO:
```bash
pco songs --query "<Song Title>"
```
If a song returns no results, find a replacement from the pool before presenting the proposal. Do not include songs that aren't in PCO.

---

### Step 6 — Present Proposal

Format as a list by Sunday:

```
April 13 — [Series Title: Sermon Title]
  Song 1 (Adoration):    <Title> — <Author> [fresh/recent]
  Song 2:                <Title> — <Author> [fresh]
  Song 3:                <Title> — <Author> [recent]
  Song 4 (Charge):       <Title> — <Author> [fresh]
  Song 5 (Lord's Supper):<Title> — <Author>

April 20 — [Series Title: Sermon Title]
  ...
```

Present all Sundays at once. Note any tradeoffs (e.g., a song being used back-to-back, a thin pool for a given role).

---

### Step 7 — Iterate

Adjust based on user feedback until the plan is approved. Common adjustments:
- Swap a specific song for a different one
- Move a song to a different slot or Sunday
- Replace a hymn with a different one
- Add a song not in the original pool (verify it's active in PCO first)

---

### Step 8 — Execute: Add Songs to PCO

For each Sunday, find the item IDs for Song 1–5:
```bash
pco plan-items <plan_id>
```

Then assign each song (you need the PCO song ID — get it via `songs --query`):
```bash
pco songs --query "<Song Title>"
# Note the song ID, then:
pco set-song <plan_id> <item_id> <song_id>
```

For the **Lord's Supper hymn**, insert it as a new item after the "Lord's Supper" item:
```bash
# Find the Lord's Supper item ID from plan-items output
pco songs --query "<Hymn Title>"
pco add-song-item <plan_id> <lords_supper_item_id> <song_id> "Lord's Supper"
```

Repeat for Songs 1–4 and the hymn across all Sundays.

After completing, run `plan-items` for each plan to verify all songs are set and the hymn appears after Lord's Supper.

---

## Notes

- Service type: Sunday Morning Worship (configure the local PCO service type ID)
- Song slots are pre-existing items named "Song 1" through "Song 5" — do not create new items
- Lord's Supper hymns don't need to come from the song block pool — search the full PCO library
- The `song-block` skill is the upstream step that produces the song pool used here
