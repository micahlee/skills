# Bible Study authoring contract

Use the canonical Hub schemas and provider validation as the exact authority:

- `axon-engineering-hub/contracts/personal-bible-study/v1/recipe.schema.json`
- `axon-engineering-hub/contracts/personal-bible-study/v1/program.schema.json`
- `axon-engineering-hub/contracts/personal-bible-study/v1/session.schema.json`
- `axon-engineering-hub/contracts/personal-bible-study/v1/recipe-draft.schema.json`
- `axon-personal/plugins/bible-study/bin/bible-study`

## Supported authored families

Use `seasonal` for Advent, Christmas, Lent, Holy Week, or Easter. Use
`external_resource` for all other agent-authored resources. Regular, Cell
Group, Wisdom Break, prayer sessions, and memory review already have canonical
provider paths and are not authored through this bundle.

Use `open_sequence` with `offer_next` when dates do not control the resource.
Use `calendar_aligned` with `stay_calendar_aligned` when a date or liturgical
day controls it. Calendar plans can have one all-day main session and up to
eight morning/midday/afternoon/evening satellites per day. A missed calendar
day remains historical; adaptation happens by authoring a reviewed future
revision, never by rewriting an active or completed session.

## Library invariants

The root must contain only `contract`, `schemaVersion`, `recipe`, `program`,
`sessions`, and `revision`. The staging helper replaces root `revision` and
`program.revision` with the next live library revision before hashing.

The Recipe must be `draft`, have a SemVer version, one to eight session
templates, one to four sample stacks, a preparation horizon of 1–30, and at
most 24 source bindings. Every sample card template and every card source
binding must resolve.

The Program must contain 1–60 day umbrellas. Each day has exactly one main
session and may reference up to eight satellites. Every referenced session must
exist exactly once; no unreferenced session may be included. Open days have a
stable identity and null `localDate`; calendar days use `YYYY-MM-DD` for both
their identity and local date.

Every prepared session is `personal.bible-study.session@1`, binds its Program,
umbrella, and Recipe version, and contains 1–128 cards plus 1–128 ledger items.
Every card ID is unique and every `sourceLedgerID` resolves.

## Source separation

Use these ledger kinds:

- `scripture_exact`: exact Scripture returned by Logos;
- `owned_source_exact`: exact commentary/devotional/reference material returned
  by Logos or another explicitly owned source;
- `ai_generated`: authored reflection, COMA, prayer, or memory scaffolding.

Record the actual provider, resource ID, resource revision, locator, and rights.
Display, cache, and export are independent. Do not infer cache/export permission
from display permission. If required content cannot be retrieved or displayed,
represent the session as blocked/degraded according to the canonical schema;
never substitute invented source text.

Card kinds are `scripture`, `commentary`, `coma_context`, `coma_observation`,
`coma_meaning`, `reference_material`, `coma_application`, `prayer`, `memory`,
and `reflection`. Keep prayer and memory prompts short enough to perform. For
Lent, satellites can increase prayer frequency while remaining connected to
the same day umbrella.

## Review projection

Write a concrete `semanticDiff` describing additions, removals, cadence/date
changes, source changes, and prayer/memory changes. Provide representative
`sampleStacks`. The app intentionally shows structure, source identities,
rights, counts, and samples while exact prepared bodies remain private.

The user approves the exact staged SHA-256, draft revision, and expected live
library revision in the app. Any changed byte or stale revision fails closed.
