# Obsidian Inbox Processing

This context describes a personal Obsidian workflow for triaging captured fragments from a single inbox note into the user's PARA-based vault, task lists, shopping lists, reading lists, daily notes, and calendar entries.

## Language

**Inbox**:
A single Obsidian note that contains unprocessed bullet points or captured fragments.
_Avoid_: inbox folder, vault crawler

**Inbox Item**:
One bullet point or captured fragment in the **Inbox** that needs a destination or disposition.
_Avoid_: note, task, thing

**Inbox Item Block**:
A top-level bullet and any indented continuation lines or nested bullets that belong to it.
_Avoid_: line

**Compressed Fragment**:
A short **Inbox Item** whose meaning or intended action is too abbreviated to route confidently.
_Avoid_: obvious task

**Processed Item**:
An **Inbox Item** that has been moved from the **Inbox** to its destination.
_Avoid_: copied item, checked-off item

**Destination Entry**:
The lightly rewritten form of a **Processed Item** inserted into its destination.
_Avoid_: raw paste

**Destination Section**:
The heading or board column within a destination note where a **Destination Entry** is inserted.
_Avoid_: file top

**New Destination**:
A destination note, list, section, or board created during inbox processing because no suitable existing destination exists.
_Avoid_: speculative category

**Low-Risk Destination**:
A **New Destination** that is narrow, obvious from the **Inbox Item**, and consistent with existing vault patterns.
_Avoid_: new project

**Ambiguous Item**:
An **Inbox Item** whose destination is not clear enough to move during an **Automation Run**.
_Avoid_: failed item, error

**Ambiguity Tag**:
The Obsidian tag `#inbox/ambiguous` applied to an **Ambiguous Item** that needs personal review.
_Avoid_: checkbox status, custom marker

**Processing Failure**:
An **Inbox Item** that has a clear destination but could not be fully processed because a required write or integration failed.
_Avoid_: ambiguous item

**Processing Failure Tag**:
The Obsidian tag `#inbox/failed` applied to a **Processing Failure** that needs troubleshooting or retry.
_Avoid_: ambiguity tag

**Duplicate Item**:
An **Inbox Item** that appears to already exist in its intended destination.
_Avoid_: ambiguous item

**Duplicate Tag**:
The Obsidian tag `#inbox/duplicate` applied to a **Duplicate Item** with inline context pointing to the likely existing entry.
_Avoid_: failure tag

**Processing Log**:
A prepend-only Obsidian note that records where each **Processed Item** was moved.
_Avoid_: audit database, changelog

**Log Entry**:
A record in the **Processing Log** containing the original inbox text, destination path or section, and final **Destination Entry**.
_Avoid_: run summary

**Interactive Run**:
An inbox processing session where the user can review a proposed routing plan before changes are applied.
_Avoid_: manual mode

**Routing Proposal**:
A numbered plan of proposed moves, destination entries, new destinations, duplicate markings, failure risks, and calendar entries shown during an **Interactive Run**.
_Avoid_: dry run output

**Run Summary**:
A compact report of how many items were moved and how many were left as ambiguous, duplicate, or failed.
_Avoid_: processing log

**Automation Run**:
An inbox processing session that can run without user input and apply eligible moves on its own.
_Avoid_: batch job, AFK script

**Run Limit**:
The maximum number of eligible **Inbox Items** an **Automation Run** may move in one session.
_Avoid_: batch size

**Inbox Processing Config**:
A local configuration file that stores vault paths, destination paths, calendar ID, and automation defaults for inbox processing.
_Avoid_: hardcoded paths

**Process Inbox Command**:
The user-facing `/process-inbox` invocation for running Obsidian inbox processing.
_Avoid_: obsidian-inbox-processing command

**Process Inbox Skill**:
The `process-inbox` Codex skill that implements the **Process Inbox Command**.
_Avoid_: obsidian-inbox-processing skill

**Destination Index**:
A runtime inventory of configured destination notes, active project folders, shopping lists, and relevant destination sections.
_Avoid_: persistent cache

**Obsidian Write**:
A vault mutation performed through the Obsidian CLI when Obsidian is available.
_Avoid_: raw edit

**Filesystem Fallback**:
A configured automation-safe vault mutation performed directly on Markdown files when an **Obsidian Write** is unavailable.
_Avoid_: ad hoc file edit

