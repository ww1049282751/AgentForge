import copy
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import urllib.error
import zipfile
from pathlib import Path
from unittest.mock import patch

from agentforge.cli import main
from agentforge.errors import AFError
from agentforge.repository import Repository
from agentforge.runtime import Runtime
from agentforge.safety import atomic_json, canonical, digest, read_json, relative, safe_zip, tree
from agentforge.schema import Schemas, validate
from agentforge.semver import Version
from agentforge.sources import Source, build, download
from agentforge.transactions import Transactions

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = 'plugin:af-product-intelligence'
SKILL = 'skill:product-intelligence'
EXPORT = 'af-product-intelligence'


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='agentforge-test-')
        self.base = Path(self.temp.name)
        self.repo = self.base / 'source'
        self.repo.mkdir()
        for name in ('manifest.json', 'catalog', 'plugins', 'skills', 'adapters'):
            src = ROOT / name
            if src.is_dir():
                shutil.copytree(src, self.repo / name)
            else:
                shutil.copy2(src, self.repo / name)
        self.project = self.base / '项目 with spaces'
        self.project.mkdir()
        self.home = self.base / 'fake home'
        self.home.mkdir()
        self.catalog = self.base / 'catalog-source'
        self.counter = 0

    def tearDown(self):
        self.temp.cleanup()

    def runtime(self, scope='project', hook=None):
        return Runtime(self.project, scope, self.home, hook)

    def alter(self, version, channel='stable', mutate=None):
        for path in (self.repo / 'plugins/af-product-intelligence/plugin.json', self.repo / 'skills/product-intelligence/skill.json'):
            meta = read_json(path)
            meta['version'] = version
            meta['channel'] = channel
            if meta['kind'] == 'plugin':
                meta['skills'][0]['version'] = version
            if mutate:
                mutate(meta)
            atomic_json(path, meta)

    def publish(self, version='0.1.0', channel='stable', mutate=None):
        self.alter(version, channel, mutate)
        self.counter += 1
        out = self.base / ('build-' + str(self.counter))
        build(self.repo, out)
        if not self.catalog.exists():
            shutil.copytree(out, self.catalog)
        else:
            for artifact in (out / 'artifacts').iterdir():
                shutil.copy2(artifact, self.catalog / 'artifacts' / artifact.name)
            path = self.catalog / 'catalog/channels' / (channel + '.json')
            current = read_json(path)
            current['releases'] += read_json(out / 'catalog/channels' / (channel + '.json'))['releases']
            atomic_json(path, current)
        return self.catalog

    def install(self, runtime=None, source=None, key=PLUGIN):
        rt = runtime or self.runtime()
        return rt.execute(rt.prepare(key, source or self.catalog, install=True))

    def exports(self):
        return tree(self.project / '.agents/skills' / EXPORT)

    def assert_code(self, code, function, *args, **kwargs):
        with self.assertRaises(AFError) as error:
            function(*args, **kwargs)
        self.assertEqual(error.exception.code, code, str(error.exception))


