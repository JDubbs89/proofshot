import json
import tempfile
import unittest
from pathlib import Path

from lib.workspace_service import discover_projects, load_workspace, normalize_paths, save_workspace


class WorkspaceServiceTests(unittest.TestCase):
    def test_workspace_round_trip_and_discovery(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); first = root / "first"; second = root / "second"
            first.mkdir(); second.mkdir(); (first / "Project B").mkdir(); (second / "Project A").mkdir()
            state = root / "state"; workspace = {"discovery_paths": [str(first), str(first), str(second)]}
            workspace["discovery_paths"] = normalize_paths(workspace["discovery_paths"]); save_workspace(state, workspace)
            self.assertEqual(load_workspace(state)["version"], 1)
            self.assertEqual([p["name"] for p in discover_projects(load_workspace(state))], ["Project A", "Project B"])

    def test_invalid_workspace_is_safe(self):
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp); (state / "workspace.json").write_text("not json")
            self.assertEqual(load_workspace(state)["discovery_paths"], [])


if __name__ == "__main__":
    unittest.main()
