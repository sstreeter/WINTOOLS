"""
RedHerring - Utilitarian Icon Converter.
Entry point for the application.
"""
import sys
from PyQt6.QtWidgets import QApplication
from ui.dashboard import DashboardWindow
from ui.styles import FLAT_THEME

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(FLAT_THEME)
    
    window = DashboardWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
