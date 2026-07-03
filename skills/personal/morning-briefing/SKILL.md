---
name: morning-briefing
description: Render a compact morning briefing from today's Obsidian daily note, Daily Dream nudge, calendar/email signals, tasks, health/food/fitness context, weather/logistics, and goal context; write the managed briefing block and optionally return a Telegram-ready message. Use when the user asks for a morning briefing, Telegram briefing, day briefing, or when a scheduled daily workflow runs /morning-briefing.
---

# Morning Briefing

Use this skill to turn prepared daily context into a concise, opinionated morning briefing. It is a renderer and light freshness checker, not a replacement for `daily-note` or `daily-dream`.

## Onboarding

Run `python3 scripts/onboard.py` from this skill directory before first unattended use. It writes:

```text
~/.config/agent-skills/morning-briefing.json
```

Read that config before assuming vault paths, source commands, goal sources, or output locations.

Prefer the `obsidian` CLI for vault reads/writes. When multiple vaults are present, pass `vault="Micah's Vault"` explicitly. Refresh the `## Morning Briefing` section while keeping the daily note clean: do not add HTML ownership markers or hidden inline metadata.

## Required References

Read these before collecting sources or writing output:

- [references/source-model.md](references/source-model.md) for source priority, freshness checks, goal context, and privacy rules.
- [references/output-format.md](references/output-format.md) for the daily note block and Telegram message shape.
- [references/events-and-logs.md](references/events-and-logs.md) for event outbox, run logs, send behavior, and deterministic IDs.

## Modes

- `/morning-briefing` or `/morning-briefing refresh`: update today's daily note block, write logs/events, and do not optimize the final answer for Telegram unless the caller explicitly asks.
- `/morning-briefing send`: update the block, write logs/events, publish a compact `personal.morning-briefing` Axon event containing the Telegram-ready message, and return only a brief implementation summary for web/operator logs. Do not put the full briefing body in the final assistant message when running from Axon.
- `/morning-briefing preview`: read sources and show the candidate briefing, but do not write the note, event outbox, or run log.

## Core Workflow

1. Load config and resolve today from Axon/system local time, defaulting to `America/New_York`.
2. Read today's daily note, especially Morning Nudge, Commitments, Focus Tasks, Needs Decision, Context, prayer sections, and Dream.
3. Add light fresh deltas from configured calendar, email/inbox, weather/logistics, health/food/fitness, and Axon event commands.
4. Read configured interim goal/context paths when present; otherwise use only explicit available goals and log that the personal context portfolio is missing.
5. Produce a one-sentence day thesis, hard commitments, 1-3 realistic focus items, relevant body/food/fitness encouragement or nudges, watch items, and one sourced prayer focus when available.
6. Refresh the `## Morning Briefing` section in today's daily note and store refresh metadata in logs/sidecars, not in visible note comments.
7. Append compact events to the briefing outbox and write a structured run log.
8. In `send` mode, publish the Telegram-ready message as a compact Axon event using the configured/public Axon CLI profile, then return only a brief implementation summary. Telegram delivery is owned by the downstream event-triggered workflow, not this workflow's final assistant response.

## Operating Rules

- Orientation first, commitment second, decision pressure last.
- Be politely opinionated when the daily plan is over capacity, but do not mutate task blocks in v1.
- Telegram gets summaries, not raw private source content.
- Include health/food/fitness only when it affects today's choices or when evidence supports a brief encouragement/nudge tied to known goals.
- Include email/inbox as bounded signal; summarize urgent/actionable exceptions only.
- Calendar is first-class: summarize day shape plus hard commitments, travel, prep windows, and conflicts.
- Include yesterday only when Daily Dream or Morning Nudge makes it relevant to today.
- Degrade by source. Send the briefing unless the daily note itself is unavailable.
