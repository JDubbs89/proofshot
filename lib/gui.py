"""Optional PySide6 GUI for project discovery and image management."""
from pathlib import Path
import shlex
import sys

from .config_service import STATE_DIR, create_project_config, load_config, load_counts, reset_indices
from .image_service import project_images
from .workspace_service import discover_projects, load_workspace, normalize_paths, save_workspace


def run_gui() -> int:
    try:
        from PySide6.QtCore import QFile, QProcess, QSize, Qt
        from PySide6.QtGui import QAction, QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPixmap
        from PySide6.QtUiTools import QUiLoader
        from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout, QInputDialog, QLabel, QListWidget, QListWidgetItem, QLineEdit, QMessageBox, QPushButton, QSizePolicy, QSpinBox, QSplitter, QStyle, QStyledItemDelegate, QTabWidget, QTreeWidget, QTreeWidgetItem, QWidget
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
    tree.setRootIsDecorated(True)
    tree.setItemsExpandable(True)
    tree.setIndentation(18)
    tree.setIconSize(QSize(16, 16))
    tree.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
    tree.setStyleSheet("""
        QTreeWidget { border: none; outline: none; }
        QTreeWidget::item { height: 24px; color: rgba(255, 255, 255, 0.82); }
        QTreeWidget::item:hover { background: rgba(255, 255, 255, 0.08); }
        QTreeWidget::item:selected { background: rgba(255, 255, 255, 0.20); }
    """)
    image_gallery = window.findChild(QListWidget, "ImageGallery")
    image_gallery.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
    search_filter = window.findChild(QLineEdit, "searchFilter")
    preview = window.findChild(QLabel, "ImagePreview")
    project_label = window.findChild(QLabel, "projectLabel")
    metadata_label = window.findChild(QLabel, "metadataLabel")
    terminal_output = window.findChild(object, "terminalOutput")
    terminal_input = window.findChild(QLineEdit, "terminalInput")
    status = window.statusBar()
    window.findChild(QSplitter, "contentSplitter").setSizes([350, 800])
    window.findChild(QSplitter, "gallerySplitter").setSizes([800, 300])
    window.findChild(QSplitter, "previewTerminalSplitter").setSizes([430, 215])
    active_project = None
    capture_window = None
    capture_window_action = None
    terminal_process = QProcess(window)
    terminal_process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)

    def append_terminal(text):
        terminal_output.appendPlainText(text.rstrip("\n"))
        terminal_output.verticalScrollBar().setValue(terminal_output.verticalScrollBar().maximum())

    def append_process_output():
        output = bytes(terminal_process.readAllStandardOutput()).decode(errors="replace")
        if output:
            append_terminal(output)

    def finish_terminal_command(exit_code, _exit_status):
        append_process_output()
        append_terminal(f"[process exited with code {exit_code}]")
        terminal_input.setEnabled(True)
        terminal_input.setFocus()
        refresh()

    def run_proofshot(arguments):
        if terminal_process.state() != QProcess.ProcessState.NotRunning:
            append_terminal("A Proofshot command is already running.")
            return
        if "--gui" in arguments:
            append_terminal("The GUI cannot be launched from its own terminal.")
            return
        if active_project and "-D" not in arguments and "--dir" not in arguments:
            arguments.extend(["-D", active_project])
        append_terminal(f"$ proofshot {shlex.join(arguments)}")
        terminal_input.setEnabled(False)
        terminal_process.setProgram(sys.executable)
        terminal_process.setArguments([str(Path(__file__).resolve().parents[1] / "proofshot.py"), *arguments])
        terminal_process.start()

    def run_terminal_command():
        command = terminal_input.text().strip()
        if not command:
            return
        terminal_input.clear()
        try:
            run_proofshot(shlex.split(command))
        except ValueError as exc:
            append_terminal(f"shell parsing error: {exc}")

    def terminal_error(_error):
        append_terminal(f"[could not start Proofshot: {terminal_process.errorString()}]")
        terminal_input.setEnabled(True)

    terminal_process.readyReadStandardOutput.connect(append_process_output)
    terminal_process.finished.connect(finish_terminal_command)
    terminal_process.errorOccurred.connect(terminal_error)

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
            font.setBold(False)
            font.setPointSize(max(9, font.pointSize() - 1))
            painter.setFont(font)
            text_rect = card.adjusted(8, 0, -8, -8)
            title = index.data(Qt.ItemDataRole.DisplayRole) or ""
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom,
                             painter.fontMetrics().elidedText(title, Qt.TextElideMode.ElideMiddle,
                                                              text_rect.width()))
            if option.state & QStyle.StateFlag.State_Selected:
                painter.setClipping(False)
                painter.setPen(QColor("#f5f5f5"))
                painter.drawRoundedRect(card.adjusted(1, 1, -1, -1), 7, 7)
            painter.restore()

        def sizeHint(self, option, index):
            return image_gallery.iconSize() + QSize(8, 8)

    image_gallery.setItemDelegate(ThumbnailDelegate(image_gallery))
    image_gallery.setUniformItemSizes(True)

    class ElidedLabel(QLabel):
        """Keep a label's source text while rendering a right-side ellipsis."""
        def __init__(self, text, parent=None):
            super().__init__(parent)
            self._full_text = text
            self.setToolTip(text)
            self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            self._update_elision()

        def resizeEvent(self, event):
            super().resizeEvent(event)
            self._update_elision()

        def _update_elision(self):
            super().setText(self.fontMetrics().elidedText(
                self._full_text, Qt.TextElideMode.ElideRight, self.contentsRect().width()))

    def add_tree_row(parent, name, objective_path=None):
        """Add a compact Explorer-style folder row with an inline, elided path."""
        item = QTreeWidgetItem(parent)
        row = QWidget()
        row.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(2, 0, 4, 0)
        layout.setSpacing(5)

        icon_label = QLabel()
        icon_label.setPixmap(window.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon).pixmap(16, 16))
        icon_label.setFixedSize(16, 16)
        layout.addWidget(icon_label)
        name_label = QLabel(name)
        name_label.setStyleSheet("color: rgba(255, 255, 255, 0.82); font-size: 12px; font-weight: 400;")
        layout.addWidget(name_label)

        if objective_path:
            path_label = ElidedLabel(objective_path)
            path_label.setStyleSheet("color: rgba(255, 255, 255, 0.50); font-size: 10px;")
            path_label.setMinimumWidth(0)
            layout.addWidget(path_label, 1)

        row.setMinimumHeight(24)
        tree.setItemWidget(item, 0, row)
        return item

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
        nonlocal active_project
        active_project = str(path)
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
            root = add_tree_row(tree, root_path.name or raw_root, raw_root)
            root.setData(0, Qt.ItemDataRole.UserRole, None)
            for project in projects:
                if Path(project["path"]).parent == root_path:
                    # Projects inherit the discovery-root path shown on their
                    # parent, so repeating their absolute paths is unnecessary.
                    child = add_tree_row(root, project["name"])
                    child.setData(0, Qt.ItemDataRole.UserRole, project["path"])
                    root.addChild(child)
            root.setExpanded(True)
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

    def open_capture_dialog():
        """Show the reusable, non-modal capture window."""
        nonlocal capture_window
        if not active_project:
            QMessageBox.information(window, "Select a project", "Select a project before starting a capture.")
            if capture_window_action:
                capture_window_action.setChecked(False)
            return

        if capture_window is not None:
            capture_window.show()
            capture_window.raise_()
            capture_window.activateWindow()
            if capture_window_action:
                capture_window_action.setChecked(True)
            return

        config = load_config(Path(active_project))
        capture_window = QDialog(window, Qt.WindowType.Window)
        capture_window.setWindowModality(Qt.WindowModality.NonModal)
        capture_window.setWindowTitle("Capture screenshot")
        capture_window.setMinimumWidth(330)
        form = QFormLayout(capture_window)

        category = QComboBox(capture_window)
        categories = list(config.get("categories", {})) or [config["form_category"], config["proof_category"]]
        category.addItems(categories)
        form.addRow("Column", category)

        mode = QComboBox(capture_window)
        mode.addItems(["Next index (-N)", "Current index (-I)", "Question number (-Q)"])
        form.addRow("Capture at", mode)

        number = QSpinBox(capture_window)
        number.setRange(1, 99999)
        number.setValue(1)
        form.addRow("Step", number)

        span = QCheckBox("Capture the full next span (-S)", capture_window)
        form.addRow("", span)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok, capture_window)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Start capture")
        form.addRow(buttons)

        def update_capture_controls():
            selected_category = category.currentText()
            current_index = load_counts().get(selected_category, 0)
            if mode.currentIndex() == 0:
                form.labelForField(number).setText("Step")
                number.setRange(1, 99999)
                number.setValue(1)
                span.setEnabled(True)
            elif mode.currentIndex() == 1:
                form.labelForField(number).setText("Index")
                number.setRange(0, 99999)
                number.setValue(current_index)
                span.setChecked(False)
                span.setEnabled(False)
            else:
                form.labelForField(number).setText("Question")
                number.setRange(1, 99999)
                number.setValue(current_index + 1)
                span.setChecked(False)
                span.setEnabled(False)

        mode.currentIndexChanged.connect(lambda _index: update_capture_controls())
        category.currentIndexChanged.connect(lambda _index: update_capture_controls())
        def start_capture():
            arguments = ["-C", category.currentText()]
            if mode.currentIndex() == 0:
                arguments.extend(["-N", str(number.value())])
                if span.isChecked():
                    arguments.append("-S")
            elif mode.currentIndex() == 1:
                arguments.extend(["-I", str(number.value())])
            else:
                arguments.extend(["-Q", str(number.value())])
            run_proofshot(arguments)
            hide_capture_window()

        def hide_capture_window():
            capture_window.hide()
            capture_window_action.setChecked(False)

        buttons.accepted.connect(start_capture)
        buttons.rejected.connect(hide_capture_window)
        capture_window.finished.connect(lambda _result: capture_window_action.setChecked(False))
        update_capture_controls()
        capture_window.show()
        capture_window.raise_()
        capture_window.activateWindow()
        capture_window_action.setChecked(True)

    file_menu = window.menuBar().addMenu("&File")
    view_menu = window.menuBar().addMenu("&View")

    add_path_action = QAction("Add discovery path…", window)
    refresh_action = QAction("Refresh", window)
    new_project_action = QAction("New project…", window)
    exit_action = QAction("Exit", window)
    add_path_action.triggered.connect(add_path)
    refresh_action.triggered.connect(refresh)
    new_project_action.triggered.connect(create_project)
    exit_action.triggered.connect(window.close)
    file_menu.addActions([add_path_action, refresh_action, new_project_action])
    file_menu.addSeparator()
    file_menu.addAction(exit_action)

    browser_panel = window.findChild(QWidget, "browserPanel")
    detail_tabs = window.findChild(QTabWidget, "detailTabs")
    gallery_tab = window.findChild(QWidget, "galleryTab")
    metadata_tab = window.findChild(QWidget, "metadataTab")

    browser_action = QAction("Project browser", window)
    browser_action.setCheckable(True)
    browser_action.setChecked(True)
    terminal_action = QAction("Terminal", window)
    terminal_action.setCheckable(True)
    terminal_action.setChecked(True)
    gallery_action = QAction("Gallery", window)
    gallery_action.setCheckable(True)
    gallery_action.setChecked(True)
    metadata_action = QAction("Metadata", window)
    metadata_action.setCheckable(True)
    metadata_action.setChecked(True)
    capture_window_action = QAction("Capture window", window)
    capture_window_action.setCheckable(True)
    browser_action.toggled.connect(browser_panel.setVisible)
    terminal_action.toggled.connect(window.findChild(QWidget, "terminalPanel").setVisible)
    gallery_action.toggled.connect(
        lambda visible: detail_tabs.setTabVisible(detail_tabs.indexOf(gallery_tab), visible))
    metadata_action.toggled.connect(
        lambda visible: detail_tabs.setTabVisible(detail_tabs.indexOf(metadata_tab), visible))
    capture_window_action.toggled.connect(
        lambda visible: open_capture_dialog() if visible else capture_window and capture_window.hide())
    view_menu.addActions([
        browser_action,
        terminal_action,
        gallery_action,
        metadata_action,
        capture_window_action,
    ])

    window.findChild(QPushButton, "captureProjectButton").clicked.connect(open_capture_dialog)
    tree.itemClicked.connect(select_tree_item)
    image_gallery.itemClicked.connect(select_image)
    search_filter.textChanged.connect(render_gallery)
    terminal_input.returnPressed.connect(run_terminal_command)
    refresh()
    window.show()
    return app.exec()
