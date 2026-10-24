"""Check repository-local Markdown targets and synthetic evidence linkage.

This is structural validation, never a semantic/model evaluation.
"""
import json
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def main():
    files = [ROOT / 'README.md', ROOT / 'CHANGELOG.md']
    for folder in ('docs', 'skills', 'examples', 'tests/skill-evals'):
        files.extend((ROOT / folder).rglob('*.md'))
    checked = 0
    for path in files:
        text = path.read_text(encoding='utf-8')
        for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)', text):
            if '://' in link or link.startswith('#'):
                continue
            target = (path.parent / unquote(link.split('#', 1)[0])).resolve()
            if not target.is_relative_to(ROOT) or not target.exists():
                raise SystemExit(f'Broken link: {path.relative_to(ROOT)} -> {link}')
            checked += 1
    folder = ROOT / 'examples/product-intelligence'
    brief = (folder / 'decision-brief.md').read_text(encoding='utf-8')
    ledger = (folder / 'evidence-ledger.md').read_text(encoding='utf-8')
    claims = re.findall(r'^\| (C\d+) \|', ledger, re.M)
    cited = set(re.findall(r'\[(C\d+)\]', brief))
    if len(claims) != len(set(claims)) or cited != set(claims):
        raise SystemExit('Evidence ledger/brief claim mapping mismatch')
    cases = json.loads((ROOT / 'tests/skill-evals/scenarios.json').read_text(encoding='utf-8'))['cases']
    if len(cases) != 10 or len({c['id'] for c in cases}) != 10 or not any(not c['shouldTrigger'] for c in cases):
        raise SystemExit('Skill scenarios are incomplete')
    print(json.dumps({'markdownFiles': len(files), 'localLinks': checked,
                      'syntheticClaimsMapped': len(claims), 'skillScenarios': len(cases),
                      'semanticOrModelEvaluation': False}, indent=2))


if __name__ == '__main__':
    main()
