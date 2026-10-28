import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from lib.config_service import load_counts, set_index_for_type


class ProjectIndexTests(TestCase):
    def test_indices_are_scoped_to_each_project(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first"
            second = root / "second"
            first.mkdir()
            second.mkdir()

            set_index_for_type("Form", 4, first)
            set_index_for_type("Proof", 7, first)
            set_index_for_type("Form", 12, second)

            self.assertEqual(load_counts(first)["Form"], 4)
            self.assertEqual(load_counts(first)["Proof"], 7)
            self.assertEqual(load_counts(second)["Form"], 12)
            self.assertEqual(load_counts(second)["Proof"], 0)

    def test_legacy_project_recovers_indices_from_manifest(self):
        with TemporaryDirectory() as directory:
            project = Path(directory)
            manifest = {
                "version": 1,
                "images": {
                    "first": [{"category": "Form", "index": 2, "index_end": 4}],
                    "second": [{"category": "Proof", "index": 9, "index_end": 9}],
                },
            }
            (project / ".manifest.json").write_text(json.dumps(manifest))

            self.assertEqual(load_counts(project), {"Form": 4, "Proof": 9})

    def test_previously_active_project_keeps_legacy_global_indices(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            project.mkdir()
            state_file = root / "last_dir"
            global_counts = root / "counts.json"
            state_file.write_text(str(project))
            global_counts.write_text(json.dumps({"Form": 3}))
            (project / ".manifest.json").write_text(json.dumps({
                "version": 1,
                "images": {
                    "first": [{"category": "Form", "index": 8, "index_end": 8}],
                    "second": [{"category": "Proof", "index": 9, "index_end": 9}],
                },
            }))

            with patch("lib.config_service.STATE_FILE", state_file), patch(
                "lib.config_service.COUNTS_FILE", global_counts
            ):
                counts = load_counts(project)

            self.assertEqual(counts, {"Form": 3, "Proof": 9})