class SchemaTests(Fixture):
    def test_schema_meta_and_valid_sources(self):
        self.assertEqual(len(Schemas().documents), 10)
        repo = Repository(self.repo)
        self.assertEqual(repo.closure(PLUGIN), [SKILL, PLUGIN])

    def test_unknown_fields_missing_and_empty(self):
        meta = read_json(self.repo / 'skills/product-intelligence/skill.json')
        for mutation in ('unknown', 'missing', 'empty', 'version'):
            broken = copy.deepcopy(meta)
            if mutation == 'unknown':
                broken['postInstall'] = 'unsafe'
            elif mutation == 'missing':
                del broken['permissions']
            elif mutation == 'empty':
                broken['description'] = ''
            else:
                broken['schemaVersion'] = 99
            self.assert_code(2, validate, 'skill', broken)

    def test_semver_precedence_and_invalid(self):
        values = ['1.0.0-alpha', '1.0.0-alpha.1', '1.0.0-alpha.beta', '1.0.0-beta', '1.0.0-beta.2', '1.0.0-beta.11', '1.0.0-rc.1', '1.0.0', '1.0.1', '1.10.0', '2.0.0']
        self.assertEqual(sorted(reversed(values), key=Version), values)
        self.assertEqual(Version('1.0.0+build'), Version('1.0.0+other'))
        for value in ('latest', '^1.0.0', '1.0', '01.0.0', '1.0.0-01', '*', 'https://x', '1.0.0\n'):
            self.assert_code(2, Version, value)

    def test_dependency_missing_cycle_version_and_duplicate(self):
        path = self.repo / 'skills/product-intelligence/skill.json'
        original = read_json(path)
        cases = [([{'kind': 'skill', 'id': 'missing', 'version': '0.1.0'}], 6),
                 ([{'kind': 'plugin', 'id': 'af-product-intelligence', 'version': '0.1.0'}], 6),
                 ([{'kind': 'skill', 'id': 'product-intelligence', 'version': '0.2.0'}], 6),
                 ([{'kind': 'skill', 'id': 'missing', 'version': '*'}], 2)]
        for deps, code in cases:
            meta = copy.deepcopy(original)
            meta['dependencies'] = deps
            atomic_json(path, meta)
            self.assert_code(code, Repository, self.repo)

    def test_paths_and_resource_links(self):
        for value in ('../outside', '/absolute', 'C:/x', 'a\\..\\b', '//host/share', 'CON', 'aux.txt', 'LPT1.md', 'a:stream', 'a/./b', 'a//b', 'a. ', 'a/' + 'b' * 101):
            self.assert_code(5, relative, value)
        self.assertEqual(relative('中文/with spaces.md'), '中文/with spaces.md')
        p = self.repo / 'skills/product-intelligence/SKILL.md'
        p.write_text(p.read_text(encoding='utf-8') + '\n[bad](../../outside.md)\n', encoding='utf-8')
        self.assert_code(5, Repository, self.repo)

    def test_deterministic_export_and_archive(self):
        a = Repository(self.repo)
        self.assertEqual(a.archive(), Repository(self.repo).archive())
        export = a.export(PLUGIN)[EXPORT]
        self.assertIn(b'name: af-product-intelligence\n', export['files']['SKILL.md'])
        self.assertEqual(export['files']['references/evidence.md'], (self.repo / 'skills/product-intelligence/references/evidence.md').read_bytes())
        self.assertNotIn('skill.json', export['files'])


