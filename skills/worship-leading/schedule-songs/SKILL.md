---
name: schedule-songs
description: Schedule worship songs into Planning Center services for a sermon series. Takes a date range, song block (from Google Doc or Basecamp), and sermon series info. Proposes five songs per Sunday with an upbeat adoration opener, flexible middle songs, a clearly marked sacramental Lord's Supper hymn, and a sermon-text-focused response/charge song, while aiming for one older/classical hymn per set. Iterates with user, then puts songs into PCO. Triggers on phrases like "schedule songs for [series/month]", "put songs in PCO", "assign songs to services", or "fill in songs for [date range]".
---

# Schedule Songs

CLI: `pco`

## Onboarding

Run `python3 scripts/onboard.py` from this skill directory to collect the local Sunday worship service type ID, song-history window, and document-reading command templates. The script writes `~/.config/agent-skills/schedule-songs.json`. Read that file before replacing placeholders or assuming a service type.

## Song Slot Structure

Each Sunday gets 5 songs placed into pre-existing PCO slots ("Song 1" through "Song 5"):

| Slot | Role | Criteria |
|------|------|----------|
| Song 1 | **Adoration** | Upbeat, joyful opener that prompts celebratory praise; avoid reflective/meditative songs here |
| Song 2 | **Flexible** | Confession, Assurance, Thanksgiving, or Petition; slower/reflective songs usually fit here or later |
| Song 3 | **Flexible** | Complements Song 2 and prepares for the sermon text |
| Song 4 | **Lord's Supper Hymn** | Clearly mark as Lord's Supper; normally an older/classical hymn directly connected to the sacrament |
| Song 5 | **Sermon Response / Charge** | Closest possible fit to the sermon text and main idea; may also function as charge/benediction |

Each service set should normally include at least one older/classical hymn, not only modern songs or modern hymns. The Lord's Supper hymn often satisfies this requirement.

Tempo matters. Treat "upbeat" as a musical feel supported by BPM, meter, and known arrangement feel, not merely an Adoration role. BPM is stored on PCO arrangements, not only songs, so fetch or inspect arrangement BPM before classifying a song as an opener.

PCO BPM may be a click-track value rather than the felt pulse; many arrangements use a doubled BPM for metronome subdivisions. When evaluating opener energy, record both the raw PCO BPM and a normalized/felt BPM when the raw number is clearly doubled (for example, 146 raw may feel like 73). Do not classify a song as upbeat from raw BPM alone.

Energy should descend after the opener. Songs 2 and 3 should move from higher energy to lower energy, helping the service settle into confession, assurance, petition, or sermon preparation. Do not put a higher-energy Song 3 after a more reflective Song 2 unless the user explicitly approves.

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
- Song title, author, tempo/BPM when provided, roles, tier, recency
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

Also gather tempo data for candidate songs:
- Prefer explicit BPM from the PCO arrangement that will be used.
- `pco plans export <plan_id> --include-raw --json` exposes arrangement attributes such as `bpm` and `meter` for songs already scheduled in recent plans.
- If the current CLI search output does not expose BPM for an unscheduled candidate, query the song's arrangements from the PCO API or inspect an existing plan where that arrangement was used.
- Do not infer "upbeat" from the song role or raw BPM alone. Record unknown BPM as `BPM unknown` and treat it as a tradeoff, especially for Song 1.
- If PCO BPM appears doubled for click-track use, show it as `raw BPM / felt BPM` in the proposal, and use the felt BPM plus musical character for opener suitability.

---

### Step 5 — Propose Songs

