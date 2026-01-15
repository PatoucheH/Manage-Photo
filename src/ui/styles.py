"""Styles and theme for the application"""

import sys


def get_system_font() -> str:
    """Get the appropriate system font for the current platform"""
    if sys.platform == "darwin":  # macOS
        return "SF Pro Display"
    elif sys.platform == "win32":  # Windows
        return "Segoe UI"
    else:  # Linux and others
        return "Ubuntu"


# Platform-specific font for use in QFont() calls
SYSTEM_FONT = get_system_font()


class Colors:
    """Modern color palette"""
    # Primary colors
    PRIMARY = "#6366f1"  # Indigo
    PRIMARY_HOVER = "#4f46e5"
    PRIMARY_LIGHT = "#e0e7ff"

    # Accent colors
    SUCCESS = "#10b981"  # Emerald
    SUCCESS_HOVER = "#059669"
    DANGER = "#ef4444"  # Red
    DANGER_HOVER = "#dc2626"

    # Neutral colors
    BG_DARK = "#1e1e2e"  # Dark background
    BG_CARD = "#2a2a3e"  # Card background
    BG_LIGHT = "#f8fafc"  # Light background
    BG_HOVER = "#3a3a4e"  # Hover on dark background

    # Text colors
    TEXT_PRIMARY = "#f1f5f9"
    TEXT_SECONDARY = "#94a3b8"
    TEXT_MUTED = "#64748b"

    # Border colors
    BORDER = "#3f3f5a"
    BORDER_LIGHT = "#e2e8f0"


