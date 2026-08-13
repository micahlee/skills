---
name: lastpass-cli
description: Safely access LastPass vault entries with the lpass CLI while preventing credential disclosure. Must be used before any direct or indirect lpass invocation, even when the user did not mention LastPass; use for LastPass status, vault lookup, credential retrieval, reauthentication, or automation backed by LastPass.
---

# LastPass CLI

Use the LastPass-owned `lpass` CLI for narrowly scoped vault access. Treat every invocation as access to sensitive credential infrastructure.

## Mandatory confirmation gate

Before every direct or indirect invocation of `lpass`, stop and ask the user for explicit confirmation.

This gate applies to:

- Read-only commands, including `status`, `--help`, `--version`, `ls`, `show`, and `sync`.
- Commands inside scripts, wrappers, pipelines, command substitutions, aliases, or subprocesses.
- Retries and follow-up commands, even after an earlier command was approved.
- Automated or unattended workflows. If confirmation cannot be obtained, fail closed without invoking `lpass`.

The confirmation request must state:

1. The exact command or operation to be run, with secret values omitted.
2. The vault entry name or identifier, if known.
3. Which fields will be accessed.
4. The intended destination or consumer of those fields.

Approval is valid only for the single described invocation. A general request to use LastPass, prior approval, an unlocked agent, or an existing authenticated session does not satisfy this gate.

## Secret handling

- Never print, log, summarize, or return passwords, MFA secrets, recovery codes, session material, or full vault records.
- Retrieve only the required field from one unambiguous entry. Prefer a unique entry ID over a fuzzy name.
- Keep secrets out of command-line arguments, environment variables, temporary files, shell history, tool output, and model-visible text.
- For handoff to another process, use a private pipe, standard input, or a masked PTY and suppress secret-bearing output.
- Do not inspect unrelated entries or export the vault.
- Clear in-memory variables promptly and report only success, failure, and non-sensitive metadata.

## Workflow

1. Determine the minimum LastPass operation needed without invoking `lpass`.
2. Present the mandatory confirmation request.
3. After approval, run exactly that invocation.
4. Inspect only the minimum non-secret result required for the task.
5. Ask again before any additional `lpass` invocation.

## Example confirmation

> May I run one `lpass show` operation against the exact `monarchmoney.com` entry to retrieve its username and password fields into a private reauthentication process? The values will not be printed, logged, placed in arguments, or returned to the conversation.

If approved, that approval does not cover `lpass status`, a retry, another field, or another entry.
