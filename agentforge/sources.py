"""Explicit local sources and immutable public GitHub catalogs; no auth propagation."""
import datetime
import http.client
import os
import re
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from .errors import AFError
from .repository import Repository, package_key, validate_releases
from .safety import MAX_TOTAL, canonical, digest, parse_json, read_bytes, read_json, relative, safe_zip, within, atomic_json
from .schema import validate
from .semver import Version

GITHUB = re.compile(r'https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?(?:#([0-9a-f]{40}))?\Z')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise AFError('Source redirect refused; use an immutable allowed URL', 5)


def download(url, limit=2 * 1024 * 1024):
    if urllib.parse.urlsplit(url).scheme != 'https':
        raise AFError('Only HTTPS downloads are permitted', 5)
    req = urllib.request.Request(url, headers={'User-Agent': 'AgentForge/0.1', 'Accept': 'application/json, application/octet-stream'})
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=15) as response:
            data = response.read(limit + 1)
            if len(data) > limit:
                raise AFError('Download exceeds size limit', 5)
            length = response.headers.get('Content-Length')
            if length is not None and int(length) != len(data):
                raise AFError('Incomplete download', 4)
            return data
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, http.client.HTTPException) as exc:
        status = getattr(exc, 'code', None)
        raise AFError('HTTPS source unavailable' + (f' (HTTP {status})' if status else '') + '; check network/access; no installation changed', 4) from exc


class Source:
    def __init__(self, location):
        self.location = str(location)
        self.remote = self.location.startswith('https://')
        self.repo = None
        if self.remote:
            match = GITHUB.fullmatch(self.location)
            if not match or any(x in ('.', '..') for x in match.group(1, 2)):
                raise AFError('Source must be an explicit GitHub repository URL (optional #commit)', 5)
            self.owner, self.name, commit = match.groups()
            self.identity = f'https://github.com/{self.owner}/{self.name}'
            if commit is None:
                info = parse_json(download(f'https://api.github.com/repos/{self.owner}/{self.name}/commits/HEAD'))
                commit = info.get('sha', '')
            if not re.fullmatch('[0-9a-f]{40}', commit):
                raise AFError('Unable to resolve immutable catalog commit', 5)
            self.revision = commit
            self.base = f'https://raw.githubusercontent.com/{self.owner}/{self.name}/{commit}/'
            self.index = validate('index', parse_json(download(self.base + 'catalog/index.json')))
        else:
            self.root = Path(location).absolute()
            self.identity = 'workspace:' + digest(os.path.normcase(str(self.root)).encode())
            self.index = validate('index', read_json(within(self.root, 'catalog/index.json')))
            if (self.root / 'manifest.json').is_file():
                self.repo = Repository(self.root)
                self.revision = digest(self.repo.archive())
            else:
                self.revision = digest(canonical({'index': self.index, 'channels': {
                    name: read_json(within(self.root, path)) for name, path in self.index['channels'].items()}}))
        keys = [package_key(row) for row in self.index['packages']]
        if len(keys) != len(set(keys)):
            raise AFError('Duplicate catalog package identity', 5)
        for row in self.index['packages']:
            relative(row['metadata'])
        for path in self.index['channels'].values():
            relative(path)

    def allowed_artifact(self, entry):
        if entry['source']['kind'] != 'git' or entry['source']['repository'] != self.identity:
            raise AFError('Release source identity changed', 5)
        url = entry['artifact']['url']
        pattern = rf'https://raw\.githubusercontent\.com/{re.escape(self.owner)}/{re.escape(self.name)}/[0-9a-f]{{40}}/(.+)'
        match = re.fullmatch(pattern, url)
        if not match:
            raise AFError('Artifact must use the selected repository and an immutable raw URL', 5)
        relative(match[1])
        return url

    def releases(self, channel):
        path = relative(self.index['channels'][channel])
        data = parse_json(download(self.base + path)) if self.remote else read_json(within(self.root, path))
        validate('channel', data)
        if data['channel'] != channel:
            raise AFError('Requested channel mismatch', 5)
        validate_releases(data)
        known = {package_key(row) for row in self.index['packages']}
        for entry in data['releases']:
            if package_key(entry) not in known:
                raise AFError('Release not declared in catalog index', 5)
            if self.remote:
                self.allowed_artifact(entry)
            else:
                relative(entry['artifact']['url'])
        return data['releases']

    def select(self, key, channel='stable', version=None):
        if version:
            Version(version)
        choices = [x for x in self.releases(channel) if package_key(x) == key]
        if self.repo and key in self.repo.packages:
            meta = self.repo.packages[key]
            if meta['channel'] == channel:
                data = self.repo.archive()
                choices.append({'kind': meta['kind'], 'id': meta['id'], 'version': meta['version'], 'channel': channel,
                                'source': {'kind': 'workspace', 'repository': None, 'revision': self.revision, 'path': meta['source']['path']},
                                'artifact': {'url': 'workspace', 'sha256': digest(data), 'size': len(data)},
                                'runtimeVersion': '0.1.0', 'releaseNotes': 'Local workspace draft; unpublished', 'workspace': True})
        if version:
            choices = [x for x in choices if x['version'] == version]
        if not choices:
            raise AFError('Source does not contain requested package/version: ' + key + ('@' + version if version else ''), 6)
        return max(choices, key=lambda x: Version(x['version']))

    def materialize(self, entry, parent):
        if Version(entry['runtimeVersion']).core[0] != 0:
            raise AFError('Unsupported catalog runtime version', 6)
        if self.remote:
            url = self.allowed_artifact(entry)
            data = download(url, MAX_TOTAL)
        elif entry.get('workspace'):
            data = self.repo.archive()
        else:
            data = read_bytes(within(self.root, entry['artifact']['url']), MAX_TOTAL)
        if len(data) != entry['artifact']['size'] or digest(data) != entry['artifact']['sha256']:
            raise AFError('Artifact digest/size mismatch', 5)
        target = Path(parent) / entry['artifact']['sha256']
        if not target.exists():
            safe_zip(data, target)
        repo = Repository(target)
        key = package_key(entry)
        meta = repo.packages.get(key)
        if not meta or meta['version'] != entry['version'] or meta['channel'] != entry['channel'] or meta['source']['path'] != entry['source']['path']:
            raise AFError('Artifact identity/version/channel mismatch', 5)
        for k in repo.closure(key):
            source = repo.packages[k]['source']
            if source['kind'] == 'git' and (source['revision'] != entry['source']['revision'] or source['repository'] != entry['source']['repository']):
                raise AFError('Artifact source/revision mismatch', 5)
        return repo


