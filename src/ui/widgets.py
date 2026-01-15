"""Custom widgets for the application"""

from typing import Callable, Optional
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect, QWidget, QApplication
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QPoint, QMimeData, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPainter, QPainterPath, QBrush, QDrag, QPixmap

from ..models import PhotoItem
from .dialogs import ImageViewerDialog
from .styles import Colors, Styles


class PhotoCard(QFrame):
    """Modern photo card with thumbnail and action buttons"""

    # Signal emitted when a card is dropped onto another
    photo_moved = pyqtSignal(int, int)  # from_index, to_index

    def __init__(
        self,
        photo: PhotoItem,
        index: int,
        on_delete: Callable[[int], None],
        on_rotate: Callable[[int], None],
        on_move: Optional[Callable[[int, int], None]] = None
    ):
        super().__init__()
        self.photo = photo
        self.index = index
        self.on_delete = on_delete
        self.on_rotate = on_rotate
        self.on_move = on_move
        self._hover = False
        self._drag_start_pos = None

        # Enable drag & drop
        self.setAcceptDrops(True)

        self._setup_ui()
        self._load_image()

    def _setup_ui(self) -> None:
        """Setup the card interface"""
        self.setObjectName("photoCard")
        self.setFixedSize(180, 230)  # Larger card with 2 button rows
        self.setCursor(Qt.OpenHandCursor)  # Indicate draggable

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
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Image container with rounded corners
        img_container = QFrame()
        img_container.setFixedSize(164, 140)
        img_container.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_DARK};
                border-radius: 10px;
            }}
        """)

        img_layout = QVBoxLayout(img_container)
        img_layout.setContentsMargins(0, 0, 0, 0)

        # Image label (no click - use button instead)
        self.img_label = QLabel()
        self.img_label.setFixedSize(164, 140)
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setStyleSheet(f"""
            QLabel {{
                background: {Colors.BG_DARK};
                border-radius: 10px;
            }}
        """)
        img_layout.addWidget(self.img_label)

        layout.addWidget(img_container, alignment=Qt.AlignCenter)

        # Action buttons container
        btn_container = QVBoxLayout()
        btn_container.setSpacing(6)
        btn_container.setContentsMargins(0, 0, 0, 0)

        # Common button style
        btn_style = f"""
            QPushButton {{
                background: {Colors.BG_DARK};
                color: {Colors.TEXT_PRIMARY};
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {Colors.PRIMARY};
                color: white;
            }}
        """

        # View button - full width on its own row
        view_btn = QPushButton("Voir")
        view_btn.setFixedHeight(32)
        view_btn.setCursor(Qt.PointingHandCursor)
        view_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        view_btn.setStyleSheet(btn_style)
        view_btn.clicked.connect(self._show_full_image)
        btn_container.addWidget(view_btn)

        # Second row: Rotate and Delete buttons (50% each)
        btn_row2 = QHBoxLayout()
        btn_row2.setSpacing(6)
        btn_row2.setContentsMargins(0, 0, 0, 0)

        # Rotate button
        rotate_btn = QPushButton("↻")
        rotate_btn.setFixedHeight(32)
        rotate_btn.setCursor(Qt.PointingHandCursor)
        rotate_btn.setFont(QFont("Segoe UI", 14))
        rotate_btn.setStyleSheet(btn_style)
        rotate_btn.clicked.connect(self._rotate)
        btn_row2.addWidget(rotate_btn, 1)  # stretch factor 1

        # Delete button
        delete_btn = QPushButton("×")
        delete_btn.setFixedHeight(32)
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setFont(QFont("Segoe UI", 16, QFont.Bold))
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.BG_DARK};
                color: {Colors.DANGER};
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background: {Colors.DANGER};
                color: white;
            }}
        """)
        delete_btn.clicked.connect(self._delete)
        btn_row2.addWidget(delete_btn, 1)  # stretch factor 1

        btn_container.addLayout(btn_row2)
        layout.addLayout(btn_container)

    def _load_image(self) -> None:
        """Load the thumbnail"""
        pixmap = self.photo.get_pixmap()
        if pixmap:
            # Scale while maintaining aspect ratio
            scaled = pixmap.scaled(
                154, 130,
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

    def _show_full_image(self) -> None:
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

    def mousePressEvent(self, event) -> None:
        """Start drag operation on left click"""
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)  # Show grabbing cursor
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """Reset cursor on release"""
        self.setCursor(Qt.OpenHandCursor)
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """Handle drag if moved enough distance"""
        if not (event.buttons() & Qt.LeftButton):
            return
        if self._drag_start_pos is None:
            return

        # Check if moved enough to start drag
        distance = (event.pos() - self._drag_start_pos).manhattanLength()
        if distance < QApplication.startDragDistance():
            return

        # Start drag operation
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(str(self.index))
        drag.setMimeData(mime_data)

        # Create drag pixmap (thumbnail of the card)
        pixmap = self.grab()
        scaled_pixmap = pixmap.scaled(120, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        drag.setPixmap(scaled_pixmap)
        drag.setHotSpot(QPoint(scaled_pixmap.width() // 2, scaled_pixmap.height() // 2))

        # Make card semi-transparent during drag
        self.setStyleSheet(f"""
            QFrame#photoCard {{
                background: {Colors.BG_CARD};
                border-radius: 14px;
                border: 2px dashed {Colors.PRIMARY};
                opacity: 0.5;
            }}
        """)

        drag.exec_(Qt.MoveAction)

        # Restore style and cursor after drag
        self.setCursor(Qt.OpenHandCursor)
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
        self._drag_start_pos = None

    def dragEnterEvent(self, event) -> None:
        """Accept drag if it contains photo index"""
        if event.mimeData().hasText():
            source_index = int(event.mimeData().text())
            if source_index != self.index:
                event.acceptProposedAction()
                # Visual feedback - highlight drop target
                self.setStyleSheet(f"""
                    QFrame#photoCard {{
                        background: {Colors.BG_CARD};
                        border-radius: 14px;
                        border: 2px solid {Colors.SUCCESS};
                    }}
                """)
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        """Reset style when drag leaves"""
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

    def dropEvent(self, event) -> None:
        """Handle drop - move photo"""
        if event.mimeData().hasText():
            source_index = int(event.mimeData().text())
            if source_index != self.index and self.on_move:
                self.on_move(source_index, self.index)
            event.acceptProposedAction()

        # Reset style
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