For each Sunday, select:
- **Song 1**: Pick an upbeat Tier 1 or 2 Adoration song from the pool that prompts joyful praise. Prefer `[fresh]` tags. Avoid songs used in the past 4 weeks. Do not use slow, reflective, or meditative songs as the opener unless the user explicitly asks. Use BPM and meter as guardrails, but normalize doubled click-track BPM before judging feel; generally prefer a clear upbeat felt pulse, while interpreting 6/8, cut time, and half-time arrangements by musical feel rather than raw BPM alone.
- **Song 2**: Any pool song that fits the week's sermon theme. Can be Confession, Assurance, Thanksgiving, or Petition. Choose a song with equal or lower energy than Song 1.
- **Song 3**: Same as Song 2, complementing Song 2's role for variety and helping move toward the sermon text. Choose a song with lower or equal energy than Song 2; the normal movement is Song 1 high, Song 2 medium, Song 3 lower/reflective.
- **Song 4 (Lord's Supper)**: Choose a hymn directly connected to the sacrament: Christ's body and blood, the cross, union with Christ, communion, pardon, atonement, or remembrance. Prefer older/classical hymns from the full PCO library, and label it clearly as `Lord's Supper` in the proposal. Search by theme if needed:
  ```bash
  pco songs --query "<keyword>"
  ```
- **Song 5 (Sermon Response / Charge)**: Pick the song with the closest connection to the sermon text and main idea. Prefer songs that quote, allude to, or directly embody the passage. If it also has a Charge/Benediction role and a strong closing chorus, that is ideal.

**Repetition:** Repeating songs within a series is good for congregational learning. Prefer staying inside the approved song block over pulling outside songs merely for variety, and expect the strongest song-block songs to appear 2-3 times per planning season. A song may normally appear up to 3 times in a series/month when it serves the text and liturgical moment well. Avoid back-to-back repeats unless the user approves or the song is intentionally anchoring the series.

**Outside songs:** Pull outside the approved song block only when the block cannot honestly cover a needed role, such as a true upbeat opener or a sacramental Lord's Supper hymn. Clearly label outside songs and why they are needed.

**Classical hymn check:** Before presenting the proposal, confirm each Sunday includes at least one older/classical hymn. If not, replace a flexible song or the Lord's Supper song with an appropriate hymn and call out any tradeoff.

**Tempo check:** Before presenting the proposal, list the raw PCO BPM and normalized/felt BPM for every Song 1 opener when they differ. If an opener's BPM is unavailable or the feel is not clearly joyful/upbeat, do not present it as the recommended opener without flagging that weakness.

**Middle-song energy check:** Before presenting the proposal, verify that Song 2 to Song 3 moves from higher energy to lower energy or stays level. If the order rises in energy, swap the songs or call out the reason.

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
  Song 1 (Adoration):    <Title> — <Author> [fresh/recent, raw BPM / felt BPM]
  Song 2:                <Title> — <Author> [fresh]
  Song 3:                <Title> — <Author> [recent]
  Song 4 (Lord's Supper):<Title> — <Author> [hymn/sacrament]
  Song 5 (Response):     <Title> — <Author> [sermon-text fit]

April 20 — [Series Title: Sermon Title]
  ...
```

Present all Sundays at once. Note any tradeoffs (e.g., a song being used back-to-back, a thin pool for a given role, unknown/weak opener BPM, missing older/classical hymn coverage, a weaker sermon-text connection for the closing response, or an outside-the-block song used because the approved block cannot cover the role).

---

### Step 7 — Iterate

Adjust based on user feedback until the plan is approved. Common adjustments:
- Swap a specific song for a different one
- Move a song to a different slot or Sunday
- Replace a Lord's Supper hymn with a different sacramental hymn
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

If the service template does not already have a song slot immediately after Lord's Supper, insert the **Lord's Supper hymn** as a new item after the "Lord's Supper" item:
```bash
# Find the Lord's Supper item ID from plan-items output
pco songs --query "<Hymn Title>"
pco add-song-item <plan_id> <lords_supper_item_id> <song_id> "Lord's Supper"
```

Repeat for all approved song slots across all Sundays.

After completing, run `plan-items` for each plan to verify all songs are set and the hymn appears after Lord's Supper.

---

## Notes

- Service type: Sunday Morning Worship (configure the local PCO service type ID)
- Song slots are usually pre-existing items named "Song 1" through "Song 5" — use them when present and only create a new Lord's Supper hymn item if the template lacks a post-communion song slot
- Lord's Supper hymns don't need to come from the song block pool — search the full PCO library for the strongest sacramental fit
- The `song-block` skill is the upstream step that produces the song pool used here
