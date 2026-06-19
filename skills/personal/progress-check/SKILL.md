---
name: progress-check
description: Check Micah's Daily Note priority tasks at scheduled checkpoints, deterministically decide whether a progress nudge is warranted, and publish a compact Axon progress-nudge event only when needed.
---

# Progress Check

Use this skill when the user says `/progress-check` or when Axon scheduled workflows run `/progress-check midday`, `/progress-check afternoon`, or `/progress-check evening`.

## Purpose

Notice when today's priority commitments are not moving and publish a small, actionable nudge event. This skill is read-only for tasks: do not complete, defer, rewrite, snooze, downgrade, or otherwise edit tasks.

## Deterministic Gate

Always run the deterministic helper first:

```sh
python3 /Users/micahlee/projects/skills/skills/personal/progress-check/scripts/progress_check.py analyze --checkpoint CHECKPOINT
```

Use `midday`, `afternoon`, or `evening`. If no checkpoint is specified, infer it from the command text, otherwise use `midday`.

The helper reads `~/.config/agent-skills/progress-check.json` when present and falls back to `~/.config/agent-skills/daily-note.json` for the vault path and daily note pattern.

Do not publish anything unless the helper returns:

```json
{"status":"nudge_required"}
```

Quiet statuses:

- `no_nudge`: return a brief web-only note that no progress nudge is needed.
- `duplicate`: return a brief web-only note that the nudge was already sent for this category today.
- `data_unavailable_first`: return a brief web-only note that task data was unavailable and no Telegram nudge was sent yet.

## Message Generation

The helper decides whether a nudge is warranted. The LLM may only turn the helper's risk context into a concise message after that deterministic decision.

When `status` is `nudge_required`:

- Write one concise Telegram-ready message.
- Include one concrete next action.
- Ask Micah to do, defer, resize, or decide.
- Do not include source implementation details, raw note text dumps, or a long explanation.

If you cannot confidently generate a useful message, do not publish an event. Return a web-only explanation that the deterministic gate found risk but message generation failed.

## Publish

Write the helper result JSON to a temp file and publish with the generated message:

```sh
python3 /Users/micahlee/projects/skills/skills/personal/progress-check/scripts/progress_check.py publish \
  --analysis /tmp/progress-check-analysis.json \
  --message "Telegram-ready nudge text"
```

The helper publishes `personal.progress-nudge.created` through the Axon CLI using the `progress-check-nudges` profile by default. If the profile is missing, create it once:

```sh
/Users/micahlee/.local/bin/axon clients create \
  --scope events:publish:personal.progress-nudge.created \
  --profile progress-check-nudges \
  --expires 8760h \
  progress-check-nudges
```

Never print bearer tokens.

## Output

For scheduled workflow runs, return a short web summary:

- If no event was published, say why in one sentence.
- If an event was published, say which checkpoint/category was nudged.
- Do not paste the full event payload unless explicitly asked.
