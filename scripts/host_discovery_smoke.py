"""Read-only Codex app-server discovery probe against an isolated project install.

Does not start a model turn or claim behavioral invocation. Saves only this skill's result.
"""
import json
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agentforge.runtime import Runtime
from agentforge.safety import atomic_json


def main():
    codex = shutil.which('codex.cmd') if os.name == 'nt' else shutil.which('codex')
    if not codex:
        raise SystemExit('Codex CLI is unavailable')
    with tempfile.TemporaryDirectory(prefix='agentforge-host-') as folder:
        project = Path(folder)
        subprocess.run(['git', 'init', '-q', str(project)], check=True)
        rt = Runtime(project)
        rt.execute(rt.prepare('plugin:af-product-intelligence', ROOT, install=True))
        process = subprocess.Popen([codex, 'app-server', '--stdio'], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                   text=True, encoding='utf-8', cwd=project)
        messages = queue.Queue()
        def reader():
            for line in process.stdout:
                try:
                    messages.put(json.loads(line))
                except ValueError:
                    pass
        threading.Thread(target=reader, daemon=True).start()
        def send(message):
            process.stdin.write(json.dumps(message) + '\n')
            process.stdin.flush()
        def receive(identifier):
            deadline = time.monotonic() + 35
            while time.monotonic() < deadline:
                try:
                    message = messages.get(timeout=1)
                except queue.Empty:
                    continue
                if message.get('id') == identifier:
                    if 'error' in message:
                        raise RuntimeError('Codex RPC failed: ' + str(message['error'].get('code')))
                    return message['result']
            raise TimeoutError('Codex discovery timed out')
        try:
            send({'id': 1, 'method': 'initialize', 'params': {'clientInfo': {'name': 'agentforge-validation', 'version': '0.1.0'}}})
            receive(1)
            send({'method': 'initialized'})
            send({'id': 2, 'method': 'skills/list', 'params': {'cwds': [str(project)], 'forceReload': True}})
            result = receive(2)
            found = []
            for group in result.get('data', []):
                for skill in group.get('skills', []):
                    if skill.get('name') == 'af-product-intelligence':
                        found.append({'name': skill['name'], 'scope': skill.get('scope'), 'enabled': skill.get('enabled'),
                                      'pathMatchesExport': Path(skill.get('path', '')).resolve() == (project / '.agents/skills/af-product-intelligence/SKILL.md').resolve()})
            report = {'codexVersion': subprocess.check_output([codex, '--version'], text=True).strip(),
                      'method': 'skills/list forceReload', 'found': found,
                      'discoveryPassed': len(found) == 1 and found[0]['pathMatchesExport'] and found[0]['enabled'],
                      'modelInvocation': 'not-run', 'globalSkillsWritten': False}
            atomic_json(ROOT / 'docs/evidence/host-discovery.json', report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0 if report['discoveryPassed'] else 1
        finally:
            process.stdin.close()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=5)


if __name__ == '__main__':
    raise SystemExit(main())