def build(root, output):
    repo = Repository(root)
    output = Path(output).absolute()
    if output.exists():
        raise AFError('Build output already exists; choose a new directory', 3)
    data = repo.archive()
    sha = digest(data)
    revision = None
    try:
        result = subprocess.run(['git', '-C', str(repo.root), 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True)
        status = subprocess.run(['git', '-C', str(repo.root), 'status', '--porcelain'], capture_output=True, text=True, check=True)
        if not status.stdout.strip():
            revision = result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        pass
    output.mkdir(parents=True)
    archive_path = 'artifacts/' + sha + '.zip'
    within(output, archive_path).parent.mkdir()
    within(output, archive_path).write_bytes(data)
    atomic_json(output / 'catalog/index.json', repo.index)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for channel, path in repo.index['channels'].items():
        entries = []
        for meta in repo.packages.values():
            if meta['channel'] != channel:
                continue
            source = {'kind': 'git' if revision else 'workspace', 'repository': repo.manifest['repository'] if revision else None,
                      'revision': revision or sha, 'path': meta['source']['path']}
            entries.append({'kind': meta['kind'], 'id': meta['id'], 'version': meta['version'], 'channel': channel,
                            'source': source, 'artifact': {'url': archive_path, 'sha256': sha, 'size': len(data)},
                            'publishedAt': now, 'runtimeVersion': '0.1.0',
                            'releaseNotes': 'LOCAL CANDIDATE; not published; see release checklist'})
        document = {'schemaVersion': 1, 'channel': channel, 'releases': entries}
        validate('channel', document)
        atomic_json(within(output, path), document)
    atomic_json(output / 'candidate.json', {'status': 'local-candidate', 'gitRevision': revision, 'artifactSha256': sha,
                                          'artifactBytes': len(data), 'signatureVerified': False, 'published': False})
    return {'status': 'candidate-created', 'artifactSha256': sha, 'gitRevision': revision, 'published': False}
