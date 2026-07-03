---
name: song-block
description: Plan song blocks for a church sermon series. Given sermon texts, titles, and main ideas, select a ranked pool of worship songs covering liturgical roles, including upbeat adoration openers, sacramental Lord's Supper hymns, sermon-text response songs, and older/classical hymn coverage. Outputs a Google Doc. Triggers on phrases like "plan a song block", "plan worship music", "build a song block", "select songs for [series]", or any request to plan music for a series.
---

# Song Block Planning

Script: `python3 scripts/build_doc.py <plan.json>` from this skill directory.

## Onboarding

Run `python3 scripts/onboard.py` from this skill directory to collect local Planning Center IDs, church/ministry naming, and song-history defaults. The script writes `~/.config/agent-skills/song-block.json`. Read that file before using local IDs or generated document naming.

## Workflow

1. **Get series info** — sermon count, texts, titles, main ideas
2. **Fetch PCO data** — recent usage + active song library
3. **Plan the pool** — rank songs by series fit + liturgical coverage
4. **Build the doc** — generate the plan JSON and run build_doc.py

---

## Step 1: Get Series Info

Ask the user for (or read from a linked sheet/doc):
- Series title
- Number of sermons
- Per sermon: passage, title, main idea (1 sentence)

---

## Step 2: Fetch PCO Data

```bash
# Recent usage (20 weeks gives good recency signal)
# This is the AUTHORITATIVE source for active songs — it paginates through all non-archived songs
pco song-history --weeks 20
```

**Reading the output:**
- Songs in `song-history` are **active** and have been used recently — note their use count and last date
- Songs NOT in the history may still be active (just not used in 20 weeks) — they can be used freely
- `pco.py songs` only shows the first 20 songs (not paginated) — **do not use it as the active library**
- Songs with `hidden: true` in PCO are archived — the song-history command already excludes them

**Critical: Verifying a song is active before including it in the pool**

Before adding any song to the pool that does NOT appear in the 20-week history, you must verify it is active. Use the full PCO songs API with pagination (not `pco.py songs` which only returns 20):

```python
# Run in a scratch Python session to get ALL active songs
import os, json
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from base64 import b64encode

CLIENT_ID = os.environ["PCO_CLIENT_ID"]
SECRET = os.environ["PCO_SECRET"]

def get(path, params=None):
    url = "https://api.planningcenteronline.com" + path
    if params:
        url += "?" + urlencode(params)
    creds = b64encode(f"{CLIENT_ID}:{SECRET}".encode()).decode()
    req = Request(url, headers={"Authorization": f"Basic {creds}"})
    with urlopen(req) as r:
        return json.loads(r.read())

offset, active = 0, []
while True:
    d = get("/services/v2/songs", {"per_page": 100, "offset": offset})
    active.extend(s["attributes"]["title"] for s in d["data"] if not s["attributes"].get("hidden"))
    if len(d["data"]) < 100: break
    offset += 100
print(f"{len(active)} active songs")
for t in sorted(active): print(" ", t)
```

**Rule: Never include a song in the pool if it does not appear in either the song-history output OR the verified active songs list above.**

**Recency tags:**
- `[fresh]` — not used in 20 weeks (or not at all)
- `[recent]` — 1–2 uses in the past 8 weeks
- `[deprioritized]` — 3+ uses in 20 weeks, or used in the past 4 weeks

**Tempo/BPM data:**
- BPM is arrangement-level in PCO. Fetch it from arrangement metadata when evaluating opener suitability.
- PCO BPM may be a click-track value rather than the felt pulse; many arrangements use a doubled BPM for metronome subdivisions.
- Raw plan exports expose BPM and meter for scheduled arrangements:
  ```bash
  pco plans export <plan_id> --include-raw --json
  ```
- If the CLI search output does not expose BPM for a candidate, query the song's arrangements from the PCO API or inspect a recent plan that used the same arrangement.
- Record both raw PCO BPM and normalized/felt BPM when the raw number is clearly doubled (for example, 146 raw may feel like 73). Use felt pulse and musical character, not raw BPM alone, when ranking openers.
- Record `BPM unknown` when it cannot be found, and do not rank that song as a primary upbeat opener without a user-confirmed feel.

---

## Step 3: Plan the Song Pool

### Liturgy Structure
Each service follows this order. Confession does not always require a song.

