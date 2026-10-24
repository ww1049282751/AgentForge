from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from .errors import AFError
from .safety import read_json

SCHEMAS = Path(__file__).resolve().parent / 'schemas'
if not SCHEMAS.is_dir():
    SCHEMAS = Path(__file__).resolve().parents[1] / 'schemas'


class Schemas:
    def __init__(self):
        self.documents = {}
        resources = []
        for path in sorted(SCHEMAS.glob('*.schema.json')):
            doc = read_json(path)
            Draft202012Validator.check_schema(doc)
            self.documents[path.stem.removesuffix('.schema')] = doc
            resources.append((doc['$id'], Resource.from_contents(doc)))
        self.registry = Registry().with_resources(resources)

    def validate(self, name, value):
        validator = Draft202012Validator(self.documents[name], registry=self.registry, format_checker=FormatChecker())
        errors = list(validator.iter_errors(value))
        if errors:
            e = errors[0]
            location = '/'.join(map(str, e.absolute_path)) or '<root>'
            # Do not echo arbitrary input values (potential secrets) in errors.
            raise AFError(f'{name} schema violation at {location}: {e.validator}')
        return value


_schemas = None


def validate(name, value):
    global _schemas
    if _schemas is None:
        _schemas = Schemas()
    return _schemas.validate(name, value)
