"""
Flat, clean stylesheet for RedHerring.
"""

FLAT_THEME = """
QMainWindow {
    background-color: #f0f0f0;
}

QScrollArea {
    background-color: #f0f0f0;
    border: none;
}

QGroupBox {
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    margin-top: 20px;
    font-size: 14px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 10px;
    color: #333;
    background-color: transparent; 
}

QPushButton {
    background-color: #007acc;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #0062a3;
}

QPushButton:disabled {
    background-color: #ccc;
}

QLabel {
    color: #333;
}
"""
