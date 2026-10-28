import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from lib.screenshot_service import FlameshotService, GrimSlurpService, ScreenshotService


class StubScreenshotService(ScreenshotService):
    def __init__(self, replacement=None, error=None):
        self.replacement = replacement
        self.error = error

    def capture_raw(self, target):
        if self.error:
            target.write_bytes(b"partial")
            raise self.error
        target.write_bytes(self.replacement)


class ScreenshotReplacementTests(unittest.TestCase):
    def test_failed_retake_preserves_the_original(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "capture.png"
            original = b"original" * 20
            target.write_bytes(original)

            success = StubScreenshotService(error=OSError("cancelled")).capture(target)

            self.assertFalse(success)
            self.assertEqual(target.read_bytes(), original)

    def test_successful_retake_atomically_replaces_the_original(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "capture.png"
            replacement = b"replacement" * 20
            target.write_bytes(b"original" * 20)

            success = StubScreenshotService(replacement=replacement).capture(target)

            self.assertTrue(success)
            self.assertEqual(target.read_bytes(), replacement)
            self.assertEqual(list(Path(temp_dir).glob(".*-capture-*.png")), [])


class FlameshotServiceTests(unittest.TestCase):
    def test_wayland_capture_uses_native_qt_backend(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "capture.png"
            with patch.dict(os.environ, {"XDG_SESSION_TYPE": "wayland"}, clear=True):
                with patch("lib.screenshot_service.subprocess.run",
                           return_value=SimpleNamespace(returncode=0, stderr="")) as run:
                    FlameshotService().capture_raw(target)

        self.assertEqual(run.call_args.kwargs["env"]["QT_QPA_PLATFORM"], "wayland")

    def test_explicit_qt_backend_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "capture.png"
            environment = {"XDG_SESSION_TYPE": "wayland", "QT_QPA_PLATFORM": "xcb"}
            with patch.dict(os.environ, environment, clear=True):
                with patch("lib.screenshot_service.subprocess.run",
                           return_value=SimpleNamespace(returncode=0, stderr="")) as run:
                    FlameshotService().capture_raw(target)

        self.assertEqual(run.call_args.kwargs["env"]["QT_QPA_PLATFORM"], "xcb")


class GrimSlurpServiceTests(unittest.TestCase):
    def test_capture_passes_selected_region_to_grim(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "capture.png"
            with patch("lib.screenshot_service.subprocess.run", side_effect=[
                SimpleNamespace(returncode=0, stdout="10,20 300x400\n", stderr=""),
                SimpleNamespace(returncode=0, stderr=""),
            ]) as run:
                GrimSlurpService().capture_raw(target)

        self.assertEqual(run.call_args_list[0].args[0], ["slurp"])
        self.assertEqual(run.call_args_list[1].args[0], ["grim", "-g", "10,20 300x400", "-"])

    def test_cancelled_selection_does_not_run_grim(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "capture.png"
            with patch("lib.screenshot_service.subprocess.run",
                       return_value=SimpleNamespace(returncode=1, stdout="", stderr="")) as run:
                with self.assertRaisesRegex(Exception, "selection was cancelled"):
                    GrimSlurpService().capture_raw(target)

        run.assert_called_once_with(["slurp"], capture_output=True, text=True, check=False)
