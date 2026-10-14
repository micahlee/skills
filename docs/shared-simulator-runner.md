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
  explicit and applies only to that selected development fixture.
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

The lock is cooperative: manually booted simulators or tools that ignore these instructions are detected as conflicts. It is not a macOS access-control boundary. Do not run a second simulator while a session is active. The caller-facing process has a separate supervisor, which cancels the job on parent death. After supervisor loss or host restart, the next admission recovers its recorded worker and devices before proceeding. Cleanup failure leaves recovery state and blocks subsequent admission. Device definitions are retained; shutdown does not delete them.
