"""Application dialogs"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QApplication, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QKeyEvent

from ..models import PhotoItem
from ..i18n import tr
from .styles import Colors


class ImageViewerDialog(QDialog):
    """Modern modal to display a photo in full size"""

    def __init__(self, photo: PhotoItem, parent=None):
        super().__init__(parent)
        self.photo = photo
        self.setWindowTitle(photo.filename)
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Max size = 90% of screen
        screen = QApplication.primaryScreen().geometry()
        self.max_w = int(screen.width() * 0.9)
        self.max_h = int(screen.height() * 0.9)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the dialog interface"""
        # Transparent outer layout
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # Main styled container
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_DARK};
                border-radius: 20px;
                border: 1px solid {Colors.BORDER};
            }}
        """)

        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(50)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 150))
        container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header with title and close button
        header = QHBoxLayout()
        header.setSpacing(12)

        # Title
        title = QLabel(self.photo.filename)
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        header.addWidget(title)

        header.addStretch()

        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(40, 40)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFont(QFont("Segoe UI", 20))
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.BG_CARD};
                color: {Colors.TEXT_SECONDARY};
                border: none;
                border-radius: 20px;
            }}
            QPushButton:hover {{
                background: {Colors.DANGER};
                color: white;
            }}
        """)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)

        layout.addLayout(header)

        # Image container with background
        img_frame = QFrame()
        img_frame.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_CARD};
                border-radius: 16px;
            }}
        """)

        img_layout = QVBoxLayout(img_frame)
        img_layout.setContentsMargins(16, 16, 16, 16)

        # Image label
        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setStyleSheet("background: transparent;")
        img_layout.addWidget(self.img_label)

        layout.addWidget(img_frame)

        # Footer with info and buttons
        footer = QHBoxLayout()
        footer.setSpacing(12)

        # Info label
        info_label = QLabel(tr("press_esc"))
        info_label.setFont(QFont("Segoe UI", 10))
        info_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; background: transparent;")
        footer.addWidget(info_label)

        footer.addStretch()

        # Bottom close button
        close_btn_bottom = QPushButton(tr("close"))
        close_btn_bottom.setCursor(Qt.PointingHandCursor)
        close_btn_bottom.setFont(QFont("Segoe UI", 11))
        close_btn_bottom.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.PRIMARY};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 32px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: {Colors.PRIMARY_HOVER};
            }}
        """)
        close_btn_bottom.clicked.connect(self.close)
        footer.addWidget(close_btn_bottom)

        layout.addLayout(footer)

        outer_layout.addWidget(container)

        # Load the image
        self._load_full_image()

    def _load_full_image(self) -> None:
        """Load the full-size image"""
        # Reserve space for margins and header/footer
        available_w = self.max_w - 80
        available_h = self.max_h - 180

        pixmap = self.photo.get_full_image(available_w, available_h)
        if pixmap:
            self.img_label.setPixmap(pixmap)
            # Adjust dialog size
            dialog_w = min(pixmap.width() + 80, self.max_w)
            dialog_h = min(pixmap.height() + 180, self.max_h)
            self.resize(dialog_w, dialog_h)

            # Center on screen
            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - dialog_w) // 2
            y = (screen.height() - dialog_h) // 2
            self.move(x, y)
        else:
            self.img_label.setText(tr("loading_error"))
            self.img_label.setStyleSheet(f"""
                color: {Colors.DANGER};
                font-size: 16px;
                background: transparent;
            """)
            self.resize(400, 300)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle keyboard events"""
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event) -> None:
        """Allow window dragging"""
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        """Handle window dragging"""
        if event.buttons() == Qt.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPos() - self._drag_pos)
            event.accept()
