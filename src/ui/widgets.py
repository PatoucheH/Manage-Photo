"""Custom widgets for the application"""

from typing import Callable
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect, QWidget
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QPoint
from PyQt5.QtGui import QFont, QColor, QPainter, QPainterPath, QBrush

from ..models import PhotoItem
from .dialogs import ImageViewerDialog
from .styles import Colors, Styles


class PhotoCard(QFrame):
    """Modern photo card with thumbnail and action buttons"""

    def __init__(
        self,
        photo: PhotoItem,
        index: int,
        on_delete: Callable[[int], None],
        on_rotate: Callable[[int], None]
    ):
        super().__init__()
        self.photo = photo
        self.index = index
        self.on_delete = on_delete
        self.on_rotate = on_rotate
        self._hover = False

        self._setup_ui()
        self._load_image()

    def _setup_ui(self) -> None:
        """Setup the card interface"""
        self.setObjectName("photoCard")
        self.setFixedSize(160, 200)
        self.setCursor(Qt.PointingHandCursor)

        # Base style
        self.setStyleSheet(f"""
            QFrame#photoCard {{
                background: {Colors.BG_CARD};
                border-radius: 14px;
                border: 2px solid transparent;
            }}
            QFrame#photoCard:hover {{
                border: 2px solid {Colors.PRIMARY};
            }}
        """)

        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 50))
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Image container with rounded corners
        img_container = QFrame()
        img_container.setFixedSize(140, 120)
        img_container.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_DARK};
                border-radius: 10px;
            }}
        """)

        img_layout = QVBoxLayout(img_container)
        img_layout.setContentsMargins(0, 0, 0, 0)

        # Clickable image label
        self.img_label = QLabel()
        self.img_label.setFixedSize(140, 120)
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setStyleSheet(f"""
            QLabel {{
                background: {Colors.BG_DARK};
                border-radius: 10px;
            }}
        """)
        self.img_label.setCursor(Qt.PointingHandCursor)
        self.img_label.mousePressEvent = self._show_full_image
        img_layout.addWidget(self.img_label)

        layout.addWidget(img_container, alignment=Qt.AlignCenter)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        rotate_btn = QPushButton()
        rotate_btn.setText("↻")
        rotate_btn.setFixedSize(40, 32)
        rotate_btn.setCursor(Qt.PointingHandCursor)
        rotate_btn.setFont(QFont("Segoe UI", 14))
        rotate_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.BG_DARK};
                color: {Colors.TEXT_PRIMARY};
                border: none;
                border-radius: 8px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background: {Colors.PRIMARY};
            }}
        """)
        rotate_btn.clicked.connect(self._rotate)
        btn_layout.addWidget(rotate_btn)

        delete_btn = QPushButton()
        delete_btn.setText("×")
        delete_btn.setFixedSize(40, 32)
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setFont(QFont("Segoe UI", 16, QFont.Bold))
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.BG_DARK};
                color: {Colors.DANGER};
                border: none;
                border-radius: 8px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background: {Colors.DANGER};
                color: white;
            }}
        """)
        delete_btn.clicked.connect(self._delete)
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)

        # Filename label
        name = self.photo.filename
        display_name = name[:16] + "..." if len(name) > 16 else name
        name_label = QLabel(display_name)
        name_label.setFont(QFont("Segoe UI", 9))
        name_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setToolTip(name)
        layout.addWidget(name_label)

    def _load_image(self) -> None:
        """Load the thumbnail"""
        pixmap = self.photo.get_pixmap()
        if pixmap:
            # Scale while maintaining aspect ratio
            scaled = pixmap.scaled(
                130, 110,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.img_label.setPixmap(scaled)
        else:
            self.img_label.setText("Error")
            self.img_label.setStyleSheet(f"""
                QLabel {{
                    background: {Colors.BG_DARK};
                    color: {Colors.DANGER};
                    border-radius: 10px;
                }}
            """)

    def _show_full_image(self, event) -> None:
        """Open full-size photo in modal"""
        dialog = ImageViewerDialog(self.photo, self.window())
        dialog.exec_()

    def _rotate(self) -> None:
        """Rotate the photo"""
        self.photo.rotate()
        self._load_image()
        self.on_rotate(self.index)

    def _delete(self) -> None:
        """Delete the photo"""
        self.on_delete(self.index)

    def enterEvent(self, event) -> None:
        """Hover effect on enter"""
        super().enterEvent(event)
        shadow = self.graphicsEffect()
        if shadow:
            shadow.setBlurRadius(30)
            shadow.setColor(QColor(99, 102, 241, 100))

    def leaveEvent(self, event) -> None:
        """Hover effect on leave"""
        super().leaveEvent(event)
        shadow = self.graphicsEffect()
        if shadow:
            shadow.setBlurRadius(20)
            shadow.setColor(QColor(0, 0, 0, 50))
