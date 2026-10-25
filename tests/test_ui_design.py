"""Portable resources and evaluator/input separation; not model behavior tests."""
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

from test_skill_creator import validate_inputs, validate_resources


SKILL = Path(__file__).resolve().parents[1] / "skills/af-ui-design"


class UiDesignMaterials(unittest.TestCase):
    def test_complete_copy_keeps_resources_inside_skill(self):
        with TemporaryDirectory() as directory:
            copied = Path(directory) / SKILL.name
            shutil.copytree(SKILL, copied)
            validate_resources(copied)

    def test_executor_inputs_are_raw_fixtures(self):
        validate_inputs(SKILL)


if __name__ == "__main__":
    unittest.main()
