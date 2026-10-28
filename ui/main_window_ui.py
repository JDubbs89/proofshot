# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.11.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QAbstractSpinBox, QApplication, QCheckBox,
    QComboBox, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QListView, QListWidget,
    QListWidgetItem, QMainWindow, QMenuBar, QPlainTextEdit,
    QPushButton, QSizePolicy, QSpacerItem, QSpinBox,
    QSplitter, QStatusBar, QTabWidget, QToolBox,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1200, 760)
        MainWindow.setMinimumSize(QSize(420, 640))
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.mainLayout = QVBoxLayout(self.centralwidget)
        self.mainLayout.setSpacing(10)
        self.mainLayout.setObjectName(u"mainLayout")
        self.mainLayout.setContentsMargins(14, 14, 14, 14)
        self.contentSplitter = QSplitter(self.centralwidget)
        self.contentSplitter.setObjectName(u"contentSplitter")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.contentSplitter.sizePolicy().hasHeightForWidth())
        self.contentSplitter.setSizePolicy(sizePolicy)
        self.contentSplitter.setOrientation(Qt.Orientation.Horizontal)
        self.browserPanel = QFrame(self.contentSplitter)
        self.browserPanel.setObjectName(u"browserPanel")
        self.browserPanel.setFrameShape(QFrame.Shape.StyledPanel)
        self.browserLayout = QVBoxLayout(self.browserPanel)
        self.browserLayout.setObjectName(u"browserLayout")
        self.browserLabel = QLabel(self.browserPanel)
        self.browserLabel.setObjectName(u"browserLabel")

        self.browserLayout.addWidget(self.browserLabel)

        self.treeView = QTreeWidget(self.browserPanel)
        self.treeView.setObjectName(u"treeView")
        self.treeView.setHeaderHidden(True)

        self.browserLayout.addWidget(self.treeView)

        self.contentSplitter.addWidget(self.browserPanel)
        self.galleryPanel = QFrame(self.contentSplitter)
        self.galleryPanel.setObjectName(u"galleryPanel")
        self.galleryPanel.setFrameShape(QFrame.Shape.StyledPanel)
        self.galleryLayout = QVBoxLayout(self.galleryPanel)
        self.galleryLayout.setObjectName(u"galleryLayout")
        self.projectHeaderLayout = QHBoxLayout()
        self.projectHeaderLayout.setObjectName(u"projectHeaderLayout")
        self.projectLabel = QLabel(self.galleryPanel)
        self.projectLabel.setObjectName(u"projectLabel")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.projectLabel.sizePolicy().hasHeightForWidth())
        self.projectLabel.setSizePolicy(sizePolicy1)

        self.projectHeaderLayout.addWidget(self.projectLabel)

        self.projectHeaderSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.projectHeaderLayout.addItem(self.projectHeaderSpacer)

        self.refreshGalleryButton = QPushButton(self.galleryPanel)
        self.refreshGalleryButton.setObjectName(u"refreshGalleryButton")

        self.projectHeaderLayout.addWidget(self.refreshGalleryButton)


        self.galleryLayout.addLayout(self.projectHeaderLayout)

        self.gallerySplitter = QSplitter(self.galleryPanel)
        self.gallerySplitter.setObjectName(u"gallerySplitter")
        self.gallerySplitter.setOrientation(Qt.Orientation.Horizontal)
        self.previewTerminalSplitter = QSplitter(self.gallerySplitter)
        self.previewTerminalSplitter.setObjectName(u"previewTerminalSplitter")
        self.previewTerminalSplitter.setOrientation(Qt.Orientation.Vertical)
        self.ImagePreview = QLabel(self.previewTerminalSplitter)
        self.ImagePreview.setObjectName(u"ImagePreview")
        self.ImagePreview.setMinimumSize(QSize(320, 260))
        self.ImagePreview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.previewTerminalSplitter.addWidget(self.ImagePreview)
        self.terminalPanel = QFrame(self.previewTerminalSplitter)
        self.terminalPanel.setObjectName(u"terminalPanel")
        self.terminalPanel.setFrameShape(QFrame.Shape.StyledPanel)
        self.terminalLayout = QVBoxLayout(self.terminalPanel)
        self.terminalLayout.setSpacing(4)
        self.terminalLayout.setObjectName(u"terminalLayout")
        self.terminalLayout.setContentsMargins(6, 6, 6, 6)
        self.terminalHeaderLayout = QHBoxLayout()
        self.terminalHeaderLayout.setSpacing(6)
        self.terminalHeaderLayout.setObjectName(u"terminalHeaderLayout")
        self.terminalLabel = QLabel(self.terminalPanel)
        self.terminalLabel.setObjectName(u"terminalLabel")

        self.terminalHeaderLayout.addWidget(self.terminalLabel)

        self.captureColumnLabel = QLabel(self.terminalPanel)
        self.captureColumnLabel.setObjectName(u"captureColumnLabel")

        self.terminalHeaderLayout.addWidget(self.captureColumnLabel)

        self.captureColumnCombo = QComboBox(self.terminalPanel)
        self.captureColumnCombo.setObjectName(u"captureColumnCombo")
        self.captureColumnCombo.setMinimumSize(QSize(96, 30))

        self.terminalHeaderLayout.addWidget(self.captureColumnCombo)

        self.captureSpanCheck = QCheckBox(self.terminalPanel)
        self.captureSpanCheck.setObjectName(u"captureSpanCheck")

        self.terminalHeaderLayout.addWidget(self.captureSpanCheck)

        self.captureIncrementSpin = QSpinBox(self.terminalPanel)
        self.captureIncrementSpin.setObjectName(u"captureIncrementSpin")
        self.captureIncrementSpin.setMinimum(1)
        self.captureIncrementSpin.setMaximum(99999)
        self.captureIncrementSpin.setValue(1)
        self.captureIncrementSpin.setMinimumSize(QSize(78, 30))

        self.terminalHeaderLayout.addWidget(self.captureIncrementSpin)

        self.indexDecrementButton = QPushButton(self.terminalPanel)
        self.indexDecrementButton.setObjectName(u"indexDecrementButton")
        self.indexDecrementButton.setMinimumSize(QSize(30, 30))
        self.indexDecrementButton.setMaximumSize(QSize(30, 30))

        self.terminalHeaderLayout.addWidget(self.indexDecrementButton)

        self.currentIndexSpin = QSpinBox(self.terminalPanel)
        self.currentIndexSpin.setObjectName(u"currentIndexSpin")
        self.currentIndexSpin.setMinimum(0)
        self.currentIndexSpin.setMaximum(99999)
        self.currentIndexSpin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.currentIndexSpin.setMinimumSize(QSize(84, 30))
        self.currentIndexSpin.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.terminalHeaderLayout.addWidget(self.currentIndexSpin)

        self.indexIncrementButton = QPushButton(self.terminalPanel)
        self.indexIncrementButton.setObjectName(u"indexIncrementButton")
        self.indexIncrementButton.setMinimumSize(QSize(30, 30))
        self.indexIncrementButton.setMaximumSize(QSize(30, 30))

        self.terminalHeaderLayout.addWidget(self.indexIncrementButton)

        self.terminalHeaderSpacer = QSpacerItem(16, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.terminalHeaderLayout.addItem(self.terminalHeaderSpacer)

        self.captureProjectButton = QPushButton(self.terminalPanel)
        self.captureProjectButton.setObjectName(u"captureProjectButton")
        self.captureProjectButton.setMinimumSize(QSize(112, 32))

        self.terminalHeaderLayout.addWidget(self.captureProjectButton)


        self.terminalLayout.addLayout(self.terminalHeaderLayout)

        self.terminalOutput = QPlainTextEdit(self.terminalPanel)
        self.terminalOutput.setObjectName(u"terminalOutput")
        self.terminalOutput.setReadOnly(True)

        self.terminalLayout.addWidget(self.terminalOutput)

        self.terminalInput = QLineEdit(self.terminalPanel)
        self.terminalInput.setObjectName(u"terminalInput")

        self.terminalLayout.addWidget(self.terminalInput)

        self.previewTerminalSplitter.addWidget(self.terminalPanel)
        self.gallerySplitter.addWidget(self.previewTerminalSplitter)
        self.detailTabs = QTabWidget(self.gallerySplitter)
        self.detailTabs.setObjectName(u"detailTabs")
        self.detailTabs.setMinimumSize(QSize(280, 0))
        self.galleryTab = QWidget()
        self.galleryTab.setObjectName(u"galleryTab")
        self.galleryControlsLayout = QVBoxLayout(self.galleryTab)
        self.galleryControlsLayout.setObjectName(u"galleryControlsLayout")
        self.searchFilter = QLineEdit(self.galleryTab)
        self.searchFilter.setObjectName(u"searchFilter")
        self.searchFilter.setClearButtonEnabled(True)

        self.galleryControlsLayout.addWidget(self.searchFilter)

        self.ImageGallery = QListWidget(self.galleryTab)
        self.ImageGallery.setObjectName(u"ImageGallery")
        self.ImageGallery.setViewMode(QListView.ViewMode.IconMode)
        self.ImageGallery.setFlow(QListView.Flow.LeftToRight)
        self.ImageGallery.setIsWrapping(True)
        self.ImageGallery.setResizeMode(QListView.ResizeMode.Adjust)
        self.ImageGallery.setMovement(QListView.Movement.Static)
        self.ImageGallery.setIconSize(QSize(160, 110))
        self.ImageGallery.setGridSize(QSize(176, 126))
        self.ImageGallery.setSpacing(8)
        self.ImageGallery.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self.galleryControlsLayout.addWidget(self.ImageGallery)

        self.detailTabs.addTab(self.galleryTab, "")
        self.metadataTab = QWidget()
        self.metadataTab.setObjectName(u"metadataTab")
        self.metadataLayout = QVBoxLayout(self.metadataTab)
        self.metadataLayout.setObjectName(u"metadataLayout")
        self.metadataAccordion = QToolBox(self.metadataTab)
        self.metadataAccordion.setObjectName(u"metadataAccordion")
        self.metadataPage = QWidget()
        self.metadataPage.setObjectName(u"metadataPage")
        self.metadataPageLayout = QVBoxLayout(self.metadataPage)
        self.metadataPageLayout.setObjectName(u"metadataPageLayout")
        self.metadataLabel = QLabel(self.metadataPage)
        self.metadataLabel.setObjectName(u"metadataLabel")
        self.metadataLabel.setAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.metadataLabel.setWordWrap(True)

        self.metadataPageLayout.addWidget(self.metadataLabel)

        self.metadataAccordion.addItem(self.metadataPage, u"Image metadata")

        self.metadataLayout.addWidget(self.metadataAccordion)

        self.detailTabs.addTab(self.metadataTab, "")
        self.gallerySplitter.addWidget(self.detailTabs)

        self.galleryLayout.addWidget(self.gallerySplitter)

        self.contentSplitter.addWidget(self.galleryPanel)

        self.mainLayout.addWidget(self.contentSplitter)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.detailTabs.setCurrentIndex(0)
        self.metadataAccordion.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Proofshot", None))
        self.browserLabel.setText(QCoreApplication.translate("MainWindow", u"Project browser", None))
        self.browserLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-weight: 600;", None))
        ___qtreewidgetitem = self.treeView.headerItem()
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("MainWindow", u"Projects", None))
        self.projectLabel.setText(QCoreApplication.translate("MainWindow", u"Select a project", None))
        self.projectLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size: 13px; font-weight: 500;", None))
        self.refreshGalleryButton.setText(QCoreApplication.translate("MainWindow", u"Refresh images", None))
