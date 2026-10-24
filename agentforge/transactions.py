"""Recoverable same-volume directory renames, deliberately not cross-path atomic."""
import contextlib
import ctypes
import os
import re
import shutil
import uuid
from pathlib import Path
from .errors import AFError
from .safety import atomic_json, canonical, digest, no_links, read_json, tree, within
from .schema import validate
from .semver import Version


@contextlib.contextmanager
def process_mutex(home):
    """Kernel-owned lock releases on process death; the marker file is never removed."""
    home = no_links(home)
    home.mkdir(parents=True, exist_ok=True)
    path = no_links(home / 'mutex')
    if path.exists() and (not path.is_file() or path.stat().st_nlink != 1):
        raise AFError('Invalid transaction mutex path', 7)
    with path.open('a+b') as stream:
        if path.stat().st_size == 0:
            stream.write(b'0')
            stream.flush()
        stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise AFError('Another process is applying or recovering this target', 7) from exc
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def alive(pid):
    if not isinstance(pid, int) or pid < 1:
        raise AFError('Invalid lock owner; preserve the lock for manual diagnosis', 7)
    if os.name == 'nt':
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            # Access denied is not proof that a process has exited.
            return ctypes.get_last_error() != 87
        code = ctypes.c_ulong()
        try:
            if not kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
                return True
            return code.value == 259
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