**Safe Move**:
A multi-note mutation that validates source items, backs up affected files, and applies all destination, inbox, and log changes carefully.
_Avoid_: best-effort append

**PARA Vault**:
An Obsidian vault organized around Projects, Areas, Resources, and Archives.
_Avoid_: notebook, generic vault

**Destination Type**:
A kind of Obsidian note or list that can receive a **Processed Item**.
_Avoid_: PARA category

**General Backlog**:
The cross-project task backlog for actionable items that do not clearly belong to a specific project board.
_Avoid_: task dump

**Project Board**:
A project-specific Kanban or checklist note for actionable work that clearly belongs to an active project.
_Avoid_: project folder, PARA project

**Project Match**:
A clear association between an **Inbox Item** and an active project, based on an exact or strongly implied project name.
_Avoid_: loose topic similarity

**Project Note**:
A project-specific note for reference or context that clearly belongs to an active project but is not itself a task.
_Avoid_: project board

**Shopping List**:
A store-specific list for items to buy when the intended store is clear.
_Avoid_: wishlist

**Store-Clear Shopping Item**:
An **Inbox Item** for something to buy where the intended store is explicit or strongly implied.
_Avoid_: generic shopping task

**Read Later**:
A low-friction holding list for raw links that should be revisited.
_Avoid_: reading list

**Link Inspection**:
Reading enough of a linked page's content to determine the correct destination for a URL-based **Inbox Item**.
_Avoid_: URL guessing

**Public Link Inspection**:
Inspecting publicly accessible page title, metadata, and readable main content without logging into the linked service.
_Avoid_: authenticated browsing, social media scraping

**Uninspected Link**:
A URL-based **Inbox Item** whose linked content could not be inspected well enough to route confidently.
_Avoid_: bare URL

**Reading List**:
A categorized list for reading ideas with enough context to place under an existing topic.
_Avoid_: read later

**Someday/Maybe**:
A low-pressure list for possible future actions with no current commitment.
_Avoid_: backlog

**Gift Idea**:
An idea for a gift for a specific person or occasion.
_Avoid_: shopping item

**People Note**:
An area note for remembering people and contact-related context.
_Avoid_: contacts database

**Person-Context Item**:
An **Inbox Item** that includes a person's name plus enough context to remember, follow up, or file it usefully.
_Avoid_: bare name

**Area Note**:
An existing note for an ongoing area of responsibility or interest.
_Avoid_: project note

**Daily Note**:
A date-specific note for time-bound tasks, day-specific context, and journal-like fragments.
_Avoid_: backlog

**Date-Bound Item**:
An **Inbox Item** with explicit or resolvable timing that belongs on a specific date.
_Avoid_: backlog task

**Dated Task**:
A task-like **Date-Bound Item** that belongs in a **Daily Note** but should not create a calendar event.
_Avoid_: calendar event

**Calendar-Worthy Item**:
A **Date-Bound Item** that represents an appointment, event, deadline, reservation, or time-block that belongs on the **Default Calendar**.
_Avoid_: dated task

**Hard Deadline**:
A **Calendar-Worthy Item** where something is due, closes, expires, or must happen by a specific date.
_Avoid_: ordinary dated task

**Default Calendar**:
The user's primary Google Calendar used for personal calendar entries created from **Date-Bound Items**.
_Avoid_: external task list

**Calendar Entry**:
A Google Calendar entry created from a **Date-Bound Item**.
_Avoid_: reminder

**All-Day Calendar Entry**:
A **Calendar Entry** for a **Date-Bound Item** that has a date but no explicit time.
_Avoid_: guessed time

**Timed Calendar Entry**:
A **Calendar Entry** for a **Date-Bound Item** that includes an explicit time.
_Avoid_: default time block

## Relationships

