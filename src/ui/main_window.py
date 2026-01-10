"""Fenetre principale de l'application"""

import os
import math
from typing import List

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QRadioButton, QButtonGroup, QScrollArea,
    QGridLayout, QFileDialog, QMessageBox, QProgressDialog, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ..models import PhotoItem
from ..config import SUPPORTED_FORMATS, PHOTOS_PER_VIEW
from ..export import WordExporter
from .widgets import PhotoCard


class PhotoManagerApp(QMainWindow):
    """Application principale"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Photo Manager")
        self.setMinimumSize(900, 600)
        self.resize(1200, 800)

        self.photos: List[PhotoItem] = []
        self.current_page = 0
        self._cards: List[PhotoCard] = []

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Configure l'interface utilisateur"""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Panneau gauche
        self._setup_left_panel(main_layout)

        # Panneau droit
        self._setup_right_panel(main_layout)

    def _setup_left_panel(self, parent_layout: QHBoxLayout) -> None:
        """Configure le panneau gauche"""
        left_panel = QFrame()
        left_panel.setFixedWidth(240)
        left_panel.setFrameStyle(QFrame.StyledPanel)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(5)

        # Titre
        title = QLabel("Photo Manager")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(title)

        subtitle = QLabel("Export Word")
        subtitle.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(subtitle)

        left_layout.addSpacing(15)

        # Section ajout
        add_label = QLabel("Ajouter")
        add_label.setFont(QFont("Arial", 11, QFont.Bold))
        left_layout.addWidget(add_label)

        folder_btn = QPushButton("+ Dossier")
        folder_btn.clicked.connect(self._add_folder)
        left_layout.addWidget(folder_btn)

        files_btn = QPushButton("+ Fichiers")
        files_btn.clicked.connect(self._add_files)
        left_layout.addWidget(files_btn)

        self.count_label = QLabel("0 photos")
        self.count_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.count_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.count_label)

        left_layout.addSpacing(10)

        # Photos par page
        ppp_label = QLabel("Photos/page")
        ppp_label.setFont(QFont("Arial", 11, QFont.Bold))
        left_layout.addWidget(ppp_label)

        self.ppp_group = QButtonGroup(self)
        for val, text in [(4, "4 (2x2)"), (6, "6 (2x3)"), (9, "9 (3x3)")]:
            radio = QRadioButton(text)
            self.ppp_group.addButton(radio, val)
            left_layout.addWidget(radio)
            if val == 6:
                radio.setChecked(True)

        left_layout.addSpacing(15)

        # Bouton export
        export_btn = QPushButton("EXPORTER WORD")
        export_btn.setFont(QFont("Arial", 12, QFont.Bold))
        export_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 10px;")
        export_btn.clicked.connect(self._export)
        left_layout.addWidget(export_btn)

        clear_btn = QPushButton("Tout effacer")
        clear_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        clear_btn.clicked.connect(self._clear)
        left_layout.addWidget(clear_btn)

        left_layout.addStretch()

        formats_label = QLabel("JPG, PNG")
        formats_label.setStyleSheet("color: gray;")
        formats_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(formats_label)

        parent_layout.addWidget(left_panel)

    def _setup_right_panel(self, parent_layout: QHBoxLayout) -> None:
        """Configure le panneau droit"""
        right_panel = QFrame()
        right_panel.setFrameStyle(QFrame.StyledPanel)
        right_layout = QVBoxLayout(right_panel)

        # Header avec navigation
        header = QHBoxLayout()

        preview_label = QLabel("Apercu")
        preview_label.setFont(QFont("Arial", 13, QFont.Bold))
        header.addWidget(preview_label)

        header.addStretch()

        self.prev_btn = QPushButton("<")
        self.prev_btn.setFixedWidth(30)
        self.prev_btn.clicked.connect(self._prev_page)
        header.addWidget(self.prev_btn)

        self.page_label = QLabel("0/0")
        self.page_label.setFixedWidth(60)
        self.page_label.setAlignment(Qt.AlignCenter)
        header.addWidget(self.page_label)

        self.next_btn = QPushButton(">")
        self.next_btn.setFixedWidth(30)
        self.next_btn.clicked.connect(self._next_page)
        header.addWidget(self.next_btn)

        right_layout.addLayout(header)

        # Zone de scroll pour les photos
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: #f5f5f5;")

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(5)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.scroll_area.setWidget(self.grid_widget)
        right_layout.addWidget(self.scroll_area)

        parent_layout.addWidget(right_panel, 1)

    def _add_folder(self) -> None:
        """Ajoute toutes les photos d'un dossier"""
        folder = QFileDialog.getExistingDirectory(self, "Dossier")
        if folder:
            files = sorted([
                os.path.join(folder, f) for f in os.listdir(folder)
                if f.lower().endswith(SUPPORTED_FORMATS) and not f.startswith('.')
            ])
            if files:
                self._add_photos(files)

    def _add_files(self) -> None:
        """Ajoute des fichiers photos"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Photos", "",
            "Images (*.jpg *.jpeg *.png *.JPG *.JPEG *.PNG)"
        )
        if files:
            self._add_photos(files)

    def _add_photos(self, files: List[str]) -> None:
        """Ajoute des photos a la liste"""
        existing = {p.path for p in self.photos}
        new_photos = [PhotoItem(f) for f in files if f not in existing]
        self.photos.extend(new_photos)
        self._update_view()

    def _delete_photo(self, index: int) -> None:
        """Supprime une photo"""
        if 0 <= index < len(self.photos):
            self.photos[index].clear()
            del self.photos[index]
            max_page = max(0, (len(self.photos) - 1) // PHOTOS_PER_VIEW)
            if self.current_page > max_page:
                self.current_page = max_page
            self._update_view()

    def _rotate_photo(self, index: int) -> None:
        """Callback pour la rotation (deja geree dans PhotoCard)"""
        pass

    def _clear(self) -> None:
        """Efface toutes les photos"""
        for p in self.photos:
            p.clear()
        self.photos.clear()
        self.current_page = 0
        self._update_view()

    def _prev_page(self) -> None:
        """Page precedente"""
        if self.current_page > 0:
            self.current_page -= 1
            self._refresh_grid()

    def _next_page(self) -> None:
        """Page suivante"""
        max_page = max(0, (len(self.photos) - 1) // PHOTOS_PER_VIEW)
        if self.current_page < max_page:
            self.current_page += 1
            self._refresh_grid()

    def _update_view(self) -> None:
        """Met a jour l'affichage"""
        self.count_label.setText(f"{len(self.photos)} photos")
        self._refresh_grid()

    def _refresh_grid(self) -> None:
        """Rafraichit la grille de photos"""
        # Nettoyer les cartes existantes
        for card in self._cards:
            card.deleteLater()
        self._cards.clear()

        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.photos:
            self.page_label.setText("0/0")
            return

        # Pagination
        total_pages = math.ceil(len(self.photos) / PHOTOS_PER_VIEW)
        self.page_label.setText(f"{self.current_page + 1}/{total_pages}")

        start = self.current_page * PHOTOS_PER_VIEW
        end = min(start + PHOTOS_PER_VIEW, len(self.photos))

        cols = 6

        for i, idx in enumerate(range(start, end)):
            card = PhotoCard(
                self.photos[idx], idx,
                self._delete_photo, self._rotate_photo
            )
            self.grid_layout.addWidget(card, i // cols, i % cols)
            self._cards.append(card)

    def _export(self) -> None:
        """Lance l'export Word"""
        if not self.photos:
            QMessageBox.warning(self, "Attention", "Aucune photo.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer", "photos.docx",
            "Word (*.docx)"
        )
        if not path:
            return

        ppp = self.ppp_group.checkedId()

        # Progress dialog
        progress = QProgressDialog("Generation du document Word...", None, 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setAutoClose(True)
        progress.show()

        # Lancer l'export en thread
        self.export_thread = WordExporter(self.photos, path, ppp)
        self.export_thread.progress.connect(progress.setValue)
        self.export_thread.finished.connect(lambda p: self._export_done(p, progress))
        self.export_thread.error.connect(lambda e: self._export_error(e, progress))
        self.export_thread.start()

    def _export_done(self, path: str, progress: QProgressDialog) -> None:
        """Export termine avec succes"""
        progress.close()
        QMessageBox.information(self, "Succes", f"Exporte:\n{path}")

    def _export_error(self, error: str, progress: QProgressDialog) -> None:
        """Erreur lors de l'export"""
        progress.close()
        QMessageBox.critical(self, "Erreur", error)
