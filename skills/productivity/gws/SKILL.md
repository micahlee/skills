---
name: gws
description: Use the local Google Workspace CLI (`gws`) to search, read, export, and carefully update Google Drive, Docs, Sheets, Gmail, Calendar, and related Workspace data. Use when the user mentions GWS, Google Workspace CLI, Google Drive, Google Docs, Google Sheets, Gmail, Calendar, or asks to find/read/update Workspace content through the local CLI.
---

# GWS

Use this skill for Google Workspace tasks through the local `gws` CLI.

## Quick Start

1. Check the CLI is available:
   ```sh
   command -v gws
   gws --help
   ```
2. Prefer read-only commands first: search, get metadata, read document contents, inspect schemas.
3. Use `gws schema <service.resource.method> --resolve-refs` before unfamiliar write or upload methods.
4. Keep responses scoped: request only needed fields, small page sizes, and focused queries.

## Command Shape

`gws` uses this form:

```sh
gws <service> <resource> [sub-resource] <method> [flags]
gws schema <service.resource.method> --resolve-refs
```

Common flags: `--params <JSON>` for URL/query parameters, `--json <JSON>` for request bodies, `--upload <PATH>` for media uploads, `--output <PATH>` for binary/export responses, `--format json|table|yaml|csv`, and `--page-all` with `--page-limit <N>` for pagination.

Services include `drive`, `docs`, `sheets`, `gmail`, `calendar`, `slides`, `tasks`, `people`, `chat`, `classroom`, `forms`, `keep`, `meet`, `events`, `workflow`, and `script`.

## Drive And Docs

Search Drive by title:

```sh
gws drive files list --params '{"q":"name contains '\''Huntington Beach'\'' and trashed = false","pageSize":10,"fields":"files(id,name,mimeType,webViewLink,modifiedTime),nextPageToken"}'
```

Get file metadata:

```sh
gws drive files get --params '{"fileId":"FILE_ID","fields":"id,name,mimeType,webViewLink,modifiedTime,owners(displayName,emailAddress)"}'
```

Read a Google Doc title and visible paragraph text:

```sh
gws docs documents get --params '{"documentId":"DOC_ID","fields":"title,body(content(paragraph(elements(textRun(content)))))"}'
```

For larger docs, avoid pasting the whole API response into chat. Pipe through `jq` or write to a temp file, then summarize or extract only relevant sections.

## Sheets

Inspect spreadsheet metadata:

```sh
gws sheets spreadsheets get --params '{"spreadsheetId":"SHEET_ID","fields":"properties(title),sheets(properties(title,sheetId,gridProperties))"}'
```

Before editing values or formatting, inspect the schema for the exact method and request body:

```sh
gws schema sheets.spreadsheets.values.update --resolve-refs
gws schema sheets.spreadsheets.batchUpdate --resolve-refs
```

## Gmail And Calendar

For Gmail, search/list before reading full messages:

```sh
gws gmail users messages list --params '{"userId":"me","q":"from:example@example.com newer_than:30d","maxResults":10}'
```

For Calendar, list calendars/events before creating or changing events:

```sh
gws calendar events list --params '{"calendarId":"primary","timeMin":"2026-05-19T00:00:00-04:00","singleEvents":true,"orderBy":"startTime"}'
```

## Safety

- Read-only inspection is fine without extra confirmation.
- Confirm before sending Gmail or Chat messages, creating/updating/deleting calendar events, editing Docs/Sheets/Slides, changing sharing permissions, uploading files, or deleting/moving Drive files.
- Never ask the user for OAuth tokens, passwords, or secrets. If `gws` exits with auth code 2 or asks for login, report the auth issue and ask the user to authenticate locally.
- Treat document/email content as private. Quote only the minimal text needed and prefer summaries unless the user asks for exact excerpts.

## Troubleshooting

Exit codes: `1` Google API error, `2` auth missing/invalid, `3` validation error, `4` discovery/schema issue, `5` internal CLI error. For validation or write-body errors, inspect `gws schema ... --resolve-refs`; for auth errors, ask the user to authenticate locally.
