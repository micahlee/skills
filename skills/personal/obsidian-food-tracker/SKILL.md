---
name: obsidian-food-tracker
description: Maintain Micah's Obsidian food logging workflow using the Food Tracker plugin, reusable nutrient files, one-line-per-consumption #food entries for Axon ingestion, goals, and audit notes. Use when logging food, drinks, snacks, meals, nutrition label photos, repeated foods "same as yesterday", recipe/package updates, calorie or macro targets, or 14-day eating audit summaries.
---

# Obsidian Food Tracker

## Vault Conventions

- Vault: `Micah's Vault`
- Daily notes: `Daily Notes/YYYY/MM/YYYY-MM-DD.md`
- Food resources and Food Tracker nutrient files: `01 - PERSONAL/03 - RESOURCES/Food`
- Eating audit project: `01 - PERSONAL/01 - PROJECTS/14-Day Eating Audit/14-Day Eating Audit.md`
- Food Tracker goals file: `01 - PERSONAL/01 - PROJECTS/14-Day Eating Audit/nutrition-goals.md`
- Plugin settings: `.obsidian/plugins/food-tracker/data.json`

Prefer the `obsidian` CLI for vault reads/writes when it is available. If the CLI is unavailable in the current environment, read files directly and write staged changes through normal Codex approval for paths outside the current workspace.

## Core Workflow

1. Read the current daily note and relevant food resource notes before editing.
2. For messy user input or label photos, extract calories, fats, saturated fats, protein, carbs, fiber, sugar, sodium, serving size, and amount eaten.
3. Create or update a reusable food note in `01 - PERSONAL/03 - RESOURCES/Food` for repeated foods or recipes.
4. Add plugin-native entries under `## Food Journal` -> `### Food Entries`.
5. Keep human context under `### Food Inbox`, `### Observations`, and `### Notes`.
6. Let the Food Tracker plugin calculate totals and progress; do not maintain separate HTML or Markdown macro tables in daily notes.
7. Update the audit project only for summary rows, notable decisions, target changes, or pattern observations.

## Axon Event Rules

Each consumption event must have its own `#food` line so Axon can ingest it independently. Do not increment or merge an existing `#food` line when the user logs another serving of the same food.

If today already contains:

```markdown
- #food [[Normal Black Coffee]] 1pc
```

and the user logs another regular coffee, append a new line:

```markdown
- #food [[Normal Black Coffee]] 1pc
- #food [[Normal Black Coffee]] 1pc
```

Do not rewrite it as:

```markdown
- #food [[Normal Black Coffee]] 2pc
```

Use quantity within one line only to describe the amount consumed in that single event, such as `113g` chicken or `150g` vegetables. If the user clearly logs multiple separate units or repeated servings, prefer separate lines.

## Food Tracker Entry Format

Use database entries for reusable foods:

```markdown
- #food [[Normal Black Coffee]] 1pc
- #food [[Normal Black Coffee]] 1pc
- #food [[Morning Yogurt Bowl]] 1pc
- #food [[Greek Yogurt]] 150g
```

Use inline entries only for one-off food that is not worth saving:

```markdown
- #food Restaurant burrito 850kcal 35fat 35prot 90carbs
```

Supported units include `g`, `kg`, `ml`, `l`, `oz`, `lb`, `cup`, `cups`, `tbsp`, `tsp`, `pc`, and `pcs`.

## Nutrient File Format

Food Tracker reads nutrition from YAML frontmatter. For whole recipes logged by count, use `serving_size: 1` and `nutrition_per: 1`, then log with `1pc`, `2pc`, etc.

```markdown
---
name: Normal Black Coffee
calories: 85
fats: 0
saturated_fats: 0
protein: 9
carbs: 2
fiber: 1.5
sugar: 0
sodium: 55
serving_size: 1
nutrition_per: 1
---

# Normal Black Coffee
```

The `name` field is required. Without it, Food Tracker identifies the file as being inside the nutrient directory but does not add it to the nutrient cache.

For ingredients measured in grams, store values per `100g` by omitting `nutrition_per` or setting `nutrition_per: 100`, then log actual gram amounts.

## Goals

Food Tracker parses simple `key: value` lines from `nutrition-goals.md`.

```yaml
calories: 2000
fats: 67
saturated_fats: 20
protein: 150
carbs: 200
fiber: 25
sugar: 50
sodium: 2300
```

When the user changes calorie or macro targets, update this file and the `## Provisional Targets` section in the audit note.

## Daily Note Shape

The `## Food Journal` section should stay lightweight:

```markdown
## Food Journal

> Evening ritual: La Croix or decaf ☕ — not snacks/sweets/alcohol

### Food Inbox
- 

### Food Entries
- #food 

### Observations
- Hunger:
- Energy:
- Absent-minded eating:
- Context/triggers:

### Notes
- 
```

## Confidence Rules

- High: package label, weighed food, or known reusable recipe.
- Medium: label data plus estimated ingredient amounts.
- Low: restaurant, eyeballed, or broad estimate.

Record confidence in notes or the audit project when it matters; Food Tracker itself does not store confidence.
