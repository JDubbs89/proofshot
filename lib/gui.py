"""Optional PySide6 GUI for project discovery and image management."""
from pathlib import Path
import shlex
import sys

from .config_service import (
    STATE_DIR,
    create_project_config,
    load_config,
    load_counts,
    reset_indices,
    set_index_for_type,
)
from .image_service import project_images
from .workspace_service import discover_projects, load_workspace, normalize_paths, save_workspace


def capture_arguments(category: str, increment: int, span: bool) -> list[str]:
    """Build the CLI arguments used by the capture toolbar."""
    arguments = ["-C", category, "-N", str(increment)]
    if span:
        arguments.append("-S")
    return arguments


def command_creates_image(arguments: list[str]) -> bool:
    """Return whether a Proofshot command can add or replace a project image."""
    capture_flags = {"-N", "--next", "-Q", "--question", "--add-screenshot", "--retake-screenshot"}
    return any(argument in capture_flags for argument in arguments)


def most_recent_image(images: list[dict]) -> dict | None:
    """Return the most recently modified image, with a stable filename tie-break."""
    return max(images, key=lambda image: (image.get("modified_ns", 0), image["filename"].casefold()), default=None)


def should_use_compact_layout(width: int, height: int) -> bool:
    """Choose the stacked layout for narrow or portrait-oriented windows."""
    return width < 900 or height > width * 1.15