- An **Inbox** contains zero or more **Inbox Items**.
- An **Inbox Item** is parsed as an **Inbox Item Block** when it has indented continuation lines or nested bullets.
- A **Compressed Fragment** remains in the **Inbox** as an **Ambiguous Item** unless its intent is clear from context.
- An **Inbox Item** becomes a **Processed Item** by being moved out of the **Inbox**.
- An **Ambiguous Item** remains in the **Inbox** for later review.
- An **Ambiguous Item** receives the **Ambiguity Tag** unless it already has it.
- An **Automation Run** skips **Inbox Items** that already have the **Ambiguity Tag**.
- A **Processing Failure** remains in the **Inbox** with the **Processing Failure Tag** and enough inline context to explain what failed.
- A **Processing Failure** is not a **Processed Item** and is not recorded in the **Processing Log**.
- An **Automation Run** skips **Inbox Items** that already have the **Processing Failure Tag**.
- A **Duplicate Item** remains in the **Inbox** with the **Duplicate Tag** and enough inline context to identify the likely existing destination entry.
- A **Duplicate Item** is not a **Processed Item** and is not recorded in the **Processing Log**.
- An **Automation Run** skips **Inbox Items** that already have the **Duplicate Tag**.
- Duplicate detection compares an **Inbox Item** against its intended destination, not the whole vault.
- A **Processed Item** is moved into one **Destination Type**.
- A **Destination Entry** may lightly rewrite a **Processed Item** to clarify intent or context without changing its meaning.
- A **Processed Item** requires a clear **Destination Section** when its destination note has meaningful sections.
- A **New Destination** may be created when confidence is high that it matches the user's existing vault organization.
- An **Automation Run** may create a **Low-Risk Destination** such as an obvious store shopping list, resource note, reading-list section, or missing **Processing Log**.
- An **Automation Run** may create a missing **Daily Note** for a clear **Date-Bound Item** using the configured daily note pattern and template rules.
- Creating a new project folder, project board, area, archive structure, or sensitive church/work destination requires an **Interactive Run** unless the item names the destination clearly.
- A **Processing Log** records the destination of each **Processed Item**.
- A **Processing Log** records only moved **Processed Items**, not **Ambiguous Items**.
- A **Log Entry** includes the original inbox text, destination path or section, and final **Destination Entry**.
- A **Log Entry** for a **Date-Bound Item** records both the **Daily Note** destination and the **Calendar Entry**.
- An **Interactive Run** may show a routing proposal before moving **Inbox Items**.
- A **Routing Proposal** supports approving all items, approving selected items, revising specific routes, or cancelling.
- An **Interactive Run** shows proposed **Calendar Entries** before creating them.
- An **Automation Run** must decide whether each **Inbox Item** is eligible to move without user input.
- An **Automation Run** creates **Calendar Entries** only for high-confidence **Calendar-Worthy Items**.
- An **Automation Run** returns a **Run Summary** that counts moved, ambiguous, duplicate, and failed items.
- An **Automation Run** respects a configurable **Run Limit**, defaulting to 25 eligible moves per session.
- An **Inbox Processing Config** stores the **Inbox**, **Processing Log**, destination paths, daily note pattern, **Default Calendar**, and **Run Limit**.
- The workflow is invoked by the **Process Inbox Command**.
- A manual **Process Inbox Command** defaults to an **Interactive Run**.
- The **Process Inbox Command** uses an explicit automation mode for AFK processing.
- The skill is named **Process Inbox Skill** and uses `process-inbox` as its skill name.
- Each run builds a **Destination Index** from the configured vault paths instead of relying on a persistent destination cache.
- Archived folders are not valid destinations for **Inbox Items**.
- Completed-task folders or notes are not valid destinations for **Inbox Items**.
- A vault mutation should use an **Obsidian Write** when available.
- An **Automation Run** may use the **Filesystem Fallback** when Obsidian is not running.
- A **Filesystem Fallback** must use a **Safe Move** before mutating the vault.
- A **Safe Move** validates that each original **Inbox Item** still exists exactly once, backs up every affected file, applies destination and inbox edits, and writes the **Processing Log**.
- The initial **Destination Types** are **General Backlog**, **Project Board**, **Project Note**, **Shopping List**, **Read Later**, **Reading List**, **Someday/Maybe**, **Gift Idea**, **People Note**, **Area Note**, and **Daily Note**.
- **PARA Vault** describes the organization model; it is not itself a **Destination Type**.
- A URL-based **Inbox Item** requires **Link Inspection** before it can be moved during an **Automation Run**.
- An **Automation Run** may perform **Public Link Inspection** to classify URL-based **Inbox Items**.
- An **Uninspected Link** is an **Ambiguous Item** and remains in the **Inbox** for review.
- A **Dated Task** is moved to the appropriate **Daily Note** and does not create a **Calendar Entry**.
- A **Calendar-Worthy Item** is moved to the appropriate **Daily Note** and added to the **Default Calendar** as a **Calendar Entry**.
- Appointments, events, reservations, travel, hard deadlines, and intentional time blocks are **Calendar-Worthy Items**.
- Ordinary dated tasks are **Dated Tasks**, not **Calendar-Worthy Items**.
- A **Hard Deadline** creates a **Daily Note** task and an **All-Day Calendar Entry** when no explicit time is given.
- A **Calendar-Worthy Item** becomes a **Processed Item** only if both the **Daily Note** write and **Calendar Entry** creation succeed.
- If **Calendar Entry** creation fails, the item becomes a **Processing Failure**, not an **Ambiguous Item**.
- A task-like **Date-Bound Item** is a **Dated Task** unless it is clearly a **Calendar-Worthy Item**.
- A **Dated Task** is inserted into the **Daily Note** Must section.
- A date-only **Calendar-Worthy Item** creates an **All-Day Calendar Entry**.
- A **Calendar-Worthy Item** with an explicit time creates a **Timed Calendar Entry**.
- A **Project Board** or **Project Note** destination requires a **Project Match**.
- An actionable **Inbox Item** without a **Project Match** goes to the **General Backlog** only when its backlog category is clear; otherwise it remains an **Ambiguous Item**.
- A shopping-related **Inbox Item** goes to a **Shopping List** only when it is a **Store-Clear Shopping Item**.
- A shopping-related **Inbox Item** without a clear store goes to the **General Backlog** when it is still an actionable task.
- A person-related **Inbox Item** goes to the **People Note** only when it is a **Person-Context Item**.
- A bare person name is an **Ambiguous Item**.

