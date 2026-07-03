# Daily Dream Source Model

Daily Dream uses a tiered evidence model. It can use broad data, but it must stay bounded and private.

## Source Tiers

Tier 1, always:

- target daily note
- Food Tracker frontmatter totals and `#food` entries in the daily note
- calendar commitments already present in the daily note
- completed/unfinished task patterns visible in the daily note
- prayer, notes, outcomes, Dream Notes, and other human-written daily content

Tier 2, default when available and cheap:

- Apple Health rings, workouts, steps, active energy, and relevant rollups
- Fitbod workouts
- calendar events for the target day
- Gmail metadata and subject-level summaries for the target day
- Axon events touching health, food, money, tasks, decisions, or daily notes

Tier 3, only when triggered by strong relevance:

- full email body reads
- finance/spending drilldowns
- shopping/order details
- project source notes
- linked worksheets or central linked notes

## Historical Backfill

For range backfill, prefer notes and existing events first.

Always use:

- daily notes
- existing food totals in daily notes
- existing Axon events/cache if available

Use only when cheap and bounded:

- calendar for the date range
- health/fitness rollups queryable by date

Avoid by default:

- full email bodies
- deep project note reads
- finance/shopping detail reads

## Link Following

Primary evidence is the daily note. Follow at most 1-3 central linked notes when they clearly shape the day, such as:

- a linked worksheet that the day focused on
- a project note central to the day's work
- an already summarized Codex or Axon thread link

Do not chase every food resource, task source, backlink, or calendar URL.

## Privacy And Source Detail

Private data can inform the synthesis, but durable notes should summarize at the right altitude.

Default email behavior:

- search/list messages from the target date
- collect counts, senders/categories, and subject-level signals
- read bodies only for likely important/actionable threads or threads already referenced in the daily note/tasks

Avoid writing sensitive email details into the Dream unless they are already in the daily note or necessary to the insight.

## Source Coverage

Each Dream should include a short coverage line, for example:

```markdown
_Source coverage: daily note, food totals, calendar, Apple Health; Gmail unavailable._
```

Full warnings and errors belong in the run log.
