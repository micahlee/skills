---
name: crossbar-cli
description: Uses the personal Crossbar sports CLI to read teams, family participants, rosters, schedules, pending RSVPs, volunteer opportunities, and website team feeds, and submit explicitly requested RSVPs. Use for Crossbar requests and Micah's family hockey requests involving Chasen, Samuel, Greenville Hockey, Greenville Rage, House 14U, or game schedule graphics. General hockey research and professional Swamp Rabbits schedules use their own sources.
---

# Crossbar hockey

Use the local client from `micahlee/crossbar-client` for live family hockey data. This is the Crossbar sports platform, not Crossbar.io or the 2600Hz telephony API.

## Locate and run

Resolve the launcher on this host in this order: an explicit `CROSSBAR_CLI`
path, `crossbar` on `PATH`, or `bin/crossbar` in the local
`micahlee/crossbar-client` checkout (normally `~/projects/crossbar-client`).
Verify that the resolved path is executable. If none is available, report the
missing client; never reuse another host's absolute checkout path. Examples
below abbreviate the resolved executable as `CLI`.

For a new host, clone `micahlee/crossbar-client`, read its `README.md`, and use
its documented Python environment and `build.sh`. The native helpers require
certificate-backed signing, and the login UI is `build/CrossbarClient.app`.
Verify an available signing identity instead of assuming one transferred with
the repo. Complete normal central and club login separately on this host;
Keychain cookies cannot be assumed to transfer. A stable launcher on `PATH`
should invoke that host's checkout. Follow Micah's main-only installation rule.

Use `CLI --help` rather than inventing commands. Global options precede the
subcommand.

## Live reads

Central Crossbar accounts and Greenville Hockey have separate cookie domains. The club is the CLI's default site. Central accounts are the verified route for the combined family calendar; central `teams` can be empty even when club memberships exist.

```sh
CLI --json status
CLI --json status --all-sites
CLI --site accounts --json status
CLI --site accounts --json participants
CLI --site accounts --json schedule --month YYYY-MM --participant PARTICIPANT_ID
CLI --json teams
CLI --json roster --team TEAM_ID
CLI --json rsvp pending --participant PARTICIPANT_ID
CLI --json rsvp list --team TEAM_ID
CLI --json volunteers
CLI --json volunteers --date all
CLI --json volunteers --session SESSION_ID
CLI --json volunteers --on YYYY-MM-DD --open-only
CLI --json volunteer-check --on YYYY-MM-DD --team TEAM_ID --team OTHER_TEAM_ID
CLI --json messages --team TEAM_ID
```

Resolve requested names to IDs from current participants/team lists. `participants` lists the account's family; `roster` lists a team's participant names. Do not guess IDs or equate an empty central team list with no memberships.

Schedules cover one calendar month per call. For an upcoming or full-season request, query the needed months, state the range checked, and distinguish no published events from a failed fetch. The calendar currently returns description, date, time, timezone, participant, team, event ID, duration, and location. Game descriptions observed include `vs.` and `@`; practice descriptions include `Practice`. These are observed labels, not a complete event-type schema. Resolve unfamiliar descriptions before claiming a games-only list is complete. Preserve TBD opponents and time exceptions. Use the source timezone, not the machine timezone.

## RSVP changes

`rsvp pending` identifies participant/event responses still unanswered; it does not submit anything. For an update, the user's instruction must identify the child, event(s), and yes/no response unambiguously. Resolve names and dates against live records; ask only for missing choices.

```sh
CLI --json rsvp set --team TEAM_ID --event EVENT_ID --participant PARTICIPANT_ID --response yes
CLI --json rsvp set --team TEAM_ID --event EVENT_ID --participant PARTICIPANT_ID --response yes --apply
```

First inspect the preview for the correct child/event. Submit with `--apply` when that exact response is authorized; `no` declines. The CLI validates membership and the server-provided action, rejects past events, sends at most one update, and reads back the result. Report success only when verified. If submission or verification fails, inspect live availability before another attempt; never blindly retry. RSVP links are state-changing GETs: do not open or fetch them as discovery links. No live RSVP was exercised during initial development.

## Authentication and current limits

