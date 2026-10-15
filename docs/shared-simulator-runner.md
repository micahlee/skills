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
