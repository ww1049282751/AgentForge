"""Portability and evaluation-input boundaries for af-product-deep-dive materials."""
import importlib.util
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/af-product-deep-dive"
spec = importlib.util.spec_from_file_location("deep_dive_links", ROOT / "scripts/check_docs.py")
links = importlib.util.module_from_spec(spec)
spec.loader.exec_module(links)


class ProductDeepDiveMaterials(unittest.TestCase):
    def test_complete_copy_keeps_resources_inside_skill(self):
        with TemporaryDirectory() as directory:
            copied = Path(directory) / "af-product-deep-dive"
            shutil.copytree(SKILL, copied)
            for document in copied.rglob("*.md"):
                for link in links.markdown_destinations(document.read_text(encoding="utf-8")):
                    parsed = urlsplit(link)
                    if parsed.scheme or parsed.netloc or not parsed.path:
                        continue
                    target = (document.parent / unquote(parsed.path)).resolve()
                    with self.subTest(document=document.relative_to(copied), link=link):
                        self.assertTrue(target.is_relative_to(copied.resolve()))
                        self.assertTrue(target.is_file())

    def test_executor_inputs_do_not_include_review_or_example_answers(self):
        evaluation = SKILL / "evals"
        cases = json.loads((evaluation / "scenarios.json").read_text(encoding="utf-8"))["cases"]
        for case in cases:
            if not case["shouldTrigger"]:
                continue
            with self.subTest(case=case["id"]):
                self.assertTrue(case.get("inputFiles"))
                for name in case["inputFiles"]:
                    material = (evaluation / name).resolve()
                    self.assertTrue(material.is_relative_to((evaluation / "fixtures").resolve()))
                    self.assertTrue(material.is_file())


if __name__ == "__main__":
    unittest.main()
