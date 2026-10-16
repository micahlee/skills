# Shared simulator runner (AXON-2735)

# Shared Apple Simulator Sessions

All threads on a Mac must use `$HOME/.local/bin/axon-simulator-run` for work
that boots or uses a simulator. The runner owns one host-wide slot across all
repositories and worktrees and holds it until verified shutdown. Never use raw
`simctl boot`, direct simulator `xcodebuild test`, Xcode previews, or another
simulator tool to bypass it. Build-only work, package tests, research, and other
non-simulator work may remain parallel.

- Tests: `axon-simulator-run xcodebuild -- <xcodebuild arguments without the executable>`.
  Supply one exact simulator destination; the runner disables parallel clones.
- Install/launch/screenshots: `axon-simulator-run run --device <UDID> --timeout 900 -- <script>`.
  Keep the entire journey inside that script. `AXON_SIMULATOR_UDID` is its owned
  device. Shutdown occurs when the script ends; never hold a slot while waiting
  for a human answer. For interactive inspection, use a bounded script/session.
- Disposable fixtures: `run --name <fixture> --erase -- <script>`; erasure is
  explicit and applies only to that selected development fixture. Newly created
  named fixtures are deleted after verified shutdown, including failed/cancelled
  runs and crash recovery. Existing fixtures and explicit device IDs are retained.
  Use `--keep-fixture` to intentionally preserve a new fixture for later work.
- Phone/Watch checks: `run --paired --device <phone-UDID> --device <watch-UDID> -- <script>`.
  This is one exclusive job, with the explicit paired-device exception.
- Use `status` for ownership and `recover` for stale managed sessions. Do not
  delete the lock file or kill unrelated simulators. Unexpected active devices
  block admission; resolve them with their owning task instead of bypassing.

Use updated repository qualification entry points. If the runner is missing,
install it using the skills repository's `scripts/install_simulator_runner.py` from a
clean freshly fetched `origin/main`; never install a task-branch runner. Do not
copy the runner into each worktree or change its shared state path. Existing
threads must read this rule before their next simulator operation.

The lock is cooperative: manually booted simulators or tools that ignore these instructions are detected as conflicts. It is not a macOS access-control boundary. Do not run a second simulator while a session is active. The caller-facing process has a separate supervisor, which cancels the job on parent death. After supervisor loss or host restart, the next admission recovers its recorded worker and devices before proceeding. Cleanup failure leaves recovery state and blocks subsequent admission. Existing device definitions are retained; only newly created disposable named fixtures are deleted after shutdown.

New invocations enroll in a FIFO waiting queue before attempting the same host
lock. A newer job cannot pass an enrolled waiter between polling attempts.
Cancellation and queue timeout remove that invocation's ticket; dead or reused
process identities and tickets from a previous host boot are pruned before
admission. Queue bookkeeping contains process identities only. The running job
continues holding the host lock through verified teardown. The `--wait` budget
remains separate from the admitted job's `--timeout` budget.

Runner processes already started before an update retain their loaded version.
Do not interrupt unrelated jobs to upgrade them; restart only a task's own
waiting invocation if needed. Both versions continue using the unchanged host
lock and session recovery path.

Cold simulator boot readiness has a separate `--boot-timeout` budget (600
seconds by default). Ordinary simctl commands retain their 120-second limit;
`--timeout` still bounds the admitted workload. A boot timeout or cancellation
prevents the workload from starting and tears down only the registered owned
devices before releasing the same host slot.

## Heavy host work without a host simulator (AXON-2790)

`axon-simulator-run host --timeout 1800 -- <command>` uses the same FIFO,
physical-host slot and crash recovery as simulator sessions, without creating
or booting a host simulator. Use it for a disposable CI VM or a main build that
must share capacity with Apple tests. Admission refuses active unowned host
simulators. The command receives an empty `AXON_SIMULATOR_DEVICES` and no
`AXON_SIMULATOR_UDID`. Simulator selection/mutation options are rejected.

