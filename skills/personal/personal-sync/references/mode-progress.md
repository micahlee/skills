# Progress Mode

Use for `/personal-sync progress midday|afternoon|evening`.

Always run the deterministic gate first:

```sh
python3 scripts/progress_check.py analyze --checkpoint CHECKPOINT
```

- `no_nudge`, `duplicate`, or first data-unavailable status: publish nothing.
- `nudge_required`: turn the returned risk context into one concise message with one concrete next action.
- If no useful message can be generated confidently, publish nothing and log why.

Publish with:

```sh
python3 scripts/progress_check.py publish \
  --analysis /tmp/personal-sync-progress-analysis.json \
  --message "Compact actionable nudge"
```

Progress mode is read-only for tasks. Never complete, defer, rewrite, snooze, downgrade, or reschedule work. Put analysis detail in agent context/logs and send only the compact nudge event.
