"""Custom widgets for the application"""

from typing import Callable, Optional
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect, QWidget, QApplication, QScrollArea
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QPoint, QMimeData, pyqtSignal, QTimer, QRect
from PyQt5.QtGui import QFont, QColor, QPainter, QPainterPath, QBrush, QDrag, QPixmap, QPen

from ..models import PhotoItem
from ..i18n import tr
from .dialogs import ImageViewerDialog
from .styles import Colors, Styles, SYSTEM_FONT
import sip


class PageChangeIndicator(QWidget):
    """Visual indicator for page change during drag"""

    page_change_triggered = pyqtSignal(str)  # "prev" or "next"

    def __init__(self, direction: str, parent=None):
        super().__init__(parent)
        self.direction = direction  # "prev" or "next"
        self.progress = 0.0  # 0.0 to 1.0
        self.active = False  # True when drag is hovering over this zone
        self.enabled = False  # True when page change is possible
        self.timer = QTimer(self)
        self.timer.setInterval(50)  # Update every 50ms
        self.timer.timeout.connect(self._update_progress)
        self.hold_time = 2000  # 2 seconds to trigger
        self.elapsed = 0

        self.setAcceptDrops(True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        # Don't hide - we want to be visible when enabled

    def set_enabled(self, enabled: bool):
        """Enable or disable this zone (based on whether page change is possible)"""
        self.enabled = enabled
        self.setAcceptDrops(enabled)
        # Set cursor to indicate clickability
        if enabled:
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        if not enabled:
            self.deactivate()
        self.update()

    def mousePressEvent(self, event):
        """Handle click to change page immediately"""
        if self.enabled and event.button() == Qt.LeftButton:
            self.page_change_triggered.emit(self.direction)
            event.accept()
        else:
            event.ignore()

    def activate(self):
        """Start the progress timer (when drag enters)"""
        if not self.active and self.enabled:
            self.active = True
            self.progress = 0.0
            self.elapsed = 0
            self.timer.start()
            self.update()

    def deactivate(self):
        """Stop and reset (when drag leaves)"""
        self.active = False
        self.timer.stop()
        self.progress = 0.0
        self.elapsed = 0
        self.update()

    def _update_progress(self):
        """Update progress towards page change"""
        self.elapsed += 50
        self.progress = min(1.0, self.elapsed / self.hold_time)
        self.update()

        if self.progress >= 1.0:
            self.timer.stop()
            self.page_change_triggered.emit(self.direction)
            self.progress = 0.0
            self.elapsed = 0
            self.update()

    def paintEvent(self, event):
        """Draw the indicator with progress"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()

        # If not enabled, draw nothing (transparent)
        if not self.enabled:
            painter.end()
            return

        # Background - subtle when enabled, more visible when active
        bg_color = QColor(Colors.PRIMARY)
        if self.active:
            bg_color.setAlpha(40 + int(60 * self.progress))
        else:
            bg_color.setAlpha(20)  # Very subtle when just enabled
        painter.fillRect(rect, bg_color)

        # Progress bar on the edge (only when active)
        if self.active:
            progress_color = QColor(Colors.PRIMARY)
            progress_color.setAlpha(180)
            painter.setBrush(QBrush(progress_color))
            painter.setPen(Qt.NoPen)

            if self.direction == "prev":
                # Progress bar on left edge
                bar_width = 6
                bar_height = int(rect.height() * self.progress)
                bar_y = (rect.height() - bar_height) // 2
                painter.drawRoundedRect(2, bar_y, bar_width, bar_height, 3, 3)
            else:
                # Progress bar on right edge
                bar_width = 6
                bar_height = int(rect.height() * self.progress)
                bar_y = (rect.height() - bar_height) // 2
                painter.drawRoundedRect(rect.width() - bar_width - 2, bar_y, bar_width, bar_height, 3, 3)

        # Arrow icon
        if self.direction == "prev":
            self._draw_arrow(painter, rect, "left")
        else:
            self._draw_arrow(painter, rect, "right")

        # Text label
        text_color = QColor(Colors.TEXT_PRIMARY)
        if self.active:
            text_color.setAlpha(150 + int(105 * self.progress))
        else:
            text_color.setAlpha(80)  # Subtle when just enabled
        painter.setPen(QPen(text_color))
        font = QFont(SYSTEM_FONT, 10, QFont.Bold)
        painter.setFont(font)

        if self.direction == "prev":
            painter.drawText(rect, Qt.AlignCenter, "Page\nprécédente")
        else:
            painter.drawText(rect, Qt.AlignCenter, "Page\nsuivante")

        painter.end()

    def _draw_arrow(self, painter, rect, direction):
        """Draw arrow indicator"""
        arrow_color = QColor(Colors.TEXT_PRIMARY)
        if self.active:
            arrow_color.setAlpha(100 + int(155 * self.progress))
        else:
            arrow_color.setAlpha(60)  # Subtle when just enabled
        painter.setPen(QPen(arrow_color, 3))

        center_y = rect.height() // 2
        arrow_size = 15

        if direction == "left":
            x = 20
            painter.drawLine(x + arrow_size, center_y - arrow_size, x, center_y)
            painter.drawLine(x, center_y, x + arrow_size, center_y + arrow_size)
        else:
            x = rect.width() - 20
            painter.drawLine(x - arrow_size, center_y - arrow_size, x, center_y)
            painter.drawLine(x, center_y, x - arrow_size, center_y + arrow_size)

    def dragEnterEvent(self, event):
        if self.enabled and event.mimeData().hasText():
            text = event.mimeData().text()
            # Only accept if it's a valid photo index
            if text and text.isdigit():
                event.acceptProposedAction()
                self.activate()

    def dragLeaveEvent(self, event):
        self.deactivate()

    def dropEvent(self, event):
        # Don't actually drop here, just trigger page change if ready
        self.deactivate()
        event.ignore()


class PhotoGridContainer(QWidget):
    """Container for photo grid with page change drop zones"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

        # Callbacks
        self.on_prev_page = None
        self.on_next_page = None
        self.can_go_prev = lambda: False
        self.can_go_next = lambda: False

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left drop zone (previous page)
        self.prev_zone = PageChangeIndicator("prev", self)
        self.prev_zone.setFixedWidth(80)
        self.prev_zone.page_change_triggered.connect(self._on_page_change)
        layout.addWidget(self.prev_zone)

        # Main scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # No horizontal scroll
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {Colors.BG_DARK};
                border: none;
                border-radius: 12px;
            }}
        """)
        self.scroll_area.setAcceptDrops(True)
        layout.addWidget(self.scroll_area, 1)

        # Right drop zone (next page)
        self.next_zone = PageChangeIndicator("next", self)
        self.next_zone.setFixedWidth(80)
        self.next_zone.page_change_triggered.connect(self._on_page_change)
        layout.addWidget(self.next_zone)

    def set_grid_widget(self, widget):
        """Set the grid widget inside the scroll area"""
        self.scroll_area.setWidget(widget)

    def _on_page_change(self, direction):
        """Handle page change trigger"""
        if direction == "prev" and self.on_prev_page and self.can_go_prev():
            self.on_prev_page()
            # Keep zone active if still possible to go back
            if self.can_go_prev():
                self.prev_zone.activate()
        elif direction == "next" and self.on_next_page and self.can_go_next():
            self.on_next_page()
            # Keep zone active if still possible to go forward
            if self.can_go_next():
                self.next_zone.activate()

    def update_zones_visibility(self, can_prev, can_next):
        """Update which zones should be visible during drag"""
        self.can_go_prev = lambda: can_prev
        self.can_go_next = lambda: can_next

        # Update zone enabled state using the new set_enabled method
        self.prev_zone.set_enabled(can_prev)
        self.next_zone.set_enabled(can_next)


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
        self.setFixedSize(180, 255)  # Larger card with bigger buttons
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
        btn_container.setContentsMargins(0, 8, 0, 0)  # margin-top of 8px

        # View button - full width on its own row
        view_btn = QPushButton(tr("view"))
        view_btn.setFixedHeight(40)
        view_btn.setCursor(Qt.PointingHandCursor)
        view_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.BG_DARK};
                color: {Colors.TEXT_PRIMARY};
                border: none;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
                font-family: "{SYSTEM_FONT}";
            }}
            QPushButton:hover {{
                background: {Colors.PRIMARY};
                color: white;
            }}
        """)
        view_btn.clicked.connect(self._show_full_image)
        btn_container.addWidget(view_btn)

        # Second row: Rotate and Delete buttons (50% each)
        btn_row2 = QHBoxLayout()
        btn_row2.setSpacing(6)
        btn_row2.setContentsMargins(0, 0, 0, 0)

        # Rotate button - large icon
        rotate_btn = QPushButton("↻")
        rotate_btn.setFixedHeight(40)
        rotate_btn.setCursor(Qt.PointingHandCursor)
        rotate_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.BG_DARK};
                color: {Colors.TEXT_PRIMARY};
                border: none;
                border-radius: 8px;
                font-size: 28px;
                font-family: "{SYSTEM_FONT}";
            }}
            QPushButton:hover {{
                background: {Colors.PRIMARY};
                color: white;
            }}
        """)
        rotate_btn.clicked.connect(self._rotate)
        btn_row2.addWidget(rotate_btn, 1)  # stretch factor 1

        # Delete button - large icon
        delete_btn = QPushButton("×")
        delete_btn.setFixedHeight(40)
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.BG_DARK};
                color: {Colors.DANGER};
                border: none;
                border-radius: 8px;
                font-size: 32px;
                font-weight: bold;
                font-family: "{SYSTEM_FONT}";
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

        # Check if the widget was deleted during drag (happens when photo is moved)
        # This prevents RuntimeError: wrapped C/C++ object has been deleted
        if sip.isdeleted(self):
            return

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
            text = event.mimeData().text()
            # Check that text is not empty and is a valid integer
            if text and text.isdigit():
                source_index = int(text)
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
                    return
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
            text = event.mimeData().text()
            if text and text.isdigit():
                source_index = int(text)
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
