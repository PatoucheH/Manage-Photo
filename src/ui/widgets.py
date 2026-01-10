"""Widgets personnalises de l'application"""

from typing import Callable
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ..models import PhotoItem
from .dialogs import ImageViewerDialog


class PhotoCard(QFrame):
    """Carte photo compacte avec miniature et boutons"""

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

        self._setup_ui()
        self._load_image()

    def _setup_ui(self) -> None:
        """Configure l'interface de la carte"""
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setFixedSize(130, 160)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)

        # Image label (cliquable)
        self.img_label = QLabel()
        self.img_label.setFixedSize(100, 100)
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setStyleSheet("background-color: #f0f0f0;")
        self.img_label.setCursor(Qt.PointingHandCursor)
        self.img_label.mousePressEvent = self._show_full_image
        layout.addWidget(self.img_label, alignment=Qt.AlignCenter)

        # Boutons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(2)

        rotate_btn = QPushButton("↻")
        rotate_btn.setFixedSize(30, 25)
        rotate_btn.clicked.connect(self._rotate)
        btn_layout.addWidget(rotate_btn)

        delete_btn = QPushButton("✕")
        delete_btn.setFixedSize(30, 25)
        delete_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        delete_btn.clicked.connect(self._delete)
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)

        # Nom du fichier
        name = self.photo.filename
        display_name = name[:14] + "..." if len(name) > 14 else name
        name_label = QLabel(display_name)
        name_label.setFont(QFont("Arial", 8))
        name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_label)

    def _load_image(self) -> None:
        """Charge la miniature"""
        pixmap = self.photo.get_pixmap()
        if pixmap:
            scaled = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.img_label.setPixmap(scaled)
        else:
            self.img_label.setText("Err")

    def _show_full_image(self, event) -> None:
        """Ouvre la photo en grand dans une modal"""
        dialog = ImageViewerDialog(self.photo, self.window())
        dialog.exec_()

    def _rotate(self) -> None:
        """Rotation de la photo"""
        self.photo.rotate()
        self._load_image()
        self.on_rotate(self.index)

    def _delete(self) -> None:
        """Suppression de la photo"""
        self.on_delete(self.index)
