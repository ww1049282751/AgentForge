import argparse
import json
import sys
from pathlib import Path
from . import __version__
from .errors import AFError
from .repository import Repository
from .runtime import Runtime
from .schema import Schemas
from .sources import build


def parser():
    root = argparse.ArgumentParser(prog='af', description='Explicit skill installs; updates are previews unless --apply is supplied.')
    root.add_argument('--version', action='version', version=__version__)
    commands = root.add_subparsers(dest='command', required=True)

    def common(p):
        p.add_argument('--project', help='Explicit existing project directory')
        p.add_argument('--scope', choices=['project', 'user'], default='project')
        p.add_argument('--target', choices=['codex'], default='codex')
        p.add_argument('--json', action='store_true')

    def install_args(p):
        common(p)
        p.add_argument('package')
        p.add_argument('--source', required=True)
        p.add_argument('--version')
        p.add_argument('--channel', choices=['stable', 'preview'])
    install_args(commands.add_parser('install', help='Explicitly install one internal plugin'))
    skill = commands.add_parser('skill').add_subparsers(dest='skill_command', required=True)
    install_args(skill.add_parser('install', help='Explicitly install one skill'))
    check = commands.add_parser('check', help='Read-only metadata check; never downloads artifact bodies')
    common(check)
    check.add_argument('--locked', action='store_true')
    update = commands.add_parser('update', help='Preview updates; pins are preserved')
    common(update)
    update.add_argument('package', nargs='?')
    update.add_argument('--apply', action='store_true')
    update.add_argument('--version')
    update.add_argument('--channel', choices=['stable', 'preview'])
    update.add_argument('--update-lock', action='store_true')
    update.add_argument('--locked', action='store_true')
    update.add_argument('--accept-permissions', action='store_true')
    rollback = commands.add_parser('rollback', help='Preview or restore the complete current transaction')
    common(rollback)
    rollback.add_argument('package', nargs='?')
    rollback.add_argument('--transaction')
    rollback.add_argument('--to')
    rollback.add_argument('--apply', action='store_true')
    recover = commands.add_parser('recover', help='Validate and recover an interrupted transaction')
    common(recover)
    recover.add_argument('--transaction', required=True)
    recover.add_argument('--apply', action='store_true')
    common(commands.add_parser('doctor', help='Read-only diagnosis'))
    validation = commands.add_parser('validate', help='Validate schemas, source metadata and dependencies')
    validation.add_argument('--source', default='.')
    builder = commands.add_parser('build', help='Prepare a local, unpublished release candidate')
    builder.add_argument('--source', default='.')
    builder.add_argument('--output', required=True)
    return root


def output(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def key(value):
    if value is None:
        return None
    if ':' in value:
        return value
    return ('plugin:' if value.startswith('af-') else 'skill:') + value


def run(args):
    if args.command == 'validate':
        schemas = Schemas()
        repo = Repository(args.source)
        return {'valid': True, 'schemas': len(schemas.documents), 'packages': sorted(repo.packages)}, 0
    if args.command == 'build':
        return build(args.source, args.output), 0
    runtime = Runtime(args.project, args.scope)
    if args.command == 'doctor':
        result = runtime.doctor()
        return result, 7 if result['pendingTransactions'] or not result['stateValid'] or result['writerLock'] else (3 if result['conflicts'] else 0)
    if args.command == 'check' or (args.command == 'update' and args.locked):
        if args.command == 'update' and (args.apply or args.version or args.update_lock or args.channel):
            raise AFError('--locked is read-only; do not combine with mutation flags')
        result = runtime.check(args.locked)
        code = 7 if result['pendingTransactions'] else (3 if result['conflicts'] else (6 if result['unsupported'] else 0))
        if result['errors']:
            code = result['errors'][0]['code']
        return result, code
    if args.command == 'recover':
        return runtime.tx.recover(args.transaction, args.apply), 0
    if args.command == 'rollback':
        if args.transaction and (args.to or args.package):
            raise AFError('Use --transaction alone to select the entire closure')
        tx = args.transaction
        if not tx:
            current = runtime.tx.snapshot()['state']
            if not current or not args.to:
                raise AFError('Specify --transaction or a package with --to version')
            tx = current['lastTransaction']
            _, journal = runtime.tx._load_journal(tx)
            if args.to != tx:
                target = journal['before']['lock']
                records = target['packages'] if target else []
                matching = [p for p in records if (not args.package or p['key'] == key(args.package)) and p['version'] == args.to]
                if not matching:
                    raise AFError('Requested version is not in the current transaction backup', 6)
        return runtime.tx.rollback(tx, args.apply), 0
    installing = args.command in ('install', 'skill')
    package = ('skill:' + args.package) if args.command == 'skill' else key(args.package)
    prepared = runtime.prepare(package, getattr(args, 'source', None), install=installing,
                               version=args.version, channel=args.channel,
                               update_lock=getattr(args, 'update_lock', False),
                               accept_permissions=getattr(args, 'accept_permissions', False))
    if installing or getattr(args, 'apply', False):
        # Present the exact bounded plan before mutating. JSON mode remains one JSON document.
        if not args.json:
            output({'plan': prepared[3]})
        result = runtime.execute(prepared)
        if args.json:
            result['plan'] = prepared[3]
        return result, 0
    return prepared[3], 0


def main(argv=None):
    try:
        args = parser().parse_args(argv)
        result, code = run(args)
        output(result)
        return code
    except AFError as exc:
        output({'error': str(exc), 'code': exc.code})
        return exc.code
    except (OSError, UnicodeError, ValueError, KeyError) as exc:
        # Raw OS/network messages can contain usernames and secret-bearing URLs.
        output({'error': 'Filesystem or malformed input failure; inspect local paths and permissions', 'code': 7, 'type': type(exc).__name__})
        return 7


if __name__ == '__main__':
    raise SystemExit(main())
