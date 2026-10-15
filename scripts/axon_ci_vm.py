#!/usr/bin/env python3
"""Disposable CI guest executor; no scheduler or paid-job admission."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import time
import uuid

ROOT = Path.home() / 'Library/Caches/axon-ci-vms'
HELPER = Path('/Library/PrivilegedHelperTools/com.micahlee.axon-ci/softnet')
HELPER_SHA = 'e5e35d61a6dd7e35a3134732e766c897b7cb6f097080ff00e1e75adeab0471c7'
TART_SHA = '6c2032761b3c4363767ac93915728107a756d672da83973b2a0343dc033eda52'
IMAGE = 'ghcr.io/cirruslabs/macos-golden-gate-xcode@sha256:324ea5656dee8ab9b0a0df70fda2cfed8912051ad0eca3b1b883bf6ddac88fab'
# A COW clone may overwrite the entire 140-GB disk, not just guest free space.
# Keep at least 20 GiB for the host even at that maximum write footprint.
MIN_STOCK_FREE_GIB = 160
LINUX_IMAGE = 'ghcr.io/cirruslabs/ubuntu@sha256:94dbb9c4b94db827a208fea301cf33eacdcbfb801155b5702b9e2faa52473a2e'
# The pinned Linux image has a 20-GB virtual disk. Account for a complete
# clone rewrite and at least 20 GiB left on the physical host.
MIN_LINUX_FREE_GIB = 45
BLOCK = '@host,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,100.64.0.0/10,169.254.0.0/16'

class Failure(RuntimeError):
    pass

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def guest_profile(config):
    profile = config.get('profile', 'macos')
    if not isinstance(profile, str) or profile not in {'macos', 'linux'}:
        raise Failure('Only pinned macos or linux guest profiles are allowed')
    return profile

def guest_image(config):
    return LINUX_IMAGE if guest_profile(config) == 'linux' else IMAGE

def frozen_config(path):
    value = json.loads(Path(path).read_text())
    if (not isinstance(value, dict) or set(value) not in ({'tart', 'tartHome'}, {'tart', 'tartHome', 'profile'})
            or any(not isinstance(value[k], str) or not Path(value[k]).is_absolute() for k in ('tart', 'tartHome'))):
        raise Failure('Expected absolute tart and tartHome paths with an optional pinned profile')
    guest_profile(value)
    return value

def verify_tart(config):
    if digest(Path(config['tart'])) != TART_SHA:
        raise Failure('Tart executable differs from the qualified 2.41.0 binary')

def verify_helper():
    info = HELPER.stat()
    if info.st_uid != 0 or info.st_gid != 80 or stat.S_IMODE(info.st_mode) != 0o4750 or digest(HELPER) != HELPER_SHA:
        raise Failure('Pinned root/admin Softnet helper unavailable')

def environment(config):
    # Do not forward operator credentials, sockets, proxies or custom search paths.
    return {'HOME': str(Path.home()), 'PATH': str(HELPER.parent) + ':/usr/bin:/bin:/usr/sbin:/sbin',
            'TART_HOME': config['tartHome'], 'TART_NO_AUTO_PRUNE': '1', 'LANG': 'en_US.UTF-8'}

def call(config, *args, timeout=30, check=True, input=None):
    result = subprocess.run([config['tart'], *args], env=environment(config), input=input,
                            capture_output=True, text=True, timeout=timeout)
    if check and result.returncode:
        raise Failure('Tart operation failed: ' + args[0])
    return result

def inventory(config):
    return json.loads(call(config, 'list', '--format', 'json').stdout)

def vm_name(job):
    if str(uuid.UUID(job)) != job:
        raise Failure('Expected canonical UUID job attempt')
    return 'axon-ci-' + job

def record_path(job):
    vm_name(job)
    return ROOT / (job + '.json')

def write_record(job, config):
    ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = record_path(job)
    # Exclusive durable record before clone creation; never replace ownership.
    with path.open('x') as stream:
        os.chmod(path, 0o600)
        json.dump({'job': job, 'config': config}, stream)
        stream.flush()
        os.fsync(stream.fileno())
    fd = os.open(ROOT, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)

def cleanup(job):
    path = record_path(job)
    if not path.exists():
        return  # No recorded clone creation; idempotent before first effect.
    value = json.loads(path.read_text())
    if not isinstance(value, dict) or set(value) != {'job', 'config'} or value['job'] != job:
        raise Failure('VM ownership record invalid; admission remains blocked')
    config = value['config']
    verify_tart(config)
    name = vm_name(job)
    rows = [row for row in inventory(config) if row['Name'] == name and row['Source'] == 'local']
    if rows:
        if rows[0]['Running']:
            call(config, 'stop', name, '--timeout', '15', timeout=20)
        remaining = [row for row in inventory(config) if row['Name'] == name]
        if any(row['Running'] for row in remaining):
            raise Failure('Guest still running; admission remains blocked')
        call(config, 'delete', name, timeout=15)
    if any(row['Name'] == name for row in inventory(config)):
        raise Failure('Guest deletion incomplete; admission remains blocked')
    path.unlink()

def eligible(config):
    if sys.platform != 'darwin':
        raise Failure('Guest execution requires a macOS physical host')
    if (ROOT / 'paused').exists():
        raise Failure('Local CI admission paused')
    power = subprocess.check_output(['/usr/bin/pmset', '-g', 'batt'], text=True)
    if "'AC Power'" not in power:
        raise Failure('Local CI requires AC power')
    ram = int(subprocess.check_output(['/usr/sbin/sysctl', '-n', 'hw.memsize'], text=True))
    minimum_free = MIN_LINUX_FREE_GIB if guest_profile(config) == 'linux' else MIN_STOCK_FREE_GIB
    if ram < 24 * 1024**3 or shutil.disk_usage(config['tartHome']).free < minimum_free * 1024**3:
        raise Failure('Pinned guest requires 24 GiB RAM and ' + str(minimum_free) + ' GiB free disk')
    verify_tart(config)
    verify_helper()
    rows = inventory(config)
    if len(rows) != 1 or rows[0]['Name'] != guest_image(config) or rows[0]['Source'] != 'OCI' or rows[0]['Running']:
        raise Failure('Expected only the qualified stopped base image; preserve other VMs')

def payload(stream):
    wire = stream.read(256 * 1024 + 1)
    if len(wire) > 256 * 1024:
        raise Failure('Guest request too large')
    value = json.loads(wire)
    if (not isinstance(value, dict) or set(value) != {'argv', 'stdin'} or not isinstance(value['argv'], list)
            or not 1 <= len(value['argv']) <= 64
            or not all(isinstance(v, str) and v and '\0' not in v for v in value['argv'])
            or not value['argv'][0].startswith('/') or not isinstance(value['stdin'], str)):
        raise Failure('Expected bounded absolute guest argv and stdin')
    return value

def prepare_toolchain(config, name):
    if guest_profile(config) == 'linux':
        if call(config, 'exec', name, '/usr/bin/uname', '-s').stdout.strip() != 'Linux':
            raise Failure('Pinned Linux guest required')
        return
    selected = call(config, 'exec', name, '/usr/bin/xcode-select', '-p').stdout.strip()
    if selected != '/Applications/Xcode_27.app/Contents/Developer':
        raise Failure('Qualified Xcode 27 selection required')
    # The pinned image has a versioned application name. Existing isolated
    # tool environments use Apple's canonical Xcode.app path. Never replace
    # another installation or silently select a different SDK.
    script = """set -eu
