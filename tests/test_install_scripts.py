import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from unittest import TestCase


ROOT = Path(__file__).resolve().parent.parent


class InstallScriptTests(TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary_directory.name)
        self.release = self.base / "release"
        self.release.mkdir()
        for filename in ("install.sh", "proofshot.py", "default_config.json"):
            shutil.copy2(ROOT / filename, self.release / filename)
        shutil.copytree(ROOT / "lib", self.release / "lib")
        shutil.copytree(ROOT / "ui", self.release / "ui")

        self.home = self.base / "home"
        self.bin_dir = self.base / "bin"
        self.data_dir = self.base / "data"
        self.desktop_dir = self.base / "Desktop"
        self.home.mkdir()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def install(self, shortcut_choice):
        environment = os.environ.copy()
        environment.update({
            "HOME": str(self.home),
            "XDG_DATA_HOME": str(self.data_dir),
            "PROOFSHOT_BIN_DIR": str(self.bin_dir),
            "PROOFSHOT_DESKTOP_DIR": str(self.desktop_dir),
            "PROOFSHOT_DESKTOP_SHORTCUT": shortcut_choice,
            "PROOFSHOT_SKIP_DEPS": "1",
        })
        return subprocess.run(
            ["bash", str(self.release / "install.sh")],
            cwd=self.release,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_installs_gui_files_and_requested_desktop_shortcut(self):
        result = self.install("yes")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.bin_dir / "proofshot-gui").is_file())
        self.assertTrue((self.bin_dir / "ui/main_window.ui").is_file())
        self.assertTrue((self.data_dir / "applications/proofshot.desktop").is_file())
        shortcut = self.desktop_dir / "proofshot.desktop"
        self.assertTrue(shortcut.is_file())
        self.assertTrue(shortcut.stat().st_mode & 0o100)
        self.assertIn(str(self.bin_dir / "proofshot-gui"), shortcut.read_text())

    def test_existing_desktop_shortcut_skips_the_choice_and_is_preserved(self):
        self.desktop_dir.mkdir()
        shortcut = self.desktop_dir / "proofshot.desktop"
        shortcut.write_text("existing shortcut\n")

        result = self.install("not-a-valid-choice")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(shortcut.read_text(), "existing shortcut\n")
        self.assertIn("already exists", result.stdout)

    def test_declining_does_not_create_a_desktop_shortcut(self):
        result = self.install("no")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.desktop_dir / "proofshot.desktop").exists())
        self.assertTrue((self.data_dir / "applications/proofshot.desktop").is_file())
