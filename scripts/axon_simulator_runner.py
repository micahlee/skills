#!/usr/bin/env python3
"""One bounded simulator session per host, including teardown and crash recovery."""
from __future__ import annotations
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import math
from contextlib import contextmanager

ROOT = Path.home() / "Library/Caches/axon-simulator-runner"

class RunnerError(RuntimeError):
    pass

class Cancelled(BaseException):
    def __init__(self, signum):
        self.signum = signum


def identity_environment():
    # Make exports TZ=UTC; interactive shells may use the local timezone.
    # Human-readable ps/sysctl identities must compare identically in both.
    return dict(os.environ, TZ="UTC", LC_ALL="C")


def boot_identity():
    linux = Path("/proc/sys/kernel/random/boot_id")
    if linux.exists():
        return linux.read_text().strip()
    return subprocess.check_output(["sysctl", "-n", "kern.boottime"], text=True, env=identity_environment()).strip()


def identity(pid):
    result = subprocess.run(["ps", "-p", str(pid), "-o", "lstart="], capture_output=True, text=True, env=identity_environment())
    return result.stdout.strip() or None


def descendants(pid):
    result = subprocess.run(["ps", "-axo", "pid=,ppid="], capture_output=True, text=True)
    children = {}
    for row in result.stdout.splitlines():
        values = row.split()
        if len(values) == 2:
            children.setdefault(int(values[1]), []).append(int(values[0]))
    found = []
    def visit(parent):
        for child in children.get(parent, []):
            visit(child)
            found.append(child)
    visit(pid)
    return found


def stop_worker(worker):
    if not worker or worker.get("bootIdentity") != boot_identity():
        return
    fingerprints = {int(pid): value for pid, value in worker.get("descendants", {}).items()}
    if identity(worker["pid"]) == worker["identity"]:
        fingerprints.update({pid: identity(pid) for pid in descendants(worker["pid"])})
        fingerprints[worker["pid"]] = worker["identity"]
    # Kill the workload's whole original group, even if its leader has exited.
    current = identity(worker["pid"])
    groups = subprocess.run(["ps", "-axo", "pid=,pgid="], capture_output=True, text=True).stdout
    group_members = [int(row.split()[0]) for row in groups.splitlines()
                     if len(row.split()) == 2 and int(row.split()[1]) == worker["pid"]]
    if current is None or current == worker["identity"]:
        fingerprints.update({pid: identity(pid) for pid in group_members})
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for pid, fingerprint in fingerprints.items():
            if fingerprint and identity(pid) == fingerprint:
                try:
                    os.kill(pid, sig)
                except ProcessLookupError:
                    pass
        if sig == signal.SIGTERM and fingerprints:
            time.sleep(1)
    deadline = time.monotonic() + 10
    while True:
        alive = []
        for pid, fingerprint in fingerprints.items():
            if fingerprint and identity(pid) == fingerprint:
                status = subprocess.run(["ps", "-p", str(pid), "-o", "stat="], capture_output=True, text=True).stdout.strip()
                if status and not status.startswith("Z"):
                    alive.append(pid)
        if not alive:
            return
        if time.monotonic() >= deadline:
            raise RunnerError("Workload did not stop; refusing to release its simulator: " + str(alive))
        time.sleep(.1)


