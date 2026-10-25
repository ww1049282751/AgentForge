"""Skill-local copy and raw-input checks; these do not test model behavior."""
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

# Existing validators are skill-parameterized and have fault-injection coverage.
# Reuse them without changing the generic checker or other skills' standards.
from test_skill_creator import validate_inputs, validate_resources


SKILL = Path(__file__).resolve().parents[1] / "skills/af-architecture-design"


class ArchitectureDesignMaterials(unittest.TestCase):
    def test_complete_copy_keeps_resources_inside_skill(self):
        with TemporaryDirectory() as directory:
            copied = Path(directory) / SKILL.name
            shutil.copytree(SKILL, copied)
            validate_resources(copied)

    def test_executor_inputs_are_raw_fixtures(self):
        validate_inputs(SKILL)


if __name__ == "__main__":
    unittest.main()