class RuntimeTests(Fixture):
    def test_install_repeat_check_preview_and_locked_update_are_read_only(self):
        self.publish()
        (self.project / 'user.txt').write_text('keep')
        rt = self.runtime()
        installed = self.install(rt)
        self.assertTrue(installed['applied'])
        baseline = tree(self.project)
        self.assertFalse(self.install(rt)['applied'])
        self.assertEqual(rt.check()['updatesAvailable'], [])
        self.assertTrue(rt.prepare()[3]['noChange'])
        self.assertEqual(tree(self.project), baseline)
        self.publish('0.2.0')
        result = rt.check()
        self.assertEqual(result['updatesAvailable'][0]['available'], '0.2.0')
        self.assertEqual(result['pinned'], [PLUGIN])
        self.assertFalse(rt.execute(rt.prepare())['applied'])
        self.assertEqual(tree(self.project), baseline)
        self.assertEqual((self.project / 'user.txt').read_text(), 'keep')
        lock = read_json(self.project / 'agentforge.lock.json')
        self.assertNotIn(str(self.base), json.dumps(lock))

    def test_explicit_update_and_full_rollback(self):
        self.publish()
        rt = self.runtime()
        self.install(rt)
        old_exports = self.exports()
        old_lock = read_json(self.project / 'agentforge.lock.json')
        self.publish('0.2.0')
        self.assert_code(3, rt.prepare, PLUGIN, version='0.2.0')
        plan = rt.prepare(PLUGIN, version='0.2.0', update_lock=True)
        self.assertTrue(plan[3]['lockChanged'])
        tx = rt.execute(plan)['transaction']
        before_preview = tree(self.project)
        self.assertFalse(rt.tx.rollback(tx)['applied'])
        self.assertEqual(tree(self.project), before_preview)
        self.assertTrue(rt.tx.rollback(tx, True)['applied'])
        self.assertEqual(self.exports(), old_exports)
        self.assertEqual(read_json(self.project / 'agentforge.lock.json'), old_lock)

    def test_stable_selection_and_user_scope(self):
        self.publish()
        rt = self.runtime('user')
        self.install(rt)
        self.publish('0.2.0')
        self.publish('1.0.0-beta.1', 'preview')
        plan = rt.prepare()
        self.assertEqual(plan[3]['changes'][0]['to'], '0.2.0')
        self.assertTrue(rt.execute(plan)['applied'])
        self.assertFalse(any(p['pinned'] for p in rt.tx.snapshot()['lock']['packages']))
        self.assertFalse((self.project / '.agents').exists())

    def test_shared_plugin_skill_reference_and_conflict(self):
        self.publish()
        rt = self.runtime()
        self.install(rt, key=SKILL)
        self.install(rt)
        state = rt.tx.snapshot()['state']
        self.assertEqual(len(state['exports']), 1)
        self.assertEqual(state['exports'][0]['owners'], [PLUGIN, SKILL])
        self.assertEqual(len(state['lock']['packages']), 2)
        self.publish('0.2.0')
        self.assert_code(6, rt.prepare, PLUGIN, version='0.2.0', update_lock=True)

    def test_local_file_modification_addition_deletion_and_directory_type(self):
        for mode in ('modified', 'added', 'deleted', 'directory'):
            with self.subTest(mode=mode):
                target = self.base / ('target-' + mode)
                target.mkdir()
                rt = Runtime(target, user_home=self.home)
                if not self.catalog.exists():
                    self.publish()
                tx = self.install(rt)['transaction']
                folder = target / '.agents/skills' / EXPORT
                p = folder / 'SKILL.md'
                if mode == 'modified':
                    p.write_text('user edit')
                elif mode == 'added':
                    (folder / 'user.md').write_text('user notes')
                elif mode == 'deleted':
                    p.unlink()
                else:
                    p.unlink()
                    p.mkdir()
                baseline = tree(folder)
                self.assert_code(3, rt.prepare)
                self.assert_code(3, rt.tx.rollback, tx, True)
                self.assertEqual(tree(folder), baseline)

    def test_unmanaged_and_global_duplicate_names(self):
        self.publish()
        dest = self.project / '.agents/skills' / EXPORT
        dest.mkdir(parents=True)
        (dest / 'mine.md').write_text('user')
        self.assert_code(3, self.install)
        other = self.base / 'other-project'
        other.mkdir()
        global_skill = self.home / '.agents/skills' / 'different-folder'
        global_skill.mkdir(parents=True)
        (global_skill / 'SKILL.md').write_text('---\nname: af-product-intelligence\ndescription: user\n---\n')
        self.assert_code(3, self.install, Runtime(other, user_home=self.home))

    def test_source_mutation_integrity_and_missing_lock_version(self):
        self.publish()
        rt = self.runtime()
        self.install(rt)
        channel_path = self.catalog / 'catalog/channels/stable.json'
        channel = read_json(channel_path)
        path = self.catalog / channel['releases'][0]['artifact']['url']
        path.write_bytes(path.read_bytes() + b'tamper')
        self.assert_code(5, rt.prepare)
        atomic_json(channel_path, {'schemaVersion': 1, 'channel': 'stable', 'releases': []})
        self.assertEqual(rt.check(locked=True)['errors'][0]['code'], 6)
        self.assert_code(6, rt.prepare)

    def test_major_and_permission_escalation(self):
        def no_network(m):
            m['permissions']['network'] = False
        self.publish(mutate=no_network)
        rt = self.runtime('user')
        self.install(rt)
        self.publish('1.0.0')
        self.assert_code(6, rt.prepare)
        self.assertTrue(rt.execute(rt.prepare(PLUGIN, version='1.0.0'))['applied'])
        self.publish('1.1.0', mutate=lambda m: m['permissions'].update(network=True))
        self.assert_code(6, rt.prepare)
        self.assertTrue(rt.execute(rt.prepare(accept_permissions=True))['applied'])

    def test_incompatible_capabilities_runtime_and_platform(self):
        mutations = [lambda m: m['compatibility'].update(runtimeMajor=1),
                     lambda m: m['compatibility'].update(requiredCapabilities=['web-research']),
                     lambda m: m['compatibility'].update(platforms=['macos'] if sys.platform != 'darwin' else ['windows'])]
        for index, mutate in enumerate(mutations):
            source = self.base / ('incompatible-' + str(index))
            shutil.copytree(self.repo, source)
            for path in source.glob('**/skill.json'):
                meta = read_json(path)
                mutate(meta)
                atomic_json(path, meta)
            self.assert_code(6, self.install, source=source)

    def test_state_lock_and_schema_tampering(self):
        self.publish()
        rt = self.runtime()
        self.install(rt)
        p = self.project / 'agentforge.lock.json'
        lock = read_json(p)
        lock['packages'][0]['version'] = '0.9.0'
        atomic_json(p, lock)
        self.assert_code(7, rt.tx.snapshot)


