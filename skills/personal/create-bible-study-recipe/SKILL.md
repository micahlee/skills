---
name: create-bible-study-recipe
description: Create or revise an agent-authored Axon Bible Study recipe and stage it for connected in-app review. Use when the user asks for an Advent, Lent, seasonal, dated, open-ended, Scripture-first, or external-resource Bible study/devotional plan, or asks to revise a recipe after requesting changes in the Bible Study app. Retrieves exact owned Scripture/commentary with logos-cli, prepares private sessions, and uses Axon's digest-bound recipe staging gate without approving on the user's behalf.
---

# Create Bible Study Recipe

Create a private Recipe, Program, and prepared-session bundle, then stage it for
review in the Bible Study app. Never approve, cancel, or submit review feedback
for the user.

## Workflow

1. Read [references/authoring-contract.md](references/authoring-contract.md).
2. Resolve only choices that materially change the plan:
   - source or Scripture sequence;
   - open sequence versus calendar aligned;
   - date range and optional liturgical-season key;
   - desired main-session and satellite-prayer rhythm.
   Infer the rest from the request and established Bible Study design.
3. Inspect the canonical contracts in the current
   `axon-engineering-hub/contracts/personal-bible-study/v1/` checkout. Treat
   them as authority over this skill if they differ.
4. For every Logos-owned source:
   - discover the exact resource with `logos-cli library --query ... --json`;
   - render each locator with
     `logos-cli passage --resource RESOURCE_ID --ref REFERENCE --json`;
   - validate the returned resource identity, reference, nonblank text,
     revision, and SHA-256;
   - place the exact text only in the private prepared-session bundle.
   Do not paste or summarize exact licensed bodies in chat, logs, notes, tests,
   or repository files.
5. Generate AI reflections, prayer prompts, COMA prompts, or memory activities
   as separate `ai_generated` ledger/card material with model and prompt
   provenance. Never label AI output as Logos or Scripture.
6. Build one bounded `personal.bible-study.program-library@1` JSON document in
   a mode-0700 temporary directory. Set `recipe.reviewState` to `draft`.
   Include every main and satellite session referenced by every day umbrella.
7. Run the staging helper:

   ```sh
   python3 scripts/stage_recipe.py --bundle /absolute/private/bundle.json
   ```

   The helper normalizes the new library revision, writes the exact bytes to
   Axon's private imports directory, creates a short-lived least-privilege
   client, stages the exact digest, waits for its content-free receipt, prints
   only the safe review projection, and revokes the client.
8. Delete the temporary authoring directory after the helper reports `applied`.
   Tell the user the named draft is waiting in Plans for review.

## Revision loop

Before revising, query `personalBibleStudyRecipeDraft`. Proceed only when the
draft status is `changes_requested`. Treat `changeRequest` as private user
material and do not repeat it outside the working response. Build a new bundle
ID and version, preserve stable semantic identities where their meaning did not
change, update `semanticDiff`, then stage the replacement through the helper.

If the draft is still `awaiting_review`, do not supersede it unless the user
explicitly asked for a replacement. If it is activated, cancelled, expired, or
superseded, start a new draft rather than mutating history.

## Hard boundaries

- Do not call `recipe.approve`; approval belongs to the connected app.
- Do not use `program.install` for agent-authored work; use `recipe.stage`.
- Do not read or write PrayerMate application/cloud databases. Use only Axon's
  canonical prayer projection after cutover or its approved shadow workflow.
- Do not put licensed source bodies, prayer text, notes, credentials, or bearer
  tokens in Core history, git, diagnostics, or final responses.
- Do not fabricate a Logos result, resource revision, source locator, or rights.
- Keep existing active/completed sessions immutable; a new recipe affects only
  future work.
