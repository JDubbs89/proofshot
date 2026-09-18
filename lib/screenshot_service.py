"""Screenshot providers and screenshot-file operations."""

import shutil
import subprocess
import os
from pathlib import Path

class ScreenshotService:
    """Common safety boundary for screenshot providers."""

    def check_dependencies(self):
        """Providers may override this when they have an external dependency."""
        return True

    def install_dependencies(self):
        raise SystemExit("This screenshot provider does not support automatic dependency installation.")

    def capture(self, target: Path) -> bool:
        """Capture safely and reject failed or partial provider output."""
        self.last_error = None
        try:
            target.unlink(missing_ok=True)
            self.capture_raw(target)
        except (OSError, subprocess.SubprocessError) as exc:
            self.last_error = str(exc)
            target.unlink(missing_ok=True)
            return False
        if not target.is_file() or target.stat().st_size < 100:
            self.last_error = "provider returned no usable PNG data"
            target.unlink(missing_ok=True)
            return False
        return True

    def capture_raw(self, target: Path):
        """Provider-specific capture implementation."""
        raise NotImplementedError

    def notify(self, target: Path):
        """Notifications are optional for every provider."""
        return None

class FlameshotService(ScreenshotService):
    def install_dependencies(self):
        install_package("flameshot")

    def check_dependencies(self):
        try: subprocess.run(["flameshot", "--version"], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError): raise SystemExit("flameshot not found. Install Flameshot or verify it is on PATH.")

    def capture_raw(self, target: Path):
        with open(target, "wb") as output:
            result = subprocess.run(["flameshot", "gui", "--raw"], stdout=output,
                                    stderr=subprocess.PIPE, text=True, check=False)
        if result.returncode != 0:
            detail = result.stderr.strip() or f"exit code {result.returncode}"
            raise subprocess.SubprocessError(f"Flameshot capture failed: {detail}")

class GnomeScreenshotService(ScreenshotService):
    """GNOME Screenshot backend using its non-interactive file output mode."""

    def install_dependencies(self):
        install_package("gnome-screenshot")

    def check_dependencies(self):
        try:
            subprocess.run(["gnome-screenshot", "--version"], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            raise SystemExit("gnome-screenshot not found. Install it or choose another provider.")

    def capture_raw(self, target: Path):
        # -a opens the interactive area selector; -f writes the selected area.
        result = subprocess.run(["gnome-screenshot", "-a", "-f", str(target)],
                                stderr=subprocess.PIPE, text=True, check=False)
        if result.returncode != 0:
            detail = result.stderr.strip() or f"exit code {result.returncode}"
            raise subprocess.SubprocessError(f"GNOME Screenshot failed: {detail}")

    @staticmethod
    def notify(target: Path):
        try: subprocess.run(["notify-send", "Screenshot Saved", str(target)], check=False)
        except FileNotFoundError: pass

def add_screenshot(source_path: str, target_dir: Path, force: bool = False):
    source = Path(source_path).expanduser().resolve()
    if not source.is_file(): raise ValueError(f"screenshot does not exist: {source}")
    if source.suffix.lower() != ".png": raise ValueError("screenshots must be PNG files")
    destination = target_dir / source.name
    if destination.exists() and not force: raise ValueError(f"screenshot already exists: {destination.name} (use --force to replace it)")
    shutil.copy2(source, destination); return destination

def remove_screenshot(name: str, target_dir: Path):
    screenshot = target_dir / Path(name).name
    if not screenshot.is_file() or screenshot.suffix.lower() != ".png": raise ValueError(f"PNG screenshot not found: {name}")
    screenshot.unlink(); return screenshot

PROVIDERS = {
    "flameshot": FlameshotService,
    "gnome-screenshot": GnomeScreenshotService,
}

def available_providers() -> list[str]:
    return list(PROVIDERS)

def get_screenshot_service(provider: str) -> ScreenshotService:
    try:
        return PROVIDERS[provider.lower()]()
    except KeyError:
        choices = ", ".join(available_providers())
        raise ValueError(f"unknown screenshot provider: {provider} (choose from: {choices})")

def install_package(package: str):
    """Install one provider package using the host's supported package manager."""
    managers = (
        ("apt-get", ["apt-get", "install", "-y", package]),
        ("dnf", ["dnf", "install", "-y", package]),
        ("pacman", ["pacman", "-Sy", "--needed", "--noconfirm", package]),
        ("zypper", ["zypper", "--non-interactive", "install", package]),
    )
    for command, arguments in managers:
        if shutil.which(command):
            runner = []
            if shutil.which("sudo") and os.geteuid() != 0:
                runner = ["sudo"]
            try:
                subprocess.run(runner + arguments, check=True)
            except (OSError, subprocess.CalledProcessError) as exc:
                raise SystemExit(f"Unable to install {package}: {exc}")
            return
    raise SystemExit(f"No supported package manager found. Install {package} manually.")
