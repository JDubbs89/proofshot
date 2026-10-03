import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from lib.screenshot_service import FlameshotService


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
