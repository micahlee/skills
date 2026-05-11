---
name: song-block
description: Plan song blocks for a church sermon series. Given sermon texts, titles, and main ideas, select a ranked pool of worship songs covering liturgical roles. Outputs a Google Doc. Triggers on phrases like "plan a song block", "plan worship music", "build a song block", "select songs for [series]", or any request to plan music for a series.
---

# Song Block Planning

Script: `python3 scripts/build_doc.py <plan.json>` from this skill directory.

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

---

## Step 3: Plan the Song Pool

### Liturgy Structure
Each service follows this order. Confession does not always require a song.

| Slot | Role | Notes |
|------|------|-------|
| 1 | **Adoration** | Bold, celebratory opening |
| 2 | **Confession** | Slow/contemplative, or corporate prayer/reading |
| 3 | **Assurance** | Response to confession — grace, gospel, union with Christ |
| 4 | **Thanksgiving / Petition** | Optional; some services omit |
| 5 | **Charge / Benediction** | Send-off song; upbeat or creedal |

### Pool Sizing
- **Pool size** = (sermons × 3 avg songs per service) ÷ avg uses per song (2.5) + 5 extra = roughly `sermons × 2`
- For an 11-sermon series: aim for 20–22 songs
- For a 6-sermon series: aim for 12–14 songs

### Pool Ranking Criteria
Rank songs 1–N by combined score:

1. **Thematic fit** (primary) — How directly does this song address the series' key themes? A song that quotes or mirrors the passage scores highest.
2. **Liturgical role coverage** (secondary) — Does adding this song fill a role that's underserved in the current pool?
3. **Recency penalty** — Deprioritized songs score lower.

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
      "recency_tag": "[fresh]",
      "recency_detail": "last used Dec 2025",
      "roles": "Assurance / Charge",
      "description": "Why this song fits the series — specific textual or thematic connection."
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

- The Galatians song block (`1ABR_rKXagX-wntfyvhdpUiDv8B4cuc57WCngUhaK8fA`) is the reference example
- Service type is Sunday Morning Worship; configure the local PCO service type ID before using PCO write commands.
- Configure any local owner/person IDs outside this public skill.
- Church-specific naming belongs in local configuration or the user's prompt, not in the shared skill.
- Always check recency before confirming the pool — the same songs can't carry every series
