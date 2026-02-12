"""
Main Dashboard UI for RedHerring.
Implements the scrollable single-page layout.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QScrollArea, QGroupBox, 
    QLabel, QPushButton, QFileDialog, QHBoxLayout, QSlider, 
    QCheckBox, QComboBox, QGridLayout, QColorDialog
)
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPixmap, QImage, QAction
from pathlib import Path
from PIL import Image, ImageOps

class DashboardWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RedHerring - Icon Converter")
        self.resize(500, 800)
        
        self.source_image = None
        self.processed_image = None
        
        # Edit State
        self.rotation = 0
        self.flip_h = False
        self.do_crop_square = False
        
        self.init_ui()
        
    def init_ui(self):
        # Main Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.setCentralWidget(self.scroll)
        
        # Container Widget
        container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.setSpacing(20)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. Select Image
        self.create_input_section()
        
        # 2. Edit Icon
        self.create_edit_section()
        
        # 3. Style Icon
        self.create_style_section()
        
        # 4. Output Settings
        self.create_output_section()
        
        # 5. Save Button
        self.convert_btn = QPushButton("Convert & Save Icon")
        self.convert_btn.setMinimumHeight(50)
        self.convert_btn.setStyleSheet("font-size: 16px; background-color: #28a745;")
        self.convert_btn.setEnabled(False)
        self.convert_btn.clicked.connect(self.convert_image)
        self.layout.addWidget(self.convert_btn)
        
        self.layout.addStretch()
        self.scroll.setWidget(container)
        
        # Enable Drag & Drop
        self.setAcceptDrops(True)
        
    def create_input_section(self):
        group = QGroupBox("1. Select Image")
        layout = QVBoxLayout()
        
        # Drop Zone / Preview
        self.drop_label = QLabel("Drag & Drop Image Here\n(or Paste from Clipboard)")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setStyleSheet("border: 2px dashed #ccc; border-radius: 8px; padding: 40px; color: #888;")
        self.drop_label.setMinimumHeight(200)
        layout.addWidget(self.drop_label)
        
        # Browse Button
        btn_browse = QPushButton("Browse Files...")
        btn_browse.clicked.connect(self.browse_file)
        layout.addWidget(btn_browse)
        
        group.setLayout(layout)
        self.layout.addWidget(group)

    def create_edit_section(self):
        group = QGroupBox("2. Edit Icon")
        layout = QVBoxLayout()
        
        tools = QHBoxLayout()
        
        btn_rot_l = QPushButton("↺ -90°")
        btn_rot_r = QPushButton("↻ +90°")
        btn_flip_h = QPushButton("↔ Flip H")
        btn_crop = QPushButton("✂ Crop Square")
        
        # Placeholder connections
        btn_rot_l.clicked.connect(lambda: self.apply_edit("rotate_left"))
        btn_rot_r.clicked.connect(lambda: self.apply_edit("rotate_right"))
        btn_flip_h.clicked.connect(lambda: self.apply_edit("flip_h"))
        btn_crop.clicked.connect(lambda: self.apply_edit("crop_square"))

        tools.addWidget(btn_rot_l)
        tools.addWidget(btn_rot_r)
        tools.addWidget(btn_flip_h)
        tools.addWidget(btn_crop)
        
        layout.addLayout(tools)
        group.setLayout(layout)
        self.layout.addWidget(group)

    def create_style_section(self):
        group = QGroupBox("3. Style Icon")
        layout = QGridLayout()
        
        # Background
        self.chk_bg = QCheckBox("Fill Background")
        self.btn_bg_color = QPushButton()
        self.btn_bg_color.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        self.btn_bg_color.setFixedSize(30, 30)
        self.btn_bg_color.clicked.connect(self.pick_color)
        self.bg_color = (255, 255, 255)
        
        layout.addWidget(self.chk_bg, 0, 0)
        layout.addWidget(self.btn_bg_color, 0, 1)
        
        # Roundness
        layout.addWidget(QLabel("Rounded Corners:"), 1, 0)
        self.slider_round = QSlider(Qt.Orientation.Horizontal)
        self.slider_round.setRange(0, 100)
        layout.addWidget(self.slider_round, 1, 1)
        
        group.setLayout(layout)
        self.layout.addWidget(group)
        
        # Connections
        self.chk_bg.toggled.connect(self.update_preview)
        self.btn_bg_color.clicked.connect(lambda: [self.pick_color(), self.update_preview()])
        self.slider_round.valueChanged.connect(self.update_preview)

    def create_output_section(self):
        group = QGroupBox("4. Output Settings")
        layout = QVBoxLayout()
        
        # Format
        fmt_layout = QHBoxLayout()
        fmt_layout.addWidget(QLabel("Format:"))
        self.combo_fmt = QComboBox()
        self.combo_fmt.addItems(["ICO (Windows)", "ICNS (Mac)", "PNG Bundle"])
        fmt_layout.addWidget(self.combo_fmt)
        layout.addLayout(fmt_layout)
        
        # Sizes Grid
        grid = QGridLayout()
        self.size_checks = {}
        sizes = [16, 24, 32, 48, 64, 96, 128, 256, 512, 1024]
        
        for i, size in enumerate(sizes):
            chk = QCheckBox(f"{size}x{size}")
            if size <= 256: chk.setChecked(True)
            self.size_checks[size] = chk
            grid.addWidget(chk, i // 3, i % 3)
            
        layout.addLayout(grid)
        group.setLayout(layout)
        self.layout.addWidget(group)

    # --- Logic Stubs ---
    def pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.bg_color = (color.red(), color.green(), color.blue())
            self.btn_bg_color.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #ccc;")

    def apply_edit(self, action):
        if not self.source_image: return
        
        if action == "rotate_left":
            self.rotation = (self.rotation + 90) % 360
        elif action == "rotate_right":
            self.rotation = (self.rotation - 90) % 360
        elif action == "flip_h":
            self.flip_h = not self.flip_h
        elif action == "crop_square":
            self.do_crop_square = not self.do_crop_square
            
        self.update_preview()

    def browse_file(self):
        formats = "*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tif *.tiff *.ico *.icns"
        path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", f"Images ({formats})")
        if path:
            self.load_image(path)
            
    def load_image(self, path):
        self.source_image = Image.open(path).convert("RGBA")
        self.update_preview()
        self.convert_btn.setEnabled(True)
        
    def update_preview(self):
        if not self.source_image: return
        
        # Gather options from UI
        options = {
            'radius': self.slider_round.value(),
            'fill_background': self.chk_bg.isChecked(),
            'background_color': self.bg_color,
            'rotate': self.rotation,
            'flip_h': self.flip_h,
            'crop_square': self.do_crop_square
        }
        
        # Process small preview
        from core.converter import IconConverter
        preview_img = self.source_image.copy()
        processed = IconConverter.process_image(preview_img, options)
        
        processed.thumbnail((200, 200))
        data = processed.convert("RGBA").tobytes("raw", "RGBA")
        qim = QImage(data, processed.width, processed.height, QImage.Format.Format_RGBA8888)
        pix = QPixmap.fromImage(qim)
        self.drop_label.setPixmap(pix)

    def convert_image(self):
        if not self.source_image: return
        
        # Get Output Path
        ext = ".ico" 
        if self.combo_fmt.currentText() == "ICNS (Mac)": ext = ".icns"
        elif self.combo_fmt.currentText() == "PNG Bundle": ext = "" # Folder
        
        path, _ = QFileDialog.getSaveFileName(self, "Save Icon", "icon" + ext, f"Icon Files (*{ext})")
        if not path: return
        
        # Gather Sizes
        sizes = [s for s, chk in self.size_checks.items() if chk.isChecked()]
        if not sizes:
            print("No size selected!")
            return

        # Process and Save
        from core.converter import IconConverter
        options = {
            'radius': self.slider_round.value(),
            'fill_background': self.chk_bg.isChecked(),
            'background_color': self.bg_color,
            'rotate': self.rotation,
            'flip_h': self.flip_h,
            'crop_square': self.do_crop_square
        }
        
        # Full resolution process
        final_img = IconConverter.process_image(self.source_image, options)
        
        fmt = []
        if "ICO" in self.combo_fmt.currentText(): fmt.append('ico')
        if "ICNS" in self.combo_fmt.currentText(): fmt.append('icns')
        if "PNG" in self.combo_fmt.currentText(): fmt.append('png')
        
        IconConverter.save_icon(final_img, path, fmt, sizes)
        print("Saved!")

    # Drag & Drop
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
    
    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.load_image(files[0])
