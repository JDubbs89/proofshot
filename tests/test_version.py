import ast
import json
from pathlib import Path
from unittest import TestCase

from lib.config_service import CURRENT_PROJECT_VERSION


ROOT = Path(__file__).resolve().parent.parent


class VersionTests(TestCase):
    def test_release_and_project_versions_match(self):
        module = ast.parse((ROOT / "proofshot.py").read_text())
        release_version = next(
            ast.literal_eval(node.value)
            for node in module.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets)
        )
        default_version = json.loads((ROOT / "default_config.json").read_text())["proofshot_version"]

        self.assertEqual(release_version, "0.3.2")
        self.assertEqual(CURRENT_PROJECT_VERSION, release_version)
        self.assertEqual(default_version, release_version)