## Example Dialogue

> **Dev:** "Should the skill scan every note in the vault for loose tasks?"
> **Domain expert:** "No. It should process **Inbox Items** from the single **Inbox** and move them into the right part of the **PARA Vault** or another personal list."
>
> **Dev:** "If a top-level bullet has nested bullets, are those separate items?"
> **Domain expert:** "No. They are one **Inbox Item Block** and should be routed together."
>
> **Dev:** "Should a very short phrase be routed by guessing the user's intent?"
> **Domain expert:** "No. A **Compressed Fragment** stays ambiguous unless its intent is clear."
>
> **Dev:** "Should processed bullets stay in the **Inbox** as checked items?"
> **Domain expert:** "No. A **Processed Item** is moved to its destination, and the **Processing Log** records where it went."
>
> **Dev:** "Can the skill always stop to ask before moving items?"
> **Domain expert:** "No. An **Automation Run** must be able to process eligible items while AFK, though an **Interactive Run** can show a proposal first."
>
> **Dev:** "Can automation silently create calendar events?"
> **Domain expert:** "Yes, but only for high-confidence **Calendar-Worthy Items**; uncertain cases stay ambiguous."
>
> **Dev:** "Should automation drain every eligible item no matter how many there are?"
> **Domain expert:** "No. It should respect a configurable **Run Limit** so one run cannot mutate too much at once."
>
> **Dev:** "Should paths and calendar IDs be hardcoded in the skill?"
> **Domain expert:** "No. They belong in the **Inbox Processing Config** so automation is explicit and stable."
>
> **Dev:** "What should the user-facing command be called?"
> **Domain expert:** "Use the **Process Inbox Command**, `/process-inbox`."
>
> **Dev:** "Should `/process-inbox` apply changes immediately when run manually?"
> **Domain expert:** "No. Manual invocation defaults to an **Interactive Run**; automation mode must be explicit."
>
> **Dev:** "Can the user approve only some proposed moves?"
> **Domain expert:** "Yes. A **Routing Proposal** can be approved all at once, approved selectively, revised, or cancelled."
>
> **Dev:** "Should the durable **Processing Log** include items that were left behind?"
> **Domain expert:** "No. Left-behind counts belong in the **Run Summary**, not the **Processing Log**."
>
> **Dev:** "Should the skill name differ from the command name?"
> **Domain expert:** "No. The **Process Inbox Skill** should be named `process-inbox`."
>
> **Dev:** "Should the skill cache all known destinations between runs?"
> **Domain expert:** "No. It should build a fresh **Destination Index** each run so project renames and archive moves are respected."
>
> **Dev:** "Can automation route new items into archived project folders?"
> **Domain expert:** "No. Archived folders are not valid destinations."
>
> **Dev:** "Can automation route new items into completed-task history?"
> **Domain expert:** "No. Completed-task folders and notes are not valid inbox-processing destinations."
>
> **Dev:** "What happens when an **Automation Run** cannot tell where an item belongs?"
> **Domain expert:** "It should leave the **Ambiguous Item** in the **Inbox** with the **Ambiguity Tag** instead of guessing."
>
> **Dev:** "Should automation retry an item that already has the **Ambiguity Tag**?"
> **Domain expert:** "No. The user removes the **Ambiguity Tag** when it is ready to be tried again."
>
> **Dev:** "Should the destination receive the exact raw bullet?"
> **Domain expert:** "Not necessarily. A **Destination Entry** may lightly rewrite the item so the intention or context is clearer."
>
> **Dev:** "Should the **Processing Log** list ambiguous items?"
> **Domain expert:** "No. It records only items actually moved, with both the original inbox text and the final **Destination Entry**."
>
> **Dev:** "Can automation append to the top of a note if it knows the file but not the right heading?"
> **Domain expert:** "No. It needs a clear **Destination Section**, or the item stays ambiguous."
>
> **Dev:** "Can automation create a destination that does not exist yet?"
> **Domain expert:** "Yes, when confidence is high that the **New Destination** matches the existing vault organization."
>
> **Dev:** "Can automation create a whole project from a vague captured idea?"
> **Domain expert:** "No. Automation may create only a **Low-Risk Destination**; higher-level organization needs an **Interactive Run** unless the destination is explicit."
>
> **Dev:** "Should a date-bound item fail because the target **Daily Note** does not exist yet?"
> **Domain expert:** "No. Automation may create the missing **Daily Note** using the configured pattern and template rules."
>
> **Dev:** "Where should a dated task land inside the **Daily Note**?"
> **Domain expert:** "Task-like **Date-Bound Items** go in the Must section."
>
> **Dev:** "Must automation fail if Obsidian is closed?"
> **Domain expert:** "No. It should prefer an **Obsidian Write**, but an **Automation Run** may use a configured **Filesystem Fallback**."
>
> **Dev:** "Can the filesystem fallback append to destinations one at a time and hope the rest succeeds?"
> **Domain expert:** "No. It needs a **Safe Move** with validation, backups, and careful application across the Inbox, destination notes, and **Processing Log**."
>
> **Dev:** "Should the router send something to 'PARA'?"
> **Domain expert:** "No. It should pick a concrete **Destination Type** such as **Project Board**, **Area Note**, or **Read Later**."
>
> **Dev:** "Can a bare URL be routed from its domain or surrounding text alone?"
> **Domain expert:** "No. It needs **Link Inspection**, or it stays in the **Inbox** as an **Ambiguous Item**."
>
> **Dev:** "Can automation open the web to classify links?"
> **Domain expert:** "Yes, but only through **Public Link Inspection**. Links that need login or cannot be inspected stay ambiguous."
>
> **Dev:** "What happens to an item with a clear date?"
> **Domain expert:** "A **Dated Task** goes to the appropriate **Daily Note** only. A **Calendar-Worthy Item** also creates a **Calendar Entry** on the **Default Calendar**."
>
> **Dev:** "Is 'call dentist tomorrow' calendar-worthy?"
> **Domain expert:** "No. It is an ordinary **Dated Task**. An appointment, reservation, hard deadline, or intentional time block would be calendar-worthy."
>
> **Dev:** "Should a hard deadline appear on the calendar?"
> **Domain expert:** "Yes. A **Hard Deadline** gets both a **Daily Note** task and a calendar date marker."
>
> **Dev:** "Should automation invent a time when the item only names a date?"
> **Domain expert:** "No. Date-only **Calendar-Worthy Items** create **All-Day Calendar Entries**; only **Calendar-Worthy Items** with explicit times create **Timed Calendar Entries**."
>
> **Dev:** "Is a date-bound item processed if it reaches the **Daily Note** but calendar creation fails?"
> **Domain expert:** "Only if it is a **Calendar-Worthy Item**. A **Dated Task** does not need a calendar write."
>
> **Dev:** "If calendar creation fails, is the item ambiguous?"
> **Domain expert:** "No. The destination is clear; it is a **Processing Failure** and should be marked with the **Processing Failure Tag** plus a useful error note."
>
> **Dev:** "Should automation retry a **Processing Failure** on every run?"
> **Domain expert:** "No. The user removes the **Processing Failure Tag** after fixing the issue or deciding to retry."
>
> **Dev:** "If an item appears to already exist in the destination, should it be marked ambiguous?"
> **Domain expert:** "No. It is a **Duplicate Item** and should use the **Duplicate Tag** with a pointer to the likely existing entry."
>
> **Dev:** "Should duplicate detection search the whole vault?"
> **Domain expert:** "No. It should compare against the intended destination so similar wording in other contexts does not block processing."
>
> **Dev:** "Can automation file a task into a project just because it sounds related?"
> **Domain expert:** "No. It needs a **Project Match**; otherwise the item stays in the **Inbox** for review or goes to the **General Backlog** if that destination is clear."
>
> **Dev:** "Should automation create or use a generic shopping list when the store is unclear?"
> **Domain expert:** "No. Only **Store-Clear Shopping Items** go to **Shopping Lists**; other buy-related tasks go to the **General Backlog** when actionable."
>
> **Dev:** "Should a bare person name go to the **People Note**?"
> **Domain expert:** "No. It needs context; a bare name stays ambiguous."