#if QT_CONFIG(tooltip)
        self.refreshGalleryButton.setToolTip(QCoreApplication.translate("MainWindow", u"Reload screenshots for the selected project", None))
#endif // QT_CONFIG(tooltip)
        self.ImagePreview.setText(QCoreApplication.translate("MainWindow", u"Select an image to preview", None))
        self.ImagePreview.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: #20252b; color: #aab2bd; border-radius: 4px;", None))
        self.terminalLabel.setText(QCoreApplication.translate("MainWindow", u"Terminal", None))
        self.terminalLabel.setStyleSheet(QCoreApplication.translate("MainWindow", u"font-size: 11px; font-weight: 600;", None))
        self.captureColumnLabel.setText(QCoreApplication.translate("MainWindow", u"Column", None))
#if QT_CONFIG(tooltip)
        self.captureColumnCombo.setToolTip(QCoreApplication.translate("MainWindow", u"Column used for the next capture", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.captureColumnCombo.setAccessibleName(QCoreApplication.translate("MainWindow", u"Capture column", None))
#endif // QT_CONFIG(accessibility)
        self.captureSpanCheck.setText(QCoreApplication.translate("MainWindow", u"-S span", None))
#if QT_CONFIG(tooltip)
        self.captureSpanCheck.setToolTip(QCoreApplication.translate("MainWindow", u"Capture the complete range from the current index to the next index", None))
#endif // QT_CONFIG(tooltip)
        self.captureIncrementSpin.setPrefix(QCoreApplication.translate("MainWindow", u"Step ", None))
#if QT_CONFIG(tooltip)
        self.captureIncrementSpin.setToolTip(QCoreApplication.translate("MainWindow", u"How far Capture Next advances; with -S, capture the full range", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.captureIncrementSpin.setAccessibleName(QCoreApplication.translate("MainWindow", u"Capture increment", None))
#endif // QT_CONFIG(accessibility)
        self.indexDecrementButton.setText(QCoreApplication.translate("MainWindow", u"\u2212", None))
#if QT_CONFIG(tooltip)
        self.indexDecrementButton.setToolTip(QCoreApplication.translate("MainWindow", u"Decrease the active index", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.indexDecrementButton.setAccessibleName(QCoreApplication.translate("MainWindow", u"Decrease active index", None))
#endif // QT_CONFIG(accessibility)
        self.currentIndexSpin.setPrefix(QCoreApplication.translate("MainWindow", u"Index ", None))
#if QT_CONFIG(tooltip)
        self.currentIndexSpin.setToolTip(QCoreApplication.translate("MainWindow", u"Current index for the selected column", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.currentIndexSpin.setAccessibleName(QCoreApplication.translate("MainWindow", u"Current active index", None))
#endif // QT_CONFIG(accessibility)
        self.indexIncrementButton.setText(QCoreApplication.translate("MainWindow", u"+", None))
#if QT_CONFIG(tooltip)
        self.indexIncrementButton.setToolTip(QCoreApplication.translate("MainWindow", u"Increase the active index", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.indexIncrementButton.setAccessibleName(QCoreApplication.translate("MainWindow", u"Increase active index", None))
#endif // QT_CONFIG(accessibility)
        self.captureProjectButton.setText(QCoreApplication.translate("MainWindow", u"Capture Next", None))
#if QT_CONFIG(tooltip)
        self.captureProjectButton.setToolTip(QCoreApplication.translate("MainWindow", u"Capture at the next index using the selected column and increment", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.captureProjectButton.setAccessibleName(QCoreApplication.translate("MainWindow", u"Capture next screenshot", None))
#endif // QT_CONFIG(accessibility)
        self.terminalOutput.setPlainText(QCoreApplication.translate("MainWindow", u"Proofshot terminal\n"
"Select a project to begin.", None))
        self.terminalOutput.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: #15191e; color: #d7dde5; border: 1px solid #30363d; font-family: monospace;", None))
        self.terminalInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Enter a command\u2026", None))
        self.terminalInput.setStyleSheet(QCoreApplication.translate("MainWindow", u"background: #15191e; color: #d7dde5; border: 1px solid #30363d; font-family: monospace;", None))
        self.searchFilter.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Filter images by filename, column, or index\u2026", None))
        self.detailTabs.setTabText(self.detailTabs.indexOf(self.galleryTab), QCoreApplication.translate("MainWindow", u"Gallery", None))
        self.metadataLabel.setText(QCoreApplication.translate("MainWindow", u"Select an image to see its metadata.", None))
        self.metadataAccordion.setItemText(self.metadataAccordion.indexOf(self.metadataPage), QCoreApplication.translate("MainWindow", u"Image metadata", None))
        self.detailTabs.setTabText(self.detailTabs.indexOf(self.metadataTab), QCoreApplication.translate("MainWindow", u"Metadata", None))
    # retranslateUi

