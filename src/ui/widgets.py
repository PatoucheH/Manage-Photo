"""Custom widgets for the application"""

from typing import Callable, Optional, List
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect, QWidget, QApplication, QScrollArea
)
from PyQt5.QtCore import Qt, QPoint, QMimeData, pyqtSignal, QTimer, QObject
from PyQt5.QtGui import QFont, QColor, QDrag, QPixmap, QCursor, QPainter, QLinearGradient, QPolygon

from ..models import PhotoItem
from ..i18n import tr
from .dialogs import ImageViewerDialog
from .styles import Colors, SYSTEM_FONT
import sip


class DragManager(QObject):
    """Global drag state manager"""

    drag_started = pyqtSignal()
    drag_ended = pyqtSignal()

    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = DragManager()
        return cls._instance

    def __init__(self):
        super().__init__()
        self._is_dragging = False

    def start_drag(self):
        """Called when a photo drag starts"""
        if not self._is_dragging:
            self._is_dragging = True
            self.drag_started.emit()

    def end_drag(self):
        """Called when a photo drag ends"""
        if self._is_dragging:
            self._is_dragging = False
            self.drag_ended.emit()

    def is_dragging(self):
        return self._is_dragging


class ScrollZoneIndicator(QWidget):
    """Visual indicator for scroll zones during drag"""

    def __init__(self, direction: str, parent=None):
        super().__init__(parent)
        self.direction = direction  # "up" or "down"
        self.active = False
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.hide()

    def set_active(self, active: bool):
        """Set whether this zone is being hovered"""
        self.active = active
        self.update()

    def paintEvent(self, event):
        """Draw the scroll zone indicator"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()

        # Create gradient
        if self.direction == "up":
            gradient = QLinearGradient(0, 0, 0, rect.height())
            if self.active:
                gradient.setColorAt(0, QColor(99, 102, 241, 150))
                gradient.setColorAt(1, QColor(99, 102, 241, 0))
            else:
                gradient.setColorAt(0, QColor(99, 102, 241, 80))
                gradient.setColorAt(1, QColor(99, 102, 241, 0))
        else:
            gradient = QLinearGradient(0, 0, 0, rect.height())
            if self.active:
                gradient.setColorAt(0, QColor(99, 102, 241, 0))
                gradient.setColorAt(1, QColor(99, 102, 241, 150))
            else:
                gradient.setColorAt(0, QColor(99, 102, 241, 0))
                gradient.setColorAt(1, QColor(99, 102, 241, 80))

        painter.fillRect(rect, gradient)

        # Draw arrow
        painter.setPen(Qt.NoPen)
        if self.active:
            painter.setBrush(QColor(255, 255, 255, 200))
        else:
            painter.setBrush(QColor(255, 255, 255, 120))

        center_x = rect.width() // 2
        arrow_size = 12

        if self.direction == "up":
            # Arrow pointing up
            center_y = rect.height() // 3
            points = [
                QPoint(center_x, center_y - arrow_size),
                QPoint(center_x - arrow_size, center_y + arrow_size // 2),
                QPoint(center_x + arrow_size, center_y + arrow_size // 2)
            ]
        else:
            # Arrow pointing down
            center_y = rect.height() * 2 // 3
            points = [
                QPoint(center_x, center_y + arrow_size),
                QPoint(center_x - arrow_size, center_y - arrow_size // 2),
                QPoint(center_x + arrow_size, center_y - arrow_size // 2)
            ]

        painter.drawPolygon(QPolygon(points))

        painter.end()


class AutoScrollArea(QScrollArea):
    """QScrollArea that auto-scrolls when dragging near edges"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

        # Auto-scroll settings
        self._scroll_timer = QTimer(self)
        self._scroll_timer.setInterval(30)  # Smooth scrolling
        self._scroll_timer.timeout.connect(self._do_auto_scroll)
        self._scroll_speed = 0
        self._scroll_margin = 80  # Pixels from edge to trigger scroll

        # Visual indicators
        self._top_indicator = ScrollZoneIndicator("up", self)
        self._bottom_indicator = ScrollZoneIndicator("down", self)

        # Connect to global drag manager
        DragManager.instance().drag_started.connect(self._on_drag_started)
        DragManager.instance().drag_ended.connect(self._on_drag_ended)

    def _on_drag_started(self):
        """Show indicators when any drag starts"""
        self._update_indicator_positions()
        self._top_indicator.show()
        self._bottom_indicator.show()
        self._top_indicator.raise_()
        self._bottom_indicator.raise_()
        self._scroll_timer.start()

    def _on_drag_ended(self):
        """Hide indicators when drag ends"""
        self._scroll_timer.stop()
        self._scroll_speed = 0
        self._top_indicator.set_active(False)
        self._bottom_indicator.set_active(False)
        self._top_indicator.hide()
        self._bottom_indicator.hide()

    def resizeEvent(self, event):
        """Reposition indicators on resize"""
        super().resizeEvent(event)
        self._update_indicator_positions()

    def _update_indicator_positions(self):
        """Update indicator positions"""
        width = self.width()
        self._top_indicator.setGeometry(0, 0, width, self._scroll_margin)
        self._bottom_indicator.setGeometry(0, self.height() - self._scroll_margin, width, self._scroll_margin)

    def dragEnterEvent(self, event):
        """Accept drag and start auto-scroll detection"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """Update scroll direction based on cursor position"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
            pos = event.pos()

            # Check if near top or bottom edge
            if pos.y() < self._scroll_margin:
                # Near top - scroll up
                distance = self._scroll_margin - pos.y()
                self._scroll_speed = -max(5, int(distance / 2))
                self._top_indicator.set_active(True)
                self._bottom_indicator.set_active(False)
            elif pos.y() > self.height() - self._scroll_margin:
                # Near bottom - scroll down
                distance = pos.y() - (self.height() - self._scroll_margin)
                self._scroll_speed = max(5, int(distance / 2))
                self._top_indicator.set_active(False)
                self._bottom_indicator.set_active(True)
            else:
                self._scroll_speed = 0
                self._top_indicator.set_active(False)
                self._bottom_indicator.set_active(False)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """Pause auto-scroll when drag leaves scroll area but keep indicators visible"""
        self._scroll_speed = 0
        self._top_indicator.set_active(False)
        self._bottom_indicator.set_active(False)

    def dropEvent(self, event):
        """Stop auto-scroll on drop"""
        self._scroll_speed = 0
        event.ignore()  # Let child widgets handle the drop

    def _do_auto_scroll(self):
        """Perform the auto-scroll"""
        if self._scroll_speed != 0:
            scrollbar = self.verticalScrollBar()
            scrollbar.setValue(scrollbar.value() + self._scroll_speed)


