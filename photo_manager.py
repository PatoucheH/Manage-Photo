#!/usr/bin/env python3
"""
Photo Manager - Photo management application for generating Word documents
Compatible with Windows and macOS (PyQt5)
"""

import sys
import subprocess


def ensure_dependencies():
    """Install missing dependencies automatically (development mode only)."""
    required = ['PyQt5', 'python-docx', 'Pillow']
    missing = []

    for package in required:
        module_name = package.replace('-', '_')
        if module_name == 'python_docx':
            module_name = 'docx'
        elif module_name == 'Pillow':
            module_name = 'PIL'
        try:
            __import__(module_name)
        except ImportError:
            missing.append(package)

    if missing:
        print(f"Installing missing dependencies: {', '.join(missing)}")
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '--quiet', *missing
        ])
        print("Dependencies installed successfully.")


# Only check dependencies when running as script (not when frozen/built)
if not getattr(sys, 'frozen', False):
    ensure_dependencies()

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
