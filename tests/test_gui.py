import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
from unittest import TestCase
from xml.etree import ElementTree

from lib.gui import (
    capture_arguments,
    command_creates_image,
    most_recent_image,
    proofshot_command,
    should_use_compact_layout,
)


ROOT = Path(__file__).resolve().parent.parent


class CaptureToolbarTests(TestCase):
    def test_source_layout_runs_proofshot_with_python(self):
        program, arguments = proofshot_command(ROOT)

        self.assertEqual(program, sys.executable)
        self.assertEqual(arguments, [str(ROOT / "proofshot.py")])

    def test_installed_layout_uses_the_installed_proofshot_executable(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            install_root = Path(temporary_directory)
            (install_root / "proofshot").touch()

            program, arguments = proofshot_command(install_root)

        self.assertEqual(program, str(install_root / "proofshot"))
        self.assertEqual(arguments, [])

    def test_builds_next_capture_arguments(self):
        self.assertEqual(capture_arguments("Proof", 2, False), ["-C", "Proof", "-N", "2"])
        self.assertEqual(capture_arguments("Form", 3, True), ["-C", "Form", "-N", "3", "-S"])

    def test_identifies_commands_that_refresh_to_the_latest_image(self):
        self.assertTrue(command_creates_image(["-C", "Proof", "-N", "1"]))
        self.assertTrue(command_creates_image(["--question", "7"]))
        self.assertTrue(command_creates_image(["--add-screenshot", "capture.png"]))
        self.assertTrue(command_creates_image(["--retake-screenshot", "capture.png"]))
        self.assertFalse(command_creates_image(["-C", "Proof", "-I", "7"]))

    def test_selects_most_recent_image(self):
        older = {"filename": "older.png", "modified_ns": 10}
        newer = {"filename": "newer.png", "modified_ns": 20}

        self.assertIs(most_recent_image([older, newer]), newer)
        self.assertIsNone(most_recent_image([]))

    def test_compact_layout_is_chosen_for_narrow_or_portrait_windows(self):
        self.assertTrue(should_use_compact_layout(620, 1000))
        self.assertTrue(should_use_compact_layout(840, 700))
        self.assertFalse(should_use_compact_layout(1200, 760))

    def test_ui_contains_the_capture_toolbar_controls(self):
        root = ElementTree.parse(ROOT / "ui" / "main_window.ui").getroot()
        names = {widget.get("name") for widget in root.iter("widget")}

        self.assertTrue({
            "captureColumnCombo",
            "captureSpanCheck",
            "captureIncrementSpin",
            "currentIndexSpin",
            "indexDecrementButton",
            "indexIncrementButton",
            "captureProjectButton",
        }.issubset(names))

    def test_selecting_a_project_enables_capture_controls(self):
        if importlib.util.find_spec("PySide6") is None:
            self.skipTest("PySide6 is not installed")
        script = textwrap.dedent("""
            import json
            import tempfile
            from pathlib import Path
            from PySide6.QtCore import QTimer
            from PySide6.QtWidgets import QApplication, QTreeWidget, QPushButton
            import lib.gui as gui
            from lib.config_service import create_project_config

            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                projects = root / "projects"
                project = projects / "Demo"
                project.mkdir(parents=True)
                create_project_config(project)
                state = root / "state"
                state.mkdir()
                (state / "workspace.json").write_text(json.dumps({
                    "version": 1, "discovery_paths": [str(projects)]
                }))
                gui.STATE_DIR = state
                app = QApplication([])
                result = {"enabled": False}

                def inspect():
                    window = next(widget for widget in app.topLevelWidgets() if widget.isVisible())
                    result["enabled"] = window.findChild(QPushButton, "captureProjectButton").isEnabled()
                    app.quit()

                def select_project():
                    window = next(widget for widget in app.topLevelWidgets() if widget.isVisible())
                    tree = window.findChild(QTreeWidget, "treeView")
                    tree.setCurrentItem(tree.topLevelItem(0).child(0))
                    QTimer.singleShot(0, inspect)

                QTimer.singleShot(100, select_project)
                gui.run_gui()
                raise SystemExit(0 if result["enabled"] else 1)
        """)
        environment = os.environ.copy()
        environment["QT_QPA_PLATFORM"] = "offscreen"
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_capture_hides_and_restores_the_window(self):
        if importlib.util.find_spec("PySide6") is None:
            self.skipTest("PySide6 is not installed")
        script = textwrap.dedent("""
            import json
            import sys
            import tempfile
            from pathlib import Path
            from PySide6.QtCore import QTimer
            from PySide6.QtWidgets import QApplication, QTreeWidget, QPushButton
            import lib.gui as gui
            from lib.config_service import create_project_config

            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                projects = root / "projects"
                project = projects / "Demo"
                project.mkdir(parents=True)
                create_project_config(project)
                state = root / "state"
                state.mkdir()
                (state / "workspace.json").write_text(json.dumps({
                    "version": 1, "discovery_paths": [str(projects)]
                }))
                gui.STATE_DIR = state
                gui.proofshot_command = lambda: (
                    sys.executable, ["-c", "import time; time.sleep(0.3)"]
                )
                app = QApplication([])
                result = {}
                window = None

                def inspect_restored():
                    result["visible_after_capture"] = window.isVisible()
                    window.close()
                    app.quit()

                def inspect_hidden():
                    result["hidden_during_capture"] = not window.isVisible()
                    QTimer.singleShot(500, inspect_restored)

                def start_capture():
                    tree = window.findChild(QTreeWidget, "treeView")
                    tree.setCurrentItem(tree.topLevelItem(0).child(0))
                    QTimer.singleShot(0, lambda: window.findChild(
                        QPushButton, "captureProjectButton").click())
                    QTimer.singleShot(80, inspect_hidden)

                def begin():
                    global window
                    window = next(widget for widget in app.topLevelWidgets() if widget.isVisible())
                    QTimer.singleShot(100, start_capture)

                QTimer.singleShot(0, begin)
                gui.run_gui()
                expected = {"hidden_during_capture": True, "visible_after_capture": True}
                raise SystemExit(0 if result == expected else 1)
        """)
        environment = os.environ.copy()
        environment["QT_QPA_PLATFORM"] = "offscreen"
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rendered_menu_bar_uses_the_dark_palette(self):
        if importlib.util.find_spec("PySide6") is None:
            self.skipTest("PySide6 is not installed")
        script = textwrap.dedent("""
            from PySide6.QtCore import QTimer
            from PySide6.QtWidgets import QApplication
            from lib.gui import run_gui

            app = QApplication([])
            result = {"light": False}

            def inspect():
                window = next(widget for widget in app.topLevelWidgets() if widget.isVisible())
                image = window.grab().toImage()
                color = image.pixelColor(window.width() // 2, 10)
                luminance = (color.red() * 299 + color.green() * 587 + color.blue() * 114) // 1000
                result["light"] = luminance > 120
                app.quit()

            QTimer.singleShot(200, inspect)
            run_gui()
            raise SystemExit(1 if result["light"] else 0)
        """)
        environment = os.environ.copy()
        environment["QT_QPA_PLATFORM"] = "offscreen"
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_responsive_layout_switches_between_compact_and_standard_modes(self):
        if importlib.util.find_spec("PySide6") is None:
            self.skipTest("PySide6 is not installed")
        script = textwrap.dedent("""
            from PySide6.QtCore import QTimer, Qt
            from PySide6.QtWidgets import QApplication, QAbstractButton, QListView, QListWidget, QListWidgetItem, QSplitter, QTabWidget, QToolBox, QWidget
            from lib.gui import run_gui

            app = QApplication([])
            result = {"valid": True}

            def inspect_compact():
                window = next(widget for widget in app.topLevelWidgets() if widget.isVisible())
                splitter = window.findChild(QSplitter, "gallerySplitter")
                gallery = window.findChild(QListWidget, "ImageGallery")
                tabs = window.findChild(QTabWidget, "compactBottomTabs")
                browser = window.findChild(QWidget, "browserPanel")
                terminal = window.findChild(QWidget, "terminalPanel")
                header = window.findChild(QWidget, "captureHeader")
                result["valid"] &= splitter.orientation() == Qt.Orientation.Vertical
                result["valid"] &= gallery.viewMode() == QListView.ViewMode.ListMode
                result["valid"] &= tabs.isVisible() and tabs.isAncestorOf(browser) and tabs.isAncestorOf(terminal)
                result["valid"] &= len(splitter.sizes()) == 3 and min(splitter.sizes()) > 0
                tabs.setCurrentIndex(1)
                QApplication.processEvents()
                control_names = (
                    "captureColumnCombo", "captureSpanCheck", "captureIncrementSpin",
                    "indexDecrementButton", "currentIndexSpin", "indexIncrementButton",
                    "captureProjectButton",
                )
                result["valid"] &= all(
                    window.findChild(QWidget, name).geometry().bottom() < header.height()
                    for name in control_names
                )
                step_heights = {
                    window.findChild(QWidget, name).height()
                    for name in ("captureStepDecrementButton", "captureIncrementSpin", "captureStepIncrementButton")
                }
                index_heights = {
                    window.findChild(QWidget, name).height()
                    for name in ("indexDecrementButton", "currentIndexSpin", "indexIncrementButton")
                }
                result["valid"] &= step_heights == {34} and index_heights == {34}
                gallery.addItem(QListWidgetItem("Example.png"))
                result["valid"] &= gallery.sizeHintForRow(gallery.count() - 1) <= 60
                window.findChild(QTabWidget, "detailTabs").setCurrentIndex(1)
                toolbox = window.findChild(QToolBox, "metadataAccordion")
                QApplication.processEvents()
                metadata_tabs = [button for button in toolbox.findChildren(QAbstractButton)
                                 if button.text() == "Image metadata"]
                result["valid"] &= bool(metadata_tabs)
                result["valid"] &= all(
                    button.height() >= button.fontMetrics().height() + 8 for button in metadata_tabs
                )
                result["valid"] &= header.height() <= 60
                window.resize(480, 900)
                QTimer.singleShot(150, inspect_wrapped)

            def inspect_wrapped():
                window = next(widget for widget in app.topLevelWidgets() if widget.isVisible())
                header = window.findChild(QWidget, "captureHeader")
                column = window.findChild(QWidget, "captureColumnCombo")
                capture = window.findChild(QWidget, "captureProjectButton")
                result["valid"] &= header.height() >= 95
                result["valid"] &= capture.geometry().top() > column.geometry().top()
                window.resize(1200, 760)
                QTimer.singleShot(150, inspect_standard)

            def inspect_standard():
                window = next(widget for widget in app.topLevelWidgets() if widget.isVisible())
                splitter = window.findChild(QSplitter, "gallerySplitter")
                gallery = window.findChild(QListWidget, "ImageGallery")
                tabs = window.findChild(QTabWidget, "compactBottomTabs")
                result["valid"] &= splitter.orientation() == Qt.Orientation.Horizontal
                result["valid"] &= gallery.viewMode() == QListView.ViewMode.IconMode
                result["valid"] &= not tabs.isVisible()
                app.quit()

            def start():
                window = next(widget for widget in app.topLevelWidgets() if widget.isVisible())
                window.resize(520, 900)
                QTimer.singleShot(150, inspect_compact)

            QTimer.singleShot(100, start)
            run_gui()
            raise SystemExit(0 if result["valid"] else 1)
        """)
        environment = os.environ.copy()
        environment["QT_QPA_PLATFORM"] = "offscreen"
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
