"""
Main Dashboard UI for RedHerring.
Implements the scrollable single-page layout.
"""
from PyQt6.QtGui import (
    QDragEnterEvent, QDropEvent, QPixmap, QImage, QAction, 
    QKeySequence, QShortcut, QIcon
)
from PyQt6.QtGui import QIcon, QAction, QPixmap, QImage, QDesktopServices, QColor, QBrush
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QScrollArea, QGroupBox, 
    QLabel, QPushButton, QFileDialog, QHBoxLayout, QSlider, 
    QCheckBox, QComboBox, QGridLayout, QColorDialog, QApplication,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit
)
from PyQt6.QtCore import Qt, QSize, QRect, QUrl
from pathlib import Path
from PIL import Image, ImageOps

from ui.widgets import InteractiveImageLabel, CollapsibleBox, InfoLabel

class DashboardWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RedHerring - Icon Converter")
        self.resize(1100, 800)
        self.setMinimumSize(900, 650)
        
        self.source_image = None
        self.processed_image = None
        
        # Edit State
        self.rotation = 0
        self.flip_h = False
        self.flip_v = False
        self.source_image_transformed = None
        
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
        
        # 2. Crop Image - optional
        self.create_crop_section()
        
        # 3. Configure Icon
        self.create_configure_section()
        
        # 4. Download
        self.create_download_section()

        
        self.layout.addStretch()
        self.scroll.setWidget(container)
        
        # Enable Drag & Drop & Clipboard
        self.setAcceptDrops(True)
        self.paste_shortcut = QShortcut(QKeySequence("Ctrl+V"), self)
        self.paste_shortcut.activated.connect(self.paste_image)
        
    def create_input_section(self):
        self.box_input = CollapsibleBox("1. Select Image")
        self.box_input.setToolTip("Drag and drop an image here, or paste from clipboard.")
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Action Bar (Browse)
        actions = QHBoxLayout()
        btn_browse = QPushButton("Browse Image...")
        btn_browse.setIcon(QIcon.fromTheme("document-open"))
        btn_browse.setFixedSize(140, 40)
        btn_browse.clicked.connect(self.browse_file)
        
        actions.addWidget(btn_browse)
        actions.addStretch()
        layout.addLayout(actions)
        
        # Interactive Editor (Replaces simple drop label)
        self.image_label = InteractiveImageLabel()
        self.image_label.setMinimumHeight(400) # Give it room
        self.image_label.setStyleSheet("border: 2px dashed #ccc; background: #333;")
        self.image_label.selectionChanged.connect(self.on_selection_changed)
        
        layout.addWidget(self.image_label)
        
        # Instructions (Small)
        instr = QLabel("Drag & Drop supported. Ctrl+V to paste.")
        instr.setStyleSheet("color: #777; font-size: 11px;")
        instr.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(instr)
        
        self.box_input.setContentLayout(layout)
        self.box_input.expand() # Default open
        self.layout.addWidget(self.box_input)

    def create_crop_section(self):
        self.box_crop = CollapsibleBox("2. Crop & Edit")
        self.box_crop.setToolTip("Adjust the crop area, rotation, and aspect ratio.")
        
        # Grid Layout for 4 quadrants
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        grid.setHorizontalSpacing(30)
        
        # --- Top Left: Aspect Ratio ---
        tl_layout = QVBoxLayout()
        tl_layout.addWidget(QLabel("Aspect Ratio"))
        
        self.combo_ar = QComboBox()
        self.combo_ar.addItems(["Free-form", "Original Ratio", "Square"])
        self.combo_ar.currentTextChanged.connect(self.on_ar_changed)
        tl_layout.addWidget(self.combo_ar)
        
        self.chk_resize_ar = QCheckBox("Resize to aspect ratio instead of cropping")
        self.chk_resize_ar.setToolTip("If checked, fits the image. If unchecked, crops it.")
        self.chk_resize_ar.toggled.connect(self.update_preview) 
        tl_layout.addWidget(self.chk_resize_ar)
        
        grid.addLayout(tl_layout, 0, 0)
        
        # --- Top Right: Rotate or Flip ---
        tr_layout = QVBoxLayout()
        tr_layout.addWidget(QLabel("Rotate or Flip"))
        
        tools = QHBoxLayout()
        btn_rot_l = QPushButton("↺") 
        btn_rot_r = QPushButton("↻")
        btn_flip_h = QPushButton("↔")
        btn_flip_v = QPushButton("↕")
        
        for btn in [btn_rot_l, btn_rot_r, btn_flip_h, btn_flip_v]:
            btn.setFixedSize(40, 30)
        
        tools.addWidget(btn_rot_l)
        tools.addWidget(btn_rot_r)
        tools.addWidget(btn_flip_h)
        tools.addWidget(btn_flip_v)
        
        # Transparency Tool
        btn_trans = QPushButton("Make Transparent")
        btn_trans.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_trans.setToolTip("Pick a color to make transparent")
        btn_trans.clicked.connect(self.make_transparent)
        tools.addWidget(btn_trans)
        
        tools.addStretch()
        
        # Connections
        btn_rot_l.clicked.connect(lambda: self.apply_edit("rotate_left"))
        btn_rot_r.clicked.connect(lambda: self.apply_edit("rotate_right"))
        btn_flip_h.clicked.connect(lambda: self.apply_edit("flip_h"))
        btn_flip_v.clicked.connect(lambda: self.apply_edit("flip_v"))
        
        tr_layout.addLayout(tools)
        # tr_layout.addWidget(QCheckBox("Show grid")) 
        
        grid.addLayout(tr_layout, 0, 1)
        
        # --- Bottom Left: Coordinates ---
        bl_layout = QHBoxLayout()
        bl_layout.addWidget(QLabel("Coordinates"))
        
        from PyQt6.QtWidgets import QSpinBox
        self.spin_left = QSpinBox()
        self.spin_top = QSpinBox()
        for idx, spin in enumerate([self.spin_left, self.spin_top]):
            spin.setRange(0, 9999)
            spin.setSuffix(" px")
            spin.valueChanged.connect(self.on_spin_changed)
            
        bl_layout.addWidget(QLabel("Left:"))
        bl_layout.addWidget(self.spin_left)
        bl_layout.addWidget(QLabel("Top:"))
        bl_layout.addWidget(self.spin_top)
        bl_layout.addStretch()
        
        grid.addLayout(bl_layout, 1, 0)
        
        # --- Bottom Right: Crop Dimensions ---
        br_layout = QHBoxLayout()
        br_layout.addWidget(QLabel("Crop Dimensions"))
        
        self.spin_width = QSpinBox()
        self.spin_height = QSpinBox()
        for spin in [self.spin_width, self.spin_height]:
            spin.setRange(1, 9999)
            spin.setSuffix(" px")
            spin.valueChanged.connect(self.on_spin_changed)
            
        br_layout.addWidget(QLabel("Width:"))
        br_layout.addWidget(self.spin_width)
        br_layout.addWidget(QLabel("Height:"))
        br_layout.addWidget(self.spin_height)
        br_layout.addStretch()
        
        grid.addLayout(br_layout, 1, 1)
        
        self.box_crop.setContentLayout(grid)
        self.box_crop.expand()
        self.layout.addWidget(self.box_crop)

    def create_configure_section(self):
        self.box_config = CollapsibleBox("3. Configure Icon")
        self.box_config.setToolTip("Select output sizes, styling, and export format.")
        
        # Two Column Layout (Keep as instance to prevent GC)
        self.config_main_layout = QHBoxLayout()
        
        # --- Left Col: Icon Sizes ---
        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout(self.left_widget)
        self.left_layout.addWidget(InfoLabel("Icon Sizes", "Select the sizes to include in the icon file."))
        
        self.size_table = QTableWidget()
        self.size_table.setColumnCount(4)
        self.size_table.setHorizontalHeaderLabels(["", "Width", "Height", ""])
        self.size_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.size_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.size_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.size_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Action Col
        self.size_table.verticalHeader().setVisible(False)
        self.size_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Dynamic Row (Index 0)
        self.size_table.insertRow(0)
        chk = QTableWidgetItem()
        chk.setCheckState(Qt.CheckState.Checked)
        chk.setToolTip("Export the current crop size")
        chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        self.size_table.setItem(0, 0, chk)
        
        # Read-only items for dynamic row
        w_item = QTableWidgetItem("0")
        w_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable) # No edit
        h_item = QTableWidgetItem("0")
        h_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        
        self.size_table.setItem(0, 1, w_item)
        self.size_table.setItem(0, 2, h_item)
        
        sizes = [16, 24, 32, 48, 64, 96, 128, 256, 512, 1024]
        # self.size_table.setRowCount(len(sizes)) # Don't pre-set, we append
        
        for size in sizes:
            row = self.size_table.rowCount()
            self.size_table.insertRow(row)
            
            # Checkbox
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk.setCheckState(Qt.CheckState.Checked)
            self.size_table.setItem(row, 0, chk)
             
            # Width/Height (Read Only for standard)
            w_item = QTableWidgetItem(str(size))
            w_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            h_item = QTableWidgetItem(str(size))
            h_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            
            self.size_table.setItem(row, 1, w_item)
            self.size_table.setItem(row, 2, h_item)
            
        self.left_layout.addWidget(self.size_table)
        
        self.left_layout.addWidget(self.size_table)
        
        # Add Custom Size Row (Integrated)
        custom_box = QHBoxLayout()
        self.btn_add_size = QPushButton("+")
        self.btn_add_size.setFixedSize(30, 30)
        self.btn_add_size.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_size.setToolTip("Add custom resolution")
        self.btn_add_size.setStyleSheet("""
            QPushButton {
                background-color: #007bff; 
                color: white; 
                border-radius: 4px; 
                font-weight: bold; 
                font-size: 16px;
                border: none;
            }
            QPushButton:hover { background-color: #0056b3; }
        """)
        self.btn_add_size.clicked.connect(self.add_custom_size)
        
        self.input_w = QLineEdit()
        self.input_w.setPlaceholderText("W")
        self.input_w.setFixedWidth(50)
        self.input_w.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.input_h = QLineEdit()
        self.input_h.setPlaceholderText("H")
        self.input_h.setFixedWidth(50)
        self.input_h.setAlignment(Qt.AlignmentFlag.AlignCenter)

        custom_box.addWidget(self.btn_add_size)
        custom_box.addWidget(self.input_w)
        custom_box.addWidget(self.input_h)
        custom_box.addStretch()
        
        self.left_layout.addLayout(custom_box)
        self.left_layout.addStretch()
        
        # --- Right Col: Styling ---
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout(self.right_widget)
        self.right_layout.setSpacing(15)
        
        # Live Preview (New)
        prev_box = QVBoxLayout()
        prev_box.addWidget(QLabel("Icon Preview"))
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(128, 128)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("border: 1px solid #ccc; background-color: #f5f5f5; border-radius: 4px;")
        prev_box.addWidget(self.preview_label)
        prev_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.right_layout.addLayout(prev_box)
        
        # Roundness
        r_box = QVBoxLayout()
        r_box.addWidget(InfoLabel("Rounded Corners & Background", "Adjust corner radius and background fill."))
        
        r_slider_box = QHBoxLayout()
        r_slider_box.addWidget(QLabel("Square"))
        self.slider_round = QSlider(Qt.Orientation.Horizontal)
        self.slider_round.setRange(0, 100)
        self.slider_round.valueChanged.connect(self.update_preview)
        r_slider_box.addWidget(self.slider_round)
        r_slider_box.addWidget(QLabel("Circle"))
        r_box.addLayout(r_slider_box)
        self.right_layout.addLayout(r_box)
        
        # Background
        bg_box = QHBoxLayout()
        self.bg_group = QGroupBox() # Invisible container for logic
        self.chk_bg = QCheckBox("Fill Background") # Reusing name for compatibility
        self.chk_bg.toggled.connect(self.update_preview)
        
        self.btn_bg_color = QPushButton()
        self.btn_bg_color.setFixedSize(24, 24)
        self.btn_bg_color.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        self.bg_color = (255, 255, 255)
        self.btn_bg_color.clicked.connect(lambda: [self.pick_color(), self.update_preview()])

        
        bg_box.addWidget(self.chk_bg)
        bg_box.addWidget(self.btn_bg_color)
        bg_box.addStretch()
        self.right_layout.addLayout(bg_box)
        
        # Image Format (Internal for ICO)
        # Image Format (Output)
        fmt_box = QVBoxLayout()
        fmt_box.addWidget(InfoLabel("Image Format", "Select output format. ICO is for Windows, ICNS for Mac, PNG for Linux/Web."))
        self.combo_output_fmt = QComboBox()
        self.combo_output_fmt.addItems(["ICO", "ICNS", "PNG", "Linux (PNG)", "BMP"])
        self.combo_output_fmt.setCurrentText("ICO") 
        self.combo_output_fmt.currentTextChanged.connect(self.toggle_ico_constraints)
        fmt_box.addWidget(self.combo_output_fmt)
        self.right_layout.addLayout(fmt_box)
        
        self.right_layout.addStretch()
        
        # Trigger initial constraint check
        self.toggle_ico_constraints("ICO")

        # Add Cols to Main
        self.config_main_layout.addWidget(self.left_widget, 1) # Stretch 1
        self.config_main_layout.addWidget(self.right_widget, 1) # Stretch 1
        
        self.box_config.setContentLayout(self.config_main_layout)
        self.box_config.expand()
        self.layout.addWidget(self.box_config)

    def add_custom_size(self):
        # Validate Inputs
        w_text = self.input_w.text()
        h_text = self.input_h.text()
        
        if not w_text.isdigit() or not h_text.isdigit():
            # If empty, maybe just add a default placeholder row?
            # Or user expects it to fail?
            # Let's assume validation required
            return

        w = int(w_text)
        h = int(h_text)
        
        row = self.size_table.rowCount()
        self.size_table.insertRow(row)
        
        # Checkbox
        chk = QTableWidgetItem()
        chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        chk.setCheckState(Qt.CheckState.Checked)
        self.size_table.setItem(row, 0, chk)
        
        # Width/Height (Editable)
        w_item = QTableWidgetItem(str(w))
        h_item = QTableWidgetItem(str(h))
        # Default flags allow editing
        
        self.size_table.setItem(row, 1, w_item)
        self.size_table.setItem(row, 2, h_item)
        
        # Delete Button
        btn_del = QPushButton("-") # Request: "-" over red button
        btn_del.setFixedSize(24, 24)
        # Red square with white -
        btn_del.setStyleSheet("""
            QPushButton {
                background-color: #dc3545; 
                color: white; 
                border-radius: 4px; 
                font-weight: bold; 
                font-size: 16px; 
                border: none;
            }
            QPushButton:hover { background-color: #a71d2a; }
        """)
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setToolTip("Remove custom resolution")
        btn_del.clicked.connect(self.delete_custom_row)
        self.size_table.setCellWidget(row, 3, btn_del)
        
        # Clear inputs
        self.input_w.clear()
        self.input_h.clear()
        
        # Immediate Validation (check constraints)
        self.toggle_ico_constraints(self.combo_output_fmt.currentText())

    def delete_custom_row(self):
        btn = self.sender()
        if not btn: return
        
        # Find row
        # Since button is in cell widget (QTableWidget -> QWidget (viewport) -> Button?)
        # safe way: use indexAt relative to viewport
        index = self.size_table.indexAt(btn.pos())
        if index.isValid():
            self.size_table.removeRow(index.row())
            self.check_resolution_quality()

    def toggle_ico_constraints(self, format_text):
        """Disable sizes > 256 for ICO."""
        is_ico = (format_text == "ICO")
        
        for row in range(self.size_table.rowCount()):
            try:
                w_item = self.size_table.item(row, 1)
                h_item = self.size_table.item(row, 2)
                chk_item = self.size_table.item(row, 0)
                
                w = int(w_item.text())
                h = int(h_item.text())
                size = max(w, h)
                
                if is_ico and size > 256:
                    # Disable
                    chk_item.setCheckState(Qt.CheckState.Unchecked)
                    chk_item.setFlags(Qt.ItemFlag.NoItemFlags) # Disable interaction
                    
                    color = QColor("gray")
                    brush = QBrush(color)
                    w_item.setForeground(brush)
                    h_item.setForeground(brush)
                    
                    chk_item.setToolTip("ICO format supports max 256x256.")
                else:
                    # Enable
                    # Restore flags (Checkable + Enabled)
                    chk_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                    
                    # Restore color (or let check_resolution_quality handle it?)
                    # We should probably reset to black, then run check_resolution_quality
                    brush = QBrush(QColor("black"))
                    w_item.setForeground(brush)
                    h_item.setForeground(brush)
                    chk_item.setToolTip("")
                    
            except ValueError:
                pass
        
        # Re-run quality check to re-apply red if upscaling (overrides black/gray?)
        self.check_resolution_quality()

    def create_download_section(self):
        # We'll use a plain widget area for the download action
        container = QWidget()
        layout = QHBoxLayout(container)
        
        # File Name Input?
        # For now just the big button
        
        # Format Selection moved to Config section
        # self.combo_fmt = QComboBox()
        
        layout.addSpacing(20)
        
        self.convert_btn = QPushButton("Download Icon")
        self.convert_btn.setMinimumHeight(50)
        self.convert_btn.setIcon(QIcon.fromTheme("document-save"))
        self.convert_btn.setStyleSheet("font-size: 16px; background-color: #007bff; color: white; font-weight: bold; border-radius: 4px;")
        self.convert_btn.setEnabled(False) # Enabled when image loaded
        self.convert_btn.clicked.connect(self.convert_image)
        
        layout.addStretch()
        layout.addWidget(self.convert_btn)
        layout.addStretch()
        
        self.layout.addWidget(container)

    def on_selection_changed(self, rect: QRect):
        """Called when widget selection changes (mouse drag)."""
        self.spin_left.blockSignals(True)
        self.spin_top.blockSignals(True)
        self.spin_width.blockSignals(True)
        self.spin_height.blockSignals(True)
        
        self.spin_left.setValue(rect.x())
        self.spin_top.setValue(rect.y())
        self.spin_width.setValue(rect.width())
        self.spin_height.setValue(rect.height())
        
        self.spin_left.blockSignals(False)
        self.spin_top.blockSignals(False)
        self.spin_width.blockSignals(False)
        self.spin_height.blockSignals(False)
        
        self.update_preview()

    def on_spin_changed(self):
        """Called when spinboxes change."""
        x = self.spin_left.value()
        y = self.spin_top.value()
        w = self.spin_width.value()
        h = self.spin_height.value()
        
        rect = QRect(x, y, w, h)
        self.image_label.set_selection(rect)
        self.update_preview()

    def pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.bg_color = (color.red(), color.green(), color.blue())
            self.btn_bg_color.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #ccc;")

    def on_ar_changed(self, text):
        mode = "Free"
        if text == "Square": mode = "Square"
        elif text == "Original Ratio": mode = "Original"
        self.image_label.set_aspect_ratio_mode(mode)

    def check_resolution_quality(self):
        """Color code sizes if they exceed source selection."""
        rect = self.image_label.selection_rect.toRect()
        if rect.width() <= 0: return
        
        # Update Dynamic Row (Row 0)
        start_row = 1
        # Careful: if table empty? (init)
        if self.size_table.rowCount() > 0:
            # We assume row 0 is dynamic
            self.size_table.item(0, 1).setText(str(rect.width()))
            self.size_table.item(0, 2).setText(str(rect.height()))
            # Update Tooltip?
            self.size_table.item(0, 0).setToolTip(f"Export selection: {rect.width()}x{rect.height()}")
            
            # Enforce ICO constraint for dynamic row immediately
            if self.combo_output_fmt.currentText() == "ICO":
                size = max(rect.width(), rect.height())
                chk_item = self.size_table.item(0, 0)
                if size > 256:
                     chk_item.setCheckState(Qt.CheckState.Unchecked)
                     chk_item.setFlags(Qt.ItemFlag.NoItemFlags)
                     chk_item.setToolTip("ICO format supports max 256x256.")
                else:
                     # Re-enable if it was disabled (but don't force check? or restore?)
                     # If user had it checked, maybe check it? Or just enable.
                     chk_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                     # If we just re-enabled, maybe check it by default?
                     if chk_item.checkState() == Qt.CheckState.Unchecked:
                         chk_item.setCheckState(Qt.CheckState.Checked)

        for row in range(start_row, self.size_table.rowCount()):
            try:
                w_item = self.size_table.item(row, 1)
                h_item = self.size_table.item(row, 2)
                
                w = int(w_item.text())
                h = int(h_item.text())
                
                # Check upscale
                is_upscale = (w > rect.width()) or (h > rect.height())
                
                # If row is disabled (ICO constraint), keep it gray?
                # toggle_ico_constraints sets gray. check_resolution_quality sets red/black.
                # Red (warning) should probably override Gray? Or Gray (disabled) overrides Red?
                # If disabled, maybe we don't care about upscale warning?
                
                chk_item = self.size_table.item(row, 0)
                if not (chk_item.flags() & Qt.ItemFlag.ItemIsEnabled):
                    color = QColor("gray")
                else:
                    color = QColor("red") if is_upscale else QColor("black")
                
                brush = QBrush(color)
                w_item.setForeground(brush)
                h_item.setForeground(brush)
                
                if color == QColor("red"):
                    msg = "Warning: Upscaling source image (Quality Loss)"
                    w_item.setToolTip(msg)
                    h_item.setToolTip(msg)
            except ValueError:
                pass


    def make_transparent(self):
        if not self.source_image: return
        
        # Pick Color
        color = QColorDialog.getColor(Qt.GlobalColor.white, self, "Select Color to Make Transparent")
        if color.isValid():
            # Convert to RGBA
            r, g, b, _ = color.getRgb()
            target_color = (r, g, b)
            
            # Process Image
            img = self.source_image.convert("RGBA")
            data = img.getdata()
            
            new_data = []
            # Tolerance? For now, exact match.
            # User might want tolerance slider later.
            for item in data:
                # item is (r,g,b,a)
                if item[:3] == target_color:
                    new_data.append((0, 0, 0, 0)) # Transparent
                else:
                    new_data.append(item)
                    
            img.putdata(new_data)
            self.source_image = img
            self.update_transformed_source()

    def apply_edit(self, action):
        if not self.source_image: return
        
        if action == "rotate_left":
            self.rotation = (self.rotation + 90) % 360
        elif action == "rotate_right":
            self.rotation = (self.rotation - 90) % 360
        elif action == "flip_h":
            self.flip_h = not self.flip_h
        elif action == "flip_v":
             # We need to add flip_v state or handle it
             # Current state only has flip_h
             # Let's add flip_v to __init__ first, but for now we can just toggle a local and re-process
             pass 
             
        # Wait, the previous logic handled rotation/flip in process_image.
        # But now we need to Rotate/Flip ONLY the source for the Interactive Widget, 
        # THEN crop, THEN style.
        
        # We need to separate "Transform" (Rotate/Flip) from "Style" (Round/Bg).
        # Let's store the current transformed image in self.source_image_transformed
        self.update_transformed_source()
            
    def update_transformed_source(self):
        if not self.source_image: return
        
        img = self.source_image.copy()
        
        # Rotate
        if self.rotation != 0:
            img = img.rotate(-self.rotation, expand=True, resample=Image.Resampling.BICUBIC)
            
        # Flip
        if self.flip_h:
            img = ImageOps.mirror(img)
        # We need flip_v support
        if hasattr(self, 'flip_v') and self.flip_v:
             img = ImageOps.flip(img)
             
        self.source_image_transformed = img
        
        # Update Widget
        # Convert to QPixmap
        data = img.convert("RGBA").tobytes("raw", "RGBA")
        qim = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
        pix = QPixmap.fromImage(qim)
        self.image_label.set_image(pix)
        
        # Reset transforms in options? 
        # No, update_preview needs to NOT re-apply rotate/flip if we stuck them here.
        self.update_preview()

    def browse_file(self):
        formats = "*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tif *.tiff *.ico *.icns"
        path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", f"Images ({formats})")
        if path:
            self.load_image(path)
            
    def load_image(self, path):
        self.source_image = Image.open(path).convert("RGBA")
        self.rotation = 0
        self.flip_h = False
        self.flip_v = False
        self.update_transformed_source()
        self.convert_btn.setEnabled(True)
        
    def update_preview(self):
        if not hasattr(self, 'source_image_transformed') or not self.source_image_transformed: return
        if not hasattr(self, 'slider_round'): return
        
        # Crop from Transformed Source
        # Get rect from widget (Image Coords)
        rect = self.image_label.selection_rect.toRect()
        
        # Validate rect
        if rect.width() <= 0 or rect.height() <= 0: return
        
        # Crop
        cropped = self.source_image_transformed.crop((rect.x(), rect.y(), rect.right(), rect.bottom()))
        
        # Gather options from UI (Only Styling now)
        resize_ar = False
        if hasattr(self, 'chk_resize_ar'):
            resize_ar = self.chk_resize_ar.isChecked()
            
        options = {
            'radius': self.slider_round.value(),
            'fill_background': self.chk_bg.isChecked(),
            'background_color': self.bg_color,
            'rotate': 0, # Already handled
            'flip_h': False, # Already handled
            'resize_to_aspect': resize_ar 
        }
        
        # Process styling (Round, Bg)
        from core.converter import IconConverter
        processed = IconConverter.process_image(cropped, options)
        
        # Resize for preview
        processed.thumbnail((300, 300))
        data = processed.convert("RGBA").tobytes("raw", "RGBA")
        qim = QImage(data, processed.width, processed.height, QImage.Format.Format_RGBA8888)
        # Resize for preview
        processed.thumbnail((128, 128))
        data = processed.convert("RGBA").tobytes("raw", "RGBA")
        qim = QImage(data, processed.width, processed.height, QImage.Format.Format_RGBA8888)
        pix = QPixmap.fromImage(qim)
        
        if hasattr(self, 'preview_label'):
            self.preview_label.setPixmap(pix)
            
        self.check_resolution_quality()

    def convert_image(self):
        if not self.source_image: return
        
        # 1. Gather Sizes (Do this first to ensure widget is valid)
        sizes = []
        max_req_size = 0
        try:
            for row in range(self.size_table.rowCount()):
                chk_item = self.size_table.item(row, 0)
                if chk_item.checkState() == Qt.CheckState.Checked:
                    try:
                        w = int(self.size_table.item(row, 1).text())
                        h = int(self.size_table.item(row, 2).text())
                        
                        sizes.append((w, h))
                        max_req_size = max(max_req_size, w, h)
                    except ValueError:
                        pass
        except RuntimeError:
            print("Error: Widget deleted?")
            return

        if not sizes:
            print("No size selected!")
            return

        # Check for Upscaling
        # Get Crop Rect to know actual source size
        rect = self.image_label.selection_rect.toRect()
        if rect.width() <= 0 or rect.height() <= 0: return
        
        # Calculate source dimension (min side if square, or just max side?)
        # For 'contain', we care if target > source
        src_w, src_h = rect.width(), rect.height()
        src_max = max(src_w, src_h)
        
        if max_req_size > src_max:
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.warning(
                self, 
                "Upscale Warning", 
                f"The requested size ({max_req_size}px) is larger than your source selection ({src_max}px).\n\nThe result may look pixelated. Do you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        # 2. Get Output Path
        fmt_text = self.combo_output_fmt.currentText()
        
        ext = ".ico"
        filter_str = "Icon Files (*.ico)"
        
        if fmt_text == "ICNS": 
            ext = ".icns"
            filter_str = "Apple Icon (*.icns)"
        elif fmt_text == "PNG" or fmt_text == "Linux (PNG)": 
            ext = "" # Folder/Base
            filter_str = "PNG Files (*.png)" 
        elif fmt_text == "BMP":
            ext = ".bmp"
            filter_str = "Bitmap (*.bmp)"
            
        path, _ = QFileDialog.getSaveFileName(self, "Save Icon", "icon" + ext, filter_str)
        if not path: return
        
        # 3. Process and Save
        from core.converter import IconConverter
        
        resize_ar = False
        if hasattr(self, 'chk_resize_ar'):
            resize_ar = self.chk_resize_ar.isChecked()

        options = {
            'radius': self.slider_round.value(),
            'fill_background': self.chk_bg.isChecked(),
            'background_color': self.bg_color,
            'rotate': 0,
            'flip_h': False,
            'resize_to_aspect': resize_ar
        }
        
        # Crop from Transformed Source
        rect = self.image_label.selection_rect.toRect()
        if rect.width() <= 0 or rect.height() <= 0: return
        
        final_img = self.source_image_transformed.crop((rect.x(), rect.y(), rect.right(), rect.bottom()))
        
        # Full resolution process
        final_img = IconConverter.process_image(final_img, options)
        
        # Determine internal format list for save_icon
        fmts = []
        if fmt_text == "ICO": fmts.append('ico')
        elif fmt_text == "ICNS": fmts.append('icns')
        elif fmt_text == "PNG" or fmt_text == "Linux (PNG)": fmts.append('png')
        elif fmt_text == "BMP": fmts.append('bmp')
        
        # Special case for BMP: If multiple sizes, save_icon might default to folder logic?
        # Converter needs a tiny update for BMP loop if not present.
        # But 'png' logic in converter does loop.
        
        IconConverter.save_icon(final_img, path, fmts, sizes, options=options)
        print("Saved!")

    # Drag & Drop
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
    
    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.load_image(files[0])

    def paste_image(self):
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()
        if mime.hasImage():
            img = clipboard.image()
            if not img.isNull():
                # Convert QImage to PIL
                # Save to buffer
                from io import BytesIO
                buf = BytesIO()
                img.save(buf, "PNG")
                buf.seek(0)
                self.source_image = Image.open(buf).convert("RGBA")
                self.update_preview()
                self.convert_btn.setEnabled(True)
                print("Image pasted from clipboard")