class TransactionTests(Fixture):
    def test_concurrent_writer_refuses_before_switch(self):
        self.publish()
        rt = self.runtime()
        prepared = rt.prepare(PLUGIN, self.catalog, install=True)
        atomic_json(rt.tx.writer, {'transaction': '0' * 32, 'pid': os.getpid()})
        self.assert_code(7, rt.execute, prepared)
        self.assertFalse((self.project / '.agents').exists())

    def test_space_and_corrupt_backup_stop_without_changes(self):
        self.publish()
        rt = self.runtime()
        tx = self.install(rt)['transaction']
        baseline = self.exports()
        backup = rt.tx.home / 'transactions' / tx / 'backup'
        (backup / 'extra').write_text('corrupt')
        self.assert_code(7, rt.tx.rollback, tx, True)
        self.assertEqual(self.exports(), baseline)
        self.publish('0.2.0')
        prepared = rt.prepare(PLUGIN, version='0.2.0', update_lock=True)
        with patch('agentforge.transactions.shutil.disk_usage') as usage:
            usage.return_value.free = 0
            self.assert_code(7, rt.execute, prepared)
        self.assertEqual(self.exports(), baseline)

    def test_second_rename_failure_restores_previous_version(self):
        self.publish()
        rt = self.runtime()
        self.install(rt)
        lock = copy.deepcopy(rt.tx.snapshot()['lock'])
        self.publish('0.2.0')
        original = Path.rename
        def deny_candidate(path, target):
            if path.parent.name == 'candidate':
                raise PermissionError('simulated Windows sharing violation')
            return original(path, target)
        prepared = rt.prepare(PLUGIN, version='0.2.0', update_lock=True)
        with patch.object(Path, 'rename', deny_candidate):
            self.assert_code(7, rt.execute, prepared)
        self.assertEqual(rt.tx.snapshot()['lock'], lock)
        self.assertEqual(rt.tx.conflicts(rt.tx.snapshot()['state']), [])
        self.assertEqual(rt.tx.unfinished(), [])

    def test_toctou_live_edit_after_backup_is_preserved(self):
        self.publish()
        rt = self.runtime()
        self.install(rt)
        self.publish('0.2.0')
        def edit(phase):
            if phase == 'backed_up':
                (self.project / '.agents/skills' / EXPORT / 'notes.md').write_text('user wrote this')
        guarded = self.runtime(hook=edit)
        prepared = guarded.prepare(PLUGIN, version='0.2.0', update_lock=True)
        self.assert_code(3, guarded.execute, prepared)
        self.assertEqual((self.project / '.agents/skills' / EXPORT / 'notes.md').read_text(), 'user wrote this')

    def test_abrupt_process_exit_at_every_mutable_phase_and_recover(self):
        self.publish()
        self.publish('0.2.0')
        phases = ['planned', 'staged', 'backed_up', 'switching', 'old_renamed:' + EXPORT, 'new_renamed:' + EXPORT, 'state_written', 'committed']
        for index, phase in enumerate(phases):
            with self.subTest(phase=phase):
                project = self.base / ('crash-' + str(index))
                project.mkdir()
                rt = Runtime(project, user_home=self.home)
                rt.execute(rt.prepare(PLUGIN, self.catalog, install=True, version='0.1.0'))
                old_lock = rt.tx.snapshot()['lock']
                script = ('import os,sys; from agentforge.runtime import Runtime; '
                          'r=Runtime(sys.argv[1], user_home=sys.argv[2], hook=lambda p: os._exit(89) if p==sys.argv[3] else None); '
                          "r.execute(r.prepare('plugin:af-product-intelligence', version='0.2.0', update_lock=True))")
                proc = subprocess.run([sys.executable, '-c', script, str(project), str(self.home), phase], cwd=ROOT, capture_output=True)
                self.assertEqual(proc.returncode, 89, proc.stderr.decode())
                owner = read_json(rt.tx.writer)
                self.assertFalse(rt.tx.recover(owner['transaction'])['applied'])
                self.assertTrue(rt.tx.recover(owner['transaction'], True)['applied'])
                self.assertFalse(rt.tx.writer.exists())
                self.assertEqual(rt.tx.conflicts(rt.tx.snapshot()['state']), [])
                if phase != 'committed':
                    self.assertEqual(rt.tx.snapshot()['lock'], old_lock)
                else:
                    self.assertEqual(rt.tx.snapshot()['lock']['packages'][0]['version'], '0.2.0')

    def test_recovery_live_edits_fail_closed(self):
        self.publish()
        rt = self.runtime()
        self.install(rt)
        self.publish('0.2.0')
        script = ('import os,sys; from agentforge.runtime import Runtime; '
                  "r=Runtime(sys.argv[1], user_home=sys.argv[2], hook=lambda p: os._exit(89) if p=='state_written' else None); "
                  "r.execute(r.prepare('plugin:af-product-intelligence', version='0.2.0', update_lock=True))")
        subprocess.run([sys.executable, '-c', script, str(self.project), str(self.home)], cwd=ROOT, check=False)
        tx = read_json(rt.tx.writer)['transaction']
        p = self.project / '.agents/skills' / EXPORT / 'user.md'
        p.write_text('must survive')
        self.assert_code(3, rt.tx.recover, tx, True)
        self.assertEqual(p.read_text(), 'must survive')