| Slot | Role | Notes |
|------|------|-------|
| 1 | **Adoration** | Upbeat, joyful opening that prompts congregational praise |
| 2 | **Confession** | Slow/contemplative, or corporate prayer/reading |
| 3 | **Assurance** | Response to confession — grace, gospel, union with Christ |
| 4 | **Thanksgiving / Petition** | Optional; some services omit |
| 5 | **Lord's Supper / Sermon Response / Charge** | Include sacramental hymns and songs with direct sermon-text fit |

### Service Set Heuristics

- Open with upbeat adoration whenever possible. Save reflective, meditative, and slower songs for confession, assurance, Lord's Supper, or response slots. Use BPM and meter as guardrails, but normalize doubled click-track BPM before judging feel; generally prefer a clear upbeat felt pulse, while interpreting 6/8, cut time, and half-time arrangements by musical feel rather than raw BPM alone.
- Sequence the middle of the set by descending energy: Song 2 should be equal or lower energy than the opener, and Song 3 should be equal or lower energy than Song 2.
- Include Lord's Supper options that are clearly connected to the sacrament: Christ's body and blood, atonement, communion, union with Christ, pardon, remembrance, and the cross.
- Include songs that closely track individual sermon texts, not only broad series themes. A song that quotes or strongly mirrors a specific passage is especially valuable for the post-sermon response.
- Ensure enough older/classical hymns are in the pool for roughly one per service set. Do not build a pool made only of modern worship songs and modern hymns.
- Build pools with enough depth for variety, but expect the best songs to repeat 2-3 times per planning season. Repetition helps the congregation learn the series vocabulary; a strong song may normally be used up to 3 times across a series/month.

### Pool Sizing
- **Pool size** = (sermons × 3 avg songs per service) ÷ avg uses per song (2.5) + 5 extra = roughly `sermons × 2`
- For an 11-sermon series: aim for 20–22 songs
- For a 6-sermon series: aim for 12–14 songs
- Add extra pool depth when needed to cover upbeat openers, sacramental hymns, direct sermon-response songs, and older/classical hymn coverage.

### Pool Ranking Criteria
Rank songs 1–N by combined score:

1. **Thematic fit** (primary) — How directly does this song address the series' key themes? A song that quotes or mirrors the passage scores highest.
2. **Sermon-text fit** — Does this song strongly connect to one or more specific sermons, especially as a post-sermon response?
3. **Tempo/energy fit** — Does the arrangement BPM, normalized/felt pulse, and musical character support its intended slot, especially upbeat adoration openers?
4. **Liturgical role coverage** — Does adding this song fill an underserved role: upbeat adoration opener, confession, assurance, Lord's Supper, charge, or response?
5. **Hymn coverage** — Does the pool provide enough older/classical hymns for about one per service set?
6. **Recency penalty** — Deprioritized songs score lower.

Assign tiers:
- **Tier 1**: Essential — would definitely use, strong thematic connection
- **Tier 2**: Strong fit — good thematic connection or important liturgical role
- **Tier 3**: Supporting — covers gaps, backup options, available for cuts

---

## Step 4: Build the Plan JSON

Create a JSON file with this structure (no `sermons` or `usage_summary` needed), then run `build_doc.py`:

```json
{
  "doc_id": null,
  "title": "Series Name — Song Block",
  "subtitle": "N songs for an X-week series through [Book]. Ranked by thematic fit...",
  "song_pool": [
    {
      "rank": 1,
      "tier": 1,
      "title": "Song Title",
      "author": "Author Name",
      "tempo": "Slow / Medium / Upbeat",
      "bpm": "raw PCO BPM and normalized/felt BPM, or unknown",
      "recency_tag": "[fresh]",
      "recency_detail": "last used Dec 2025",
      "roles": "Assurance / Charge",
      "description": "Why this song fits the series — include specific textual or thematic connection, and note if it is a strong opener, Lord's Supper hymn, sermon response, or older/classical hymn."
    }
  ]
}
```

**To update an existing doc** instead of creating a new one, set `"doc_id": "<google-doc-id>"`.

```bash
python3 scripts/build_doc.py /path/to/plan.json
```

---

## Notes

- Service type is Sunday Morning Worship; configure the local PCO service type ID before using PCO write commands.
- Configure any local owner/person IDs outside this public skill.
- Church-specific naming belongs in local configuration or the user's prompt, not in the shared skill.
- Always check recency before confirming the pool — the same songs can't carry every series
