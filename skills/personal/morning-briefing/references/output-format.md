# Morning Briefing Output Format

Morning Briefing writes the same core content to the daily note and Telegram. The daily note may contain a slightly richer coverage line, but implementation metadata belongs in logs or sidecars.

## Daily Note Section

Refresh the `## Morning Briefing` section by heading. Do not add HTML markers such as `<!-- morning-briefing:start -->` or `<!-- morning-briefing:end -->`.

If the section is missing in an existing daily note, insert it after `## Morning Nudge` when present, otherwise after `## Scripture Memory`, otherwise near the top before task sections. Preserve all human content.

Recommended section shape:

```markdown
## Morning Briefing

_Generated 2026-05-29 05:12 America/New_York. Coverage: daily note, calendar, tasks, food; weather unavailable._

**Today:** One-sentence thesis.

**Hard commitments**
- 08:30 School dropoff
- 10:00 Call with X

**Realistic focus**
1. Finish Y [src](obsidian://...)
2. Decide Z [src](obsidian://...)

**Body / food**
- Concrete encouragement or nudge tied to known goals.

**Prayer**
- One sourced focus prayer subject.

**Watch**
- Overcapacity, logistics, dinner, urgent inbox, or decision pressure.
```

Omit empty sections.

## Refresh Rules

Use heading boundaries and previous generated content from the run log/sidecar when available. If `## Morning Notes` contains human content after the briefing, do not touch it. If the current `## Morning Briefing` section has substantial human edits that cannot be safely merged, leave it unchanged and log a warning instead of reintroducing machine comments.

When cleaning legacy notes, remove old `morning-briefing` HTML markers while preserving the content inside them.

## Telegram Message

Return exactly the Telegram-ready message in `send` mode. No preface, no implementation summary, no mention of files/tools/logs unless a missing source changes trust in the briefing.

Stable shape:

```text
Morning Briefing · Fri May 29

Today is a logistics-heavy day; win by keeping the plan narrow and protecting one focused work block.

Hard commitments
8:30 School dropoff
10:00 Call with X

Focus
1. Finish Y src
2. Decide Z src

Body / food
Protein has been steady this week. Keep the usual morning anchor; dinner is the risk point.

Prayer
Patience and steadiness in a logistics-heavy afternoon.

Watch
Calendar is tight before 2pm. Treat anything beyond the focus list as optional unless you swap intentionally.

Open daily note
obsidian://...
```

Guidelines:

- One compact message, not a thread by default.
- Include a one-sentence day thesis near the top.
- Prefer hard caps over exhaustiveness.
- Use 1-3 focus items.
- Use source links only for selected tasks/decisions.
- If the message gets long, compress harder.

## Selection Rules

When the daily note has too many candidate tasks, Telegram should name the overcapacity and select a realistic plan.

Prefer:

- calendar/time-sensitive commitments
- tasks already selected by daily-note as Must/Focus
- recurring responsibilities due today
- high-consequence items
- clear next actions

Decision items should appear only when blocking or time-sensitive.

## Prayer Focus

Pick at most one focus prayer subject.

Priority order:

1. Explicit prayer item in today's daily note.
2. Theme from Morning Nudge or Dream.
3. Calendar/task pressure that clearly suggests a prayer subject.
4. Omit when no real signal exists.

Do not generate devotional content from scratch. Keep spiritual context sourced, light, and integrated with the day.