class Styles:
    """QSS styles for the application"""

    @staticmethod
    def get_main_stylesheet() -> str:
        """Returns the main application stylesheet"""
        return f"""
            /* === GLOBAL === */
            QMainWindow {{
                background-color: {Colors.BG_DARK};
            }}

            QWidget {{
                font-family: '{SYSTEM_FONT}', -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 13px;
                color: {Colors.TEXT_PRIMARY};
            }}

            /* === SCROLL BARS === */
            QScrollBar:vertical {{
                background: {Colors.BG_DARK};
                width: 10px;
                margin: 0;
                border-radius: 5px;
            }}

            QScrollBar::handle:vertical {{
                background: {Colors.BORDER};
                min-height: 30px;
                border-radius: 5px;
            }}

            QScrollBar::handle:vertical:hover {{
                background: {Colors.TEXT_MUTED};
            }}

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0;
            }}

            QScrollBar:horizontal {{
                background: {Colors.BG_DARK};
                height: 10px;
                margin: 0;
                border-radius: 5px;
            }}

            QScrollBar::handle:horizontal {{
                background: {Colors.BORDER};
                min-width: 30px;
                border-radius: 5px;
            }}

            QScrollBar::handle:horizontal:hover {{
                background: {Colors.TEXT_MUTED};
            }}

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0;
            }}

            /* === LABELS === */
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                background: transparent;
            }}

            /* === BUTTONS === */
            QPushButton {{
                background-color: {Colors.BG_CARD};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 500;
            }}

            QPushButton:hover {{
                background-color: {Colors.BG_HOVER};
                border-color: {Colors.PRIMARY};
            }}

            QPushButton:pressed {{
                background-color: {Colors.PRIMARY};
            }}

            /* === RADIO BUTTONS === */
            QRadioButton {{
                color: {Colors.TEXT_PRIMARY};
                spacing: 8px;
                padding: 6px 0;
            }}

            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid {Colors.BORDER};
                background: {Colors.BG_CARD};
            }}

            QRadioButton::indicator:hover {{
                border-color: {Colors.PRIMARY};
            }}

            QRadioButton::indicator:checked {{
                background: {Colors.PRIMARY};
                border-color: {Colors.PRIMARY};
            }}

            /* === FRAMES === */
            QFrame {{
                background-color: transparent;
                border: none;
            }}

            /* === SCROLL AREA === */
            QScrollArea {{
                background-color: {Colors.BG_DARK};
                border: none;
            }}

            QScrollArea > QWidget > QWidget {{
                background-color: {Colors.BG_DARK};
            }}

            /* === MESSAGE BOX === */
            QMessageBox {{
                background-color: {Colors.BG_CARD};
            }}

            QMessageBox QLabel {{
                color: {Colors.TEXT_PRIMARY};
            }}

            /* === PROGRESS DIALOG === */
            QProgressDialog {{
                background-color: {Colors.BG_CARD};
            }}

            QProgressBar {{
                border: none;
                border-radius: 4px;
                background: {Colors.BG_DARK};
                height: 8px;
                text-align: center;
            }}

            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.PRIMARY}, stop:1 {Colors.SUCCESS});
                border-radius: 4px;
            }}

            /* === FILE DIALOG === */
            QFileDialog {{
                background-color: {Colors.BG_CARD};
            }}
        """

    @staticmethod
    def get_sidebar_style() -> str:
        """Style for the sidebar"""
        return f"""
            QFrame#sidebar {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.BG_CARD}, stop:1 {Colors.BG_DARK});
                border-radius: 16px;
                border: 1px solid {Colors.BORDER};
            }}
        """

    @staticmethod
    def get_primary_button_style() -> str:
        """Style for the primary button (export)"""
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Colors.SUCCESS}, stop:1 #059669);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 14px 20px;
                font-size: 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Colors.SUCCESS_HOVER}, stop:1 #047857);
            }}
            QPushButton:pressed {{
                background: #047857;
            }}
        """

    @staticmethod
    def get_danger_button_style() -> str:
        """Style for the danger button (clear)"""
        return f"""
            QPushButton {{
                background: transparent;
                color: {Colors.DANGER};
                border: 1px solid {Colors.DANGER};
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: {Colors.DANGER};
                color: white;
            }}
        """

    @staticmethod
    def get_action_button_style() -> str:
        """Style for action buttons (add)"""
        return f"""
            QPushButton {{
                background: {Colors.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: {Colors.PRIMARY_HOVER};
            }}
        """

    @staticmethod
    def get_photo_card_style() -> str:
        """Style for photo cards"""
        return f"""
            QFrame#photoCard {{
                background: {Colors.BG_CARD};
                border-radius: 12px;
                border: 1px solid {Colors.BORDER};
            }}
            QFrame#photoCard:hover {{
                border-color: {Colors.PRIMARY};
                background: {Colors.BG_HOVER};
            }}
        """

    @staticmethod
    def get_nav_button_style() -> str:
        """Style for navigation buttons"""
        return f"""
            QPushButton {{
                background: {Colors.BG_CARD};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {Colors.PRIMARY};
                border-color: {Colors.PRIMARY};
            }}
            QPushButton:disabled {{
                background: {Colors.BG_DARK};
                color: {Colors.TEXT_MUTED};
                border-color: {Colors.BG_DARK};
            }}
        """

    @staticmethod
    def get_icon_button_style(color: str = None) -> str:
        """Style for icon buttons"""
        bg_color = color if color else Colors.BG_CARD
        return f"""
            QPushButton {{
                background: {bg_color};
                border: none;
                border-radius: 6px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background: {Colors.BG_HOVER if not color else Colors.DANGER_HOVER};
            }}
        """

    @staticmethod
    def get_content_area_style() -> str:
        """Style for the content area"""
        return f"""
            QFrame#contentArea {{
                background: {Colors.BG_DARK};
                border-radius: 16px;
                border: 1px solid {Colors.BORDER};
            }}
        """

    @staticmethod
    def get_dialog_style() -> str:
        """Style for dialogs"""
        return f"""
            QDialog {{
                background: {Colors.BG_DARK};
            }}
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
            }}
            QPushButton {{
                background: {Colors.BG_CARD};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: {Colors.PRIMARY};
                border-color: {Colors.PRIMARY};
            }}
        """

    @staticmethod
    def get_language_button_style(active: bool = False) -> str:
        """Style for language toggle buttons"""
        if active:
            return f"""
                QPushButton {{
                    background: {Colors.PRIMARY};
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-weight: 600;
                    font-size: 11px;
                    padding: 0px;
                    min-width: 40px;
                    min-height: 26px;
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background: transparent;
                    color: {Colors.TEXT_MUTED};
                    border: 1px solid {Colors.BORDER};
                    border-radius: 5px;
                    font-weight: 500;
                    font-size: 11px;
                    padding: 0px;
                    min-width: 40px;
                    min-height: 26px;
                }}
                QPushButton:hover {{
                    background: {Colors.BG_HOVER};
                    color: {Colors.TEXT_PRIMARY};
                    border-color: {Colors.PRIMARY};
                }}
            """
