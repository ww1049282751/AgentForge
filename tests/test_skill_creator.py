"""Skill-local portability and raw-input isolation, not model behavior tests."""
import importlib.util
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/af-skill-creator"
spec = importlib.util.spec_from_file_location("creator_links", ROOT / "scripts/check_docs.py")
links = importlib.util.module_from_spec(spec)
spec.loader.exec_module(links)


def validate_resources(skill):
    skill = skill.resolve()
    if not (skill / "SKILL.md").is_file():
        raise ValueError("Missing skill entry")
    for document in skill.rglob("*.md"):
        for link in links.markdown_destinations(document.read_text(encoding="utf-8")):
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (document.parent / unquote(parsed.path)).resolve()
            if not target.is_relative_to(skill) or not target.is_file():
                raise ValueError(f"Missing or nonportable resource: {link}")


def validate_inputs(skill):
    evaluation = skill / "evals"
    cases = json.loads((evaluation / "scenarios.json").read_text(encoding="utf-8"))["cases"]
    fixtures = (evaluation / "fixtures").resolve()
    for case in cases:
        # No-input tasks are valid. Any supplied input must be raw material.
        for name in case.get("inputFiles", []):
            material = (evaluation / name).resolve()
            if not material.is_relative_to(fixtures) or not material.is_file():
                raise ValueError(f"Missing or non-fixture executor input: {name}")


class SkillCreatorMaterials(unittest.TestCase):
    def copy_skill(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        copied = Path(directory.name) / "af-skill-creator"
        shutil.copytree(SKILL, copied)
        return copied

    def test_complete_copy_keeps_resources_inside_skill(self):
        validate_resources(self.copy_skill())

    def test_missing_resource_is_detected(self):
        copied = self.copy_skill()
        (copied / "templates/skill-spec.md").unlink()
        with self.assertRaisesRegex(ValueError, "Missing or nonportable"):
            validate_resources(copied)

    def test_existing_file_outside_skill_is_rejected(self):
        copied = self.copy_skill()
        (copied.parent / "outside.md").write_text("Private file", encoding="utf-8")
        with (copied / "SKILL.md").open("a", encoding="utf-8") as stream:
            stream.write("\n[external dependency](../outside.md)\n")
        with self.assertRaisesRegex(ValueError, "Missing or nonportable"):
            validate_resources(copied)

    def test_executor_inputs_are_raw_fixtures(self):
        validate_inputs(self.copy_skill())

    def test_review_instructions_cannot_be_executor_input(self):
        copied = self.copy_skill()
        path = copied / "evals/scenarios.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["cases"][0]["inputFiles"] = ["README.md"]
        path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "non-fixture"):
            validate_inputs(copied)

    def test_missing_raw_input_is_detected(self):
        copied = self.copy_skill()
        (copied / "evals/fixtures/handoff-need.md").unlink()
        with self.assertRaisesRegex(ValueError, "Missing or non-fixture"):
            validate_inputs(copied)


if __name__ == "__main__":
    unittest.main()