class ArchiveAndNetworkTests(Fixture):
    def archive(self, items):
        b = io.BytesIO()
        with zipfile.ZipFile(b, 'w') as z:
            for name, content, mode in items:
                info = zipfile.ZipInfo(name)
                info.create_system = 3
                info.external_attr = mode << 16
                z.writestr(info, content)
        return b.getvalue()

    def test_archive_traversal_links_special_collisions_and_bombs(self):
        cases = [[('../escape', b'x', 0o100644)], [('C:/escape', b'x', 0o100644)],
                 [('link', b'outside', stat.S_IFLNK | 0o777)], [('pipe', b'', stat.S_IFIFO | 0o600)],
                 [('a.md', b'a', 0o100644), ('A.md', b'b', 0o100644)],
                 [('a', b'a', 0o100644), ('a/b', b'b', 0o100644)],
                 [('a', b'x' * (2 * 1024 * 1024 + 1), 0o100644)]]
        for index, items in enumerate(cases):
            self.assert_code(5, safe_zip, self.archive(items), self.base / ('bad-' + str(index)))
        b = io.BytesIO()
        with zipfile.ZipFile(b, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('bomb', b'a' * 1024 * 1024)
        self.assert_code(5, safe_zip, b.getvalue(), self.base / 'bomb')
        self.assertFalse((self.base / 'escape').exists())

    def test_hardlink_and_symlink_tree_escape(self):
        outside = self.base / 'outside'
        outside.write_text('preserve')
        testdir = self.base / 'links'
        testdir.mkdir()
        os.link(outside, testdir / 'hard')
        self.assert_code(5, tree, testdir)
        (testdir / 'hard').unlink()
        try:
            (testdir / 'sym').symlink_to(outside)
        except OSError:
            self.skipTest('OS does not permit symlink creation')
        self.assert_code(5, tree, testdir)

    def test_network_errors_no_sensitive_exception_echo(self):
        for err in (urllib.error.HTTPError('https://token@host', 401, 'secret', {}, None),
                    urllib.error.HTTPError('https://token@host', 403, 'secret', {}, None), TimeoutError('secret')):
            with patch('urllib.request.OpenerDirector.open', side_effect=err):
                with self.assertRaises(AFError) as caught:
                    download('https://api.github.com/repos/a/b')
                self.assertEqual(caught.exception.code, 4)
                self.assertNotIn('secret', str(caught.exception))
                self.assertNotIn('token', str(caught.exception))

    def test_remote_catalog_check_does_not_fetch_artifact_and_rejects_source_change(self):
        self.publish()
        commit = 'a' * 40
        repo_url = 'https://github.com/example/skills'
        base = 'https://raw.githubusercontent.com/example/skills/' + commit + '/'
        index = read_json(self.catalog / 'catalog/index.json')
        channel = read_json(self.catalog / 'catalog/channels/stable.json')
        files = {base + 'catalog/index.json': canonical(index)}
        for e in channel['releases']:
            local_url = e['artifact']['url']
            e['source'].update(kind='git', repository=repo_url, revision=commit)
            e['artifact']['url'] = base + local_url
            files[base + local_url] = (self.catalog / local_url).read_bytes()
        files[base + 'catalog/channels/stable.json'] = canonical(channel)
        calls = []
        def fetch(url, limit=None):
            calls.append(url)
            return files[url]
        rt = self.runtime()
        with patch('agentforge.sources.download', side_effect=fetch):
            self.install(rt, source=repo_url + '#' + commit)
            calls.clear()
            self.assertEqual(rt.check()['errors'], [])
            self.assertFalse(any('/artifacts/' in u for u in calls))
            altered = copy.deepcopy(channel)
            altered['releases'][0]['artifact']['url'] = 'https://evil.example/package.zip'
            files[base + 'catalog/channels/stable.json'] = canonical(altered)
            self.assert_code(5, rt.prepare)


if __name__ == '__main__':
    unittest.main()
