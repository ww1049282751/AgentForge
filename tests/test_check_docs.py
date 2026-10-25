import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('collection_check', root / 'scripts/check_docs.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class CollectionChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='personal-skill-check-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        self.root.mkdir()
        for name in ('README.md', 'AGENTS.md', 'CHANGELOG.md'):
            (self.root / name).write_text('# Notes\n', encoding='utf-8')
        self.skill = self.add_skill('example-skill')

    def add_skill(self, name):
        folder = self.root / 'skills' / name
        folder.mkdir(parents=True)
        (folder / 'SKILL.md').write_text(
            f'---\nname: {name}\ndescription: A specific reusable task\n---\n\n# Skill\n',
            encoding='utf-8')
        return folder

    def write_cases(self, cases):
        path = self.skill / 'evals/scenarios.json'
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps({'cases': cases}), encoding='utf-8')

    def case(self, case_id, trigger=True):
        return {'id': case_id, 'request': 'A real task shape', 'shouldTrigger': trigger,
                'expected': ['Preserve task scope']}

    def test_minimal_skill_needs_no_examples_or_evals(self):
        result = checker.check_repo(self.root)
        self.assertEqual((result['skills'], result['skillScenarios']), (1, 0))

    def test_multiple_skills_without_registry(self):
        self.add_skill('another-skill')
        self.assertEqual(checker.check_repo(self.root)['skills'], 2)

    def test_missing_entry_is_rejected(self):
        (self.root / 'skills/incomplete').mkdir()
        with self.assertRaisesRegex(ValueError, 'Missing entry'):
            checker.check_repo(self.root)

    def test_name_mismatch_is_rejected(self):
        path = self.skill / 'SKILL.md'
        path.write_text(path.read_text().replace('name: example-skill', 'name: other'), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'differs from directory'):
            checker.check_repo(self.root)

    def test_empty_description_is_rejected(self):
        path = self.skill / 'SKILL.md'
        path.write_text(path.read_text().replace('A specific reusable task', ''), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'description must be'):
            checker.check_repo(self.root)

    def test_missing_file_link_is_rejected(self):
        (self.root / 'README.md').write_text('[missing](missing.md)', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Broken or external local link'):
            checker.check_repo(self.root)

    def test_link_outside_repository_is_rejected(self):
        (self.root.parent / 'private.md').write_text('private', encoding='utf-8')
        (self.root / 'README.md').write_text('[outside](../private.md)', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Broken or external local link'):
            checker.check_repo(self.root)

    def test_private_working_materials_are_not_scanned(self):
        private = self.root / '.local/skill-evals'
        private.mkdir(parents=True)
        (private / 'raw.md').write_text('[untrusted](does-not-exist.md)', encoding='utf-8')
        self.assertEqual(checker.check_repo(self.root)['markdownFiles'], 4)

    def test_scenario_count_is_not_fixed_to_ten(self):
        self.write_cases([self.case('one'), self.case('negative', False)])
        self.assertEqual(checker.check_repo(self.root)['skillScenarios'], 2)

    def test_duplicate_scenario_ids_are_rejected(self):
        self.write_cases([self.case('one'), self.case('one')])
        with self.assertRaisesRegex(ValueError, 'duplicate scenario id'):
            checker.check_repo(self.root)

    def test_non_boolean_trigger_flag_is_rejected(self):
        self.write_cases([self.case('one', 'yes')])
        with self.assertRaisesRegex(ValueError, 'Invalid trigger flag'):
            checker.check_repo(self.root)

    def test_standalone_examples_have_no_product_research_format_requirement(self):
        folder = self.skill / 'examples'
        folder.mkdir()
        for name in ('decision-brief.md', 'evidence-ledger.md'):
            with self.subTest(name=name):
                path = folder / name
                path.write_text('A standalone example.\n', encoding='utf-8')
                checker.check_repo(self.root)
                path.unlink()  # Temporary fixture only.

    def test_code_examples_are_not_links(self):
        examples = [
            '```markdown\n[example](missing.md)\n```\n',
            '~~~~\n[example](missing.md)\n~~~~\n',
            '````markdown\n```\n[example](missing.md)\n````\n',
            'Use `[example](missing.md)` as syntax.\n',
            'Use ``a ` backtick and [example](missing.md)``.\n',
            '    [example](missing.md)\n',
            '<!-- [example](missing.md) -->\n',
        ]
        for text in examples:
            with self.subTest(text=text):
                (self.root / 'README.md').write_text(text, encoding='utf-8')
                self.assertEqual(checker.check_repo(self.root)['localLinks'], 0)

    def test_real_link_after_code_is_still_checked(self):
        text = '```\n[example](ignored.md)\n```\n[real](missing.md)'
        (self.root / 'README.md').write_text(text, encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'missing.md'):
            checker.check_repo(self.root)

    def test_link_titles_are_not_part_of_file_names(self):
        (self.root / 'guide.md').write_text('# Guide\n', encoding='utf-8')
        for title in ('"A title"', "'A title'", '(A title)'):
            with self.subTest(title=title):
                (self.root / 'README.md').write_text(f'[guide](guide.md {title})', encoding='utf-8')
                self.assertEqual(checker.check_repo(self.root)['localLinks'], 1)

    def test_titled_broken_link_is_rejected(self):
        (self.root / 'README.md').write_text('[guide](missing.md "A title")', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'missing.md'):
            checker.check_repo(self.root)

    def test_angle_paths_spaces_unicode_and_percent_encoding(self):
        folder = self.root / '资料 文件'
        folder.mkdir()
        (folder / 'guide.md').write_text('# Guide\n', encoding='utf-8')
        for text in ('[guide](<资料 文件/guide.md> "Title")', '[guide](资料%20文件/guide.md#section)'):
            with self.subTest(text=text):
                (self.root / 'README.md').write_text(text, encoding='utf-8')
                self.assertEqual(checker.check_repo(self.root)['localLinks'], 1)

    def test_balanced_and_escaped_parentheses(self):
        for filename, link in [('a(b(c)).md', 'a(b(c)).md'), ('a(b).md', r'a\(b\).md')]:
            with self.subTest(link=link):
                (self.root / filename).write_text('# Guide\n', encoding='utf-8')
                (self.root / 'README.md').write_text(f'[guide]({link})', encoding='utf-8')
                self.assertEqual(checker.check_repo(self.root)['localLinks'], 1)

    def test_image_paths_are_checked(self):
        (self.root / 'README.md').write_text('![image](missing.png "Caption")', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'missing.png'):
            checker.check_repo(self.root)

    def test_external_links_are_not_fetched(self):
        (self.root / 'README.md').write_text('[remote](https://example.invalid/a(b) "Title")', encoding='utf-8')
        self.assertEqual(checker.check_repo(self.root)['localLinks'], 0)

    def test_scenario_input_must_exist(self):
        case = self.case('materials')
        case['inputFiles'] = ['fixtures/notes.md']
        self.write_cases([case])
        with self.assertRaisesRegex(ValueError, 'Missing or external scenario input'):
            checker.check_repo(self.root)
        path = self.skill / 'evals/fixtures/notes.md'
        path.parent.mkdir()
        path.write_text('Synthetic raw observations.\n', encoding='utf-8')
        checker.check_repo(self.root)

    def test_scenario_can_reuse_material_within_skill(self):
        material = self.skill / 'examples/notes.md'
        material.parent.mkdir()
        material.write_text('Synthetic input.\n', encoding='utf-8')
        case = self.case('materials')
        case['inputFiles'] = ['../examples/notes.md']
        self.write_cases([case])
        checker.check_repo(self.root)

    def test_scenario_input_cannot_escape_skill(self):
        case = self.case('materials')
        case['inputFiles'] = ['../../../README.md']
        self.write_cases([case])
        with self.assertRaisesRegex(ValueError, 'Missing or external scenario input'):
            checker.check_repo(self.root)

    def test_scenario_input_list_rejects_empty_or_invalid_types(self):
        for value in ([], 'notes.md', [5], ['']):
            with self.subTest(value=value):
                case = self.case('materials')
                case['inputFiles'] = value
                self.write_cases([case])
                with self.assertRaisesRegex(ValueError, 'Invalid input files'):
                    checker.check_repo(self.root)


if __name__ == '__main__':
    unittest.main()