def run_gui() -> int:
    try:
        from PySide6.QtCore import QEvent, QFile, QFileSystemWatcher, QObject, QProcess, QSize, QTimer, Qt
        from PySide6.QtGui import QAction, QColor, QIcon, QKeySequence, QLinearGradient, QPainter, QPainterPath, QPalette, QPen, QPixmap
        from PySide6.QtUiTools import QUiLoader
        from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QInputDialog, QLabel, QListView, QListWidget, QListWidgetItem, QLineEdit, QMenu, QMessageBox, QPushButton, QSizePolicy, QSpinBox, QSplitter, QStyle, QStyledItemDelegate, QTabWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
    except ImportError:
        print("The Proofshot GUI requires PySide6. Install the optional GUI dependency first.", file=sys.stderr)
        return 2

    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    palette = app.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#11151a"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e7ebf0"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#151a20"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#1c2229"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#252c34"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#f4f6f8"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e7ebf0"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#252c34"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#edf1f5"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Link, QColor("#6da9e3"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#316ca8"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#7f8a96"))
    app.setPalette(palette)
    ui_path = Path(__file__).resolve().parents[1] / "ui" / "main_window.ui"
    ui_file = QFile(str(ui_path))
    ui_file.open(QFile.OpenModeFlag.ReadOnly)
    window = QUiLoader().load(ui_file)
    ui_file.close()
    if window is None:
        print(f"Could not load GUI definition: {ui_path}", file=sys.stderr)
        return 2

    window.setWindowTitle("Proofshot")
    window.setStyleSheet("""
        QMainWindow, QWidget#centralwidget { background: #11151a; color: #e7ebf0; }
        QMenuBar { background: #11151a; color: #e7ebf0; border-bottom: 1px solid #2b333d; }
        QMenuBar::item { background: transparent; padding: 5px 9px; }
        QMenuBar::item:selected, QMenuBar::item:pressed { background: #28313a; }
        QMenu { background: #181d23; color: #e7ebf0; border: 1px solid #3a4654; padding: 4px; }
        QMenu::item { background: transparent; padding: 6px 28px 6px 10px; }
        QMenu::item:selected { background: #316ca8; color: white; }
        QMenu::separator { background: #3a4654; height: 1px; margin: 4px 8px; }
        QFrame#browserPanel, QFrame#galleryPanel, QFrame#terminalPanel {
            background: #181d23; border: 1px solid #2b333d; border-radius: 8px;
        }
        QLabel { color: #e7ebf0; }
        QLabel#projectLabel { color: #b8c2ce; padding: 2px 4px; }
        QLabel#terminalLabel { color: #f4f6f8; padding-right: 4px; }
        QLineEdit, QSpinBox, QComboBox {
            background: #11151a; color: #f4f6f8; border: 1px solid #3a4654;
            border-radius: 5px; padding: 5px 8px; selection-background-color: #316ca8;
        }
        QComboBox { border-radius: 6px; }
        QComboBox::drop-down {
            background: transparent; border: none;
            subcontrol-origin: padding; subcontrol-position: top right;
            border-top-right-radius: 6px; border-bottom-right-radius: 6px; width: 28px;
        }
        QLineEdit:focus, QSpinBox:focus, QComboBox:focus { border: 1px solid #6da9e3; }
        QComboBox QAbstractItemView {
            background: #181d23; color: #e7ebf0; border: 1px solid #3a4654;
            selection-background-color: #316ca8; selection-color: white; outline: none;
        }
        QPushButton {
            background: #252c34; color: #edf1f5; border: 1px solid #3a4654;
            border-radius: 5px; padding: 6px 10px; min-height: 18px;
        }
        QPushButton:hover { background: #303944; border-color: #536375; }
        QPushButton:pressed { background: #1d232a; }
        QPushButton:disabled { color: #697480; background: #1b2026; border-color: #29313a; }
        QPushButton#captureProjectButton {
            background: #2d78bd; border-color: #4b92d0; color: white; font-weight: 600;
            padding: 4px;
        }
        QPushButton#captureProjectButton:hover { background: #3888ce; }
        QPushButton#indexDecrementButton, QPushButton#indexIncrementButton,
        QPushButton#captureStepDecrementButton, QPushButton#captureStepIncrementButton {
            padding: 2px; font-weight: 600;
        }
        QPushButton#indexDecrementButton, QPushButton#captureStepDecrementButton {
            border-top-right-radius: 0; border-bottom-right-radius: 0;
        }
        QPushButton#indexIncrementButton, QPushButton#captureStepIncrementButton {
            border-top-left-radius: 0; border-bottom-left-radius: 0;
        }
        QSpinBox#currentIndexSpin, QSpinBox#captureIncrementSpin {
            border-radius: 0; border-left: none; border-right: none; padding-left: 4px; padding-right: 4px;
        }
        QCheckBox { spacing: 6px; color: #d8dee6; }
        QPlainTextEdit#terminalOutput, QLineEdit#terminalInput {
            background: #0d1116; color: #d7dde5; border: 1px solid #2b333d;
            border-radius: 5px; font-family: monospace;
        }
        QListWidget, QTreeWidget, QTabWidget::pane, QToolBox {
            background: #151a20; color: #e7ebf0; border: 1px solid #2b333d;
        }
        QAbstractItemView { alternate-background-color: #1c2229; }
        QTabBar::tab { background: #1c2229; padding: 7px 12px; color: #aeb8c4; }
        QTabBar::tab:selected { background: #28313a; color: #f4f6f8; }
        QToolBox::tab {
            background: #1c2229; color: #aeb8c4; min-height: 22px;
            padding: 6px 8px; margin-bottom: 2px;
        }
        QToolBox::tab:selected { background: #28313a; color: #f4f6f8; }
        QScrollBar:vertical { background: #11151a; width: 12px; margin: 0; }
        QScrollBar:horizontal { background: #11151a; height: 12px; margin: 0; }
        QScrollBar::handle { background: #465363; border-radius: 5px; min-height: 24px; min-width: 24px; }
        QScrollBar::handle:hover { background: #5b6b7d; }
        QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; background: transparent; }
        QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
        QToolTip { background: #252c34; color: #f4f6f8; border: 1px solid #536375; padding: 4px; }
        QStatusBar { background: #11151a; color: #9da8b5; }
        QSplitter::handle { background: #2b333d; }
    """)
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
    capture_column = window.findChild(QComboBox, "captureColumnCombo")
    capture_span = window.findChild(QCheckBox, "captureSpanCheck")
    capture_increment = window.findChild(QSpinBox, "captureIncrementSpin")
    current_index = window.findChild(QSpinBox, "currentIndexSpin")
    decrement_index = window.findChild(QPushButton, "indexDecrementButton")
    increment_index = window.findChild(QPushButton, "indexIncrementButton")
    decrement_index.setMaximumHeight(16777215)
    increment_index.setMaximumHeight(16777215)
    capture_button = window.findChild(QPushButton, "captureProjectButton")
    refresh_gallery_button = window.findChild(QPushButton, "refreshGalleryButton")
    capture_column_label = window.findChild(QLabel, "captureColumnLabel")
    browser_panel = window.findChild(QWidget, "browserPanel")
    gallery_panel = window.findChild(QWidget, "galleryPanel")
    terminal_panel = window.findChild(QWidget, "terminalPanel")
    detail_tabs = window.findChild(QTabWidget, "detailTabs")
    gallery_tab = window.findChild(QWidget, "galleryTab")
    metadata_tab = window.findChild(QWidget, "metadataTab")
    content_splitter = window.findChild(QSplitter, "contentSplitter")
    gallery_splitter = window.findChild(QSplitter, "gallerySplitter")
    preview_terminal_splitter = window.findChild(QSplitter, "previewTerminalSplitter")
    capture_controls = (capture_column, capture_span, capture_increment, current_index,
                        decrement_index, increment_index, capture_button)
    for control in capture_controls:
        control.setEnabled(False)
    status = window.statusBar()
    content_splitter.setSizes([250, 950])
    gallery_splitter.setSizes([650, 300])
    preview_terminal_splitter.setSizes([430, 215])
    compact_mode = False
    compact_action = None
    automatic_layout_action = None
    active_project = None
    current_preview_image = None
    pending_select_latest = False
    pending_preferred_path = None
    retake_restore = None
    terminal_process = QProcess(window)
    terminal_process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
    project_watcher = QFileSystemWatcher(window)
    refresh_timer = QTimer(window)
    refresh_timer.setSingleShot(True)
    refresh_timer.setInterval(200)

    terminal_label = window.findChild(QLabel, "terminalLabel")
    old_header_layout = window.findChild(QHBoxLayout, "terminalHeaderLayout")
    main_terminal_layout = terminal_panel.layout()
    for position in range(main_terminal_layout.count()):
        if main_terminal_layout.itemAt(position).layout() is old_header_layout:
            main_terminal_layout.takeAt(position)
            break
    while old_header_layout.count():
        old_header_layout.takeAt(0)
    old_header_layout.deleteLater()

    capture_header = QWidget(terminal_panel)
    capture_header.setObjectName("captureHeader")
    capture_header_layout = QGridLayout(capture_header)
    capture_header_layout.setContentsMargins(0, 0, 0, 0)
    capture_header_layout.setHorizontalSpacing(6)
    capture_header_layout.setVerticalSpacing(1)
    main_terminal_layout.insertWidget(0, capture_header)

    capture_column_label.setText("COLUMN")
    capture_step_label = QLabel("STEP", capture_header)
    capture_step_label.setObjectName("captureStepLabel")
    current_index_label = QLabel("INDEX", capture_header)
    current_index_label.setObjectName("currentIndexLabel")
    for label in (capture_column_label, capture_step_label, current_index_label):
        label.setStyleSheet("color: #8f9aa7; font-size: 9px; font-weight: 600; letter-spacing: 1px;")

    step_decrement = QPushButton("−", capture_header)
    step_decrement.setObjectName("captureStepDecrementButton")
    step_increment = QPushButton("+", capture_header)
    step_increment.setObjectName("captureStepIncrementButton")
    for button in (step_decrement, step_increment, decrement_index, increment_index):
        button.setFixedWidth(26)
        button.setFixedHeight(34)
    capture_increment.setPrefix("")
    capture_increment.setButtonSymbols(current_index.buttonSymbols())
    capture_increment.setFixedWidth(46)
    capture_increment.setFixedHeight(34)
    current_index.setPrefix("")
    current_index.setFixedWidth(52)
    current_index.setFixedHeight(34)

    step_group = QWidget(capture_header)
    step_group.setObjectName("captureStepGroup")
    step_group_layout = QHBoxLayout(step_group)
    step_group_layout.setContentsMargins(0, 0, 0, 0)
    step_group_layout.setSpacing(0)
    step_group_layout.addWidget(step_decrement)
    step_group_layout.addWidget(capture_increment)
    step_group_layout.addWidget(step_increment)
    step_group.setFixedHeight(34)

    index_group = QWidget(capture_header)
    index_group.setObjectName("captureIndexGroup")
    index_group_layout = QHBoxLayout(index_group)
    index_group_layout.setContentsMargins(0, 0, 0, 0)
    index_group_layout.setSpacing(0)
    index_group_layout.addWidget(decrement_index)
    index_group_layout.addWidget(current_index)
    index_group_layout.addWidget(increment_index)
    index_group.setFixedHeight(34)

    capture_column.setMinimumWidth(125)
    capture_column.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    capture_span.setText("-S")
    capture_span.setToolTip("Capture the complete range from the current index to the next index")
    capture_button.setText("")
    capture_icon_pixmap = QPixmap(18, 18)
    capture_icon_pixmap.fill(Qt.GlobalColor.transparent)
    capture_icon_painter = QPainter(capture_icon_pixmap)
    capture_icon_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    capture_icon_painter.setPen(QPen(QColor("#102238"), 2))
    for start, end in (
        ((3, 7), (3, 3)), ((3, 3), (7, 3)),
        ((11, 3), (15, 3)), ((15, 3), (15, 7)),
        ((15, 11), (15, 15)), ((15, 15), (11, 15)),
        ((7, 15), (3, 15)), ((3, 15), (3, 11)),
    ):
        capture_icon_painter.drawLine(*start, *end)
    capture_icon_painter.setBrush(QColor("#102238"))
    capture_icon_painter.drawEllipse(7, 7, 4, 4)
    capture_icon_painter.end()
    capture_button.setIcon(QIcon(capture_icon_pixmap))
    capture_button.setFixedWidth(36)
    capture_button.setToolTip("Capture Next")
    capture_controls = (*capture_controls, step_decrement, step_increment)
    step_decrement.setEnabled(False)
    step_increment.setEnabled(False)

    compact_header_wrapped = None

    def configure_capture_header(compact):
        nonlocal compact_header_wrapped
        while capture_header_layout.count():
            capture_header_layout.takeAt(0)
        for column in range(6):
            capture_header_layout.setColumnStretch(column, 0)
        terminal_label.hide()
        for label in (capture_column_label, capture_step_label, current_index_label):
            label.show()
        wrapped = compact and window.width() < 500
        compact_header_wrapped = wrapped if compact else None
        capture_header_layout.setContentsMargins(0, 2, 0, 2)
        capture_header_layout.setColumnStretch(0, 1)
        if wrapped:
            capture_header.setMinimumHeight(98)
            capture_header_layout.addWidget(capture_column_label, 0, 0)
            capture_header_layout.addWidget(capture_step_label, 0, 2)
            capture_header_layout.addWidget(capture_column, 1, 0)
            capture_header_layout.addWidget(capture_span, 1, 1)
            capture_header_layout.addWidget(step_group, 1, 2)
            capture_header_layout.addWidget(current_index_label, 2, 0)
            capture_header_layout.addWidget(index_group, 3, 0)
            capture_header_layout.setColumnStretch(1, 1)
            capture_header_layout.addWidget(capture_button, 3, 2)
        else:
            capture_header.setMinimumHeight(53)
            capture_header_layout.addWidget(capture_column_label, 0, 0)
            capture_header_layout.addWidget(capture_step_label, 0, 2)
            capture_header_layout.addWidget(current_index_label, 0, 3)
            capture_header_layout.addWidget(capture_column, 1, 0)
            capture_header_layout.addWidget(capture_span, 1, 1)
            capture_header_layout.addWidget(step_group, 1, 2)
            capture_header_layout.addWidget(index_group, 1, 3)
            capture_header_layout.addWidget(capture_button, 1, 4)

    def update_compact_capture_layout():
        if compact_mode and compact_header_wrapped != (window.width() < 500):
            configure_capture_header(True)

    configure_capture_header(False)

    compact_tabs = QTabWidget(window)
    compact_tabs.setObjectName("compactBottomTabs")
    compact_projects_page = QWidget(compact_tabs)
    compact_terminal_page = QWidget(compact_tabs)
    compact_projects_layout = QVBoxLayout(compact_projects_page)
    compact_terminal_layout = QVBoxLayout(compact_terminal_page)
    for layout in (compact_projects_layout, compact_terminal_layout):
        layout.setContentsMargins(0, 0, 0, 0)
    compact_tabs.addTab(compact_projects_page, "Projects")
    compact_tabs.addTab(compact_terminal_page, "Terminal")
    compact_tabs.hide()

    def append_terminal(text):
        terminal_output.appendPlainText(text.rstrip("\n"))
        terminal_output.verticalScrollBar().setValue(terminal_output.verticalScrollBar().maximum())

    def append_process_output():
        output = bytes(terminal_process.readAllStandardOutput()).decode(errors="replace")
        if output:
            append_terminal(output)

    def restore_retake_controls():
        if not retake_restore:
            return
        restore_category, restore_index = retake_restore
        if capture_column.findText(restore_category) >= 0:
            capture_column.blockSignals(True)
            capture_column.setCurrentText(restore_category)
            capture_column.blockSignals(False)
        current_index.blockSignals(True)
        current_index.setValue(restore_index)
        current_index.blockSignals(False)

    def finish_terminal_command(exit_code, _exit_status):
        nonlocal pending_preferred_path, pending_select_latest, retake_restore
        append_process_output()
        append_terminal(f"[process exited with code {exit_code}]")
        terminal_input.setEnabled(True)
        terminal_input.setFocus()
        for control in capture_controls:
            control.setEnabled(active_project is not None)
        if active_project:
            refresh_active_project(
                select_latest=exit_code == 0 and pending_select_latest,
                preferred_path=pending_preferred_path if exit_code == 0 else None,
            )
            sync_capture_controls()
            restore_retake_controls()
        pending_select_latest = False
        pending_preferred_path = None
        retake_restore = None

    def run_proofshot(arguments, preferred_path=None):
        nonlocal pending_preferred_path, pending_select_latest
        if terminal_process.state() != QProcess.ProcessState.NotRunning:
            append_terminal("A Proofshot command is already running.")
            return
        if "--gui" in arguments:
            append_terminal("The GUI cannot be launched from its own terminal.")
            return
        if active_project and "-D" not in arguments and "--dir" not in arguments:
            arguments.extend(["-D", active_project])
        pending_select_latest = command_creates_image(arguments)
        pending_preferred_path = Path(preferred_path) if preferred_path else None
        append_terminal(f"$ proofshot {shlex.join(arguments)}")
        terminal_input.setEnabled(False)
        for control in capture_controls:
            control.setEnabled(False)
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
        nonlocal pending_preferred_path, pending_select_latest, retake_restore
        append_terminal(f"[could not start Proofshot: {terminal_process.errorString()}]")
        terminal_input.setEnabled(True)
        for control in capture_controls:
            control.setEnabled(active_project is not None)
        if active_project:
            sync_capture_controls()
            restore_retake_controls()
        pending_select_latest = False
        pending_preferred_path = None
        retake_restore = None

    terminal_process.readyReadStandardOutput.connect(append_process_output)
    terminal_process.finished.connect(finish_terminal_command)
    terminal_process.errorOccurred.connect(terminal_error)

    class ThumbnailDelegate(QStyledItemDelegate):
        """Render gallery items as uniform rounded image cards with title overlays."""
        def paint(self, painter, option, index):
            if compact_mode:
                self.paint_list_row(painter, option, index)
                return
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

        def paint_list_row(self, painter, option, index):
            painter.save()
            row = option.rect.adjusted(3, 3, -3, -3)
            path = QPainterPath()
            path.addRoundedRect(row, 6, 6)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            selected = bool(option.state & QStyle.StateFlag.State_Selected)
            painter.fillPath(path, QColor("#2b3947" if selected else "#20252b"))

            thumbnail = row.adjusted(5, 4, 0, -4)
            thumbnail.setWidth(min(96, max(64, row.width() // 4)))
            icon = index.data(Qt.ItemDataRole.DecorationRole)
            if icon:
                pixmap = icon.pixmap(thumbnail.size()).scaled(
                    thumbnail.size(), Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)
                painter.drawPixmap(
                    thumbnail.left() + (thumbnail.width() - pixmap.width()) // 2,
                    thumbnail.top() + (thumbnail.height() - pixmap.height()) // 2,
                    pixmap)

            text_left = thumbnail.right() + 12
            text_width = max(40, row.right() - text_left - 8)
            title = index.data(Qt.ItemDataRole.DisplayRole) or ""
            image = index.data(Qt.ItemDataRole.UserRole) or {}
            image_index = image.get("index")
            image_end = image.get("index_end")
            if image_index is None:
                index_text = "Unindexed"
            elif image_end is not None and image_end != image_index:
                index_text = f"Index {image_index}–{image_end}"
            else:
                index_text = f"Index {image_index}"

            font = painter.font()
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor("#f4f6f8"))
            line_height = painter.fontMetrics().height()
            title_top = row.top() + 4
            painter.drawText(
                text_left, title_top, text_width, line_height,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                painter.fontMetrics().elidedText(title, Qt.TextElideMode.ElideMiddle, text_width),
            )
            font.setBold(False)
            painter.setFont(font)
            painter.setPen(QColor("#aeb8c4"))
            detail = f"{image.get('category') or 'Unknown column'} · {index_text}"
            painter.drawText(
                text_left, title_top + line_height + 1, text_width, line_height,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                painter.fontMetrics().elidedText(detail, Qt.TextElideMode.ElideRight, text_width),
            )
            if selected:
                painter.setPen(QColor("#6da9e3"))
                painter.drawRoundedRect(row.adjusted(1, 1, -1, -1), 5, 5)
            painter.restore()

        def sizeHint(self, option, index):
            if compact_mode:
                row_height = max(56, image_gallery.fontMetrics().height() * 2 + 12)
                return QSize(max(220, image_gallery.viewport().width() - 12), row_height)
            return image_gallery.iconSize() + QSize(8, 8)

    thumbnail_delegate = ThumbnailDelegate(image_gallery)
    image_gallery.setItemDelegate(thumbnail_delegate)
    image_gallery.setUniformItemSizes(True)

    def set_gallery_presentation(compact):
        if compact:
            image_gallery.setViewMode(QListView.ViewMode.ListMode)
            image_gallery.setFlow(QListView.Flow.TopToBottom)
            image_gallery.setWrapping(False)
            image_gallery.setIconSize(QSize(96, 60))
            image_gallery.setGridSize(QSize())
            image_gallery.setSpacing(3)
        else:
            image_gallery.setViewMode(QListView.ViewMode.IconMode)
            image_gallery.setFlow(QListView.Flow.LeftToRight)
            image_gallery.setWrapping(True)
            image_gallery.setIconSize(QSize(160, 110))
            image_gallery.setGridSize(QSize(176, 126))
            image_gallery.setSpacing(8)
        image_gallery.scheduleDelayedItemsLayout()
        image_gallery.viewport().update()

    def set_compact_mode(enabled):
        nonlocal compact_mode
        enabled = bool(enabled)
        if compact_mode == enabled:
            return
        compact_mode = enabled
        if enabled:
            compact_projects_layout.addWidget(browser_panel)
            compact_terminal_layout.addWidget(terminal_panel)
            gallery_splitter.setOrientation(Qt.Orientation.Vertical)
            gallery_splitter.insertWidget(2, compact_tabs)
            compact_tabs.show()
            preview.setMinimumSize(0, 160)
            detail_tabs.setMinimumWidth(0)
            configure_capture_header(True)
            set_gallery_presentation(True)
            gallery_splitter.setSizes([1, 1, 1])
        else:
            compact_projects_layout.removeWidget(browser_panel)
            compact_terminal_layout.removeWidget(terminal_panel)
            content_splitter.insertWidget(0, browser_panel)
            preview_terminal_splitter.insertWidget(1, terminal_panel)
            compact_tabs.hide()
            compact_tabs.setParent(window)
            gallery_splitter.setOrientation(Qt.Orientation.Horizontal)
            preview.setMinimumSize(320, 260)
            detail_tabs.setMinimumWidth(280)
            configure_capture_header(False)
            set_gallery_presentation(False)
            content_splitter.setSizes([250, 950])
            gallery_splitter.setSizes([650, 300])
            preview_terminal_splitter.setSizes([430, 215])
        if compact_action is not None:
            compact_action.blockSignals(True)
            compact_action.setChecked(enabled)
            compact_action.blockSignals(False)

    def apply_automatic_layout():
        if automatic_layout_action is not None and automatic_layout_action.isChecked():
            set_compact_mode(should_use_compact_layout(window.width(), window.height()))

    def update_responsive_layout():
        apply_automatic_layout()
        update_compact_capture_layout()

    class WindowLayoutFilter(QObject):
        def eventFilter(self, watched, event):
            if watched is window and event.type() == QEvent.Type.Resize:
                QTimer.singleShot(0, update_responsive_layout)
            return False

    window_layout_filter = WindowLayoutFilter(window)
    window.installEventFilter(window_layout_filter)

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
        nonlocal current_preview_image
        current_preview_image = image
        pixmap = QPixmap(str(image["path"]))
        if pixmap.isNull():
            preview.clear()
            preview.setText("Unable to load image")
            return
        preview.setPixmap(pixmap.scaled(preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        preview.setToolTip(f"{image['filename']} — {pixmap.width()} × {pixmap.height()} px")

    class PreviewResizeFilter(QObject):
        def eventFilter(self, watched, event):
            if watched is preview and event.type() == QEvent.Type.Resize and current_preview_image:
                QTimer.singleShot(0, lambda: show_preview(current_preview_image))
            return False

    preview_resize_filter = PreviewResizeFilter(preview)
    preview.installEventFilter(preview_resize_filter)

    def update_metadata(image):
        pixmap = QPixmap(str(image["path"]))
        metadata_label.setText(
            f"<b>{image['filename']}</b><br>"
            f"Column: {image['category'] or 'Unknown'}<br>"
            f"Index: {image['index'] if image['index'] is not None else 'Unknown'}<br>"
            f"Dimensions: {pixmap.width()} × {pixmap.height()} px<br>"
            f"File size: {image['size']:,} bytes<br>"
            f"Manifest: {'yes' if image['manifested'] else 'no'}"
        )

    def render_gallery(preferred_path=None, select_latest=False):
        nonlocal current_preview_image
        current_item = image_gallery.currentItem()
        current_image = current_item.data(Qt.ItemDataRole.UserRole) if current_item else None
        preserved_path = preferred_path or (current_image and current_image["path"])
        image_gallery.clear()
        query = search_filter.text().strip().lower()
        visible = [image for image in selected_images if not query or query in " ".join((image["filename"], image["category"], str(image["index"] or ""))).lower()]
        for image in visible:
            item = QListWidgetItem(QIcon(str(image["path"])), image["filename"])
            item.setData(Qt.ItemDataRole.UserRole, image)
            shown_index = image["index"] if image["index"] is not None else "Unknown"
            item.setToolTip(f"{image['filename']}\n{image['category'] or 'Unknown'} · {shown_index}")
            image_gallery.addItem(item)
        status.showMessage(f"{len(visible)} of {len(selected_images)} image(s)")
        if not visible:
            current_preview_image = None
            preview.clear()
            preview.setText("No matching images" if selected_images else "No PNG images in this project")
            metadata_label.setText("Select an image to see its metadata.")
            return

        selected = None
        if preserved_path:
            selected = next((image for image in visible if image["path"] == Path(preserved_path)), None)
        if selected is None and select_latest:
            selected = most_recent_image(visible)
        selected = selected or most_recent_image(visible)
        selected_row = visible.index(selected)
        image_gallery.setCurrentRow(selected_row)
        show_preview(selected)
        update_metadata(selected)

    def populate_images(path, select_latest=False, preferred_path=None):
        nonlocal active_project
        active_project = str(path)
        watched = project_watcher.directories()
        if watched != [active_project]:
            if watched:
                project_watcher.removePaths(watched)
            if Path(active_project).is_dir():
                project_watcher.addPath(active_project)
        selected_images[:] = project_images(Path(path))
        project_label.setText(str(path))
        project_label.setToolTip(str(path))
        render_gallery(preferred_path=preferred_path, select_latest=select_latest)
        sync_capture_controls()
        controls_enabled = terminal_process.state() == QProcess.ProcessState.NotRunning
        for control in capture_controls:
            control.setEnabled(controls_enabled)

    def refresh_active_project(select_latest=False, preferred_path=None):
        if not active_project or not Path(active_project).is_dir():
            return
        current_item = image_gallery.currentItem()
        current_image = current_item.data(Qt.ItemDataRole.UserRole) if current_item else None
        if preferred_path is None and not select_latest:
            preferred_path = current_image["path"] if current_image else None
        if select_latest and search_filter.text():
            search_filter.blockSignals(True)
            search_filter.clear()
            search_filter.blockSignals(False)
        populate_images(active_project, select_latest=select_latest, preferred_path=preferred_path)

    def refresh():
        tree.clear()
        projects = discover_projects(workspace)
        active_item = None
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
                    if project["path"] == active_project:
                        active_item = child
            root.setExpanded(True)
        if active_item is not None:
            tree.setCurrentItem(active_item)
            refresh_active_project()
        else:
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
            reset_indices(load_config(target), target)
            refresh()
        except (OSError, ValueError) as exc:
            QMessageBox.critical(window, "Create project failed", str(exc))

    def select_tree_item(item, _column):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path:
            populate_images(path, select_latest=True)

    def select_image(item, _previous=None):
        if item is None:
            return
        image = item.data(Qt.ItemDataRole.UserRole)
        if image:
            show_preview(image)
            update_metadata(image)

    def selected_image():
        item = image_gallery.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def delete_selected_image():
        image = selected_image()
        if image is None or terminal_process.state() != QProcess.ProcessState.NotRunning:
            return
        answer = QMessageBox.warning(
            window,
            "Delete screenshot",
            f"Delete {image['filename']}?\n\nThis removes the image and its manifest record.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Yes:
            run_proofshot(["--remove-screenshot", image["filename"]])

    def retake_selected_image():
        nonlocal retake_restore
        image = selected_image()
        if image is None or terminal_process.state() != QProcess.ProcessState.NotRunning:
            return
        category = image.get("category")
        index = image.get("index")
        if not image.get("manifested") or not category or index is None:
            QMessageBox.information(
                window,
                "Cannot retake screenshot",
                "This image has no manifest column and index. Add it to the manifest before retaking it.",
            )
            return
        answer = QMessageBox.question(
            window,
            "Retake screenshot",
            f"Retake {image['filename']} at {category} index {index}?\n\n"
            "The original remains unchanged if you cancel the capture.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        retake_restore = (capture_column.currentText(), current_index.value())
        if capture_column.findText(category) >= 0:
            capture_column.blockSignals(True)
            capture_column.setCurrentText(category)
            capture_column.blockSignals(False)
        current_index.blockSignals(True)
        current_index.setValue(index)
        current_index.blockSignals(False)
        run_proofshot(["--retake-screenshot", image["filename"]], preferred_path=image["path"])

    def show_image_context_menu(global_position):
        image = selected_image()
        if image is None:
            return
        menu = QMenu(window)
        retake_action = menu.addAction(
            window.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload),
            "Retake screenshot…",
        )
        delete_action = menu.addAction(
            window.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon),
            "Delete screenshot…",
        )
        ready = terminal_process.state() == QProcess.ProcessState.NotRunning
        retake_action.setEnabled(
            ready and image.get("manifested") and bool(image.get("category")) and image.get("index") is not None
        )
        delete_action.setEnabled(ready)
        selected_action = menu.exec(global_position)
        if selected_action is retake_action:
            retake_selected_image()
        elif selected_action is delete_action:
            delete_selected_image()

    def show_gallery_context_menu(position):
        item = image_gallery.itemAt(position)
        if item is None:
            return
        image_gallery.setCurrentItem(item)
        show_image_context_menu(image_gallery.viewport().mapToGlobal(position))

    def show_preview_context_menu(position):
        show_image_context_menu(preview.mapToGlobal(position))

    def sync_current_index():
        category = capture_column.currentText()
        value = load_counts(Path(active_project)).get(category, 0) if category and active_project else 0
        current_index.blockSignals(True)
        current_index.setValue(value)
        current_index.blockSignals(False)

    def sync_capture_controls():
        if not active_project:
            return
        config = load_config(Path(active_project))
        categories = list(config.get("categories", {})) or [config["form_category"], config["proof_category"]]
        selected_category = capture_column.currentText()
        capture_column.blockSignals(True)
        capture_column.clear()
        capture_column.addItems(categories)
        if selected_category in categories:
            capture_column.setCurrentText(selected_category)
        capture_column.blockSignals(False)
        sync_current_index()

    def set_active_index(value):
        if not active_project or not capture_column.currentText():
            return
        category = capture_column.currentText()
        set_index_for_type(category, value, Path(active_project))
        status.showMessage(f"{category} index set to {value}", 2500)

    def capture_next():
        if not active_project:
            QMessageBox.information(window, "Select a project", "Select a project before starting a capture.")
            return
        run_proofshot(capture_arguments(
            capture_column.currentText(),
            capture_increment.value(),
            capture_span.isChecked(),
        ))

    file_menu = window.menuBar().addMenu("&File")
    view_menu = window.menuBar().addMenu("&View")

    add_path_action = QAction("Add discovery path…", window)
    refresh_action = QAction("Refresh", window)
    refresh_action.setShortcut(QKeySequence.StandardKey.Refresh)
    new_project_action = QAction("New project…", window)
    exit_action = QAction("Exit", window)
    add_path_action.triggered.connect(add_path)
    refresh_action.triggered.connect(refresh)
    new_project_action.triggered.connect(create_project)
    exit_action.triggered.connect(window.close)
    file_menu.addActions([add_path_action, refresh_action, new_project_action])
    file_menu.addSeparator()
    file_menu.addAction(exit_action)

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
    automatic_layout_action = QAction("Automatic layout", window)
    automatic_layout_action.setCheckable(True)
    automatic_layout_action.setChecked(True)
    compact_action = QAction("Compact layout", window)
    compact_action.setCheckable(True)
    compact_action.setEnabled(False)
    compact_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
    browser_action.toggled.connect(browser_panel.setVisible)
    terminal_action.toggled.connect(terminal_panel.setVisible)
    gallery_action.toggled.connect(
        lambda visible: detail_tabs.setTabVisible(detail_tabs.indexOf(gallery_tab), visible))
    metadata_action.toggled.connect(
        lambda visible: detail_tabs.setTabVisible(detail_tabs.indexOf(metadata_tab), visible))
    automatic_layout_action.toggled.connect(
        lambda automatic: (compact_action.setEnabled(not automatic), apply_automatic_layout()))
    compact_action.toggled.connect(set_compact_mode)
    view_menu.addActions([
        browser_action,
        terminal_action,
        gallery_action,
        metadata_action,
    ])
    view_menu.addSeparator()
    view_menu.addActions([automatic_layout_action, compact_action])

    capture_button.setShortcut(QKeySequence("Ctrl+Return"))
    capture_button.clicked.connect(capture_next)
    refresh_gallery_button.clicked.connect(lambda: refresh_active_project(select_latest=True))
    capture_column.currentTextChanged.connect(lambda _category: sync_current_index())
    current_index.valueChanged.connect(set_active_index)
    decrement_index.clicked.connect(lambda: current_index.stepDown())
    increment_index.clicked.connect(lambda: current_index.stepUp())
    step_decrement.clicked.connect(lambda: capture_increment.stepDown())
    step_increment.clicked.connect(lambda: capture_increment.stepUp())
    image_gallery.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    preview.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    image_gallery.customContextMenuRequested.connect(show_gallery_context_menu)
    preview.customContextMenuRequested.connect(show_preview_context_menu)
    delete_image_action = QAction("Delete selected screenshot", image_gallery)
    delete_image_action.setShortcut(QKeySequence.StandardKey.Delete)
    delete_image_action.setShortcutContext(Qt.ShortcutContext.WidgetShortcut)
    delete_image_action.triggered.connect(delete_selected_image)
    image_gallery.addAction(delete_image_action)
    retake_image_action = QAction("Retake selected screenshot", image_gallery)
    retake_image_action.setShortcut(QKeySequence("Ctrl+Shift+R"))
    retake_image_action.setShortcutContext(Qt.ShortcutContext.WidgetShortcut)
    retake_image_action.triggered.connect(retake_selected_image)
    image_gallery.addAction(retake_image_action)
    tree.itemClicked.connect(select_tree_item)
    image_gallery.currentItemChanged.connect(select_image)
    search_filter.textChanged.connect(lambda _text: render_gallery())
    terminal_input.returnPressed.connect(run_terminal_command)
    project_watcher.directoryChanged.connect(lambda _path: refresh_timer.start())
    refresh_timer.timeout.connect(lambda: refresh_active_project(select_latest=True))
    QWidget.setTabOrder(capture_column, capture_span)
    QWidget.setTabOrder(capture_span, capture_increment)
    QWidget.setTabOrder(capture_increment, current_index)
    QWidget.setTabOrder(current_index, capture_button)
    QWidget.setTabOrder(capture_button, terminal_output)
    QWidget.setTabOrder(terminal_output, terminal_input)
    refresh()
    window.show()
    QTimer.singleShot(0, update_responsive_layout)
    return app.exec()
