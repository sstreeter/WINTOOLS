"""
Modern Dark Theme QSS for IconForge.
Inspired by modern web applications (e.g. RedKetchup, Carbon Design).
"""

MODERN_STYLESHEET = """
/* Main Window & Backgrounds */
QMainWindow, QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif;
    font-size: 13px;
}

/* Group Boxes (Cards) */
QGroupBox {
    background-color: #252526;
    border: 1px solid #3e3e42;
    border-radius: 6px;
    margin-top: 24px; /* Space for title */
    padding-top: 10px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #007acc; /* Accent Color */
    font-size: 14px;
    font-weight: bold;
    background-color: transparent;
}

/* Buttons */
QPushButton {
    background-color: #0e639c;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #1177bb;
}

QPushButton:pressed {
    background-color: #094770;
}

QPushButton:disabled {
    background-color: #3e3e42;
    color: #888888;
}

/* Secondary / Tool Buttons */
QPushButton#ToolBtn {
    background-color: #3e3e42;
    color: #f0f0f0;
}

QPushButton#ToolBtn:hover {
    background-color: #4e4e52;
}

/* Labels */
QLabel {
    color: #cccccc;
}

QLabel#Header {
    font-size: 18px;
    font-weight: bold;
    color: #ffffff;
    padding: 5px 0;
}

QLabel#SubHeader {
    font-size: 14px;
    font-weight: 600;
    color: #aaaaaa;
    margin-top: 10px;
}

/* Sliders */
QSlider::groove:horizontal {
    border: 1px solid #3e3e42;
    height: 6px;
    background: #2d2d30;
    margin: 2px 0;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #007acc;
    border: 1px solid #007acc;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background: #1177bb;
}

/* Scroll Area */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    border: none;
    background: #1e1e1e;
    width: 10px;
    margin: 0px 0px 0px 0px;
}

QScrollBar::handle:vertical {
    background: #424242;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    background: none;
}

/* Checkboxes */
QCheckBox {
    spacing: 5px;
    color: #e0e0e0;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 3px;
    border: 1px solid #555;
    background-color: #2d2d30;
}

QCheckBox::indicator:checked {
    background-color: #007acc;
    border-color: #007acc;
    image: url(resources/check.png); /* Fallback or use unicode if no image */
}

QCheckBox::indicator:hover {
    border-color: #007acc;
}

/* Text Inputs */
QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: #2d2d30;
    border: 1px solid #3e3e42;
    color: #f0f0f0;
    padding: 5px;
    border-radius: 4px;
}

QLineEdit:focus, QSpinBox:focus {
    border-color: #007acc;
}
"""
