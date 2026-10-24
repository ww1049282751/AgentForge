"""Include authoritative root schemas in distributions; do not author a second copy."""
from pathlib import Path
from setuptools import setup
from setuptools.command.build_py import build_py


class BuildPy(build_py):
    def run(self):
        super().run()
        self.copy_tree(str(Path(__file__).parent / 'schemas'), str(Path(self.build_lib) / 'agentforge/schemas'))


setup(cmdclass={'build_py': BuildPy})
