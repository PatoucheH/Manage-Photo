"""Dialogues de l'application"""

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QApplication
)
from PyQt5.QtCore import Qt

from ..models import PhotoItem


class ImageViewerDialog(QDialog):
    """Modal pour afficher une photo en grand"""

    def __init__(self, photo: PhotoItem, parent=None):
        super().__init__(parent)
        self.photo = photo
        self.setWindowTitle(photo.filename)
        self.setModal(True)

        # Taille max = 90% de l'ecran
        screen = QApplication.primaryScreen().geometry()
        max_w = int(screen.width() * 0.9)
        max_h = int(screen.height() * 0.9)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Image label
        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.img_label)

        # Bouton fermer
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        # Charger l'image en grand
        self._load_full_image(max_w, max_h - 50)

    def _load_full_image(self, max_w: int, max_h: int) -> None:
        """Charge l'image en taille complete"""
        pixmap = self.photo.get_full_image(max_w, max_h)
        if pixmap:
            self.img_label.setPixmap(pixmap)
            self.resize(pixmap.width() + 20, pixmap.height() + 70)
        else:
            self.img_label.setText("Erreur de chargement")
