---
name: progress-check
description: Compatibility alias for the unified Personal Sync progress mode. Use when the user invokes /progress-check or when an existing scheduled midday, afternoon, or evening checkpoint still uses the legacy command.
---

# Progress Check Compatibility Alias

This skill is deprecated in favor of `/personal-sync progress`.

Read `../personal-sync/SKILL.md`, then execute its `progress` mode with the original checkpoint arguments. Always use `../personal-sync/scripts/progress_check.py` as the deterministic gate. Do not use the legacy helper or instructions in this directory as current behavior.

Return the normal compact checkpoint result.