## Flagged Ambiguities

- "Inbox processing" was clarified to mean triaging a single Obsidian note of bullets/fragments, not scanning an inbox folder or the whole vault.
- "Inbox item" was clarified to mean a top-level bullet with any nested context, not each physical line.
- "Compressed fragment" was clarified as too abbreviated to route unless intent is clear.
- "Processed" was clarified to mean moved out of the **Inbox**, not copied, checked off, or left in place.
- "Non-interactive" was clarified as an **Automation Run** that can apply eligible moves without user input.
- "Automation scope" was clarified to use a configurable **Run Limit**, defaulting to 25 eligible moves.
- "Configuration" was clarified as a local **Inbox Processing Config**, not hardcoded skill paths.
- "Destination discovery" was clarified as per-run **Destination Index** construction, not a persistent cache.
- "Archive" was clarified as not a valid destination for inbox processing.
- "Completed" was clarified as task history, not a valid destination for inbox processing.
- "Ambiguous" was clarified as a normal review state, not a processing failure.
- "Ambiguous tag" was clarified as the Obsidian tag `#inbox/ambiguous`, not a checkbox or custom syntax.
- "Processing failure" was clarified as distinct from ambiguity; use `#inbox/failed` when a known route cannot be completed.
- "Failure retry" was clarified as user-controlled by removing `#inbox/failed`.
- "Duplicate" was clarified as its own review state using `#inbox/duplicate`.
- "Duplicate detection" was clarified as destination-scoped, not a whole-vault search.
- "Retry" was clarified as user-controlled by removing `#inbox/ambiguous`, not by adding a separate retry tag.
- "Move" was clarified to allow a light rewrite in the **Destination Entry**, with the original meaning preserved.
- "Processing log" was clarified as a prepend-only record of moved items, not a list of ambiguous review items.
- "Destination" was clarified to include a clear **Destination Section** when the note has meaningful headings or board columns.
- "Destination creation" was clarified as allowed when confidence is high, not limited to existing notes only.
- "New destination" was clarified to distinguish low-risk obvious containers from higher-level PARA organization.
- "Vault writes" were clarified to prefer the Obsidian CLI while allowing a configured safe filesystem fallback for automation.
- "Filesystem fallback" was clarified to require **Safe Move** behavior, including backups and source validation.
- "PARA" was clarified as the organization model for the vault, not a concrete destination.
- "Bare URL" was clarified as insufficient for routing unless the linked content has been inspected.
- "Web inspection" was clarified as public, bounded inspection for classification, not authenticated browsing.
- "Date-bound" was corrected to distinguish **Dated Tasks** from **Calendar-Worthy Items**.
- "Calendar creation" was clarified as only for appointments, events, deadlines, reservations, or time-blocks, not ordinary dated tasks.
- "Calendar timing" was clarified as all-day by default only for date-only **Calendar-Worthy Items**.
- "Project routing" was clarified to require a **Project Match**, not loose topic similarity.
- "Shopping list routing" was clarified as store-specific; shopping tasks without a clear store route to the **General Backlog** when actionable.
- "People routing" was clarified as requiring context beyond a bare person name.
