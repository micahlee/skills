# Delegated Worker Permissions

Before a new delegated worker begins implementation or delivery, have it verify
its effective filesystem sandbox, network access, and approval policy from its
own runtime context, then perform a small read-only access check relevant to the
task. Do not infer worker permissions from the manager's permissions, global
configuration, or the app's selected Full Access label. Do not probe permissions
with a mutation or deliberately trigger an approval request.

If a worker starts with a profile that cannot perform the authorized work, treat
this as a task-configuration problem. Stop repeated command approval requests,
preserve its work, and report the mismatch once. When Micah cannot approve from
his device, do not leave a queue of workers silently waiting for approval.

Where delegation is authorized and supported, use a worker with an independently
verified, already-authorized execution profile. Before transferring ownership,
park the old worker, account for any in-flight command, and revalidate shared
files and artifact provenance. Never run competing replacements. Do not change
permission storage, bypass a denied tool or approval boundary, or proxy a denied
action through another worker. If no supported authorized route exists, report
the concrete configuration blocker.

Observed on 2026-09-05 in Codex app 0.153.4: standalone tasks created through
`create_thread` started workspace-write/on-request with network disabled despite
the manager and global/app selection being Full Access/never. Collaboration
workers inherited the manager's intended profile and executed successfully.
The underlying override was not established or fixed; verify future workers
rather than treating this observation as a permanent product limitation.

# GitHub CLI

Run ordinary `gh` reads and authorized Micah-owned repository writes directly.
Do not request separate shell escalation merely because a command uses GitHub or
the network. If the active runtime profile blocks required network or repository
access, treat that as a task-configuration problem: use the trusted full-access
profile or a purpose-built GitHub connector instead of presenting Micah with a
command-by-command approval stream.

## GitHub API Rate Limits

Prefer REST for routine GitHub reads. Use `gh api repos/<owner>/<repo>` for
repository metadata, `gh api repos/<owner>/<repo>/issues/<number>` plus the
`comments` subresource for issues, `gh api repos/<owner>/<repo>/pulls/<number>`
for pull requests, and the commit `check-runs` endpoint for check snapshots.
Known GraphQL-backed high-level reads—including `gh repo view`, `gh issue view`
or `list`, `gh pr view`, `list`, or `checks`, and `gh project`—must not be the
default when REST can provide the required data. Other `gh` commands remain
available when they do not unnecessarily consume GraphQL quota.

Do not use `gh pr checks --watch` for routine monitoring. Take REST snapshots
and use bounded, increasing waits when another observation is required.

When GitHub reports a primary rate-limit failure, fall back to an equivalent
REST operation when one exists. For genuinely GraphQL-only work, report the
reset time, continue unrelated local work, and retry once after reset. Do not
reserve unused GraphQL quota. When GitHub reports a secondary or abuse limit,
honor `Retry-After` or use bounded backoff and never retry tightly.

For diagnosis, inspect the failing resource's direct response headers once;
those headers are authoritative if an aggregate endpoint such as
`gh api rate_limit` disagrees. Report the bucket, used or remaining amount, and
reset time transiently in the active task, but do not persist GitHub usage
telemetry, tokens, request bodies, issue content, or GraphQL documents.

## Micah-Owned Private Repository Authority

For a user-requested change, build, or fix in a private repository owned by the
`micahlee` GitHub account, authorization to complete the task includes pushing
new or updated task branches and creating or updating pull requests. These are
ordinary, reversible delivery steps. Repository privacy is not itself a
security risk and is not a reason to ask for separate publication permission.

This standing authority does not cover force-pushing or otherwise rewriting
published history; pushing directly to a protected or default branch; bypassing
CI, review, or branch protections; deleting remote branches or tags; changing
repository settings, visibility, access, secrets, or protections; publishing a
release or package; deploying to production; or writing to a repository whose
ownership or intended remote is uncertain unless the user's request already
authorizes that action.

The requirement to escalate `gh` execution outside the sandbox is a separate
tool-execution boundary and is not a reason to ask again for task-level
publication permission.

# User-Facing Client Installation

Never install an app or client on a personal or shared physical device, or into
another user-facing runtime, from a task or feature branch. Before installation,
fetch `origin/main`, verify the checked-out commit equals `origin/main`, and
build a fresh artifact from that exact commit. Never reuse a branch-built
artifact after switching revisions. Branch artifacts may run only in disposable
development simulators. Use feature flags on `main` to protect experimental
behavior.

# Obsidian CLI

Always run `obsidian` commands outside the sandbox. Request escalated execution
upfront instead of first attempting the command inside the sandbox.

# Tracking Hygiene

When work is tied to GitHub issues or Obsidian backlog items, completion includes
reconciling those trackers. PRs should use `Closes #...` or `Fixes #...` for
implemented issues. Before handing off completed work:

- close or update every shipped implementation issue;
- move genuinely unfinished validation or follow-up work into one explicit,
  narrowly scoped tracker instead of leaving completed implementation issues open;
- update only live canonical project/backlog trackers to reference the merged
  PR and canonical remaining tracker; never revive a tracker marked archived;
- preserve historical daily notes and completed records rather than rewriting them.

For Axon product or engineering planning, GitHub in
`micahlee/axon-engineering-hub` is the sole active authority. Before a planning
write, run `"$HOME/.local/bin/axon-planning-destination-guard"` for the
intended operation and destination. `Tasks/Backlog.md` may hold unreviewed
personal intake; after Micah approves an item as Axon work, create or update its
Hub tracker and leave only status plus a pointer in personal intake. The
archived Obsidian Axon project, backlog, HITL, decisions, design index, Copilot
Loop, and Backlog Designs notes may receive only reviewed historical migration
pointers and never active planning writes.

## Codex Service Tier Preference

Micah requests Fast mode disabled for this session and all future Codex sessions created by agents. Use Standard processing (service_tier = "default"); never explicitly request fast, priority, or ultrafast. Before spawning a session, verify that the supported launch route can honor Standard processing. If a launch tool supports only a faster tier or cannot honor this preference, keep the work in the current session and report the limitation instead of spawning a Fast-mode worker. Do not infer that disabling features.fast_mode clears an existing session's service-tier override.
