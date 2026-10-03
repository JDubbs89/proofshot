"""Optional PySide6 GUI for project discovery and image management."""
from pathlib import Path
import sys
from .config_service import STATE_DIR, create_project_config, load_config, reset_indices
from .image_service import project_images
from .workspace_service import discover_projects, load_workspace, normalize_paths, save_workspace

def run_gui() -> int:
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QPixmap
        from PySide6.QtWidgets import QApplication, QFileDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget, QInputDialog, QDialog
    except ImportError:
        print("The Proofshot GUI requires PySide6. Install the optional GUI dependency first.", file=sys.stderr); return 2

    class Window(QMainWindow):
        def __init__(self):
            super().__init__(); self.setWindowTitle("Proofshot"); self.resize(1100, 700)
            self.workspace = load_workspace(STATE_DIR); self.projects = QListWidget(); self.images = QListWidget(); self.detail = QLabel("Select an image"); self.detail.setAlignment(Qt.AlignmentFlag.AlignCenter); self.project_label = QLabel("No project selected")
            buttons = QHBoxLayout()
            for label, handler in (("Add discovery path", self.add_path), ("Refresh", self.refresh), ("Create project", self.create_project)):
                button = QPushButton(label); button.clicked.connect(handler); buttons.addWidget(button)
            left = QVBoxLayout(); left.addWidget(QLabel("Projects")); left.addLayout(buttons); left.addWidget(self.projects)
            center = QVBoxLayout(); center.addWidget(self.project_label); center.addWidget(self.images)
            right = QVBoxLayout(); right.addWidget(self.detail)
            container = QWidget(); layout = QHBoxLayout(container)
            for section in (left, center, right): widget = QWidget(); widget.setLayout(section); layout.addWidget(widget)
            self.setCentralWidget(container); self.projects.currentItemChanged.connect(self.select_project); self.images.currentItemChanged.connect(self.select_image); self.refresh()

        def refresh(self):
            self.projects.clear()
            for project in discover_projects(self.workspace):
                item = QListWidgetItem(project["name"]); item.setData(Qt.ItemDataRole.UserRole, project["path"]); self.projects.addItem(item)

        def add_path(self):
            path = QFileDialog.getExistingDirectory(self, "Add discovery path")
            if path: self.workspace["discovery_paths"] = normalize_paths(self.workspace["discovery_paths"] + [path]); save_workspace(STATE_DIR, self.workspace); self.refresh()

        def create_project(self):
            if not self.workspace["discovery_paths"]: QMessageBox.information(self, "No discovery path", "Add a discovery path first."); return
            name, ok = QInputDialog.getText(self, "Create project", "Project name:")
            if ok and name:
                target = Path(self.workspace["discovery_paths"][0]) / name
                try: target.mkdir(); create_project_config(target); reset_indices(load_config(target)); self.refresh()
                except (OSError, ValueError) as exc: QMessageBox.critical(self, "Create project failed", str(exc))

        def select_project(self, item, _old):
            self.images.clear(); self.detail.setText("Select an image")
            if not item: return
            path = Path(item.data(Qt.ItemDataRole.UserRole)); self.project_label.setText(str(path))
            for image in project_images(path):
                row = QListWidgetItem(image["filename"]); row.setData(Qt.ItemDataRole.UserRole, image); self.images.addItem(row)

        def select_image(self, item, _old):
            if not item: return
            image = item.data(Qt.ItemDataRole.UserRole); pixmap = QPixmap(str(image["path"]))
            self.detail.setPixmap(pixmap.scaled(500, 500, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            dialog = QDialog(self); dialog.setWindowTitle(f"Image Detail — {image['filename']}"); dialog.resize(800, 700)
            layout = QVBoxLayout(dialog); preview = QLabel(); preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
            preview.setPixmap(pixmap.scaled(760, 560, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)); layout.addWidget(preview)
            layout.addWidget(QLabel(f"Filename: {image['filename']}\nProject: {self.project_label.text()}\nColumn: {image['category'] or 'Unknown'}\nIndex: {image['index'] or 'Unknown'}\nDimensions: {pixmap.width()} × {pixmap.height()}\nFile size: {image['size']} bytes\nManifest: {'yes' if image['manifested'] else 'no'}"))
            dialog.exec()

    app = QApplication.instance() or QApplication(sys.argv); window = Window(); window.show(); return app.exec()
