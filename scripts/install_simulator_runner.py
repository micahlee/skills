#!/usr/bin/env python3
"""Install the shared runner only from clean, freshly fetched protected main."""
import os
from pathlib import Path
import subprocess
import tempfile
root = Path(__file__).resolve().parent.parent
subprocess.run(["git", "-C", str(root), "fetch", "origin", "main"], check=True)
def git(*args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()
if git("rev-parse", "HEAD") != git("rev-parse", "origin/main") or git("status", "--porcelain", "--untracked-files=all"):
    raise SystemExit("Install requires a clean checkout at freshly fetched origin/main")
source = root / "scripts/axon_simulator_runner.py"
subprocess.run(["python3", "-B", str(source), "--help"], check=True)
target = Path.home() / ".local/bin/axon-simulator-run"
target.parent.mkdir(parents=True, exist_ok=True)
with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
    temporary.write(source.read_bytes())
    stage = Path(temporary.name)
try:
    stage.chmod(0o755)
    os.replace(stage, target)
finally:
    stage.unlink(missing_ok=True)
print("Installed", target, "from", git("rev-parse", "HEAD"))
