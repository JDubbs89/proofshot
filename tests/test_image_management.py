from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from lib.config_service import (
    image_hash,
    load_counts,
    load_manifest,
    record_screenshot,
    set_index_for_type,
)
from lib.cli_service import CLIService
from proofshot import manage_project


def project_arguments(**overrides):
    values = {
        "rename_column": None,
        "add_column": None,
        "remove_column": None,
        "add_screenshot": None,
        "remove_screenshot": None,
        "retake_screenshot": None,
        "force": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class FakeCaptureService:
    last_error = None

    def check_dependencies(self):
        return True

    def capture(self, target):
        target.write_bytes(b"replacement screenshot" * 20)
        return True

    def notify(self, target):
        return None


class ImageManagementTests(TestCase):
    def test_retake_command_is_dispatched_as_a_project_operation(self):
        cli = CLIService("test")
        arguments = cli.parse_args(["--retake-screenshot", "capture.png", "-D", "/tmp/project"])

        self.assertEqual(arguments.retake_screenshot, "capture.png")
        self.assertTrue(cli.has_project_operation(arguments))

    def test_retake_replaces_the_selected_file_without_changing_project_index(self):
        with TemporaryDirectory() as directory:
            project = Path(directory)
            screenshot = project / "renamed.png"
            screenshot.write_bytes(b"original screenshot" * 20)
            record_screenshot(project, screenshot, 4, "Proof", 6)
            set_index_for_type("Proof", 12, project)
            original_digest = image_hash(screenshot)

            with patch("proofshot.get_screenshot_service", return_value=FakeCaptureService()), patch(
                "proofshot.load_provider", return_value="fake"
            ):
                handled = manage_project(
                    project_arguments(retake_screenshot=screenshot.name),
                    project,
                    {"categories": {"Form": {}, "Proof": {}}},
                )

            manifest = load_manifest(project)
            new_digest = image_hash(screenshot)
            self.assertTrue(handled)
            self.assertNotEqual(new_digest, original_digest)
            self.assertNotIn(original_digest, manifest["images"])
            self.assertEqual(manifest["images"][new_digest][0]["index"], 4)
            self.assertEqual(manifest["images"][new_digest][0]["index_end"], 6)
            self.assertEqual(manifest["images"][new_digest][0]["category"], "Proof")
            self.assertEqual(load_counts(project)["Proof"], 12)

    def test_delete_removes_the_file_and_manifest_record(self):
        with TemporaryDirectory() as directory:
            project = Path(directory)
            screenshot = project / "capture.png"
            screenshot.write_bytes(b"screenshot" * 20)
            record_screenshot(project, screenshot, 3, "Form")
            digest = image_hash(screenshot)

            handled = manage_project(
                project_arguments(remove_screenshot=screenshot.name),
                project,
                {"categories": {"Form": {}, "Proof": {}}},
            )

            self.assertTrue(handled)
            self.assertFalse(screenshot.exists())
            self.assertNotIn(digest, load_manifest(project)["images"])
