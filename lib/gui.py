"""Optional PySide6 GUI for project discovery and image management."""
from pathlib import Path
import sys

from .config_service import STATE_DIR, create_project_config, load_config, reset_indices
from .image_service import project_images
from .workspace_service import discover_projects, load_workspace, normalize_paths, save_workspace


def run_gui() -> int:
    try:
        from PySide6.QtCore import QFile, QSize, Qt
        from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPixmap
        from PySide6.QtUiTools import QUiLoader
        from PySide6.QtWidgets import QApplication, QFileDialog, QInputDialog, QLabel, QListWidget, QListWidgetItem, QLineEdit, QMessageBox, QPushButton, QSplitter, QStyledItemDelegate, QTreeWidget, QTreeWidgetItem
    except ImportError:
        print("The Proofshot GUI requires PySide6. Install the optional GUI dependency first.", file=sys.stderr)
        return 2

    app = QApplication.instance() or QApplication(sys.argv)
    ui_path = Path(__file__).resolve().parents[1] / "ui" / "main_window.ui"
    ui_file = QFile(str(ui_path))
    ui_file.open(QFile.OpenModeFlag.ReadOnly)
    window = QUiLoader().load(ui_file)
    ui_file.close()
    if window is None:
        print(f"Could not load GUI definition: {ui_path}", file=sys.stderr)
        return 2

    window.setWindowTitle("Proofshot")
    workspace = load_workspace(STATE_DIR)
    selected_images = []
    tree = window.findChild(QTreeWidget, "treeView")
    image_gallery = window.findChild(QListWidget, "ImageGallery")
    search_filter = window.findChild(QLineEdit, "searchFilter")
    preview = window.findChild(QLabel, "ImagePreview")
    project_label = window.findChild(QLabel, "projectLabel")
    metadata_label = window.findChild(QLabel, "metadataLabel")
    status = window.statusBar()
    window.findChild(QSplitter, "contentSplitter").setSizes([350, 800])
    window.findChild(QSplitter, "gallerySplitter").setSizes([430, 215])

    class ThumbnailDelegate(QStyledItemDelegate):
        """Render gallery items as uniform rounded image cards with title overlays."""
        def paint(self, painter, option, index):
            painter.save()
            card = option.rect.adjusted(4, 4, -4, -4)
            path = QPainterPath()
            path.addRoundedRect(card, 8, 8)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setClipPath(path)
            painter.fillPath(path, QColor("#20252b"))

            icon = index.data(Qt.ItemDataRole.DecorationRole)
            if icon:
                pixmap = icon.pixmap(card.size()).scaled(
                    card.size(), Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)

                # Use a deliberately low-resolution copy as a soft, dimmed
                # backdrop.  It keeps the card visually tied to its image
                # without competing with the readable foreground thumbnail.
                background = pixmap.scaled(
                    QSize(24, 16), Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation).scaled(
                    card.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation)
                painter.save()
                painter.setOpacity(0.34)
                painter.drawPixmap(
                    card.left() + (card.width() - background.width()) // 2,
                    card.top() + (card.height() - background.height()) // 2,
                    background)
                painter.restore()
                painter.fillRect(card, QColor(0, 0, 0, 105))

                painter.drawPixmap(
                    card.left() + (card.width() - pixmap.width()) // 2,
                    card.top() + (card.height() - pixmap.height()) // 2,
                    pixmap)

            gradient = QLinearGradient(0, card.bottom() - 58, 0, card.bottom())
            gradient.setColorAt(0, Qt.GlobalColor.transparent)
            gradient.setColorAt(1, Qt.GlobalColor.black)
            painter.fillRect(card.left(), card.bottom() - 58, card.width(), 58, gradient)
            painter.setPen(Qt.GlobalColor.white)
            font = painter.font()
            font.setBold(True)
            painter.setFont(font)
            text_rect = card.adjusted(8, 0, -8, -8)
            title = index.data(Qt.ItemDataRole.DisplayRole) or ""
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom,
                             painter.fontMetrics().elidedText(title, Qt.TextElideMode.ElideMiddle,
                                                              text_rect.width()))
            painter.restore()

        def sizeHint(self, option, index):
            return image_gallery.iconSize() + QSize(8, 8)

    image_gallery.setItemDelegate(ThumbnailDelegate(image_gallery))
    image_gallery.setUniformItemSizes(True)

    def show_preview(image):
        pixmap = QPixmap(str(image["path"]))
        if pixmap.isNull():
            preview.setText("Unable to load image")
            return
        preview.setPixmap(pixmap.scaled(preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        preview.setToolTip(f"{image['filename']} — {pixmap.width()} × {pixmap.height()} px")

    def update_metadata(image):
        pixmap = QPixmap(str(image["path"]))
        metadata_label.setText(
            f"<b>{image['filename']}</b><br>"
            f"Column: {image['category'] or 'Unknown'}<br>"
            f"Index: {image['index'] or 'Unknown'}<br>"
            f"Dimensions: {pixmap.width()} × {pixmap.height()} px<br>"
            f"File size: {image['size']:,} bytes<br>"
            f"Manifest: {'yes' if image['manifested'] else 'no'}"
        )

    def render_gallery():
        image_gallery.clear()
        query = search_filter.text().strip().lower()
        visible = [image for image in selected_images if not query or query in " ".join((image["filename"], image["category"], str(image["index"] or ""))).lower()]
        for image in visible:
            item = QListWidgetItem(QIcon(str(image["path"])), image["filename"])
            item.setData(Qt.ItemDataRole.UserRole, image)
            item.setToolTip(f"{image['filename']}\n{image['category'] or 'Unknown'} · {image['index'] or 'Unknown'}")
            image_gallery.addItem(item)
        status.showMessage(f"{len(visible)} of {len(selected_images)} image(s)")
        if image_gallery.count():
            image_gallery.setCurrentRow(0)
            show_preview(visible[0])
            update_metadata(visible[0])

    def populate_images(path):
        selected_images[:] = project_images(Path(path))
        project_label.setText(str(path))
        render_gallery()
        if selected_images:
            update_metadata(selected_images[0])
        else:
            preview.clear()
            preview.setText("No PNG images in this project")

    def refresh():
        tree.clear()
        projects = discover_projects(workspace)
        for raw_root in normalize_paths(workspace.get("discovery_paths", [])):
            root_path = Path(raw_root)
            root = QTreeWidgetItem([root_path.name or raw_root, raw_root])
            root.setData(0, Qt.ItemDataRole.UserRole, None)
            tree.addTopLevelItem(root)
            for project in projects:
                if Path(project["path"]).parent == root_path:
                    child = QTreeWidgetItem([project["name"], project["path"]])
                    child.setData(0, Qt.ItemDataRole.UserRole, project["path"])
                    root.addChild(child)
            root.setExpanded(True)
        tree.resizeColumnToContents(0)
        status.showMessage(f"{len(projects)} project(s) found")

    def add_path():
        path = QFileDialog.getExistingDirectory(window, "Add discovery path")
        if path:
            workspace["discovery_paths"] = normalize_paths(workspace["discovery_paths"] + [path])
            save_workspace(STATE_DIR, workspace)
            refresh()

    def create_project():
        if not workspace["discovery_paths"]:
            QMessageBox.information(window, "No discovery path", "Add a discovery path first.")
            return
        name, ok = QInputDialog.getText(window, "Create project", "Project name:")
        if not ok or not name.strip():
            return
        target = Path(workspace["discovery_paths"][0]) / name.strip()
        try:
            target.mkdir()
            create_project_config(target)
            reset_indices(load_config(target))
            refresh()
        except (OSError, ValueError) as exc:
            QMessageBox.critical(window, "Create project failed", str(exc))

    def select_tree_item(item, _column):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path:
            populate_images(path)

    def select_image(item):
        image = item.data(Qt.ItemDataRole.UserRole)
        if image:
            show_preview(image)
            update_metadata(image)

    window.findChild(QPushButton, "addPathButton").clicked.connect(add_path)
    window.findChild(QPushButton, "refreshButton").clicked.connect(refresh)
    window.findChild(QPushButton, "createProjectButton").clicked.connect(create_project)
    tree.itemClicked.connect(select_tree_item)
    image_gallery.itemClicked.connect(select_image)
    search_filter.textChanged.connect(render_gallery)
    refresh()
    window.show()
    return app.exec()
