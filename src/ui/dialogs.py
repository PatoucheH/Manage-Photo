"""Application dialogs"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QApplication, QFrame, QGraphicsDropShadowEffect, QSizeGrip
)
from PyQt5.QtCore import Qt, QRect, QPoint, QSize
from PyQt5.QtGui import QFont, QColor, QKeyEvent, QCursor, QPainter, QPen, QBrush

from ..models import PhotoItem
from ..i18n import tr
from .styles import Colors


class ImageViewerDialog(QDialog):
    """Modern modal to display a photo in full size"""

    # Resize edge detection margin (larger for easier interaction)
    RESIZE_MARGIN = 15
    MIN_WIDTH = 400
    MIN_HEIGHT = 300
    # Visual grip size in corners
    GRIP_SIZE = 24

    def __init__(self, photo: PhotoItem, parent=None):
        super().__init__(parent)
        self.photo = photo
        self.setWindowTitle(photo.filename)
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)

        # Resize state
        self._resizing = False
        self._resize_edge = None
        self._drag_pos = None
        self._hover_edge = None  # Track which edge is being hovered

        # Max size = 90% of screen
        screen = QApplication.primaryScreen().geometry()
        self.max_w = int(screen.width() * 0.9)
        self.max_h = int(screen.height() * 0.9)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the dialog interface"""
        # Transparent outer layout with margin for resize detection
        outer_layout = QVBoxLayout(self)
        margin = self.RESIZE_MARGIN
        outer_layout.setContentsMargins(margin, margin, margin, margin)

        # Main styled container
        container = QFrame()
        container.setMouseTracking(True)  # Propagate mouse tracking
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
        # Reserve space for margins, borders and header/footer
        extra_margin = self.RESIZE_MARGIN * 2
        available_w = self.max_w - 80 - extra_margin
        available_h = self.max_h - 180 - extra_margin

        pixmap = self.photo.get_full_image(available_w, available_h)
        if pixmap:
            self.img_label.setPixmap(pixmap)
            # Adjust dialog size (include resize margins)
            dialog_w = min(pixmap.width() + 80 + extra_margin, self.max_w)
            dialog_h = min(pixmap.height() + 180 + extra_margin, self.max_h)
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

    def _get_resize_edge(self, pos: QPoint) -> str:
        """Detect which edge/corner the mouse is on for resizing"""
        rect = self.rect()
        margin = self.RESIZE_MARGIN

        left = pos.x() < margin
        right = pos.x() > rect.width() - margin
        top = pos.y() < margin
        bottom = pos.y() > rect.height() - margin

        if top and left:
            return "top-left"
        elif top and right:
            return "top-right"
        elif bottom and left:
            return "bottom-left"
        elif bottom and right:
            return "bottom-right"
        elif left:
            return "left"
        elif right:
            return "right"
        elif top:
            return "top"
        elif bottom:
            return "bottom"
        return None

    def _update_cursor(self, edge: str) -> None:
        """Update cursor based on resize edge"""
        cursors = {
            "left": Qt.SizeHorCursor,
            "right": Qt.SizeHorCursor,
            "top": Qt.SizeVerCursor,
            "bottom": Qt.SizeVerCursor,
            "top-left": Qt.SizeFDiagCursor,
            "bottom-right": Qt.SizeFDiagCursor,
            "top-right": Qt.SizeBDiagCursor,
            "bottom-left": Qt.SizeBDiagCursor,
        }
        # Update hover state and trigger repaint for visual feedback
        if self._hover_edge != edge:
            self._hover_edge = edge
            self.update()  # Trigger repaint

        if edge in cursors:
            self.setCursor(cursors[edge])
        else:
            self.setCursor(Qt.ArrowCursor)

    def paintEvent(self, event) -> None:
        """Draw resize indicators on edges"""
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw corner grips (always visible, subtle)
        grip_color = QColor(Colors.PRIMARY)
        grip_color.setAlpha(60)  # Subtle when not hovering

        # Highlight color when hovering
        highlight_color = QColor(Colors.PRIMARY)
        highlight_color.setAlpha(180)

        rect = self.rect()
        grip = self.GRIP_SIZE

        corners = {
            "bottom-right": (rect.width() - grip, rect.height() - grip, grip, grip),
            "bottom-left": (0, rect.height() - grip, grip, grip),
            "top-right": (rect.width() - grip, 0, grip, grip),
            "top-left": (0, 0, grip, grip),
        }

        for corner_name, (x, y, w, h) in corners.items():
            # Use highlight color if this corner is being hovered
            if self._hover_edge == corner_name:
                painter.setBrush(QBrush(highlight_color))
                painter.setPen(QPen(highlight_color.darker(120), 2))
            else:
                painter.setBrush(QBrush(grip_color))
                painter.setPen(Qt.NoPen)

            # Draw grip lines (diagonal lines in corner)
            if corner_name == "bottom-right":
                painter.drawLine(x + 4, y + h, x + w, y + 4)
                painter.drawLine(x + 10, y + h, x + w, y + 10)
                painter.drawLine(x + 16, y + h, x + w, y + 16)
            elif corner_name == "bottom-left":
                painter.drawLine(x, y + 4, x + w - 4, y + h)
                painter.drawLine(x, y + 10, x + w - 10, y + h)
                painter.drawLine(x, y + 16, x + w - 16, y + h)
            elif corner_name == "top-right":
                painter.drawLine(x + w, y + h - 4, x + 4, y)
                painter.drawLine(x + w, y + h - 10, x + 10, y)
                painter.drawLine(x + w, y + h - 16, x + 16, y)
            elif corner_name == "top-left":
                painter.drawLine(x, y + h - 4, x + w - 4, y)
                painter.drawLine(x, y + h - 10, x + w - 10, y)
                painter.drawLine(x, y + h - 16, x + w - 16, y)

        # Draw edge highlights when hovering
        edge_highlight = QColor(Colors.PRIMARY)
        edge_highlight.setAlpha(100)
        pen = QPen(edge_highlight, 3)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        margin = 20  # Rounded corner offset
        if self._hover_edge == "left":
            painter.drawLine(0, margin, 0, rect.height() - margin)
        elif self._hover_edge == "right":
            painter.drawLine(rect.width(), margin, rect.width(), rect.height() - margin)
        elif self._hover_edge == "top":
            painter.drawLine(margin, 0, rect.width() - margin, 0)
        elif self._hover_edge == "bottom":
            painter.drawLine(margin, rect.height(), rect.width() - margin, rect.height())

        painter.end()

    def mousePressEvent(self, event) -> None:
        """Handle mouse press for dragging and resizing"""
        if event.button() == Qt.LeftButton:
            edge = self._get_resize_edge(event.pos())
            if edge:
                self._resizing = True
                self._resize_edge = edge
                self._resize_start_pos = event.globalPos()
                self._resize_start_geometry = self.geometry()
            else:
                self._resizing = False
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move for dragging and resizing"""
        if self._resizing and event.buttons() == Qt.LeftButton:
            self._do_resize(event.globalPos())
            event.accept()
        elif event.buttons() == Qt.LeftButton and self._drag_pos:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()
        else:
            # Update cursor when hovering
            edge = self._get_resize_edge(event.pos())
            self._update_cursor(edge)

    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release - reload image after resize"""
        if self._resizing:
            self._resizing = False
            self._resize_edge = None
            # Reload image at new size
            self._reload_image()
        self._drag_pos = None
        event.accept()

    def _do_resize(self, global_pos: QPoint) -> None:
        """Perform the actual resize operation"""
        diff = global_pos - self._resize_start_pos
        geo = QRect(self._resize_start_geometry)

        min_w = self.MIN_WIDTH
        min_h = self.MIN_HEIGHT

        edge = self._resize_edge

        if "right" in edge:
            new_w = max(min_w, geo.width() + diff.x())
            geo.setWidth(min(new_w, self.max_w))
        if "left" in edge:
            new_w = max(min_w, geo.width() - diff.x())
            if new_w <= self.max_w:
                geo.setLeft(geo.right() - new_w)
        if "bottom" in edge:
            new_h = max(min_h, geo.height() + diff.y())
            geo.setHeight(min(new_h, self.max_h))
        if "top" in edge:
            new_h = max(min_h, geo.height() - diff.y())
            if new_h <= self.max_h:
                geo.setTop(geo.bottom() - new_h)

        self.setGeometry(geo)

    def _reload_image(self) -> None:
        """Reload the image at the current dialog size"""
        # Calculate available space for image (subtract resize margins)
        extra_margin = self.RESIZE_MARGIN * 2
        available_w = self.width() - 80 - extra_margin
        available_h = self.height() - 180 - extra_margin

        if available_w > 0 and available_h > 0:
            pixmap = self.photo.get_full_image(available_w, available_h)
            if pixmap:
                self.img_label.setPixmap(pixmap)
