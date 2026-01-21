"""Main application window"""

import os
from typing import List

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QRadioButton, QButtonGroup, QScrollArea,
    QGridLayout, QFileDialog, QMessageBox, QProgressDialog, QFrame,
    QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor

from ..models import PhotoItem
from ..config import SUPPORTED_FORMATS
from ..export import WordExporter
from ..i18n import Translations, Language, tr
from .widgets import PhotoCard, AutoScrollArea, LoadMoreButton
from .styles import Styles, Colors, SYSTEM_FONT

# Number of photos to load at a time
PHOTOS_BATCH_SIZE = 50


class PhotoManagerApp(QMainWindow):
    """Main application"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Photo Manager")
        self.setMinimumSize(1000, 700)
        self.resize(1300, 850)

        self.photos: List[PhotoItem] = []
        self._cards: List[PhotoCard] = []
        self._photos_displayed = 0  # Number of photos currently displayed

        # Apply theme
        self.setStyleSheet(Styles.get_main_stylesheet())

        # Register for language changes
        Translations.add_listener(self._on_language_changed)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the user interface"""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Left panel (sidebar)
        self._setup_sidebar(main_layout)

        # Right panel (content)
        self._setup_content_area(main_layout)

    def _setup_sidebar(self, parent_layout: QHBoxLayout) -> None:
        """Setup the sidebar"""
        # Outer container for the sidebar (fixed width, holds scroll area)
        sidebar_outer = QFrame()
        sidebar_outer.setObjectName("sidebar")
        sidebar_outer.setFixedWidth(280)
        sidebar_outer.setStyleSheet(Styles.get_sidebar_style())

        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 60))
        sidebar_outer.setGraphicsEffect(shadow)

        # Layout for the outer container
        outer_layout = QVBoxLayout(sidebar_outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Scroll area for sidebar content
        sidebar_scroll = QScrollArea()
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sidebar_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        sidebar_scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background: transparent;
            }}
        """)

        # Inner widget that contains all sidebar content
        sidebar = QWidget()
        sidebar.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(24, 28, 24, 16)
        layout.setSpacing(8)

        # Logo / Title
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        self.title_label = QLabel(tr("app_title"))
        self.title_label.setFont(QFont(SYSTEM_FONT, 26, QFont.Bold))
        self.title_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        self.title_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel(tr("app_subtitle"))
        self.subtitle_label.setFont(QFont(SYSTEM_FONT, 13))
        self.subtitle_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(self.subtitle_label)

        layout.addWidget(title_container)
        layout.addSpacing(24)

        # Separator
        self._add_separator(layout)
        layout.addSpacing(16)

        # Add section
        self.add_section_label = QLabel(tr("add_photos"))
        self.add_section_label.setFont(QFont(SYSTEM_FONT, 12, QFont.Bold))
        self.add_section_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; letter-spacing: 1px;")
        self.add_section_label.setMinimumHeight(20)
        layout.addWidget(self.add_section_label)
        layout.addSpacing(12)

        self.folder_btn = QPushButton(f"  {tr('folder')}")
        self.folder_btn.setStyleSheet(Styles.get_action_button_style())
        self.folder_btn.setCursor(Qt.PointingHandCursor)
        self.folder_btn.setMinimumHeight(44)
        self.folder_btn.clicked.connect(self._add_folder)
        layout.addWidget(self.folder_btn)

        self.files_btn = QPushButton(f"  {tr('files')}")
        self.files_btn.setStyleSheet(Styles.get_action_button_style())
        self.files_btn.setCursor(Qt.PointingHandCursor)
        self.files_btn.setMinimumHeight(44)
        self.files_btn.clicked.connect(self._add_files)
        layout.addWidget(self.files_btn)

        layout.addSpacing(16)

        # Photo counter (single line)
        self.count_container = QFrame()
        self.count_container.setMinimumHeight(60)
        self.count_container.setMaximumHeight(60)
        self.count_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.count_container.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_DARK};
                border-radius: 10px;
            }}
        """)
        count_layout = QHBoxLayout(self.count_container)
        count_layout.setContentsMargins(16, 8, 16, 8)
        count_layout.setSpacing(8)

        count_layout.addStretch()

        self.count_label = QLabel("0")
        self.count_label.setFont(QFont(SYSTEM_FONT, 28, QFont.Bold))
        self.count_label.setStyleSheet(f"color: {Colors.PRIMARY};")
        self.count_label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        count_layout.addWidget(self.count_label)

        self.count_text = QLabel(tr("photos"))
        self.count_text.setFont(QFont(SYSTEM_FONT, 14))
        self.count_text.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        self.count_text.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        count_layout.addWidget(self.count_text)

        count_layout.addStretch()

        layout.addWidget(self.count_container)
        layout.addSpacing(20)

        # Separator
        self._add_separator(layout)
        layout.addSpacing(16)

        # Photos per page (for export)
        self.ppp_section_label = QLabel(tr("photos_per_page"))
        self.ppp_section_label.setFont(QFont(SYSTEM_FONT, 12, QFont.Bold))
        self.ppp_section_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; letter-spacing: 1px;")
        self.ppp_section_label.setMinimumHeight(20)
        layout.addWidget(self.ppp_section_label)
        layout.addSpacing(8)

        self.ppp_group = QButtonGroup(self)
        radio_container = QFrame()
        radio_container.setMinimumHeight(110)
        radio_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        radio_container.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_DARK};
                border-radius: 10px;
            }}
        """)
        radio_layout = QVBoxLayout(radio_container)
        radio_layout.setContentsMargins(16, 12, 16, 12)
        radio_layout.setSpacing(6)

        self.radio_4 = QRadioButton(tr("photos_layout_4"))
        self.radio_4.setFont(QFont(SYSTEM_FONT, 13))
        self.radio_4.setCursor(Qt.PointingHandCursor)
        self.radio_4.setMinimumHeight(28)
        self.ppp_group.addButton(self.radio_4, 4)
        radio_layout.addWidget(self.radio_4)

        self.radio_6 = QRadioButton(tr("photos_layout_6"))
        self.radio_6.setFont(QFont(SYSTEM_FONT, 13))
        self.radio_6.setCursor(Qt.PointingHandCursor)
        self.radio_6.setMinimumHeight(28)
        self.radio_6.setChecked(True)
        self.ppp_group.addButton(self.radio_6, 6)
        radio_layout.addWidget(self.radio_6)

        self.radio_9 = QRadioButton(tr("photos_layout_9"))
        self.radio_9.setFont(QFont(SYSTEM_FONT, 13))
        self.radio_9.setCursor(Qt.PointingHandCursor)
        self.radio_9.setMinimumHeight(28)
        self.ppp_group.addButton(self.radio_9, 9)
        radio_layout.addWidget(self.radio_9)

        layout.addWidget(radio_container)
        layout.addSpacing(16)

        # Separator
        self._add_separator(layout)
        layout.addSpacing(16)

        # Image size section
        self.size_section_label = QLabel(tr("image_size"))
        self.size_section_label.setFont(QFont(SYSTEM_FONT, 12, QFont.Bold))
        self.size_section_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; letter-spacing: 1px;")
        self.size_section_label.setMinimumHeight(20)
        layout.addWidget(self.size_section_label)
        layout.addSpacing(8)

        self.size_group = QButtonGroup(self)
        size_container = QFrame()
        size_container.setMinimumHeight(110)
        size_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        size_container.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_DARK};
                border-radius: 10px;
            }}
        """)
        size_layout = QVBoxLayout(size_container)
        size_layout.setContentsMargins(16, 12, 16, 12)
        size_layout.setSpacing(6)

        self.radio_half = QRadioButton(tr("size_half_page"))
        self.radio_half.setFont(QFont(SYSTEM_FONT, 13))
        self.radio_half.setCursor(Qt.PointingHandCursor)
        self.radio_half.setMinimumHeight(28)
        self.size_group.addButton(self.radio_half, 1)  # 1 = half
        size_layout.addWidget(self.radio_half)

        self.radio_three_quarter = QRadioButton(tr("size_three_quarter_page"))
        self.radio_three_quarter.setFont(QFont(SYSTEM_FONT, 13))
        self.radio_three_quarter.setCursor(Qt.PointingHandCursor)
        self.radio_three_quarter.setMinimumHeight(28)
        self.size_group.addButton(self.radio_three_quarter, 2)  # 2 = three_quarter
        size_layout.addWidget(self.radio_three_quarter)

        self.radio_full = QRadioButton(tr("size_full_page"))
        self.radio_full.setFont(QFont(SYSTEM_FONT, 13))
        self.radio_full.setCursor(Qt.PointingHandCursor)
        self.radio_full.setMinimumHeight(28)
        self.radio_full.setChecked(True)  # Default: full page
        self.size_group.addButton(self.radio_full, 3)  # 3 = full
        size_layout.addWidget(self.radio_full)

        layout.addWidget(size_container)
        layout.addSpacing(24)

        # Export button
        self.export_btn = QPushButton(f"  {tr('export_word')}")
        self.export_btn.setStyleSheet(Styles.get_primary_button_style())
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setMinimumHeight(50)
        self.export_btn.clicked.connect(self._export)
        layout.addWidget(self.export_btn)

        layout.addSpacing(8)

        # Clear button
        self.clear_btn = QPushButton(tr("clear_all"))
        self.clear_btn.setStyleSheet(Styles.get_danger_button_style())
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setMinimumHeight(40)
        self.clear_btn.clicked.connect(self._clear)
        layout.addWidget(self.clear_btn)

        # Add sidebar content to scroll area
        sidebar_scroll.setWidget(sidebar)
        outer_layout.addWidget(sidebar_scroll, 1)

        # Footer stays at bottom, outside scroll area
        footer_container = QWidget()
        footer_container.setStyleSheet("background: transparent;")
        footer_layout = QVBoxLayout(footer_container)
        footer_layout.setContentsMargins(24, 12, 24, 20)
        footer_layout.setSpacing(8)

        # Language toggle (small, in footer)
        lang_row = QHBoxLayout()
        lang_row.setSpacing(6)

        lang_row.addStretch()

        self.en_btn = QPushButton("EN")
        self.en_btn.setMinimumSize(40, 26)
        self.en_btn.setMaximumSize(40, 26)
        self.en_btn.setCursor(Qt.PointingHandCursor)
        self.en_btn.clicked.connect(self._switch_to_english)
        lang_row.addWidget(self.en_btn)

        self.fr_btn = QPushButton("FR")
        self.fr_btn.setMinimumSize(40, 26)
        self.fr_btn.setMaximumSize(40, 26)
        self.fr_btn.setCursor(Qt.PointingHandCursor)
        self.fr_btn.clicked.connect(self._switch_to_french)
        lang_row.addWidget(self.fr_btn)

        lang_row.addStretch()

        self._update_language_buttons()
        footer_layout.addLayout(lang_row)

        # Supported formats
        self.footer_label = QLabel(tr("supported_formats"))
        self.footer_label.setFont(QFont(SYSTEM_FONT, 10))
        self.footer_label.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        self.footer_label.setAlignment(Qt.AlignCenter)
        footer_layout.addWidget(self.footer_label)

        outer_layout.addWidget(footer_container)

        parent_layout.addWidget(sidebar_outer)

    def _add_separator(self, layout: QVBoxLayout) -> None:
        """Add a horizontal separator"""
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {Colors.BORDER};")
        layout.addWidget(separator)

    def _setup_content_area(self, parent_layout: QHBoxLayout) -> None:
        """Setup the content area"""
        content = QFrame()
        content.setObjectName("contentArea")
        content.setStyleSheet(Styles.get_content_area_style())

        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 40))
        content.setGraphicsEffect(shadow)

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        header.setSpacing(12)

        self.preview_label = QLabel(tr("preview"))
        self.preview_label.setFont(QFont(SYSTEM_FONT, 18, QFont.Bold))
        self.preview_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        header.addWidget(self.preview_label)

        header.addStretch()

        # Photos loaded indicator
        self.loaded_label = QLabel("")
        self.loaded_label.setFont(QFont(SYSTEM_FONT, 12))
        self.loaded_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        header.addWidget(self.loaded_label)

        content_layout.addLayout(header)

        # Scroll area for photo grid (with auto-scroll during drag)
        self.scroll_area = AutoScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {Colors.BG_DARK};
                border: none;
                border-radius: 12px;
            }}
        """)

        # Container for grid + load more button
        self.grid_container = QWidget()
        self.grid_container.setStyleSheet(f"background-color: {Colors.BG_DARK};")
        container_layout = QVBoxLayout(self.grid_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(16)

        # Grid widget
        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet(f"background-color: {Colors.BG_DARK};")
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setContentsMargins(8, 8, 8, 8)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        container_layout.addWidget(self.grid_widget)

        # Load more button (supports drag hover to trigger)
        self.load_more_btn = LoadMoreButton(tr("load_more"))
        self.load_more_btn.set_base_style(f"""
            QPushButton {{
                background: {Colors.BG_CARD};
                color: {Colors.TEXT_PRIMARY};
                border: 2px dashed {Colors.BORDER};
                border-radius: 12px;
                padding: 20px;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: {Colors.BG_HOVER};
                border-color: {Colors.PRIMARY};
                color: {Colors.PRIMARY};
            }}
        """)
        self.load_more_btn.setCursor(Qt.PointingHandCursor)
        self.load_more_btn.setMinimumHeight(60)
        self.load_more_btn.clicked.connect(self._load_more)
        self.load_more_btn.load_triggered.connect(self._load_more)  # Also trigger on drag hover
        self.load_more_btn.hide()  # Hidden by default
        container_layout.addWidget(self.load_more_btn)

        # Add spacing at bottom so load more button isn't covered by scroll zone indicator
        container_layout.addSpacing(100)

        self.scroll_area.setWidget(self.grid_container)
        content_layout.addWidget(self.scroll_area)

        parent_layout.addWidget(content, 1)

    def _set_language(self, language: Language) -> None:
        """Set the application language"""
        Translations.set_language(language)

    def _switch_to_english(self) -> None:
        """Switch to English"""
        self._set_language(Language.ENGLISH)

    def _switch_to_french(self) -> None:
        """Switch to French"""
        self._set_language(Language.FRENCH)

    def _update_language_buttons(self) -> None:
        """Update language button styles"""
        is_english = Translations.get_language() == Language.ENGLISH
        self.en_btn.setStyleSheet(Styles.get_language_button_style(active=is_english))
        self.fr_btn.setStyleSheet(Styles.get_language_button_style(active=not is_english))

    def _on_language_changed(self) -> None:
        """Handle language change"""
        # Update all translatable texts
        self.title_label.setText(tr("app_title"))
        self.subtitle_label.setText(tr("app_subtitle"))
        self.add_section_label.setText(tr("add_photos"))
        self.folder_btn.setText(f"  {tr('folder')}")
        self.files_btn.setText(f"  {tr('files')}")
        self.count_text.setText(tr("photos"))
        self.ppp_section_label.setText(tr("photos_per_page"))
        self.radio_4.setText(tr("photos_layout_4"))
        self.radio_6.setText(tr("photos_layout_6"))
        self.radio_9.setText(tr("photos_layout_9"))
        self.size_section_label.setText(tr("image_size"))
        self.radio_half.setText(tr("size_half_page"))
        self.radio_three_quarter.setText(tr("size_three_quarter_page"))
        self.radio_full.setText(tr("size_full_page"))
        self.export_btn.setText(f"  {tr('export_word')}")
        self.clear_btn.setText(tr("clear_all"))
        self.footer_label.setText(tr("supported_formats"))
        self.preview_label.setText(tr("preview"))
        self.load_more_btn.setText(tr("load_more"))

        # Update language buttons
        self._update_language_buttons()

        # Update loaded label
        self._update_loaded_label()

        # Refresh grid to update card buttons text
        if self.photos:
            self._refresh_grid()

    def _add_folder(self) -> None:
        """Add all photos from a folder"""
        folder = QFileDialog.getExistingDirectory(self, tr("select_folder"))
        if folder:
            files = sorted([
                os.path.join(folder, f) for f in os.listdir(folder)
                if f.lower().endswith(SUPPORTED_FORMATS) and not f.startswith('.')
            ])
            if files:
                self._add_photos(files)

    def _add_files(self) -> None:
        """Add photo files"""
        files, _ = QFileDialog.getOpenFileNames(
            self, tr("select_photos"), "",
            "Images (*.jpg *.jpeg *.png *.JPG *.JPEG *.PNG)"
        )
        if files:
            self._add_photos(files)

    def _add_photos(self, files: List[str]) -> None:
        """Add photos to the list"""
        existing = {p.path for p in self.photos}
        new_photos = [PhotoItem(f) for f in files if f not in existing]
        self.photos.extend(new_photos)

        # Reset displayed count to show first batch
        self._photos_displayed = min(PHOTOS_BATCH_SIZE, len(self.photos))
        self._update_view()

    def _delete_photo(self, index: int) -> None:
        """Delete a photo"""
        if 0 <= index < len(self.photos):
            self.photos[index].clear()
            del self.photos[index]
            # Adjust displayed count
            self._photos_displayed = min(self._photos_displayed, len(self.photos))
            self._update_view()

    def _rotate_photo(self, index: int) -> None:
        """Rotation callback"""
        pass

    def _move_photo(self, from_index: int, to_index: int) -> None:
        """Move a photo from one position to another"""
        if from_index == to_index:
            return
        if not (0 <= from_index < len(self.photos) and 0 <= to_index < len(self.photos)):
            return

        # Remove photo from original position and insert at new position
        photo = self.photos.pop(from_index)
        self.photos.insert(to_index, photo)

        # Refresh the grid
        self._refresh_grid()

    def _load_more(self) -> None:
        """Load more photos"""
        remaining = len(self.photos) - self._photos_displayed
        to_load = min(PHOTOS_BATCH_SIZE, remaining)
        self._photos_displayed += to_load
        self._refresh_grid()

    def _clear(self) -> None:
        """Clear all photos"""
        if not self.photos:
            return

        reply = QMessageBox.question(
            self, tr("confirm"),
            tr("confirm_clear"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            for p in self.photos:
                p.clear()
            self.photos.clear()
            self._photos_displayed = 0
            self._update_view()

    def _update_view(self) -> None:
        """Update the display"""
        self.count_label.setText(str(len(self.photos)))
        self._update_loaded_label()
        self._refresh_grid()

    def _update_loaded_label(self) -> None:
        """Update the loaded photos label"""
        if not self.photos:
            self.loaded_label.setText("")
        else:
            displayed = min(self._photos_displayed, len(self.photos))
            total = len(self.photos)
            if displayed < total:
                self.loaded_label.setText(f"{displayed} / {total}")
            else:
                self.loaded_label.setText(f"{total} photos")

    def _calculate_columns(self) -> int:
        """Calculate number of columns based on available width"""
        # Get available width from the scroll area
        scrollbar_width = self.scroll_area.verticalScrollBar().width() if self.scroll_area.verticalScrollBar().isVisible() else 0
        scroll_width = self.scroll_area.width() - scrollbar_width - 2

        # Card dimensions and spacing
        card_width = 180
        spacing = 16
        margins = 16

        # Calculate how many cards fit
        available = scroll_width - margins
        if available <= 0:
            return 1

        cols = max(1, (available + spacing) // (card_width + spacing))
        return cols

    def _refresh_grid(self) -> None:
        """Refresh the photo grid"""
        # Clean existing cards
        for card in self._cards:
            card.deleteLater()
        self._cards.clear()

        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.photos:
            self.load_more_btn.hide()
            self.loaded_label.setText("")
            return

        # Update loaded label
        self._update_loaded_label()

        # Calculate columns dynamically
        cols = self._calculate_columns()

        # Display photos up to _photos_displayed
        displayed = min(self._photos_displayed, len(self.photos))

        for i in range(displayed):
            card = PhotoCard(
                self.photos[i], i,
                self._delete_photo, self._rotate_photo,
                self._move_photo
            )
            self.grid_layout.addWidget(card, i // cols, i % cols)
            self._cards.append(card)

        # Show/hide load more button
        if displayed < len(self.photos):
            remaining = len(self.photos) - displayed
            self.load_more_btn.setText(f"{tr('load_more')} ({remaining})")
            self.load_more_btn.show()
        else:
            self.load_more_btn.hide()

    def _export(self) -> None:
        """Start Word export"""
        if not self.photos:
            QMessageBox.warning(self, tr("warning"), tr("no_photos"))
            return

        path, _ = QFileDialog.getSaveFileName(
            self, tr("save_document"), "photos.docx",
            tr("word_document")
        )
        if not path:
            return

        ppp = self.ppp_group.checkedId()

        # Get image size option (1=half, 2=three_quarter, 3=full)
        size_id = self.size_group.checkedId()
        size_map = {1: 'half', 2: 'three_quarter', 3: 'full'}
        image_size = size_map.get(size_id, 'full')

        # Progress dialog
        progress = QProgressDialog(tr("generating_word"), None, 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setAutoClose(True)
        progress.setMinimumDuration(0)
        progress.setMinimumWidth(400)
        progress.setMinimumHeight(120)
        progress.setStyleSheet(f"""
            QProgressDialog {{
                background: {Colors.BG_CARD};
                border-radius: 12px;
            }}
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: 16px;
                font-weight: bold;
                padding: 20px;
            }}
            QProgressBar {{
                border: none;
                border-radius: 10px;
                background: {Colors.BG_DARK};
                min-height: 24px;
                max-height: 24px;
                margin: 10px 20px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.PRIMARY}, stop:1 {Colors.SUCCESS});
                border-radius: 10px;
            }}
        """)
        progress.show()

        # Start export thread
        self.export_thread = WordExporter(self.photos, path, ppp, image_size)
        self.export_thread.progress.connect(progress.setValue)
        self.export_thread.finished.connect(lambda p: self._export_done(p, progress))
        self.export_thread.error.connect(lambda e: self._export_error(e, progress))
        self.export_thread.start()

    def _export_done(self, path: str, progress: QProgressDialog) -> None:
        """Export completed successfully"""
        progress.close()
        QMessageBox.information(
            self, tr("export_success"),
            f"{tr('export_success_msg')}\n\n{path}"
        )

    def _export_error(self, error: str, progress: QProgressDialog) -> None:
        """Export error"""
        progress.close()
        QMessageBox.critical(self, tr("export_error"), error)

    def resizeEvent(self, event) -> None:
        """Handle window resize - refresh grid to adapt columns"""
        super().resizeEvent(event)
        # Use a timer to debounce resize events
        if not hasattr(self, '_resize_timer'):
            self._resize_timer = QTimer()
            self._resize_timer.setSingleShot(True)
            self._resize_timer.timeout.connect(self._on_resize_done)
        self._resize_timer.start(100)

    def _on_resize_done(self) -> None:
        """Called after resize is complete"""
        if self.photos:
            self._refresh_grid()

    def closeEvent(self, event) -> None:
        """Clean up on close"""
        Translations.remove_listener(self._on_language_changed)
        super().closeEvent(event)
