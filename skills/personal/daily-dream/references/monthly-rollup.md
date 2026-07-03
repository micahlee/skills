# Monthly Dream Rollup

Daily Dream updates the month note every night and can regenerate higher-level synthesis on demand.

## Month Note

Default month note pattern:

```text
Daily Notes/YYYY/MM/MM.md
```

If the month note is missing, create it from the configured month template when available, then add missing dream blocks.

## Sections

Add or refresh these sections:

```markdown
## Daily Dream Index
<!-- monthly-dream:daily-index:start -->
### 2026-05-29
- Theme: ...
- Signals: ...
- Watch: ...
<!-- monthly-dream:daily-index:end -->

## Rolling Themes
<!-- monthly-dream:rolling-themes:start -->
...
<!-- monthly-dream:rolling-themes:end -->

## Monthly Synthesis
<!-- monthly-dream:synthesis:start -->
...
<!-- monthly-dream:synthesis:end -->
```

## Nightly Behavior

Each 11pm run:

- updates the target day's entry in Daily Dream Index
- may update Rolling Themes lightly
- does not need to regenerate full Monthly Synthesis unless configured

The daily index is evidence. The synthesis is meaning.

## Month-End Or On-Demand Behavior

When asked for a monthly dream, or after a range backfill:

1. Read all Daily Dream Index entries and daily Dream blocks for the month.
2. Include objective metrics as signals, not dashboard tables.
3. Regenerate Monthly Synthesis from the collected evidence.

Monthly synthesis may include:

- strongest recurring themes
- health/food/fitness patterns
- work/project rhythms
- relationships/home/family patterns
- faith/interior life patterns
- money/admin pressure points
- experiments or decisions worth considering

Do not turn the monthly note into a health, finance, or task dashboard. Distill meaning from metrics.