External resources can survive their launcher's process tree. A VM owner must
supply `--host-cleanup '["/absolute/protected-main/cleanup", "owned-vm-id"]'`.
The callback must verify ownership, stop and remove its exact resource, verify
teardown, and return success only when reuse is safe. It must be idempotent:
normal completion, cancellation and crash recovery can all invoke it. Never
include secrets in its persisted arguments. Pin the callback to a trusted
protected-main installation; this runner does not establish VM ownership itself.

The runner stops the workload before calling cleanup and retains the slot
through its 60-second cleanup deadline. A failing or interrupted callback leaves
the recovery record; subsequent admission must successfully repeat cleanup.
There is no background polling service. A native process-only build may omit
the callback. Guest simulator operations still use the shared runner inside
the guest.

Install this version from clean fetched main only while all host runners and
waiters are idle. Older processes do not understand external-resource cleanup;
do not mix them with host-mode sessions. The lock and recovery directory stay
unchanged.

## Disposable Apple CI guest executor (AXON-2790)

The same main-only installer provides `axon-ci-vm`. It is a physical resource
executor, not a scheduler, runner registration service or paid-budget authority.
No daemon, image download or VM starts on installation.

The current qualified configuration accepts only the pinned Tart 2.41.0 arm64
executable and Softnet 0.24.1 helper hashes in source, with the pinned Xcode 27
image already cached. It requires AC power, 24 GiB host RAM, 100 GiB free disk,
and exactly one stopped qualified base in the configured Tart cache. This stock
configuration is for the mini; do not install its image on the MacBook.

An operator-owned JSON config contains only absolute `tart` and `tartHome` paths.
Invoke `axon-ci-vm run --config /absolute/config.json --job <canonical-UUID>`
with JSON `{"argv":["/absolute/guest/command"],"stdin":"..."}` on stdin.
Single-job JIT credentials may use that stdin; personal tokens must never enter
the guest. Requests are bounded to 256 KiB and aren't persisted on the host.
The worker starts only under the shared host slot. It uses 8 CPUs/14 GiB RAM,
no host shares/UI/clipboard/accessory passthrough, public DNS, and Softnet
host/private/link-local/CGNAT denial. IPv6 frames are discarded by this pinned
Softnet implementation. Guest simulator journeys still need the guest runner.

An exclusive durable resource record precedes cloning. Frozen tool/cache paths
and the exact random guest name survive cancellation or supervisor loss. Only
the recorded shared-runner cleanup callback may stop/delete that guest; failures
preserve recovery state and block further admission. Other guests are preserved
and prevent new work. Each job deletes its clone; only the base is retained.
`~/Library/Caches/axon-ci-vms/paused` stops new admission (including queued work)
without cancelling accepted work. Remove that file to resume. There is no idle
VM, guest cache, persistent runner or background polling.

The host-slot wait is five minutes; workload timeout defaults to one hour and is
bounded to two hours. A trusted dispatcher must interpret capacity failure,
recheck freshness and pause/power state, and atomically reserve any paid cloud
fallback before dispatch. This tool alone never starts cloud jobs or creates
GitHub credentials. Its cleanup deadline comes from the shared runner.

## Retired build outputs and legacy fixtures (AXON-2779)

Install from a clean freshly fetched main:

```sh
python3 scripts/install_simulator_runner.py --install-cleanup-schedule
```

`axon-dev-cleanup` previews by default; `--apply` removes only allowlisted,
ignored generated directories in clean linked worktrees whose exact HEAD has a
merged PR and whose branch has no open PR. Main/detached worktrees, active
process directories or open files, tracked/unignored paths, symlinks and outputs changed within
24 hours are preserved. Source, `.axon-dev/qualification-results`, production
controller artifacts, Go build/module caches, generic simulator devices and
unknown fixtures are outside this policy. Shared program issues may stay open
after a specific task branch merges; branch retirement uses exact PR evidence.

