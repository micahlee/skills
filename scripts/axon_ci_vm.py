#!/usr/bin/env python3
"""Disposable CI guest executor; no scheduler or paid-job admission."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import os
import re
import selectors
from pathlib import Path
import shutil
import stat
import struct
import subprocess
import sys
import time
import uuid
import zlib

ROOT = Path.home() / 'Library/Caches/axon-ci-vms'
HELPER = Path('/Library/PrivilegedHelperTools/com.micahlee.axon-ci/softnet')
HELPER_SHA = 'e5e35d61a6dd7e35a3134732e766c897b7cb6f097080ff00e1e75adeab0471c7'
TART_SHA = '6c2032761b3c4363767ac93915728107a756d672da83973b2a0343dc033eda52'
IMAGE = 'ghcr.io/cirruslabs/macos-golden-gate-xcode@sha256:324ea5656dee8ab9b0a0df70fda2cfed8912051ad0eca3b1b883bf6ddac88fab'
# A COW clone may overwrite the entire 140-GB disk, not just guest free space.
# Keep at least 20 GiB for the host even at that maximum write footprint.
MIN_STOCK_FREE_GIB = 161
EVIDENCE_ROOT = Path.home() / 'Library/Caches/axon-ci-evidence'
EVIDENCE_JOB_BYTES = 32 * 1024**2
EVIDENCE_TOTAL_BYTES = 256 * 1024**2
EVIDENCE_METADATA_BYTES = 256 * 1024
EVIDENCE_MAX_FILES = 64
EVIDENCE_WIRE_BYTES = 48 * 1024**2
EVIDENCE_EXPORT_SECONDS = 60
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

def private_directory(path, create=False):
    if create:
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise Failure('Evidence directory ownership or permissions invalid')

def evidence_usage():
    if not EVIDENCE_ROOT.exists() and not EVIDENCE_ROOT.is_symlink():
        return 0, 0
    private_directory(EVIDENCE_ROOT)
    total = count = 0
    for directory in EVIDENCE_ROOT.iterdir():
        vm_name(directory.name)
        private_directory(directory)
        count += 1
        if count > 64:
            raise Failure('Evidence job count exceeds limit; release reviewed evidence')
        files = list(directory.iterdir())
        if len(files) > EVIDENCE_MAX_FILES + 1:
            raise Failure('Evidence file count exceeds limit')
        for path in files:
            if path.name != 'manifest.json' and not re.fullmatch(r'[a-f0-9]{64}\.png', path.name):
                raise Failure('Unexpected evidence file; preserve it for inspection')
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600:
                raise Failure('Evidence file ownership or permissions invalid')
            total += info.st_size
            if total > EVIDENCE_TOTAL_BYTES:
                raise Failure('Evidence content exceeds host limit')
    return total, count

def evidence_capacity():
    used, count = evidence_usage()
    if count >= 64 or used + EVIDENCE_JOB_BYTES + EVIDENCE_METADATA_BYTES > EVIDENCE_TOTAL_BYTES:
        raise Failure('Evidence capacity full; release only reviewed retired job evidence')

def canonical_png(data):
    if not data.startswith(b'\x89PNG\r\n\x1a\n') or len(data) > EVIDENCE_JOB_BYTES:
        raise Failure('Invalid or oversized evidence PNG')
    position = 8
    output = bytearray(data[:8])
    width = height = None
    image = ended = False
    while position < len(data):
        if position + 12 > len(data):
            raise Failure('Truncated evidence PNG')
        length = struct.unpack('>I', data[position:position+4])[0]
        end = position + 12 + length
        if end > len(data):
            raise Failure('Truncated evidence PNG chunk')
        kind = data[position+4:position+8]
        payload = data[position+8:end-4]
        if zlib.crc32(kind + payload) & 0xffffffff != struct.unpack('>I', data[end-4:end])[0]:
            raise Failure('Evidence PNG checksum invalid')
        if width is None:
            if kind != b'IHDR' or length != 13:
                raise Failure('Evidence PNG header missing')
            width, height = struct.unpack('>II', payload[:8])
            if not width or not height or max(width, height) > 8192 or width * height > 32_000_000:
                raise Failure('Evidence PNG dimensions exceed limit')
        elif kind == b'IHDR':
            raise Failure('Duplicate evidence PNG header')
        # Drop textual/EXIF metadata. No guest paths, logs or arbitrary files
        # cross the boundary; filenames on the host are content hashes only.
        if kind in (b'IHDR', b'PLTE', b'tRNS', b'IDAT', b'IEND', b'sRGB', b'gAMA', b'cHRM'):
            output.extend(data[position:end])
        elif kind[0] & 32 == 0:
            raise Failure('Unsupported critical evidence PNG chunk')
        image = image or kind == b'IDAT'
        position = end
        if kind == b'IEND':
            ended = length == 0 and position == len(data)
            break
    if not image or not ended:
        raise Failure('Evidence PNG incomplete')
    return bytes(output), width, height

# This runs inside the disposable Mac only, after the Actions listener exits.
# Apple's exporter handles xcresult parsing there; no guest executable is run
# on the host. The host independently validates all returned bytes and sizes.
EVIDENCE_COLLECTOR = r'''import pathlib, subprocess, tempfile, json, base64, os, stat
root=pathlib.Path('/private/tmp/ci-actions/_work/_temp/axon-qualification-results')
files=[]; total=0
if root.exists():
 if root.is_symlink() or not root.is_dir():raise RuntimeError('results root invalid')
 runs=[]
 for p in root.iterdir():
  if p.is_symlink() or not p.is_dir():continue
  bundle=p/'tests.xcresult'
  if bundle.is_symlink():raise RuntimeError('result bundle symlink')
  if bundle.is_dir():runs.append(bundle)
  if len(runs)>4:raise RuntimeError('too many result bundles')
 for bundle in sorted(runs):
  with tempfile.TemporaryDirectory(prefix='axon-png-export-') as temp:
   subprocess.run(['/usr/bin/xcrun','xcresulttool','export','attachments','--path',str(bundle),'--output-path',temp,'--filter','*.png'],check=True,timeout=20,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   directory=pathlib.Path(temp); manifest=directory/'manifest.json'
   if manifest.is_symlink() or manifest.stat().st_size>262144:raise RuntimeError('manifest limit')
   rows=json.loads(manifest.read_text())
   if not isinstance(rows,list) or len(rows)>1000:raise RuntimeError('manifest shape')
   for row in rows:
    for a in row['attachments']:
     name=a['exportedFileName']
     if not isinstance(name,str) or pathlib.Path(name).name!=name or not name.lower().endswith('.png'):raise RuntimeError('attachment filename')
     path=directory/name; info=path.lstat()
     if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_size>33554432:raise RuntimeError('attachment type/size')
     total+=info.st_size
     if total>33554432 or len(files)>=64:raise RuntimeError('attachment budget')
     test=row['testIdentifier']; title=a['suggestedHumanReadableName']
     if not all(isinstance(s,str) and len(s)<=256 and all(c.isprintable() for c in s) for s in (test,title)):raise RuntimeError('attachment label')
     files.append({'testIdentifier':test,'name':title,'png':base64.b64encode(path.read_bytes()).decode('ascii')})
print(json.dumps({'version':1,'files':files},separators=(',',':')))
'''

def bounded_guest_evidence(config, job):
    command = [config['tart'], 'exec', vm_name(job), '/usr/bin/python3', '-c', EVIDENCE_COLLECTOR]
    process = subprocess.Popen(command, env=environment(config), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    deadline = time.monotonic() + EVIDENCE_EXPORT_SECONDS
    output = bytearray()
    try:
        while True:
            if time.monotonic() >= deadline:
                raise Failure('Evidence export deadline exceeded')
            if not selector.select(min(0.5, max(0, deadline-time.monotonic()))):
                continue
            block = os.read(process.stdout.fileno(), 65536)
            if not block:
                break
            output.extend(block)
            if len(output) > EVIDENCE_WIRE_BYTES:
                raise Failure('Evidence transport exceeds limit')
        if process.wait(timeout=max(0.1, deadline-time.monotonic())) != 0:
            raise Failure('Guest evidence export failed')
        return bytes(output)
    finally:
        selector.close()
        process.stdout.close()
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)

def retain_evidence(config, job):
    vm_name(job)
    if guest_profile(config) != 'macos':
        return None
    evidence_capacity()
    result = json.loads(bounded_guest_evidence(config, job))
    if not isinstance(result, dict) or set(result) != {'version', 'files'} or result['version'] != 1 or not isinstance(result['files'], list) or len(result['files']) > EVIDENCE_MAX_FILES:
        raise Failure('Evidence response invalid')
    if not result['files']:
        return None
    entries = []; images = {}; total = 0
    for item in result['files']:
        if not isinstance(item, dict) or set(item) != {'testIdentifier', 'name', 'png'} or not isinstance(item['png'], str) or len(item['png']) > 45 * 1024**2:
            raise Failure('Evidence entry invalid')
        if not all(isinstance(item[k], str) and len(item[k]) <= 256 and all(c.isprintable() for c in item[k]) for k in ('testIdentifier', 'name')):
            raise Failure('Evidence label invalid')
        data = base64.b64decode(item['png'], validate=True)
        total += len(data)
        if total > EVIDENCE_JOB_BYTES:
            raise Failure('Evidence job content exceeds limit')
        data, width, height = canonical_png(data)
        sha = hashlib.sha256(data).hexdigest(); name = sha + '.png'
        images[name] = data
        entries.append({'file': name, 'sha256': sha, 'bytes': len(data), 'width': width, 'height': height, 'testIdentifier': item['testIdentifier'], 'name': item['name']})
    manifest = {'version': 1, 'guest': job, 'createdAt': int(time.time()), 'files': entries}
    wire = json.dumps(manifest, ensure_ascii=False, indent=2).encode()
    if len(wire) > EVIDENCE_METADATA_BYTES:
        raise Failure('Evidence metadata exceeds limit')
    private_directory(EVIDENCE_ROOT, create=True)
    destination = EVIDENCE_ROOT / job
    destination.mkdir(mode=0o700)  # exclusive, never replace another receipt
    def write(name, data):
        fd = os.open(destination / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
    for name, data in images.items():
        write(name, data)
    write('manifest.json', wire)  # publication marker, after every image is durable
    for directory in (destination, EVIDENCE_ROOT):
        fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    return destination

def read_evidence(job):
    vm_name(job)
    evidence_usage()
    directory = EVIDENCE_ROOT / job
    private_directory(directory)
    path = directory / 'manifest.json'
    if path.stat().st_size > EVIDENCE_METADATA_BYTES:
        raise Failure('Evidence manifest exceeds limit')
    result = json.loads(path.read_text())
    if result.get('version') != 1 or result.get('guest') != job or not isinstance(result.get('files'), list) or len(result['files']) > EVIDENCE_MAX_FILES:
        raise Failure('Evidence manifest identity invalid')
    names = set()
    for item in result['files']:
        name = item['file']
        if not re.fullmatch(r'[a-f0-9]{64}\.png', name) or name != item['sha256'] + '.png':
            raise Failure('Evidence filename invalid')
        data = (directory / name).read_bytes()
        if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
            raise Failure('Evidence content changed')
        names.add(name)
    if names != {p.name for p in directory.iterdir() if p.name != 'manifest.json'}:
        raise Failure('Evidence receipt incomplete')
    return dict(result, directory=str(directory), manifestPath=str(path))

def release_evidence(job):
    vm_name(job)
    if record_path(job).exists():
        raise Failure('Guest is still owned or active; preserve its evidence')
    private_directory(EVIDENCE_ROOT)
    directory = EVIDENCE_ROOT / job
    private_directory(directory)
    # Also permits retiring an interrupted, unpublished receipt. Never follow a
    # link or remove an unrelated file, and never evict another active job.
    for count, path in enumerate(directory.iterdir(), 1):
        if count > EVIDENCE_MAX_FILES + 1 or (path.name != 'manifest.json' and not re.fullmatch(r'[a-f0-9]{64}\.png', path.name)):
            raise Failure('Unexpected evidence file; preserve it for inspection')
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600:
            raise Failure('Evidence file ownership or permissions invalid')
    shutil.rmtree(directory)

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
    if guest_profile(config) == 'macos':
        evidence_capacity()
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

def prepare_updates(config, name):
    if guest_profile(config) != 'linux':
        return
    # A pinned disposable image must not upgrade itself underneath a job.
    # Ubuntu's unattended upgrades can restart tart-guest-agent and terminate
    # its entire Actions process tree, leaving the host exec waiting forever.
    timers = ('apt-daily.timer', 'apt-daily-upgrade.timer')
    services = ('apt-daily.service', 'apt-daily-upgrade.service')
    call(config, 'exec', name, '/usr/bin/sudo', '/usr/bin/systemctl',
         'mask', '--runtime', *timers, *services)
    call(config, 'exec', name, '/usr/bin/sudo', '/usr/bin/systemctl', 'stop', *timers)
    # Do not interrupt dpkg halfway through an already-started upgrade. Refuse
    # this disposable clone before starting a workload instead.
    script = '''set -eu
for unit in apt-daily.timer apt-daily-upgrade.timer apt-daily.service apt-daily-upgrade.service; do
    test "$(systemctl show --property=LoadState --value "$unit")" = masked
    case "$(systemctl show --property=ActiveState --value "$unit")" in
        inactive|failed) ;;
        *) exit 78 ;;
    esac
done
'''
    call(config, 'exec', name, '/bin/sh', '-c', script)
    # Explicit browser dependency installation remains available, but may only
    # list restart requirements; it must not restart the active guest agent.
    directory = '/etc/needrestart/conf.d'
    policy = "$nrconf{restart} = 'l';\n"
    path = directory + '/99-axon-ci.conf'
    call(config, 'exec', name, '/usr/bin/sudo', '/bin/mkdir', '-p', directory)
    call(config, 'exec', '-i', name, '/usr/bin/sudo', '/usr/bin/tee', path, input=policy)
    if call(config, 'exec', name, '/usr/bin/cat', path).stdout != policy:
        raise Failure('Guest update restart policy was not written')

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
        status = call(config, 'exec', name, '/usr/bin/networkctl', 'status', interface, '--no-pager').stdout
        units = re.findall(r'^\s*Network File:\s+/(?:run|etc|usr/lib)/systemd/network/([A-Za-z0-9_-][A-Za-z0-9_.-]{0,120}\.network)\s*$', status, re.MULTILINE)
        if len(units) != 1:
            raise Failure('Expected one explicit networkd unit for the Linux interface')
        directory = '/etc/systemd/network/' + units[0] + '.d'
        # Runtime resolvectl settings are lost when DHCP or package setup
        # reconfigures the link. Persist DNS in its existing unit instead.
        settings = '[Network]\nDNS=\nDNS=1.1.1.1\nDNS=8.8.8.8\nDomains=\nDomains=~.\n[DHCPv4]\nUseDNS=no\n[DHCPv6]\nUseDNS=no\n[IPv6AcceptRA]\nUseDNS=no\n'
        call(config, 'exec', name, '/usr/bin/sudo', '/bin/mkdir', '-p', directory)
        policy = directory + '/99-axon-ci-public-dns.conf'
        call(config, 'exec', '-i', name, '/usr/bin/sudo', '/usr/bin/tee', policy, input=settings)
        if call(config, 'exec', name, '/usr/bin/cat', policy).stdout != settings:
            raise Failure('Persistent public Linux DNS policy was not written')
        call(config, 'exec', name, '/usr/bin/sudo', '/usr/bin/networkctl', 'reload')
        call(config, 'exec', name, '/usr/bin/sudo', '/usr/bin/networkctl', 'reconfigure', interface)
        # A fresh boot can retain its already-acquired DHCP DNS until the next
        # link reset. Seed the current resolved state as well as future leases.
        call(config, 'exec', name, '/usr/bin/sudo', '/usr/bin/resolvectl', 'dns', interface, '1.1.1.1', '8.8.8.8')
        call(config, 'exec', name, '/usr/bin/sudo', '/usr/bin/resolvectl', 'domain', interface, '~.')
        deadline = time.monotonic() + 10
        while True:
            dns = call(config, 'exec', name, '/usr/bin/resolvectl', 'dns', interface).stdout.split(':', 1)[-1].split()
            domains = call(config, 'exec', name, '/usr/bin/resolvectl', 'domain', interface).stdout.split(':', 1)[-1].split()
            if sorted(dns) == ['1.1.1.1', '8.8.8.8'] and domains == ['~.']:
                break
            if time.monotonic() >= deadline:
                raise Failure('Persistent public Linux DNS configuration unavailable')
            time.sleep(0.25)
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
    if (EVIDENCE_ROOT / job).exists() or (EVIDENCE_ROOT / job).is_symlink():
        raise Failure('Guest identity already has retained evidence; use a new job identity')
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
    prepare_updates(config, name)
    prepare_network(config, name)
    prepare_toolchain(config, name)
    process = subprocess.run([config['tart'], 'exec', '-i', name, *request['argv']],
                             env=environment(config), input=request['stdin'], text=True)
    try:
        saved = retain_evidence(config, job)
        if saved:
            print('Retained CI PNG evidence for managed guest ' + job, flush=True)
    except (Failure, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        # A screenshot is an additional review gate, not authority to rewrite
        # GitHub's test result or leak arbitrary guest diagnostics. Cleanup still
        # executes normally; missing evidence is never reported as visual proof.
        print('CI PNG evidence retention unavailable for managed guest ' + job, file=sys.stderr, flush=True)
    return process.returncode

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['run', '_worker', 'cleanup', 'check', 'evidence', 'release-evidence'])
    parser.add_argument('--config')
    parser.add_argument('--job')
    parser.add_argument('--timeout', type=int, default=3600)
    args = parser.parse_args()
    if args.mode in ('evidence', 'release-evidence'):
        if not args.job or args.config:
            raise Failure('Evidence commands require one exact job and no config')
        if args.mode == 'release-evidence':
            release_evidence(args.job)
            print(json.dumps({'guest': args.job, 'released': True}))
        else:
            print(json.dumps(read_evidence(args.job), indent=2))
        return 0
    if args.mode == 'check':
        if not args.config or args.job is not None:
            raise Failure('Read-only check requires a config and no job identity')
        config = frozen_config(str(Path(args.config).resolve(strict=True)))
        eligible(config)
        print(json.dumps({'eligible': True, 'profile': guest_profile(config)}))
        return 0
    if not args.job:
        raise Failure('A job attempt is required for guest execution or cleanup')
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
