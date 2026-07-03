---
name: daily-dream
description: Synthesize a day from Obsidian daily notes, health/food/fitness, calendar/email, Axon events, and other bounded data sources; refresh daily Dream blocks, prepare tomorrow's Morning Nudge, and roll learnings into monthly notes. Use when the user asks to dream, distill daily learnings, summarize yesterday/today, prepare morning briefing inputs, or create daily/monthly reflective summaries.
---

# Daily Dream

Use this skill for reflective synthesis, not task planning. The goal is to notice meaning, patterns, tensions, health/food signals, and open questions from the day, then write durable summaries into daily and monthly notes.

## Onboarding

Run `python3 scripts/onboard.py` from this skill directory before first unattended use. It writes:

```text
~/.config/agent-skills/daily-dream.json
```

Read that config before assuming vault paths, daily/monthly note patterns, source commands, or outbox locations.

Prefer the `obsidian` CLI for vault reads/writes. When multiple vaults are present, pass `vault="Micah's Vault"` explicitly.

## Required References

Read these before collecting sources or writing notes:

- [references/source-model.md](references/source-model.md) for source tiers, privacy boundaries, and evidence rules.
- [references/output-format.md](references/output-format.md) for daily Dream, tomorrow Morning Nudge, and human-owned Dream Notes sections.
- [references/monthly-rollup.md](references/monthly-rollup.md) for monthly Daily Dream Index, Rolling Themes, and Monthly Synthesis behavior.
- [references/events-and-logs.md](references/events-and-logs.md) for outbox events, run logs, and deterministic event IDs.

## Core Workflow

For the default 11pm run:

1. Load config and resolve the target date, defaulting to today.
2. Read the target daily note and Tier 1 sources.
3. Pull Tier 2 summaries when available and cheap.
4. Follow only 1-3 central linked notes when they clearly matter.
5. Draft a first-person, humble Dream synthesis for the target day.
6. Refresh the target daily note's `## Dream` section without adding HTML ownership markers.
7. Prepare a short Morning Nudge in tomorrow's daily note.
8. Create or update the month note, then refresh the target day's entry in the Monthly Dream index.
9. Append compact workflow events to the Dream event outbox.
10. Write a structured run log with source coverage and warnings.

For range backfill, process each date independently, update daily Dream blocks and monthly index entries, then regenerate monthly synthesis only once at the end.

## Operating Rules

- Reflection first; action extraction second.
- Use confidence language: `Strong signal`, `Possible pattern`, and `One-off note`.
- Abstract private email/source details unless the note already names them or the detail is necessary.
- Do not write directly to Axon agent memory notes in v1.
- Do not turn every insight into homework. Emit action or decision events only when evidence is strong enough and the next step is clear.
- Treat missing data as a possible signal only when it is normally expected; phrase absences gently.
- Refresh heading-bounded generated sections without adding HTML ownership markers. Preserve human-owned `Dream Notes`.
