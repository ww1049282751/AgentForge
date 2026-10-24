import io
import re
import sys
import zipfile
from pathlib import Path
from .errors import AFError
from .safety import canonical, digest, read_bytes, read_json, relative, tree, within
from .schema import validate
from .semver import Version


def package_key(meta):
    return meta['kind'] + ':' + meta['id']


def frontmatter(data):
    try:
        text = data.decode('utf-8')
    except UnicodeError as exc:
        raise AFError('Skill must be UTF-8') from exc
    match = re.match(r'\A---\r?\nname: ([a-z0-9-]+)\r?\ndescription: ([^\r\n]+)\r?\n---\r?\n', text)
    if not match or not match[2].strip() or len(match[2]) > 1024:
        raise AFError('Skill requires single-line name and description frontmatter')
    return match[1], text


class Repository:
    def __init__(self, root):
        self.root = Path(root).absolute()
        self.manifest = validate('manifest', read_json(within(self.root, 'manifest.json')))
        Version(self.manifest['runtimeVersion'])
        self.index = validate('index', read_json(within(self.root, 'catalog/index.json')))
        self.packages = {}
        self.paths = {}
        self.files = {'manifest.json', 'catalog/index.json'}
        for row in self.index['packages']:
            path = relative(row['metadata'])
            meta = validate(row['kind'], read_json(within(self.root, path)))
            key = package_key(meta)
            if key != row['kind'] + ':' + row['id'] or key in self.packages:
                raise AFError('Catalog identity mismatch or duplicate', 6)
            version = Version(meta['version'])
            if meta['channel'] == 'stable' and version.pre:
                raise AFError('Prerelease cannot be stable')
            if meta['source']['path'] != str(Path(path).parent).replace('\\', '/'):
                raise AFError('Source path must equal metadata directory', 5)
            if meta['source']['kind'] == 'workspace' and (meta['source']['repository'] is not None or meta['source']['revision'] is not None):
                raise AFError('Workspace source must use null remote identity', 5)
            self.paths[key] = path
            self.packages[key] = meta
            for rel, value in tree(within(self.root, meta['source']['path'])).items():
                if value != 'directory':
                    self.files.add(meta['source']['path'] + '/' + rel)
            if meta['kind'] == 'skill':
                self._skill(meta)
            hosts = meta['compatibility']['hosts']
            if len({h['id'] for h in hosts}) != len(hosts):
                raise AFError('Duplicate host identity', 6)
            for host in hosts:
                adapter = relative(host['adapter'])
                if host['id'] != 'codex':
                    raise AFError('Only Codex adapter is implemented', 6)
                validate('adapter', read_json(within(self.root, adapter)))
                self.files.add(adapter)
        for name, path in self.index['channels'].items():
            ch = validate('channel', read_json(within(self.root, path)))
            if ch['channel'] != name:
                raise AFError('Channel identity mismatch', 5)
            validate_releases(ch)
            self.files.add(path)
        for key in self.packages:
            self.closure(key)

    def _skill(self, meta):
        root = within(self.root, meta['source']['path'])
        name, text = frontmatter(read_bytes(root / meta['entry']))
        if name != meta['id'] or root.name != meta['id']:
            raise AFError('Skill frontmatter/directory/metadata name mismatch')
        for rel, value in tree(root).items():
            if value == 'directory':
                continue
            if not rel.endswith(('.md', '.json')):
                raise AFError('Instruction-only packages accept Markdown and JSON only', 5)
            if rel.endswith('.md'):
                body = read_bytes(root / rel).decode('utf-8')
                for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)', body):
                    if '://' in link or link.startswith('#'):
                        continue
                    target = link.split('#', 1)[0]
                    if not within((root / rel).parent, target).is_file():
                        raise AFError('Missing or unsafe skill resource: ' + target, 5)

    def closure(self, key):
        done, active, versions = [], [], {}

        def visit(k, expected=None):
            if k not in self.packages:
                raise AFError('Missing dependency: ' + ' -> '.join(active + [k]), 6)
            meta = self.packages[k]
            if expected is not None:
                Version(expected)
                if expected != meta['version']:
                    raise AFError('Dependency version conflict: ' + k, 6)
            if k in active:
                raise AFError('Dependency cycle: ' + ' -> '.join(active + [k]), 6)
            if k in done:
                return
            if meta['id'] in versions and versions[meta['id']] != (meta['kind'], meta['version']):
                raise AFError('ID/kind/version conflict: ' + meta['id'], 6)
            versions[meta['id']] = (meta['kind'], meta['version'])
            active.append(k)
            deps = list(meta['dependencies'])
            if meta['kind'] == 'plugin':
                for s in meta['skills']:
                    child = self.packages.get('skill:' + s['id'])
                    if not child or child['source']['path'] != relative(s['path']):
                        raise AFError('Plugin skill path mismatch', 6)
                    deps.append({'kind': 'skill', 'id': s['id'], 'version': s['version']})
            keys = [d['kind'] + ':' + d['id'] for d in deps]
            if len(keys) != len(set(keys)):
                raise AFError('Duplicate dependency/skill reference', 6)
            for dep in deps:
                if dep['kind'] == 'plugin' and not dep['id'].startswith('af-'):
                    raise AFError('Plugin dependency requires af- prefix', 6)
                visit(dep['kind'] + ':' + dep['id'], dep['version'])
            active.pop()
            done.append(k)
        visit(key)
        return done

    def check_compatibility(self, key):
        platform = {'win32': 'windows', 'darwin': 'macos'}.get(sys.platform, 'linux')
        for k in self.closure(key):
            meta = self.packages[k]
            compat = meta['compatibility']
            if compat['runtimeMajor'] != 0 or platform not in compat['platforms']:
                raise AFError('Unsupported runtime/platform: ' + k, 6)
            host = next((h for h in compat['hosts'] if h['id'] == 'codex'), None)
            if host is None:
                raise AFError('Codex adapter missing', 6)
            adapter = read_json(within(self.root, host['adapter']))
            if not set(compat['requiredCapabilities']).issubset(set(adapter['capabilities']) & {'instructions', 'local-files'}):
                raise AFError('Missing required host capability: ' + k, 6)

    def archive(self):
        output = io.BytesIO()
        # Stored entries avoid platform/compression variability and expansion surprises.
        with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED) as z:
            for name in sorted(self.files):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                z.writestr(info, read_bytes(within(self.root, name)))
        return output.getvalue()

    def export(self, key):
        self.check_compatibility(key)
        result = {}
        for k in self.closure(key):
            meta = self.packages[k]
            if meta['kind'] != 'skill':
                continue
            host = next(h for h in meta['compatibility']['hosts'] if h['id'] == 'codex')
            adapter_bytes = read_bytes(within(self.root, host['adapter']))
            adapter = read_json(within(self.root, host['adapter']))
            name = adapter['namePrefix'] + meta['id']
            files = {}
            root = within(self.root, meta['source']['path'])
            for rel, value in tree(root).items():
                if value == 'directory' or rel == 'skill.json':
                    continue
                data = read_bytes(root / rel)
                if rel == 'SKILL.md':
                    _, text = frontmatter(data)
                    text = text.replace('\r\n', '\n')
                    data = text.replace('name: ' + meta['id'] + '\n', 'name: ' + name + '\n', 1).encode('utf-8')
                files[rel] = data
            result[name] = {'skillKey': k, 'version': meta['version'], 'adapterSha256': digest(adapter_bytes), 'files': files}
        return result


def validate_releases(channel):
    seen = set()
    for entry in channel['releases']:
        Version(entry['runtimeVersion'])
        v = Version(entry['version'])
        identity = (entry['kind'], entry['id'], entry['version'])
        if identity in seen or entry['channel'] != channel['channel'] or (entry['channel'] == 'stable' and v.pre):
            raise AFError('Duplicate release or channel violation', 5)
        seen.add(identity)
        relative(entry['source']['path'])
        if not re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})', entry['source']['revision'] or ''):
            raise AFError('Catalog releases require an immutable source revision', 5)
