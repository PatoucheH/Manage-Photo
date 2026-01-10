#!/usr/bin/env python3
"""
Photo Manager - Application de gestion de photos pour generer des documents Word
Compatible Windows et macOS (PyQt5)
"""

import sys
from PyQt5.QtWidgets import QApplication

from src.ui import PhotoManagerApp


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = PhotoManagerApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
