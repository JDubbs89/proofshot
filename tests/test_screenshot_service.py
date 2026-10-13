import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from lib.screenshot_service import FlameshotService, GrimSlurpService


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