class Runner:
    def __init__(self, root=ROOT, simctl=None):
        self.root = Path(root)
        self.simctl = simctl or ["xcrun", "simctl"]
        self.state = {"devices": [], "worker": None}
        self.lock = None
        self.cleaning = False
        self.parent = os.getppid()
        self.parent_identity = identity(self.parent)

    def tool(self, *args):
        process = subprocess.Popen(self.simctl + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, start_new_session=True)
        deadline = time.monotonic() + 120
        try:
            while True:
                try:
                    stdout, stderr = process.communicate(timeout=.5)
                    break
                except subprocess.TimeoutExpired:
                    self.check_parent()
                    if time.monotonic() > deadline:
                        raise RunnerError("simctl " + args[0] + " command timed out")
        except BaseException:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            raise
        result = subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)
        if result.returncode:
            raise RunnerError("simctl " + args[0] + ": " + result.stderr.strip())
        return result.stdout.strip()

    def check_parent(self):
        if self.cleaning:
            return
        if os.getppid() != self.parent or identity(self.parent) != self.parent_identity:
            raise RunnerError("Calling process exited; cancelling simulator job")

    def inventory(self):
        payload = json.loads(self.tool("list", "devices", "--json"))
        return {d["udid"]: dict(d, runtime=runtime) for runtime, devices in payload["devices"].items() for d in devices}

    def save(self):
        temporary = self.root / "session.tmp"
        temporary.write_text(json.dumps(self.state) + "\n")
        temporary.replace(self.root / "session.json")

    def cleanup(self):
        # Stop the workload before its device; keep the lock through verified teardown.
        self.parent = os.getppid()
        self.parent_identity = identity(self.parent)
        stop_worker(self.state.get("worker"))
        inventory = self.inventory()
        if "initialDeviceIDs" in self.state:
            self.state["devices"] = list(set(self.state["devices"]) | {
                d for d, value in inventory.items() if value["state"] != "Shutdown"
                and d not in self.state["initialDeviceIDs"]})
            self.save()
        errors = []
        for device in self.state["devices"]:
            if device in inventory and inventory[device]["state"] != "Shutdown":
                try:
                    self.tool("shutdown", device)
                except Exception as error:
                    errors.append(str(error))
        inventory = self.inventory()
        remaining = [d for d in self.state["devices"] if d in inventory and inventory[d]["state"] != "Shutdown"]
        if errors or remaining:
            raise RunnerError("Cleanup incomplete; next admission must recover: " + "; ".join(errors + remaining))
        (self.root / "session.json").unlink(missing_ok=True)

    @contextmanager
    def queue_guard(self, deadline, watch_parent=True):
        # Separate short transactions from the host lock held by a running job.
        # Neither lock inode is replaced, including during crash recovery.
        with (self.root / "queue.lock").open("a+") as lock:
            while True:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise RunnerError("Timed out waiting for the host simulator slot")
                    if watch_parent:
                        self.check_parent()
                    time.sleep(.02)
            yield

    def queue_entries(self):
        path = self.root / "queue.json"
        entries = json.loads(path.read_text()) if path.exists() else []
        if not isinstance(entries, list) or any(
                not isinstance(entry, dict) or type(entry.get("pid")) is not int or entry["pid"] <= 0 or
                not isinstance(entry.get("identity"), str) or not entry["identity"] or
                not isinstance(entry.get("bootIdentity"), str) or not entry["bootIdentity"] for entry in entries):
            raise RunnerError("Invalid simulator waiting queue; refusing admission")
        return entries

    def save_queue(self, entries):
        temporary = self.root / "queue.tmp"
        temporary.write_text(json.dumps(entries) + "\n")
        temporary.replace(self.root / "queue.json")

    def acquire(self, wait):
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Never unlink/replace the lock inode; every worktree uses the same path.
        self.lock = (self.root / "host.lock").open("a+")
        deadline = time.monotonic() + wait
        ticket = {"pid": os.getpid(), "identity": identity(os.getpid()), "bootIdentity": boot_identity()}
        if not ticket["identity"]:
            raise RunnerError("Could not verify simulator waiter process identity")
        queued = False
        announced = False
        try:
            with self.queue_guard(deadline):
                entries = self.queue_entries()
                entries.append(ticket)
                self.save_queue(entries)
                queued = True
            while True:
                acquired = False
                with self.queue_guard(deadline):
                    entries = self.queue_entries()
                    # SIGKILL/host restart may leave a waiter behind. PID alone
                    # is insufficient because the OS can reuse it.
                    while entries and entries[0] != ticket and (
                            entries[0]["bootIdentity"] != ticket["bootIdentity"] or
                            identity(entries[0]["pid"]) != entries[0]["identity"]):
                        entries.pop(0)
                    if entries and entries[0] == ticket:
                        try:
                            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        except BlockingIOError:
                            pass
                        else:
                            entries.pop(0)
                            acquired = True
                    self.save_queue(entries)
                if acquired:
                    queued = False
                    break
                if not announced:
                    print("Waiting for the current simulator session to finish...", file=sys.stderr, flush=True)
                    announced = True
                if time.monotonic() >= deadline:
                    raise RunnerError("Timed out waiting for the host simulator slot")
                self.check_parent()
                time.sleep(.2)
        finally:
            if queued:
                # Cancellation/timeout must not strand a live ticket at the
                # front. If cleanup itself fails, the next admission prunes
                # this process by its exact identity after it exits.
                with self.queue_guard(time.monotonic() + 5, watch_parent=False):
                    self.save_queue([entry for entry in self.queue_entries() if entry != ticket])
        state_file = self.root / "session.json"
        if state_file.exists():
            self.state = json.loads(state_file.read_text())
            self.cleanup()
            self.state = {"devices": [], "worker": None}

    def select(self, devices, name, runtime, device_type):
        inventory = self.inventory()
        if name:
            matches = [d for d in inventory.values() if d["name"] == name and d["runtime"] == runtime and d.get("isAvailable")]
            if len(matches) > 1:
                raise RunnerError("Ambiguous managed simulator name")
            devices = [matches[0]["udid"]] if matches else [self.tool("create", name, device_type, runtime)]
            inventory = self.inventory()
        if not devices or len(set(devices)) != len(devices):
            raise RunnerError("Select exact, distinct simulator IDs")
        for device in devices:
            if device not in inventory or not inventory[device].get("isAvailable"):
                raise RunnerError("Simulator unavailable: " + device)
        conflicts = [d["name"] + " (" + d["udid"] + ")" for d in inventory.values()
                     if d["state"] != "Shutdown" and d["udid"] not in devices]
        if conflicts:
            raise RunnerError("Other simulators are active; shut them down through their owner first: " + ", ".join(conflicts))
        self.state["devices"] = devices
        self.state["initialDeviceIDs"] = list(inventory)
        self.state["supervisorPID"] = os.getpid()
        self.save()  # Register before boot, including partial boot failure.
        return devices

    def execute(self, command, devices, *, timeout=1800, erase=False, setenv=()):
        process = None
        try:
            for device in devices:
                if erase:
                    if self.inventory()[device]["state"] != "Shutdown":
                        self.tool("shutdown", device)
                    self.tool("erase", device)
                if self.inventory()[device]["state"] != "Booted":
                    self.tool("boot", device)
                self.tool("bootstatus", device, "-b")
                for value in setenv:
                    key, content = value.split("=", 1)
                    self.tool("spawn", device, "launchctl", "setenv", key, content)
            environment = os.environ.copy()
            environment["AXON_SIMULATOR_UDID"] = devices[0]
            environment["AXON_SIMULATOR_DEVICES"] = ",".join(devices)
            # Inform nested scripts; only the supervisor can admit new jobs.
            environment["AXON_SIMULATOR_SESSION_PID"] = str(os.getpid())
            # The worker cannot execute before its recovery identity is durable.
            # If the supervisor dies in this window, pipe EOF exits the worker.
            read_fd, write_fd = os.pipe()
            gate = "import os,sys; fd=int(sys.argv[1]); ready=os.read(fd,1); os.close(fd); " + \
                   "sys.exit(125) if ready!=b'1' else os.execvpe(sys.argv[2],sys.argv[2:],os.environ)"
            try:
                process = subprocess.Popen([sys.executable, "-c", gate, str(read_fd)] + command,
                                           env=environment, start_new_session=True, pass_fds=(read_fd,))
                self.state["worker"] = {"pid": process.pid, "identity": identity(process.pid), "bootIdentity": boot_identity()}
                self.save()
                os.write(write_fd, b"1")
            finally:
                os.close(read_fd)
                os.close(write_fd)
            deadline = time.monotonic() + timeout
            while process.poll() is None:
                if time.monotonic() >= deadline:
                    raise RunnerError("Simulator job exceeded its time limit")
                self.check_parent()
                self.state["worker"].setdefault("descendants", {}).update({pid: identity(pid) for pid in descendants(process.pid)})
                self.save()
                inventory = self.inventory()
                extras = [d for d, value in inventory.items() if value["state"] != "Shutdown" and d not in devices]
                if extras:
                    self.state["devices"] += [d for d in extras if d not in self.state["initialDeviceIDs"]]
                    self.save()
                    raise RunnerError("Job booted additional simulators; parallel simulator execution is disabled")
                time.sleep(.5)
            return process.returncode if process.returncode >= 0 else 128 - process.returncode
        finally:
            # Repeated cancellation must not interrupt cleanup.
            previous = {sig: signal.signal(sig, signal.SIG_IGN) for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
            try:
                self.cleaning = True
                if process and not self.state.get("worker"):
                    self.state["worker"] = {"pid": process.pid, "identity": identity(process.pid), "bootIdentity": boot_identity()}
                stop_worker(self.state.get("worker"))
                self.state["worker"] = None
                self.save()
                # Catch clones booted just before the child exits.
                inventory = self.inventory()
                self.state["devices"] = list(set(self.state["devices"]) | {d for d, v in inventory.items() if v["state"] != "Shutdown" and d not in self.state["initialDeviceIDs"]})
                self.save()
                self.cleanup()
                if process:
                    process.wait(timeout=10)
            finally:
                for sig, handler in previous.items():
                    signal.signal(sig, handler)

    def close(self):
        if self.lock:
            self.lock.close()


def xcode_job(arguments, inventory):
    destinations = []
    clean = []
    i = 0
    options = {"-parallel-testing-enabled", "-parallel-testing-worker-count", "-maximum-parallel-testing-workers", "-maximum-concurrent-test-simulator-destinations"}
    while i < len(arguments):
        value = arguments[i]
        if value == "-destination":
            destinations.append(arguments[i + 1]); i += 2
        elif value in options:
            i += 2
        else:
            clean.append(value); i += 1
    if len(destinations) != 1:
        raise RunnerError("Simulator tests require exactly one destination")
    parts = dict(item.split("=", 1) for item in destinations[0].split(",") if "=" in item)
    if parts.get("platform") != "iOS Simulator":
        raise RunnerError("Expected an iOS Simulator destination")
    matches = [d for d in inventory.values() if d.get("isAvailable") and
               ((parts.get("id") and d["udid"] == parts["id"]) or
                (not parts.get("id") and d["name"] == parts.get("name") and
                 (parts.get("OS") in (None, "latest") or d["runtime"].endswith("iOS-" + parts["OS"].replace(".", "-")))))]
    if len(matches) != 1:
        raise RunnerError("Destination must resolve to exactly one simulator; use its UDID")
    device = matches[0]["udid"]
    return ["xcodebuild"] + clean + ["-destination", "platform=iOS Simulator,id=" + device,
            "-parallel-testing-enabled", "NO", "-maximum-concurrent-test-simulator-destinations", "1"], [device]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["run", "xcodebuild", "status", "recover"])
    parser.add_argument("--device", action="append", default=[])
    parser.add_argument("--paired", action="store_true", help="Exclusive iPhone/Watch pair exception")
    parser.add_argument("--name")
    parser.add_argument("--runtime", default="com.apple.CoreSimulator.SimRuntime.iOS-26-5")
    parser.add_argument("--device-type", default="com.apple.CoreSimulator.SimDeviceType.iPhone-17")
    parser.add_argument("--erase", action="store_true", help="Erase only the selected disposable fixture")
    parser.add_argument("--setenv", action="append", default=[])
    parser.add_argument("--wait", type=float, default=3600)
    parser.add_argument("--timeout", type=float, default=1800)
    # Split explicitly so runner options remain available after the mode.
    argv = list(sys.argv[1:] if argv is None else argv)
    separator = argv.index("--") if "--" in argv else len(argv)
    args = parser.parse_args(argv[:separator])
    command = argv[separator + 1:]
    if not all(math.isfinite(v) and v > 0 for v in (args.wait, args.timeout)):
        parser.error("wait and timeout must be positive")
    runner = Runner()
    handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
    def cancelled(sig, frame):
        raise Cancelled(sig)
    for sig in handlers:
        signal.signal(sig, cancelled)
    try:
        if args.mode == "status":
            print((ROOT / "session.json").read_text() if (ROOT / "session.json").exists() else "No recorded simulator session")
            return 0
        runner.acquire(args.wait)
        if args.mode == "recover":
            return 0
        if args.mode == "xcodebuild":
            command, devices = xcode_job(command, runner.inventory())
        else:
            devices = args.device
        if args.name and devices:
            raise RunnerError("Choose a fixture name or exact devices, not both")
        if args.mode == "run" and not command:
            parser.error("run requires a command after --")
        if len(devices) > (2 if args.paired else 1) or (args.paired and len(devices) != 2):
            raise RunnerError("One device per session; use --paired for an exact phone/Watch pair")
        devices = runner.select(devices, args.name, args.runtime, args.device_type)
        if args.paired:
            pairs = json.loads(runner.tool("list", "pairs", "--json"))["pairs"].values()
            if not any(p.get("state", "").startswith("(active,") and {p["phone"]["udid"], p["watch"]["udid"]} == set(devices) for p in pairs):
                raise RunnerError("Selected devices are not a registered phone/Watch pair")
        return runner.execute(command, devices, timeout=args.timeout, erase=args.erase, setenv=args.setenv)
    except Cancelled as error:
        return 128 + error.signum
    except (RunnerError, subprocess.TimeoutExpired, OSError, ValueError) as error:
        print("Simulator runner: " + str(error), file=sys.stderr)
        return 1
    finally:
        runner.close()
        for sig, handler in handlers.items():
            signal.signal(sig, handler)

def entry():
    # A separate supervisor survives cancellation/SIGKILL of the caller-facing
    # process. Parent-death detection then stops the job and tears down devices.
    if len(sys.argv) > 1 and sys.argv[1] == "_supervise":
        return main(sys.argv[2:])
    process = subprocess.Popen([sys.executable, "-B", __file__, "_supervise"] + sys.argv[1:],
                               start_new_session=True)
    def forward(sig, frame):
        if process.poll() is None:
            try:
                os.kill(process.pid, sig)
            except ProcessLookupError:
                pass
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, forward)
    result = process.wait()
    return result if result >= 0 else 128 - result

if __name__ == "__main__":
    sys.exit(entry())