For legacy fixtures, `Axon CI Qualification <hash>` must map to that retired
worktree (SHA-256 of its resolved path, first 12 digits); `AXON-<issue>` fixtures
require the owning Hub issue closed/completed. Last use must be known and older
than 24 hours. Deletion rechecks retirement and uses
`axon-simulator-run delete-retired --device <UDID>` under the unchanged host-wide
slot; active devices or queued simulator jobs defer maintenance. This operator
command requires positively verified retirement; it does not infer it itself.

The opt-in LaunchAgent runs with `--projects-only` at 03:30 local time, at background CPU/I/O priority,
with no RunAtLoad or persistent worker. Unattended worktree cleanup is limited
to `~/projects`; Documents and other locations require a foreground invocation
because macOS can deny background access. No privacy permissions are changed.
Simulator retirement still requires the same explicit ownership evidence.
It removes at most 30 items per pass,
never runs concurrent cleanup passes, and replaces one bounded last-run report
at `~/Library/Caches/axon-dev-cleanup/last-run.json`. No GitHub credentials are
installed; the existing `gh` login must be available or cleanup fails closed.
Disable with `launchctl bootout gui/$(id -u)/com.micahlee.axon-dev-cleanup`.
Preview again with `axon-dev-cleanup`; rerun with `--apply` as needed. API
failures preserve candidates; the tool does not retry tightly.

The manual `Disposable CI guest smoke` workflow accepts a unique runner label
for first JIT-runner acceptance. Only a write-authorized dispatch starts it; it
allocates no GitHub-hosted runner and has no schedule or pull-request trigger.
It checks guest CPU/memory and runs the lightweight executor-policy tests.
It is a bootstrap probe, not repository qualification or a production router.

The pinned guest selects `/Applications/Xcode_27.app/Contents/Developer`.
Before untrusted work starts, the executor verifies that exact selection and
provides `/Applications/Xcode.app` as an alias to the same installation. A
conflicting existing path or another selected SDK fails admission; nothing is
replaced or reselected. A Git/Xcode lookup through the canonical path must pass.
This is guest-only setup; physical host Xcode and sandbox permissions stay intact.
## Managed CI screenshot evidence

Completed managed Mac guests export PNG attachments from
`$RUNNER_TEMP/axon-qualification-results/*/tests.xcresult` before teardown.
Images and a test-name manifest remain private on the physical host at
`~/Library/Caches/axon-ci-evidence/<guest-UUID>/`. The exporter copies no full
xcresults, logs, environment files or credential files, and makes no GitHub
storage upload. Screenshot fixtures must be synthetic; their contents still
require private review.

Use the UUID from the successful GitHub job's `axon-ci-managed-<UUID>` runner
name. Verify that job's exact source head and result before inspecting images.
Wait for normal guest cleanup, then use this read-only command on its host:

```sh
axon-ci-vm evidence --job <guest-UUID>
```

It returns the manifest path and content-hashed PNG filenames. Copy only those
files over the existing verified SSH connection and inspect them locally.
The guest UUID binds the receipt to the GitHub runner; the test identifier in
the manifest identifies the screenshot. Image existence does not establish
product acceptance: inspect the expected synthetic surface itself.

After inspection and the owning PR's merge/closure, release only that job:

```sh
axon-ci-vm release-evidence --job <guest-UUID>
```

Release refuses an active owned guest. It also supports safely retiring an
interrupted receipt after guest cleanup. Evidence is not automatically evicted
while its task may still need review. The owner must release it at completion.
Admission preserves existing proof and stops before another Mac job if the
store cannot reserve its maximum export: 32 MiB and 64 PNGs per job, 256 MiB
content and 64 retained jobs per host, plus bounded manifest/filesystem overhead.
Mac admission reserves 161 GiB free to preserve the 20 GiB host margin during
clone writes and evidence export. No resident exporter or idle guest is added.
Linux jobs and the paid-overflow storage policy are unchanged. Hosted-cloud
evidence needs its separately budgeted retention path; this exporter is for
the managed local guest route.
