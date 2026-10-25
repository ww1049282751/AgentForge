"""Checks for this skill's specific example, not requirements for all skills."""
import importlib.util
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('skill_document_links', ROOT / 'scripts/check_docs.py')
links = importlib.util.module_from_spec(spec)
spec.loader.exec_module(links)


class ProductIntelligenceExamples(unittest.TestCase):
    def test_skill_local_resources_are_portable(self):
        skill = (ROOT / 'skills/af-product-intelligence').resolve()
        for document in skill.rglob('*.md'):
            for link in links.markdown_destinations(document.read_text(encoding='utf-8')):
                parsed = urlsplit(link)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                target = (document.parent / unquote(parsed.path)).resolve()
                with self.subTest(document=document.name, link=link):
                    self.assertTrue(target.is_relative_to(skill), 'Skill depends on a file outside its folder')
                    self.assertTrue(target.exists(), 'Skill resource is missing')

    def test_example_claims_map_to_the_ledger(self):
        folder = ROOT / 'skills/af-product-intelligence/examples'
        ledger = (folder / 'evidence-ledger.md').read_text(encoding='utf-8')
        brief = (folder / 'decision-brief.md').read_text(encoding='utf-8')
        claims = re.findall(r'^\| (C\d+) \|', ledger, re.M)
        cited = set(re.findall(r'\[(C\d+)\]', brief))
        self.assertTrue(claims, 'Example ledger has no claims')
        self.assertEqual(len(claims), len(set(claims)), 'Duplicate claim IDs')
        self.assertEqual(cited, set(claims), 'Example claims and ledger differ')


if __name__ == '__main__':
    unittest.main()
