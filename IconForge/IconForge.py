#!/usr/bin/env python3
"""
IconForge - Professional Icon Creation Utility
Main application entry point with optimized startup.
"""

import sys


def main():
    """Main application entry point."""
    # Lazy imports for faster startup
    from PyQt6.QtWidgets import QApplication
    from ui import MainWindow
    
    app = QApplication(sys.argv)
    app.setApplicationName("IconForge")
    app.setOrganizationName("IconForge")
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
