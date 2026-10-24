"""Authoring utility: emit the project's closed Draft 2020-12 contracts."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'schemas'
URI = 'https://agentforge.local/schemas/'
DRAFT = 'https://json-schema.org/draft/2020-12/schema'


def obj(properties, optional=()):
    return {'type': 'object', 'additionalProperties': False,
            'required': [k for k in properties if k not in optional], 'properties': properties}


def arr(items, **kw):
    return {'type': 'array', 'items': items, **kw}


def ref(name):
    return {'$ref': 'package.schema.json#/$defs/' + name}


def emit(name, body):
    data = {'$schema': DRAFT, '$id': URI + name + '.schema.json', **body}
    (ROOT / (name + '.schema.json')).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def main():
    ROOT.mkdir(exist_ok=True)
    string = {'type': 'string', 'minLength': 1}
    boolean = {'type': 'boolean'}
    version = {'type': 'string', 'minLength': 5}
    sha = {'type': 'string', 'pattern': '^[0-9a-f]{64}$'}
    revision = {'type': 'string', 'pattern': '^(?:[0-9a-f]{40}|[0-9a-f]{64})$'}
    channel = {'enum': ['stable', 'preview']}
    kind = {'enum': ['plugin', 'skill']}
    identifier = {'type': 'string', 'pattern': '^[a-z0-9]+(?:-[a-z0-9]+)*$', 'maxLength': 64}
    source = obj({'kind': {'enum': ['workspace', 'git']},
                  'repository': {'type': ['string', 'null']}, 'revision': {'type': ['string', 'null']}, 'path': string})
    source['allOf'] = [{'if': {'properties': {'kind': {'const': 'git'}}}, 'then': {'properties': {
        'repository': {'type': 'string', 'pattern': '^https://github.com/[^/]+/[^/]+$'}, 'revision': revision}}}]
    dependency = obj({'kind': kind, 'id': identifier, 'version': version})
    permissions = obj({'network': boolean, 'writes': {'enum': ['none', 'user-selected-output']}, 'exec': {'const': False}})
    compatibility = obj({'runtimeMajor': {'type': 'integer', 'minimum': 0},
                         'platforms': arr({'enum': ['windows', 'macos', 'linux']}, minItems=1, uniqueItems=True),
                         'hosts': arr(obj({'id': identifier, 'adapter': string, 'testedVersions': arr(string, uniqueItems=True)}), minItems=1),
                         'requiredCapabilities': arr({'enum': ['instructions', 'local-files', 'web-research']}, uniqueItems=True)})
    base = {'schemaVersion': {'const': 1}, 'kind': kind, 'id': identifier, 'description': string,
            'version': version, 'channel': channel, 'dependencies': arr(ref('dependency')),
            'source': ref('source'), 'permissions': ref('permissions'), 'compatibility': ref('compatibility')}
    plugin = obj({**base, 'kind': {'const': 'plugin'}, 'id': {**identifier, 'pattern': '^af-[a-z0-9]+(?:-[a-z0-9]+)*$'},
                  'displayName': string, 'skills': arr(obj({'id': identifier, 'version': version, 'path': string}), minItems=1)})
    skill = obj({**base, 'kind': {'const': 'skill'}, 'entry': {'const': 'SKILL.md'}})
    emit('package', {'$defs': {'dependency': dependency, 'source': source, 'permissions': permissions,
                              'compatibility': compatibility, 'plugin': plugin, 'skill': skill},
                     'oneOf': [ref('plugin'), ref('skill')]})
    emit('plugin', ref('plugin'))
    emit('skill', ref('skill'))
    emit('manifest', obj({'schemaVersion': {'const': 1}, 'brand': string, 'repositoryName': string,
                          'repository': string, 'cliName': string, 'pluginPrefix': {'const': 'af-'},
                          'defaultChannel': {'const': 'stable'}, 'runtimeVersion': version,
                          'supportedSchemaVersions': arr({'const': 1}, minItems=1, uniqueItems=True)}))
    emit('index', obj({'schemaVersion': {'const': 1}, 'packages': arr(obj({'kind': kind, 'id': identifier, 'metadata': string})),
                       'channels': obj({'stable': string, 'preview': string})}))
    entry = obj({'kind': kind, 'id': identifier, 'version': version, 'channel': channel,
                 'source': ref('source'), 'artifact': obj({'url': string, 'sha256': sha, 'size': {'type': 'integer', 'minimum': 1, 'maximum': 16777216}}),
                 'publishedAt': {'type': 'string', 'format': 'date-time'}, 'runtimeVersion': version, 'releaseNotes': string})
    emit('channel', obj({'schemaVersion': {'const': 1}, 'channel': channel, 'releases': arr(entry)}))
    emit('adapter', obj({'schemaVersion': {'const': 1}, 'host': {'const': 'codex'}, 'namePrefix': {'const': 'af-'},
                         'discoveryPath': {'const': '.agents/skills'}, 'capabilities': arr({'enum': ['instructions', 'local-files']}, uniqueItems=True)}))
    resolution = obj({'key': string, 'kind': kind, 'id': identifier, 'version': version, 'channel': channel,
                      'sourceIdentity': string, 'revision': revision, 'catalogRevision': revision, 'artifactSha256': sha, 'adapterSha256': sha,
                      'dependencies': arr(string, uniqueItems=True), 'target': {'const': 'codex'}, 'pinned': boolean})
    emit('lock', obj({'schemaVersion': {'const': 1}, 'packages': arr(resolution)}))
    filemap = {'type': 'object', 'additionalProperties': {'anyOf': [sha, {'const': 'directory'}]}}
    export = obj({'name': identifier, 'skillKey': string, 'files': filemap, 'owners': arr(string, minItems=1, uniqueItems=True)})
    root = obj({'key': string, 'source': string, 'channel': channel, 'permissions': ref('permissions')})
    emit('state', obj({'schemaVersion': {'const': 1}, 'scope': {'enum': ['project', 'user']}, 'targetRoot': string,
                       'roots': arr(root), 'lock': {'$ref': 'lock.schema.json'}, 'exports': arr(export),
                       'lastTransaction': {'type': ['string', 'null']}, 'previousTransaction': {'type': ['string', 'null']}}))
    snapshot = obj({'state': {'anyOf': [{'$ref': 'state.schema.json'}, {'type': 'null'}]},
                    'lock': {'anyOf': [{'$ref': 'lock.schema.json'}, {'type': 'null'}]}})
    emit('transaction', obj({'schemaVersion': {'const': 1}, 'id': {'type': 'string', 'pattern': '^[0-9a-f]{32}$'},
                             'targetRoot': string, 'phase': {'enum': ['planned', 'staged', 'backed_up', 'switching', 'committed', 'restoring', 'rolled_back', 'recovery_required']},
                             'before': snapshot, 'after': snapshot,
                             'names': arr(identifier, uniqueItems=True), 'backupFiles': filemap, 'candidateFiles': filemap}))


if __name__ == '__main__':
    main()