if test -e /Applications/Xcode.app || test -L /Applications/Xcode.app; then
    test "$(readlink /Applications/Xcode.app)" = /Applications/Xcode_27.app
else
    /usr/bin/sudo /bin/ln -s /Applications/Xcode_27.app /Applications/Xcode.app
fi
/usr/bin/env DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer /usr/bin/git --version >/dev/null
"""
    call(config, 'exec', name, '/bin/sh', '-c', script)

def prepare_network(config, name):
    if guest_profile(config) == 'linux':
        routes = json.loads(call(config, 'exec', name, '/usr/sbin/ip', '-j', 'route', 'show', 'default').stdout)
        if (not isinstance(routes, list) or len(routes) != 1 or not isinstance(routes[0], dict)
                or not isinstance(routes[0].get('dev'), str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,32}', routes[0]['dev'])):
            raise Failure('Expected one explicit Linux default-route interface')
        interface = routes[0]['dev']
        call(config, 'exec', name, '/usr/bin/sudo', '/usr/bin/resolvectl', 'dns', interface, '1.1.1.1', '8.8.8.8')
        call(config, 'exec', name, '/usr/bin/sudo', '/usr/bin/resolvectl', 'domain', interface, '~.')
    else:
        call(config, 'exec', name, '/usr/bin/sudo', '/usr/sbin/networksetup',
             '-setdnsservers', 'Ethernet', '1.1.1.1', '8.8.8.8')

def worker(config, job):
    # The unchanged shared runner owns admission and its cleanup callback.
    session = json.loads((Path.home() / 'Library/Caches/axon-simulator-runner/session.json').read_text())
    if (session.get('mode') != 'host' or session.get('worker', {}).get('pid') != os.getpid()
            or str(session.get('supervisorPID')) != os.environ.get('AXON_SIMULATOR_SESSION_PID')):
        raise Failure('VM worker requires shared host admission')
    request = payload(sys.stdin)
    eligible(config)
    write_record(job, config)
    name = vm_name(job)
    call(config, 'clone', guest_image(config), name, timeout=60)
    linux = guest_profile(config) == 'linux'
    call(config, 'set', name, '--cpu', '4' if linux else '8', '--memory', '6144' if linux else '14336')
    # No host shares, UI, clipboard, accessory passthrough or private networking.
    subprocess.Popen([config['tart'], 'run', name, '--no-graphics', '--no-audio',
                      '--no-clipboard', '--no-usb-accessories', '--net-softnet',
                      '--net-softnet-block', BLOCK], env=environment(config),
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.monotonic() + 90
    while True:
        try:
            if call(config, 'exec', name, '/usr/bin/true', timeout=5, check=False).returncode == 0:
                break
        except subprocess.TimeoutExpired:
            pass
        if time.monotonic() >= deadline:
            raise Failure('Guest startup deadline exceeded')
        time.sleep(1)
    prepare_network(config, name)
    prepare_toolchain(config, name)
    process = subprocess.run([config['tart'], 'exec', '-i', name, *request['argv']],
                             env=environment(config), input=request['stdin'], text=True)
    return process.returncode

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['run', '_worker', 'cleanup'])
    parser.add_argument('--config')
    parser.add_argument('--job', required=True)
    parser.add_argument('--timeout', type=int, default=3600)
    args = parser.parse_args()
    vm_name(args.job)
    if args.mode == 'cleanup':
        session = json.loads((Path.home() / 'Library/Caches/axon-simulator-runner/session.json').read_text())
        expected = [sys.executable, '-B', str(Path(__file__).resolve()), 'cleanup', '--job', args.job]
        if (session.get('mode') != 'host' or session.get('worker', {}).get('pid') != os.getpid()
                or session.get('hostCleanup') != expected):
            raise Failure('VM cleanup requires its recorded shared host admission')
        cleanup(args.job)
        return 0
    if not args.config or not 1 <= args.timeout <= 7200:
        raise Failure('Config and a bounded timeout required')
    config_path = str(Path(args.config).resolve(strict=True))
    config = frozen_config(config_path)
    if args.mode == '_worker':
        return worker(config, args.job)
    if (ROOT / 'paused').exists():
        raise Failure('Local CI admission paused')
    script = str(Path(__file__).resolve())
    callback = [sys.executable, '-B', script, 'cleanup', '--job', args.job]
    command = [str(Path.home()/'.local/bin/axon-simulator-run'), 'host', '--wait', '300',
               '--timeout', str(args.timeout), '--host-cleanup', json.dumps(callback), '--',
               sys.executable, '-B', script, '_worker', '--config', config_path, '--job', args.job]
    # stdin goes directly to the admitted worker; no guest credentials on disk.
    return subprocess.run(command).returncode

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (Failure, OSError, ValueError, subprocess.SubprocessError) as error:
        print('CI VM executor: ' + str(error), file=sys.stderr)
        sys.exit(1)