class Transactions:
    def __init__(self, target, *, hook=None):
        self.target = no_links(target)
        self.home = no_links(self.target / '.agentforge')
        self.exports = no_links(self.target / '.agents/skills')
        self.state_path = self.home / 'state.json'
        self.lock_path = self.target / 'agentforge.lock.json'
        self.writer = self.home / 'write.lock'
        self.hook = hook or (lambda phase: None)
        self.expected_scope = None

    def snapshot(self):
        state = validate('state', read_json(self.state_path)) if self.state_path.exists() else None
        lock = validate('lock', read_json(self.lock_path)) if self.lock_path.exists() else None
        if state and (state['targetRoot'] != str(self.target) or state['lock'] != lock):
            raise AFError('State/target/lock mismatch; inspect doctor and recovery logs', 7)
        if not state and lock:
            raise AFError('Unmanaged lock file; refusing to adopt or replace it', 3)
        if state:
            self.validate_state(state)
        return {'state': state, 'lock': lock}

    def validate_state(self, state):
        validate('state', state)
        if state['targetRoot'] != str(self.target):
            raise AFError('State belongs to another target', 7)
        if self.expected_scope and state['scope'] != self.expected_scope:
            raise AFError('Installed scope differs from requested scope', 3)
        names = [e['name'] for e in state['exports']]
        keys = [p['key'] for p in state['lock']['packages']]
        roots = [r['key'] for r in state['roots']]
        if len(names) != len(set(names)) or len(keys) != len(set(keys)) or len(roots) != len(set(roots)):
            raise AFError('Duplicate state ownership', 7)
        if not set(roots).issubset(keys):
            raise AFError('Root missing from lock closure', 7)
        for package in state['lock']['packages']:
            Version(package['version'])
            if package['key'] != package['kind'] + ':' + package['id'] or not set(package['dependencies']).issubset(keys):
                raise AFError('Invalid lock dependency/identity', 7)
            if package['key'] in package['dependencies']:
                raise AFError('Cyclic lock dependency', 7)
        for e in state['exports']:
            if e['skillKey'] not in keys or not set(e['owners']).issubset(roots):
                raise AFError('Invalid export ownership', 7)
            within(self.exports, e['name'])
            for rel in e['files']:
                within(self.exports / e['name'], rel.rstrip('/'))

    def conflicts(self, state):
        problems = []
        if state:
            for export in state['exports']:
                path = within(self.exports, export['name'])
                try:
                    current = tree(path)
                    if current != export['files']:
                        for rel in sorted(set(current) | set(export['files'])):
                            if current.get(rel) != export['files'].get(rel):
                                problems.append(export['name'] + '/' + rel)
                except (AFError, OSError):
                    problems.append(export['name'] + '/<missing-or-path-type-change>')
        return problems

    def assert_clean(self, state):
        conflicts = self.conflicts(state)
        if conflicts:
            raise AFError('Local changes: ' + ', '.join(conflicts) + '. Keep current version, copy edits elsewhere, or manually merge and reinstall into a new target. No force overwrite.', 3)

    def unfinished(self):
        results = []
        root = no_links(self.home / 'transactions')
        if root.exists():
            for path in root.glob('*/journal.json'):
                doc = validate('transaction', read_json(path))
                if doc['phase'] not in ('committed', 'rolled_back'):
                    results.append({'id': doc['id'], 'phase': doc['phase']})
        return results

    def _exclusive(self, path, content):
        no_links(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open('xb') as f:
                f.write(canonical(content))
                f.flush()
                os.fsync(f.fileno())
        except FileExistsError as exc:
            raise AFError('Target is locked; use doctor, never delete locks by age', 7) from exc

    def _phase(self, directory, journal, phase):
        journal['phase'] = phase
        atomic_json(directory / 'journal.json', journal)
        self.hook(phase)

    def _write_snapshot(self, snapshot):
        for path, value in ((self.state_path, snapshot['state']), (self.lock_path, snapshot['lock'])):
            no_links(path)
            if value is None:
                if path.exists():
                    path.unlink()
            else:
                atomic_json(path, value)

    def apply(self, before, after, files):
        with process_mutex(self.home):
            return self._apply(before, after, files)

    def _apply(self, before, after, files):
        if self.unfinished():
            raise AFError('An unfinished transaction requires recovery first', 7)
        tx = uuid.uuid4().hex
        self._exclusive(self.writer, {'transaction': tx, 'pid': os.getpid()})
        directory = within(self.home, 'transactions/' + tx)
        journal = None
        try:
            if self.snapshot() != before:
                raise AFError('State changed while planning; retry', 3)
            self.assert_clean(before['state'])
            old_names = {e['name'] for e in before['state']['exports']} if before['state'] else set()
            new_names = {e['name'] for e in after['state']['exports']} if after['state'] else set()
            names = sorted(old_names | new_names)
            for name in new_names - old_names:
                if within(self.exports, name).exists():
                    raise AFError('Unmanaged skill directory: ' + name, 3)
            old_bytes = sum(p.stat().st_size for name in old_names for p in within(self.exports, name).rglob('*') if p.is_file())
            needed = sum(len(v) for v in files.values()) * 2 + old_bytes * 3 + 1024 * 1024
            if shutil.disk_usage(self.target).free < needed:
                raise AFError('Insufficient free space for candidate and verified backup', 7)
            directory.mkdir(parents=True)
            if after['state']:
                after['state']['previousTransaction'] = before['state']['lastTransaction'] if before['state'] else None
                after['state']['lastTransaction'] = tx
                validate('state', after['state'])
            journal = {'schemaVersion': 1, 'id': tx, 'targetRoot': str(self.target), 'phase': 'planned',
                       'before': before, 'after': after, 'names': names, 'backupFiles': {}, 'candidateFiles': {}}
            self._phase(directory, journal, 'planned')
            candidate = directory / 'candidate'
            candidate.mkdir()
            for rel, data in files.items():
                path = within(candidate, rel)
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open('xb') as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
            journal['candidateFiles'] = tree(candidate)
            self._verify_export_snapshot(candidate, after['state'])
            self._phase(directory, journal, 'staged')
            backup = directory / 'backup'
            backup.mkdir()
            for name in sorted(old_names):
                shutil.copytree(within(self.exports, name), within(backup, name))
            journal['backupFiles'] = tree(backup)
            self._verify_export_snapshot(backup, before['state'])
            self._phase(directory, journal, 'backed_up')
            # Recheck both the state and live files immediately before first rename.
            if self.snapshot() != before:
                raise AFError('State changed before activation', 3)
            self.assert_clean(before['state'])
            self.exports.mkdir(parents=True, exist_ok=True)
            retired = directory / 'retired'
            retired.mkdir()
            self._phase(directory, journal, 'switching')
            for name in names:
                dest = within(self.exports, name)
                if name in old_names:
                    dest.rename(within(retired, name))
                    self.hook('old_renamed:' + name)
                if name in new_names:
                    within(candidate, name).rename(dest)
                    self.hook('new_renamed:' + name)
            self._write_snapshot(after)
            self.hook('state_written')
            self.assert_clean(after['state'])
            if self.snapshot() != after:
                raise AFError('Post-activation state mismatch', 7)
            self._phase(directory, journal, 'committed')
            return tx
        except Exception as exc:
            if journal and journal['phase'] in ('switching', 'restoring', 'recovery_required'):
                try:
                    self._restore(directory, journal)
                except Exception as recovery_error:
                    self._phase(directory, journal, 'recovery_required')
                    raise AFError('Transaction needs recovery: ' + tx + '; preserve logs, staging and backup', 7) from recovery_error
            elif journal and journal['phase'] != 'committed':
                self._phase(directory, journal, 'rolled_back')
            if isinstance(exc, AFError):
                raise
            raise AFError('Transaction failed and prior state was preserved: ' + tx, 7) from exc
        finally:
            # Abrupt exit/BaseException keeps ownership evidence for recovery.
            if journal is None or journal['phase'] in ('committed', 'rolled_back'):
                self.writer.unlink(missing_ok=True)

    def _verify_export_snapshot(self, folder, state):
        expected = {e['name']: e for e in state['exports']} if state else {}
        actual = {p.name for p in folder.iterdir()} if folder.exists() else set()
        if actual != set(expected):
            raise AFError('Snapshot export set mismatch', 7)
        for name, e in expected.items():
            if tree(within(folder, name)) != e['files']:
                raise AFError('Snapshot checksum mismatch: ' + name, 7)

    def _load_journal(self, tx):
        if not re.fullmatch('[0-9a-f]{32}', tx):
            raise AFError('Invalid transaction ID')
        directory = within(self.home, 'transactions/' + tx)
        journal = validate('transaction', read_json(directory / 'journal.json'))
        if journal['id'] != tx or journal['targetRoot'] != str(self.target):
            raise AFError('Transaction identity/target mismatch', 7)
        names = set()
        for snapshot in (journal['before'], journal['after']):
            state = snapshot['state']
            if state:
                self.validate_state(state)
                if state['lock'] != snapshot['lock']:
                    raise AFError('Transaction lock/state mismatch', 7)
                names.update(e['name'] for e in state['exports'])
            elif snapshot['lock'] is not None:
                raise AFError('Transaction has orphan lock snapshot', 7)
        if set(journal['names']) != names:
            raise AFError('Transaction scope mismatch', 7)
        return directory, journal

    def _validate_recovery_live(self, journal):
        before, after = journal['before'], journal['after']
        for name in journal['names']:
            path = within(self.exports, name)
            if not path.exists():
                continue
            allowed = [e['files'] for s in (before, after) if s['state'] for e in s['state']['exports'] if e['name'] == name]
            if tree(path) not in allowed:
                raise AFError('Local changes prevent recovery: ' + name, 3)
        for path, key in ((self.state_path, 'state'), (self.lock_path, 'lock')):
            if path.exists() and read_json(path) not in (before[key], after[key]):
                raise AFError('Changed state/lock prevents recovery', 3)

    def _restore(self, directory, journal):
        backup = directory / 'backup'
        if tree(backup) != journal['backupFiles']:
            raise AFError('Backup is corrupt; preserve live files and logs', 7)
        self._verify_export_snapshot(backup, journal['before']['state'])
        self._validate_recovery_live(journal)
        self._phase(directory, journal, 'restoring')
        restore = directory / ('restore-' + uuid.uuid4().hex)
        shutil.copytree(backup, restore)
        self._verify_export_snapshot(restore, journal['before']['state'])
        self._validate_recovery_live(journal)
        displaced = directory / ('displaced-' + uuid.uuid4().hex)
        displaced.mkdir()
        self.exports.mkdir(parents=True, exist_ok=True)
        for name in journal['names']:
            dest = within(self.exports, name)
            if dest.exists():
                dest.rename(within(displaced, name))
            source = within(restore, name)
            if source.exists():
                source.rename(dest)
        self._write_snapshot(journal['before'])
        self.assert_clean(journal['before']['state'])
        self._phase(directory, journal, 'rolled_back')

    def recover(self, tx, apply=False):
        if apply:
            with process_mutex(self.home):
                return self._recover(tx, True)
        return self._recover(tx, False)

    def _recover(self, tx, apply=False):
        directory, journal = self._load_journal(tx)
        if journal['phase'] in ('committed', 'rolled_back'):
            # A crash can leave a terminal journal with a stale writer lock.
            action = 'release-terminal-lock'
        else:
            action = 'restore-before'
        if not apply:
            return {'transaction': tx, 'phase': journal['phase'], 'action': action, 'applied': False}
        guard = self.home / 'recover.lock'
        if guard.exists():
            recovery_owner = read_json(guard)
            if set(recovery_owner) != {'pid', 'transaction'} or alive(recovery_owner['pid']):
                raise AFError('Recovery process is active or its ownership is invalid', 7)
            # Kernel mutex excludes another recovery while removing a proven-dead guard.
            guard.unlink()
        self._exclusive(guard, {'pid': os.getpid(), 'transaction': tx})
        try:
            if self.writer.exists():
                owner = read_json(self.writer)
                if set(owner) != {'transaction', 'pid'} or owner['transaction'] != tx:
                    raise AFError('Writer lock belongs to another or invalid transaction', 7)
                if alive(owner['pid']):
                    raise AFError('Writer process is still alive; recovery refused', 7)
            else:
                self._exclusive(self.writer, {'pid': os.getpid(), 'transaction': tx})
            if journal['phase'] in ('planned', 'staged'):
                # No target mutations have occurred at these durable phases.
                if self.snapshot() != journal['before']:
                    raise AFError('Live state differs from pre-switch snapshot', 3)
                self.assert_clean(journal['before']['state'])
                self._phase(directory, journal, 'rolled_back')
            elif journal['phase'] not in ('committed', 'rolled_back'):
                self._restore(directory, journal)
            else:
                expected = journal['after'] if journal['phase'] == 'committed' else journal['before']
                if self.snapshot() != expected:
                    raise AFError('Terminal transaction does not match live state', 7)
                self.assert_clean(expected['state'])
            self.writer.unlink(missing_ok=True)
            return {'transaction': tx, 'phase': journal['phase'], 'applied': True}
        finally:
            guard.unlink(missing_ok=True)

    def rollback(self, tx, apply=False):
        directory, journal = self._load_journal(tx)
        if journal['phase'] != 'committed':
            raise AFError('Rollback requires a committed transaction', 7)
        current = self.snapshot()
        self.assert_clean(current['state'])
        def content(snapshot):
            import copy
            value = copy.deepcopy(snapshot)
            if value['state']:
                value['state'].pop('lastTransaction', None)
                value['state'].pop('previousTransaction', None)
            return value
        if content(current) != content(journal['after']):
            raise AFError('Rollback only supports the current transaction; reverse newer transactions first', 7)
        if tree(directory / 'backup') != journal['backupFiles']:
            raise AFError('Backup checksum mismatch', 7)
        self._verify_export_snapshot(directory / 'backup', journal['before']['state'])
        if not apply:
            return {'transaction': tx, 'action': 'rollback-entire-closure', 'applied': False}
        from .safety import read_bytes
        files = {rel: read_bytes(directory / 'backup' / rel) for rel, value in journal['backupFiles'].items() if value != 'directory'}
        after = journal['before']
        new_tx = self.apply(current, after, files)
        return {'transaction': new_tx, 'restoredTransaction': tx, 'applied': True}
