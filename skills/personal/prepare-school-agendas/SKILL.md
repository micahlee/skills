---
name: prepare-school-agendas
description: Prepare Samuel's and Chasen's printable Monday, Wednesday, or Friday school agendas from live ClassReach data, render-verify the DOCX files, and file them in the family's OneDrive school folder. Use when Micah asks to make or print the boys' next school agendas.
---

# Prepare School Agendas

Create one dated DOCX for Samuel and one for Chasen using verified, read-only
ClassReach data. Follow [references/agenda-spec.md](references/agenda-spec.md) for
content, date logic, parent reports, and filing rules.

## Workflow

1. Resolve the target date explicitly. Without an explicit date, run only on
   Sunday for Monday, Tuesday for Wednesday, or Thursday for Friday. On other
   days, ask for the intended date instead of jumping ahead.
2. Run `scripts/check_classreach_cli.sh`. It records the selected executable and
   version and fails unless the required guardian-aware commands exist. Do not
   bypass a failed preflight with another executable unless the user explicitly
   selects that executable.
3. Use the `classreach` skill and the ClassReach CLI exclusively for every
   ClassReach read. Never use a browser, Computer Use, direct HTTP requests, or
   scraped portal HTML as a fallback. If the CLI is stale, unauthenticated,
   Keychain-blocked, or missing a required resource, stop and report that exact
   limitation instead of producing agendas from another source.
4. Resolve Samuel and Chasen exactly and gather:
   - target-day assignments and completion states;
   - compact relevant handout, discussion, and message context;
   - special preparation notes for Tuesday (Monday agenda) or Thursday
     (Wednesday agenda);
   - Monday parent-report context or Friday's unchecked Monday-Thursday work.
   Save the next-day `prep agenda --json` response in the temporary run
   workspace and pass it through `scripts/classify_next_day_prep.py`. Every
   selected-date item must receive one closed classification. Use its
   `next_day_prep` output in the normalized agenda JSON; never print a no-prep
   line when the classifier sets `no_special_preparation_allowed` to false.
5. Fail closed if either student's data cannot be verified or appears
   incomplete. Do not turn a retrieval failure into an empty agenda, and do not
   merge CLI output with data recovered through another interface.
6. Normalize the verified result into the JSON schema documented in the
   reference, then run `scripts/build_agendas.py` once per child. Immediately
   run `scripts/validate_agenda.py NORMALIZED_JSON OUTPUT_DOCX`; treat any
   nonzero result as a hard failure and fix the data or builder before rendering.
7. Publish with `scripts/publish_agendas.py`, passing each normalized JSON/DOCX
   pair, the dated OneDrive destination, and a temporary `--render-dir`. The
   publisher revalidates, renders, enforces the weekday page count, hashes the
   DOCX and page PNGs, creates an immutable revision filename when needed, and
   writes a content-free manifest. Inspect every PNG it returns at 100% using
   the `documents` skill. Never cite or hand off a path other than the exact
   `published_docx` returned by this command.
8. Save final files under
   `/Users/micahlee/Library/CloudStorage/OneDrive-Personal/FAMILY/SCHOOL/Printable Agendas/2026-2027/YYYY-MM-DD/`.
   The top-level folder is shared once with Carrie, Chasen, and Samuel; future
   dated folders inherit that access. Do not change sharing on routine runs.

All routine execution must use CLI and local document-rendering tools only.
Finder, OneDrive UI, browser automation, and Computer Use are outside this
workflow. File into the established synchronized OneDrive path with filesystem
commands; if sharing or another UI-only administrative change is needed, stop
and ask the user to handle it separately.

Treat an on-demand request to prepare the agendas as authorization to persist
the two requested student documents in that established shared destination.
Request confirmation again before changing recipients, permissions, or the
destination hierarchy.

## Deterministic tools

- `scripts/classify_next_day_prep.py NEXT_DAY_JSON --student NAME` emits the
  classification audit and normalized `next_day_prep` rows. Use
  `--expect-empty` only to verify a proposed no-preparation result.
- `scripts/validate_agenda.py NORMALIZED_JSON OUTPUT_DOCX` compares visible DOCX
  tables and geometry with the normalized source contract.
- `scripts/publish_agendas.py --agenda NORMALIZED_JSON DOCX ... --destination
  DIR --render-dir TEMP_DIR` is the only routine publication path.

Run the regression suite after changing the skill:

```sh
python -m unittest discover -s tests -p 'test_*.py'
```
