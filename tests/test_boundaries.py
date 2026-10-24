import copy
import http.client
import io
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path
from unittest.mock import patch

from test_agentforge import Fixture, ROOT, PLUGIN, SKILL, EXPORT
from agentforge.cli import main
from agentforge.errors import AFError
from agentforge.repository import Repository
from agentforge.runtime import Runtime
from agentforge.safety import atomic_json, canonical, digest, parse_json, read_json, tree
from agentforge.sources import NoRedirect, Source, download


class BoundaryTests(Fixture):
    def test_no_target_no_install_and_cli_errors(self):
        for argv in (['install'], ['skill', 'install'], ['update', '--locked', '--apply', '--project', str(self.project)]):
            with patch('sys.stdout', new_callable=io.StringIO), patch('sys.stderr', new_callable=io.StringIO):
                try:
                    code = main(argv)
                except SystemExit as exc:
                    code = exc.code
            self.assertEqual(code, 2)
        self.assertFalse((self.project / '.agentforge').exists())

    def test_json_output_and_readonly_check_doctor_in_empty_target(self):
        baseline = tree(self.project)
        for command in ('check', 'doctor'):
            with patch('sys.stdout', new_callable=io.StringIO) as output:
                code = main([command, '--project', str(self.project), '--json'])
            self.assertEqual(code, 0)
            self.assertTrue(json.loads(output.getvalue())['readOnly'])
        self.assertEqual(tree(self.project), baseline)

    def test_duplicate_json_keys_and_nonfinite_values(self):
        for value in (b'{"schemaVersion":1,"schemaVersion":2}', b'{"value":NaN}'):
            self.assert_code(2, parse_json, value)

    def test_build_candidate_is_unpublished_and_never_overwrites(self):
        from agentforge.sources import build
        dest = self.base / 'candidate'
        result = build(self.repo, dest)
        self.assertFalse(result['published'])
        before = tree(dest)
        self.assert_code(3, build, self.repo, dest)
        self.assertEqual(tree(dest), before)
        self.assertEqual(read_json(self.repo / 'catalog/channels/stable.json')['releases'], [])

    def test_workspace_same_version_byte_changes_fail_closed(self):
        rt = self.runtime()
        self.install(rt, self.repo)
        path = self.repo / 'skills/product-intelligence/references/evidence.md'
        path.write_text(path.read_text(encoding='utf-8') + '\nnew content\n', encoding='utf-8')
        self.assert_code(5, rt.prepare)

    def test_source_identity_replacement_is_not_silently_trusted(self):
        self.publish()
        rt = self.runtime()
        self.install(rt)
        other = self.base / 'another-source'
        import shutil
        shutil.copytree(self.catalog, other)
        self.assert_code(5, rt.prepare, PLUGIN, other, install=True)

    def test_same_version_source_revision_and_scope_cannot_change(self):
        self.publish()
        rt = self.runtime()
        self.install(rt)
        path = self.catalog / 'catalog/channels/stable.json'
        doc = read_json(path)
        doc['releases'][0]['source']['revision'] = 'b' * 40
        atomic_json(path, doc)
        self.assert_code(5, rt.prepare)
        self.assertEqual(rt.check(locked=True)['errors'][0]['code'], 5)
        self.assert_code(3, Runtime(user_home=self.project, scope='user').check)

    def test_catalog_semver_channel_duplicate_and_source_revision(self):
        self.publish()
        path = self.catalog / 'catalog/channels/stable.json'
        original = read_json(path)
        for mutation in ('duplicate', 'prerelease', 'channel', 'bad-version'):
            doc = copy.deepcopy(original)
            if mutation == 'duplicate':
                doc['releases'].append(copy.deepcopy(doc['releases'][0]))
            elif mutation == 'prerelease':
                doc['releases'][0]['version'] = '1.0.0-beta.1'
            elif mutation == 'channel':
                doc['releases'][0]['channel'] = 'preview'
            else:
                doc['releases'][0]['version'] = '1.2.*'
            atomic_json(path, doc)
            self.assert_code(2 if mutation == 'bad-version' else 5, Source(self.catalog).select, PLUGIN)

    def test_catalog_artifact_identity_mismatch_and_digest_mismatch(self):
        self.publish()
        self.publish('0.2.0')
        path = self.catalog / 'catalog/channels/stable.json'
        original = read_json(path)
        doc = copy.deepcopy(original)
        new = next(e for e in doc['releases'] if e['kind'] == 'plugin' and e['version'] == '0.2.0')
        old = next(e for e in doc['releases'] if e['kind'] == 'plugin' and e['version'] == '0.1.0')
        new['artifact'] = old['artifact']
        atomic_json(path, doc)
        self.assert_code(5, self.install)
        doc = copy.deepcopy(original)
        for e in doc['releases']:
            e['artifact']['sha256'] = '0' * 64
        atomic_json(path, doc)
        self.assert_code(5, self.install)
        self.assertFalse((self.project / '.agents').exists())

    def test_unsupported_schema_adapter_hook_and_stable_prerelease(self):
        path = self.repo / 'adapters/codex/adapter.json'
        adapter = read_json(path)
        adapter['capabilities'].append('web-research')
        atomic_json(path, adapter)
        self.assert_code(2, Repository, self.repo)

    def test_redirect_and_interrupted_response(self):
        self.assert_code(5, NoRedirect().redirect_request, None, None, 302, '', {}, 'https://evil.example')
        err = http.client.IncompleteRead(b'partial', 200)
        with patch('urllib.request.OpenerDirector.open', side_effect=err):
            self.assert_code(4, download, 'https://api.github.com/example')

    def test_external_edit_during_planning_detected_before_switch(self):
        self.publish()
        rt = self.runtime()
        self.install(rt)
        self.publish('0.2.0')
        prepared = rt.prepare(PLUGIN, version='0.2.0', update_lock=True)
        p = self.project / '.agents/skills' / EXPORT / 'SKILL.md'
        p.write_text('edited after preview')
        self.assert_code(3, rt.execute, prepared)
        self.assertEqual(p.read_text(), 'edited after preview')

    def test_stale_plan_after_another_commit(self):
        self.publish()
        rt = self.runtime()
        prepared = rt.prepare(PLUGIN, self.catalog, install=True)
        self.install(rt)
        self.assert_code(3, rt.execute, prepared)

    def test_restore_failure_marks_recovery_and_retains_writer(self):
        self.publish()
        rt = self.runtime()
        self.install(rt)
        self.publish('0.2.0')
        def failure(phase):
            if phase == 'new_renamed:' + EXPORT:
                raise OSError('fault')
        guarded = self.runtime(hook=failure)
        prepared = guarded.prepare(PLUGIN, version='0.2.0', update_lock=True)
        with patch.object(guarded.tx, '_restore', side_effect=PermissionError('locked')):
            self.assert_code(7, guarded.execute, prepared)
        self.assertTrue(guarded.tx.writer.exists())
        self.assertEqual(guarded.tx.unfinished()[0]['phase'], 'recovery_required')
        owner = read_json(guarded.tx.writer)
        self.assert_code(7, guarded.tx.recover, owner['transaction'], True)

    def test_foreign_journal_target_and_corrupt_backup_rejected(self):
        self.publish()
        rt = self.runtime()
        tx = self.install(rt)['transaction']
        path = rt.tx.home / 'transactions' / tx / 'journal.json'
        journal = read_json(path)
        journal['targetRoot'] = str(self.base / 'other')
        atomic_json(path, journal)
        self.assert_code(7, rt.tx.rollback, tx, True)
        self.assert_code(7, rt.tx.recover, tx, True)

    def test_rollback_older_transaction_requires_reverse_order(self):
        self.publish()
        rt = self.runtime()
        first = self.install(rt)['transaction']
        self.publish('0.2.0')
        rt.execute(rt.prepare(PLUGIN, version='0.2.0', update_lock=True))
        self.assert_code(7, rt.tx.rollback, first, True)

    def test_multiple_updates_can_be_rolled_back_in_reverse(self):
        self.publish()
        rt = self.runtime()
        self.install(rt)
        self.publish('0.2.0')
        second = rt.execute(rt.prepare(PLUGIN, version='0.2.0', update_lock=True))['transaction']
        self.publish('0.3.0')
        third = rt.execute(rt.prepare(PLUGIN, version='0.3.0', update_lock=True))['transaction']
        rt.tx.rollback(third, True)
        rt.tx.rollback(second, True)
        self.assertEqual(rt.tx.snapshot()['lock']['packages'][0]['version'], '0.1.0')

    def test_recovery_itself_can_crash_and_resume(self):
        self.publish()
        rt = self.runtime()
        self.install(rt)
        self.publish('0.2.0')
        crash_update = ('import os,sys; from agentforge.runtime import Runtime; '
                        "r=Runtime(sys.argv[1],user_home=sys.argv[2],hook=lambda p: os._exit(89) if p=='state_written' else None); "
                        "r.execute(r.prepare('plugin:af-product-intelligence',version='0.2.0',update_lock=True))")
        subprocess.run([sys.executable, '-c', crash_update, str(self.project), str(self.home)], cwd=ROOT)
        tx = read_json(rt.tx.writer)['transaction']
        crash_recovery = ('import os,sys; from agentforge.transactions import Transactions; '
                          "t=Transactions(sys.argv[1],hook=lambda p: os._exit(90) if p=='restoring' else None); t.recover(sys.argv[2],True)")
        process = subprocess.run([sys.executable, '-c', crash_recovery, str(self.project), tx], cwd=ROOT)
        self.assertEqual(process.returncode, 90)
        self.assertTrue((rt.tx.home / 'recover.lock').exists())
        rt.tx.recover(tx, True)
        self.assertEqual(rt.tx.snapshot()['lock']['packages'][0]['version'], '0.1.0')
        self.assertFalse((rt.tx.home / 'recover.lock').exists())

    def test_windows_junction_rejected_without_touching_target(self):
        if os.name != 'nt':
            self.skipTest('Windows-only reparse-point scenario')
        from agentforge.safety import no_links
        outside = self.base / 'junction-destination'
        outside.mkdir()
        (outside / 'keep.txt').write_text('keep')
        junction = self.project / 'junction'
        proc = subprocess.run(['cmd', '/c', 'mklink', '/J', str(junction), str(outside)], capture_output=True)
        if proc.returncode:
            self.skipTest('Windows junction creation unavailable')
        try:
            self.assert_code(5, no_links, junction / 'keep.txt')
            self.assertEqual((outside / 'keep.txt').read_text(), 'keep')
        finally:
            os.rmdir(junction)