class LoadMoreButton(QPushButton):
    """Button that can be triggered by hovering with a dragged photo"""

    load_triggered = pyqtSignal()

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setAcceptDrops(True)

        # Timer for hover-to-trigger
        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._update_progress)
        self._hold_time = 1000  # 1 second to trigger
        self._elapsed = 0
        self._progress = 0.0
        self._is_drag_hover = False

        # Store original style
        self._base_style = ""

    def set_base_style(self, style: str):
        """Set the base style for the button"""
        self._base_style = style
        self.setStyleSheet(style)

    def _update_progress(self):
        """Update progress towards triggering load"""
        self._elapsed += 50
        self._progress = min(1.0, self._elapsed / self._hold_time)

        # Update visual feedback
        self._update_style()

        if self._progress >= 1.0:
            self._timer.stop()
            self._reset_state()
            self.load_triggered.emit()

    def _update_style(self):
        """Update button style based on progress"""
        if self._is_drag_hover:
            # Interpolate color based on progress
            alpha = int(100 + 155 * self._progress)
            self.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(99, 102, 241, {int(50 + 100 * self._progress)});
                    color: white;
                    border: 3px solid rgba(99, 102, 241, {alpha});
                    border-radius: 12px;
                    padding: 20px;
                    font-size: 14px;
                    font-weight: bold;
                }}
            """)
        else:
            self.setStyleSheet(self._base_style)

    def _reset_state(self):
        """Reset the hover state"""
        self._timer.stop()
        self._elapsed = 0
        self._progress = 0.0
        self._is_drag_hover = False
        self.setStyleSheet(self._base_style)

    def dragEnterEvent(self, event):
        """Start progress timer when drag enters"""
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if text and text.isdigit():
                event.acceptProposedAction()
                self._is_drag_hover = True
                self._elapsed = 0
                self._progress = 0.0
                self._timer.start()
                self._update_style()
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        """Stop timer when drag leaves"""
        self._reset_state()

    def dropEvent(self, event):
        """Handle drop - trigger load immediately"""
        self._reset_state()
        self.load_triggered.emit()
        event.ignore()  # Don't consume the drop


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

        # Notify drag manager that drag started
        DragManager.instance().start_drag()

        drag.exec_(Qt.MoveAction)

        # Notify drag manager that drag ended
        DragManager.instance().end_drag()

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
