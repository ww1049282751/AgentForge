import copy
import re
import tempfile
from pathlib import Path
from .errors import AFError
from .repository import package_key
from .safety import digest, no_links, read_bytes, read_json, relative, within
from .schema import validate
from .semver import Version
from .sources import Source
from .transactions import Transactions


def file_baseline(files):
    result = {}
    for rel, data in files.items():
        relative(rel)
        result[rel] = digest(data)
        for parent in Path(rel).parents:
            if str(parent) != '.':
                result[parent.as_posix() + '/'] = 'directory'
    return result


class Runtime:
    def __init__(self, project=None, scope='project', user_home=None, hook=None):
        self.user_home = no_links(user_home or Path.home())
        self.scope = scope
        if scope == 'user':
            self.target = self.user_home
        else:
            self.target = no_links(project or Path.cwd())
            if project is None and not any((p / '.git').exists() for p in (self.target, *self.target.parents)):
                raise AFError('No project detected; specify --project or --scope user')
        if not self.target.is_dir():
            raise AFError('Target directory must already exist')
        self.tx = Transactions(self.target, hook=hook)
        self.tx.expected_scope = scope

    def _ambiguity(self, names, current):
        owned = {e['name'] for e in current['exports']} if current else set()
        locations = [self.user_home / '.agents/skills', self.user_home / '.codex/skills']
        locations += [p / '.agents/skills' for p in self.target.parents if (p / '.git').exists()]
        for location in locations:
            if location == self.tx.exports or not location.exists():
                continue
            no_links(location)
            for folder in location.iterdir():
                entry = folder / 'SKILL.md'
                if not entry.is_file():
                    continue
                # Other host skills may have richer YAML; only inspect the name line.
                text = read_bytes(entry).decode('utf-8')
                match = re.search(r'^name:\s*[\'"]?([a-z0-9-]+)[\'"]?\s*$', text, re.M)
                if folder.name in names or (match and match[1] in names):
                    raise AFError('Ambiguous global/ancestor skill: ' + folder.name + '; choose or move it manually before project installation', 3)
        if self.tx.exports.exists():
            for folder in self.tx.exports.iterdir():
                if folder.name in owned:
                    continue
                if folder.name in names:
                    raise AFError('Unmanaged skill directory: ' + folder.name, 3)
                entry = folder / 'SKILL.md'
                if entry.is_file():
                    text = read_bytes(entry).decode('utf-8')
                    match = re.search(r'^name:\s*[\'"]?([a-z0-9-]+)[\'"]?\s*$', text, re.M)
                    if match and match[1] in names:
                        raise AFError('Duplicate host skill name: ' + match[1], 3)

    def check(self, locked=False):
        snapshot = self.tx.snapshot()
        state = snapshot['state']
        result = {'updatesAvailable': [], 'pinned': [], 'conflicts': self.tx.conflicts(state),
                  'unsupported': [], 'errors': [], 'pendingTransactions': self.tx.unfinished(), 'readOnly': True}
        if not state:
            return result
        packages = {p['key']: p for p in state['lock']['packages']}
        for root in state['roots']:
            current = packages[root['key']]
            if current['pinned']:
                result['pinned'].append(root['key'])
            try:
                source = Source(root['source'])
                if source.identity != current['sourceIdentity']:
                    raise AFError('Source identity changed', 5)
                candidate = source.select(root['key'], root['channel'])
                if Version(candidate['runtimeVersion']).core[0] != 0:
                    result['unsupported'].append(root['key'])
                if Version(candidate['version']) > Version(current['version']):
                    result['updatesAvailable'].append({'key': root['key'], 'installed': current['version'],
                                                       'available': candidate['version'], 'pinned': current['pinned'],
                                                       'catalogRevision': source.revision})
                if locked:
                    original = source.select(root['key'], root['channel'], current['version'])
                    if original['artifact']['sha256'] != current['artifactSha256'] or original['source']['revision'] != current['revision']:
                        raise AFError('Locked artifact changed at the source', 5)
            except AFError as exc:
                result['errors'].append({'key': root['key'], 'code': exc.code, 'message': str(exc)})
        return result

    def doctor(self):
        result = {'scope': self.scope, 'host': 'codex', 'requiredCapabilities': ['instructions', 'local-files'],
                  'hostInvocationVerified': False, 'pendingTransactions': self.tx.unfinished(),
                  'writerLock': self.tx.writer.exists(), 'readOnly': True}
        try:
            snapshot = self.tx.snapshot()
            result['conflicts'] = self.tx.conflicts(snapshot['state'])
            result['stateValid'] = True
        except AFError as exc:
            result.update(stateValid=False, error=str(exc), code=exc.code)
        return result

    def prepare(self, key=None, source_location=None, *, install=False, version=None,
                channel=None, update_lock=False, accept_permissions=False):
        before = self.tx.snapshot()
        self.tx.assert_clean(before['state'])
        if self.tx.writer.exists() or self.tx.unfinished():
            raise AFError('Writer lock or unfinished transaction; run doctor/recover', 7)
        state = before['state']
        roots = copy.deepcopy(state['roots']) if state else []
        old = {p['key']: p for p in state['lock']['packages']} if state else {}
        if install:
            if not key or not source_location:
                raise AFError('Install requires a package and explicit --source')
            location = str(source_location) if str(source_location).startswith('https://') else str(Path(source_location).absolute())
            existing = next((r for r in roots if r['key'] == key), None)
            if existing and existing['source'] != location:
                raise AFError('Source change refused; review and install into a separate target', 5)
            if not existing:
                roots.append({'key': key, 'source': location, 'channel': channel or 'stable',
                              'permissions': {'network': False, 'writes': 'none', 'exec': False}})
        elif key and not any(r['key'] == key for r in roots):
            raise AFError('Package is not installed: ' + key, 6)
        if version and not key:
            raise AFError('--version requires one explicit package')
        if update_lock and not version:
            raise AFError('--update-lock requires --version')
        if not roots:
            raise AFError('No installed packages in this scope', 6)
        resolved, exports, changes, source_cache = {}, {}, [], {}
        with tempfile.TemporaryDirectory(prefix='agentforge-resolve-') as temporary:
            for root in roots:
                selected = root['key'] == key if key else not install
                previous = old.get(root['key'])
                if selected and channel:
                    root['channel'] = channel
                if root['source'] not in source_cache:
                    source_cache[root['source']] = Source(root['source'])
                source = source_cache[root['source']]
                if previous and source.identity != previous['sourceIdentity']:
                    raise AFError('Source identity changed', 5)
                exact = None
                if previous and (not selected or previous['pinned'] or install):
                    exact = previous['version']
                if selected and version:
                    if previous and previous['pinned'] and version != previous['version'] and not update_lock:
                        raise AFError('Pinned version changes require --version and --update-lock', 3)
                    exact = version
                entry = source.select(root['key'], root['channel'], exact)
                if previous:
                    new, prior = Version(entry['version']), Version(previous['version'])
                    if new < prior:
                        raise AFError('Downgrades use rollback; update never silently downgrades', 6)
                    if new.core[0] != prior.core[0] and not (selected and version):
                        raise AFError('Major update requires an exact --version and migration review', 6)
                    if entry['version'] == previous['version'] and (entry['artifact']['sha256'] != previous['artifactSha256'] or entry['source']['revision'] != previous['revision']):
                        raise AFError('Immutable version has changed bytes or source revision; bump component versions', 5)
                repo = source.materialize(entry, temporary)
                closure = repo.closure(root['key'])
                repo.check_compatibility(root['key'])
                permissions = {'network': False, 'writes': 'none', 'exec': False}
                for dep in closure:
                    p = repo.packages[dep]['permissions']
                    permissions['network'] |= p['network']
                    if p['writes'] != 'none':
                        permissions['writes'] = p['writes']
                escalation = previous and ((permissions['network'] and not root['permissions']['network']) or
                                           (permissions['writes'] != 'none' and root['permissions']['writes'] == 'none'))
                if escalation and not accept_permissions:
                    raise AFError('Permissions expand; inspect package and explicitly use --accept-permissions', 6)
                root['permissions'] = permissions
                generated = repo.export(root['key'])
                adapter_digests = {e['adapterSha256'] for e in generated.values()}
                adapter_digest = digest(''.join(sorted(adapter_digests)).encode())
                for dep in closure:
                    meta = repo.packages[dep]
                    prior_dep = old.get(dep)
                    record = {'key': dep, 'kind': meta['kind'], 'id': meta['id'], 'version': meta['version'],
                              'channel': meta['channel'], 'sourceIdentity': source.identity,
                              'revision': entry['source']['revision'] or source.revision,
                              'catalogRevision': prior_dep['catalogRevision'] if prior_dep and meta['version'] == prior_dep['version'] and entry['artifact']['sha256'] == prior_dep['artifactSha256'] else source.revision,
                              'artifactSha256': entry['artifact']['sha256'], 'adapterSha256': adapter_digest,
                              'dependencies': [k for k in repo.closure(dep) if k != dep], 'target': 'codex',
                              'pinned': self.scope == 'project'}
                    if dep in resolved and resolved[dep] != record:
                        raise AFError('Shared dependency source/version/artifact conflict: ' + dep, 6)
                    resolved[dep] = record
                for name, exported in generated.items():
                    if name in exports:
                        if exports[name]['data'] != exported:
                            raise AFError('Conflicting host export: ' + name, 6)
                        exports[name]['owners'].append(root['key'])
                    else:
                        exports[name] = {'data': exported, 'owners': [root['key']]}
                changes.append({'key': root['key'], 'from': previous['version'] if previous else None, 'to': entry['version'],
                                'source': source.identity, 'catalogRevision': source.revision,
                                'sourceRevision': entry['source']['revision'] or source.revision,
                                'artifactSha256': entry['artifact']['sha256'], 'permissions': permissions,
                                'pinned': self.scope == 'project', 'releaseNotes': entry['releaseNotes']})
        self._ambiguity(set(exports), state)
        files = {}
        export_records = []
        for name, item in sorted(exports.items()):
            data = item['data']
            files.update({name + '/' + path: value for path, value in data['files'].items()})
            export_records.append({'name': name, 'skillKey': data['skillKey'], 'files': file_baseline(data['files']),
                                   'owners': sorted(item['owners'])})
        lock = validate('lock', {'schemaVersion': 1, 'packages': [resolved[k] for k in sorted(resolved)]})
        after_state = {'schemaVersion': 1, 'scope': self.scope, 'targetRoot': str(self.target),
                       'roots': sorted(roots, key=lambda r: r['key']), 'lock': lock, 'exports': export_records,
                       'lastTransaction': state['lastTransaction'] if state else None,
                       'previousTransaction': state['previousTransaction'] if state else None}
        validate('state', after_state)
        after = {'state': after_state, 'lock': lock}
        no_change = after == before
        plan = {'changes': changes, 'exports': ['.agents/skills/' + name for name in sorted(exports)],
                'lockChanged': before['lock'] != lock, 'lockBefore': before['lock'], 'lockAfter': lock,
                'candidateBytes': sum(len(v) for v in files.values()),
                'backupRequired': bool(state), 'noChange': no_change, 'applied': False,
                'activation': 'Close host readers before apply; recoverable directory renames, not hot reload'}
        return before, after, files, plan

    def execute(self, prepared):
        before, after, files, plan = prepared
        if plan['noChange']:
            return {'status': 'already-installed-or-locked', 'applied': False}
        tx = self.tx.apply(before, after, files)
        return {'status': 'committed', 'transaction': tx, 'applied': True}