Credentials/cookies live only in this client's macOS Keychain entries. Never print them, extract another browser's cookie database, change cookie domains, or add them to repo files. A Keychain-approval error requires Micah to run the native `build/crossbar status` in his own Terminal and approve locally. On October 6, agent filesystem-sandbox execution returned `Keychain: One or more parameters passed to a function were not valid.`, while the same unchanged native helper succeeded noninteractively outside that sandbox. Do not treat that error alone as expired authentication or repair Keychain permissions; an approved read outside that sandbox can distinguish the restriction. Native `build/crossbar status` defaults to central accounts; add `--site club --json` for the club. High-level `CLI --json status` defaults to the club, and `CLI --json status --all-sites` checks both independently. Inspect `authenticated` and `state`: missing site/session, login required, Keychain approval/access failures, network verification failure, rate limiting, server errors, and unexpected responses are separate. It never submits credentials. A central success does not establish club authentication. It sends no password. Do not substitute `login`, which may submit credentials, merely to approve access.

A missing/expired session for the requested site requires normal login and **Save session** in `build/CrossbarClient.app` (the executable `build/CrossbarClient` remains available); use **Club login** for Greenville Hockey. Complete CAPTCHA/MFA through the normal user login. The tested direct credential flow requires CAPTCHA; avoid repeated credential attempts. Both native executables use stable certificate-backed signing; rebuild with `build.sh`, preserving identifiers and signing identity. Rebuild only for native changes, and never weaken Keychain access controls to suppress prompts.

Website messages cover the team feed, not mobile Team Chat. An empty feed does not imply no chat messages. Volunteer discovery and dated shifts are supported. `volunteers` defaults to the future list; `--date future|past|all` selects session lists. Detailed reads (`--session ID`, `--details`, `--on YYYY-MM-DD`, `--open-only`) default to both future and past lists and require discovery before session reads. Filter actual shift dates, not session-card dates. Output counts explicit `claimed`/`unclaimed` shift cells, handles multiple positions per role, and excludes `.noshift` padding. `--open-only` filters rows while preserving counts. Open means unclaimed, including historical shifts with disabled claim controls; it does not guarantee signup eligibility. The JSON distinguishes `no_matching_published_shifts` from verified dated shifts; empty discovery or no matching shifts never proves full staffing. Unknown or contradictory layouts fail. Sessions are organization-wide and not linked to team IDs: output has `team_id: null` and `team_match_verified: false`. Compare session scope and actual date/time/location with the team event; never equate 12U House with travel 12A by age alone. Shift timezone is null if unpublished; use Eastern dates for Greenville day-before checks. Club reads require a club session. Message sending, RSVP notes, and volunteer signup are not implemented.

## Family volunteer checks

Use `CLI --json volunteer-check --on YYYY-MM-DD --team TEAM_ID [--team OTHER_TEAM_ID]` for the selected family teams. It validates owned IDs, reads typed team schedules (Game, Practice, Extra-Practice), preserves other event types for review, and skips volunteer reads when no requested event exists. With events, it inspects both session lists and actual shifts. Compare dates in America/New_York using site-displayed time labels; do not assume timezone metadata was published.

Without confirmed session scope, date/venue/time-compatible positions stay `possible_openings`, not definite family-team vacancies. Only pass `--session-team SESSION_ID=TEAM_ID` when that session's team association has been explicitly confirmed by the user or authoritative source evidence. Never infer that mapping from age, a shared venue, or overlapping time alone. Mappings are per invocation, checked against discovered sessions/selected teams, and recorded in output. `confirmed_openings` require the explicit mapping, actual time overlap, and unique event association. Adjacent/TBD/ambiguous events require review. Report confirmed roles/counts with direct shift links; distinguish possible matches needing review. Unmatched shifts remain visible. No matching published positions never establishes full staffing.

Before relying on the CLI for recurring checks, validate the club `status`, populated session counts, and matching results against the authenticated browser. If club auth is missing, perform normal club capture and verify the selected-site success message and club status; do not extract browser cookies. Native builds preserve the existing certificate-backed identifiers and Keychain access controls.

## Schedule graphics

Fetch current data before making or updating a schedule; prior PDF/PNG files are snapshots. Keep dates, weekdays, opponents, home/away labels, venue, and timezone consistent with live results, and show the retrieval date. Prefer exact text in a printable PDF plus PNG for sharing. Use an available PDF/document skill for rendering and visual verification.

For Chasen's House 14U - Mease schedule, use Swamp Rabbits-inspired midnight navy, copper orange, and white. For Samuel's Greenville Rage schedule, use the supplied Rage reference and colors. Do not label a house schedule as the professional Swamp Rabbits team. If a requested design reference is unavailable, request its location and clearly describe any provisional layout. The existing `tools/create_chasen_schedule.py` is a static snapshot generator with local font dependencies; replace its game data and update its date/count checks before reusing it for a new schedule.
