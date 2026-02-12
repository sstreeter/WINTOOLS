"""
Main window for IconForge application.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QGroupBox, QRadioButton, QCheckBox,
    QSlider, QLineEdit, QProgressBar, QMessageBox, QColorDialog,
    QSpinBox, QTabWidget, QComboBox, QScrollArea, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QDragEnterEvent, QDropEvent
from PIL import Image, ImageChops, ImageFilter
from pathlib import Path
import sys

from core import ImageProcessor, AutoCropper, MaskingEngine, IconExporter, EdgeProcessor, BorderMasking, CompositionEngine
from core.stroke import StrokeGenerator, SuperPolisher
from core.filters import FilterEngine
from core.icon_audit import IconAuditor, IssueSeverity
from core.icon_audit import IconAuditor, IssueSeverity
from ui.audit_dialog import AuditReportDialog
from ui.styles import MODERN_STYLESHEET
from ui.widgets import TransparencyLabel
from utils import ArchiveManager


class IconGeneratorThread(QThread):
    """Background thread for icon generation."""
    
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, processor, settings):
        super().__init__()
        self.processor = processor
        self.settings = settings
    
    def run(self):
        """Generate icons in background."""
        try:
            # Generate all sizes
            images = self.processor.generate_all_sizes()
            self.progress.emit(20)
            
            # Apply masking variants if needed
            from core.masking import MaskingEngine
            
            # Create output directory
            output_dir = Path(self.settings['output_dir'])
            icon_name = self.settings['icon_name']
            
            if self.settings['create_archive']:
                icon_dir = ArchiveManager.create_organized_structure(
                    str(output_dir),
                    icon_name,
                    self.settings.get('source_path')
                )
                paths = ArchiveManager.get_output_paths(icon_dir, icon_name)
            else:
                output_dir.mkdir(parents=True, exist_ok=True)
                paths = {
                    'ico_full_alpha': output_dir / f"{icon_name}_full_alpha.ico",
                    'ico_binary_alpha': output_dir / f"{icon_name}_binary_alpha.ico",
                    'ico_with_glow': output_dir / f"{icon_name}_with_glow.ico",
                    'icns': output_dir / f"{icon_name}.icns",
                    'png_dir': output_dir / 'png'
                }
            
            self.progress.emit(40)
            
            # Export Windows ICO files
            if self.settings['export_windows']:
                # Full alpha version
                IconExporter.export_ico(images, str(paths['ico_full_alpha']))
                
                # Binary alpha version
                binary_images = {
                    size: MaskingEngine.binary_alpha(img)
                    for size, img in images.items()
                }
                IconExporter.export_ico(binary_images, str(paths['ico_binary_alpha']))
                
                # Glow version
                glow_images = {
                    size: MaskingEngine.add_glow(img)
                    for size, img in images.items()
                }
                IconExporter.export_ico(glow_images, str(paths['ico_with_glow']))
                
                self.progress.emit(60)
            
            # Export Mac ICNS
            if self.settings['export_mac']:
                IconExporter.export_icns_macos(images, str(paths['icns']))
                self.progress.emit(80)
            
            # Export PNG set
            if self.settings['export_png']:
                IconExporter.export_png_set(images, str(paths['png_dir']))
                self.progress.emit(90)
            
            # Create ZIP if requested
            if self.settings['create_archive'] and self.settings.get('create_zip'):
                zip_path = output_dir / f"{icon_name}.zip"
                ArchiveManager.create_zip_archive(str(icon_dir), str(zip_path))
            
            self.progress.emit(100)
            self.finished.emit(True, str(output_dir))
            
        except Exception as e:
            self.finished.emit(False, str(e))


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.processor = ImageProcessor()
        self.current_mask_color = (255, 255, 255)
        self.processor = ImageProcessor()
        self.reference_image = None # Phase 21: Reference Comparison
        self.reference_pixmap = None
        self.current_mask_color = (255, 255, 255)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the modern user interface."""
        self.setWindowTitle("IconForge - Professional Edition")
        self.setMinimumSize(1200, 850) # Wider default
        self.setStyleSheet(MODERN_STYLESHEET)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout (Split View with QSplitter)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(2)
        # Style the handle? It's tricky with QSS but doable in theory. 
        # For now rely on standard look or minimal style.
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #3e3e42; }")
        
        main_layout.addWidget(self.splitter)
        
        # --- LEFT PANEL: CONTROLS (Scrollable) ---
        control_container = QWidget()
        # control_container.setFixedWidth(400) # REMOVED: Let splitter handle width
        control_container.setMinimumWidth(320) # Minimum usable width
        control_container.setStyleSheet("background-color: #252526; border-right: 1px solid #3e3e42;")
        
        control_layout = QVBoxLayout(control_container)
        control_layout.setContentsMargins(0,0,0,0)
        
        # Scroll Area for Controls
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)
        scroll_layout.setContentsMargins(15, 15, 15, 15)
        
        # 1. Header
        header = QLabel("ICON FORGE")
        header.setObjectName("Header")
        scroll_layout.addWidget(header)
        
        # 2. Source Inspector (Input)
        # We'll use a simplified version for the sidebar
        self.source_group = self.create_source_inspector()
        scroll_layout.addWidget(self.source_group)
        
        # 3. Quick Enhancements (Prep)
        enhance_group = self.create_quick_enhance_panel()
        scroll_layout.addWidget(enhance_group)
        
        # 4. Cleanup (Masking)
        masking_group = self.create_masking_panel()
        scroll_layout.addWidget(masking_group)
        
        # 5. Geometry (Enforcer)
        geometry_group = self.create_geometry_panel()
        scroll_layout.addWidget(geometry_group)
        
        # 6. Composition (Fit)
        comp_group = self.create_composition_panel()
        scroll_layout.addWidget(comp_group)
        
        # 7. Effects (Stroke/Polish)
        stroke_group = self.create_stroke_panel()
        scroll_layout.addWidget(stroke_group)
        
        # 8. Export (Output)
        export_group = self.create_export_panel()
        # We need to manually add the Generate button inside or near this group
        # Let's add it to the bottom of the scroll layout
        scroll_layout.addWidget(export_group)
        
        # Generate Button (Big)
        self.generate_btn = QPushButton("🚀 GENERATE ICONS")
        self.generate_btn.setMinimumHeight(50)
        self.generate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.generate_btn.setStyleSheet("font-size: 14px; font-weight: bold; background-color: #007acc;")
        self.generate_btn.setEnabled(False)
        self.generate_btn.clicked.connect(self.generate_icons)
        scroll_layout.addWidget(self.generate_btn)
        # Progress Bar (Phase 2)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { height: 8px; border-radius: 4px; } QProgressBar::chunk { background-color: #007acc; border-radius: 4px; }")
        scroll_layout.addWidget(self.progress_bar)
        
        scroll_layout.addStretch() # Push everything up
        
        scroll.setWidget(scroll_content)
        control_layout.addWidget(scroll)
        
        # Add Control Panel to Splitter
        self.splitter.addWidget(control_container)
        
        # --- RIGHT PANEL: PREVIEW (Sticky) ---
        preview_container = QWidget()
        preview_container.setStyleSheet("background-color: #1e1e1e;")
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(20, 20, 20, 20)
        
        # Artboard (Reused)
        self.artboard_group = self.create_artboard()
        # Ensure artboard expands
        self.preview_scroll.setStyleSheet("QScrollArea { background-color: #1e1e1e; border: none; }") 
        preview_layout.addWidget(self.artboard_group)
        
        # Add Preview Panel to Splitter
        self.splitter.addWidget(preview_container)
        
        # Set Initial Sizes (420px for controls - wider default)
        self.splitter.setSizes([420, 780])
        self.splitter.setCollapsible(0, False) # Keep controls visible
        
        # Enable drag and drop
        self.setAcceptDrops(True)
    

    
    def create_artboard(self):
        """Create the Artboard panel (Right Canvas)."""
        group = QGroupBox("Artboard (Live Preview)")
        layout = QVBoxLayout()
        
        # --- VIEW TOOLBAR ---
        view_toolbar = QHBoxLayout()
        view_toolbar.setContentsMargins(0, 0, 0, 0)
        view_toolbar.setSpacing(15)
        
        view_label = QLabel("View Mode:")
        view_label.setStyleSheet("color: #888; font-weight: bold;")
        view_toolbar.addWidget(view_label)
        
        self.btn_view_live = QRadioButton("Live Result")
        self.btn_view_live.setChecked(True)
        self.btn_view_live.clicked.connect(lambda: self.set_view_mode("live"))
        view_toolbar.addWidget(self.btn_view_live)
        
        self.btn_view_source = QRadioButton("Source Input")
        self.btn_view_source.clicked.connect(lambda: self.set_view_mode("source"))
        view_toolbar.addWidget(self.btn_view_source)
        
        self.btn_view_split = QRadioButton("Split Compare")
        self.btn_view_split.setEnabled(False) # Enabled when Ref loaded
        self.btn_view_split.clicked.connect(lambda: self.set_view_mode("split"))
        view_toolbar.addWidget(self.btn_view_split)
        
        # Load Ref Button
        self.btn_load_ref = QPushButton("📂 Ref")
        self.btn_load_ref.setFixedWidth(60)
        self.btn_load_ref.setToolTip("Load Reference Image for Comparison")
        self.btn_load_ref.clicked.connect(self.load_reference_image)
        view_toolbar.addWidget(self.btn_load_ref)
        
        # Split Slider (Wipe)
        self.split_slider = QSlider(Qt.Orientation.Horizontal)
        self.split_slider.setRange(0, 100)
        self.split_slider.setValue(50)
        self.split_slider.setFixedWidth(100)
        self.split_slider.setVisible(False)
        self.split_slider.setToolTip("Wipe: Left = Reference, Right = Result")
        self.split_slider.valueChanged.connect(lambda: self.refresh_viewport())
        view_toolbar.addWidget(self.split_slider)
        
        view_toolbar.addStretch()
        layout.addLayout(view_toolbar)
        
        # Artboard viewing area (Zoomable Viewport)
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True) # Fit by default
        self.preview_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_scroll.setStyleSheet("QScrollArea { background-color: #2b2b2b; border: none; }")
        
        self.preview_label = TransparencyLabel()
        self.preview_label.setText("Preview")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_scroll.setWidget(self.preview_label)
        
        layout.addWidget(self.preview_scroll, 1) # Stretch 1
        
        # Zoom Toolbar (Phase 18)
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Zoom:"))
        
        self.btn_fit = QPushButton("Fit")
        self.btn_fit.setCheckable(True)
        self.btn_fit.setChecked(True)
        self.btn_fit.setFixedWidth(50)
        self.btn_fit.clicked.connect(self.toggle_fit_zoom)
        zoom_layout.addWidget(self.btn_fit)
        
        self.btn_100 = QPushButton("1:1")
        self.btn_100.setFixedWidth(50)
        self.btn_100.clicked.connect(lambda: self.set_zoom_level(1.0))
        zoom_layout.addWidget(self.btn_100)
        
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10, 400) # 10% to 400%
        self.zoom_slider.setValue(100) # Start at 100% logic (though overwritten by Fit)
        self.zoom_slider.setToolTip("View Zoom")
        self.zoom_slider.valueChanged.connect(self.update_zoom_from_slider)
        zoom_layout.addWidget(self.zoom_slider)
        
        self.zoom_label = QLabel("Fit")
        self.zoom_label.setFixedWidth(50)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        zoom_layout.addWidget(self.zoom_label)
        
        layout.addLayout(zoom_layout)
        
        # Tool Bar
        tools_layout = QHBoxLayout()
        tools_layout.addWidget(QLabel("Overlays:"))
        
        tools_help = self.create_help_btn(
            "Artboard Overlays",
            "<b>Visual aids for perfect icons.</b><br><br>"
            "<ul>"
            "<li><b>Mask (Red):</b> Shows removed/transparent areas in Red. Use this to adjustments.</li>"
            "<li><b>Safe Zone:</b> Shows the Industry Standard 10% safety margin. Maintain key content inside the box.</li>"
            "</ul>"
        )
        tools_layout.addWidget(tools_help)
        tools_layout.addStretch() # Spacer
        
        self.show_mask_overlay = QCheckBox("Mask (Red)")
        self.show_mask_overlay.setToolTip("Show removed areas in red")
        self.show_mask_overlay.toggled.connect(self.update_preview)
        tools_layout.addWidget(self.show_mask_overlay)
        
        self.show_safe_zone = QCheckBox("Safe Zone")
        self.show_safe_zone.setToolTip("Show 10% Safe Zone Grid")
        self.show_safe_zone.setChecked(True)
        self.show_safe_zone.toggled.connect(self.update_preview)
        tools_layout.addWidget(self.show_safe_zone)
        
        tools_layout.addStretch()
        layout.addLayout(tools_layout)
        
        # Background selector (for export preview)
        bg_layout = QHBoxLayout()
        bg_layout.addWidget(QLabel("Preview BG:"))
        
        self.bg_transparent = QRadioButton("🏁 Checker")
        self.bg_transparent.setChecked(True)
        self.bg_transparent.toggled.connect(self.update_preview)
        bg_layout.addWidget(self.bg_transparent)
        
        self.bg_white = QRadioButton("⚪ White")
        self.bg_white.toggled.connect(self.update_preview)
        bg_layout.addWidget(self.bg_white)
        
        self.bg_black = QRadioButton("⚫ Black")
        self.bg_black.toggled.connect(self.update_preview)
        bg_layout.addWidget(self.bg_black)
        
        bg_layout.addStretch()
        layout.addLayout(bg_layout)
        
        group.setLayout(layout)
        return group
    
    def create_masking_panel(self):
        """Create masking options panel."""
        group = QGroupBox("Masking Options")
        layout = QVBoxLayout()
        
        # Radio buttons for masking mode
        mode_layout = QHBoxLayout()
        
        self.mask_none = QRadioButton("None (Keep Original)")
        self.mask_none.setChecked(True)
        self.mask_none.toggled.connect(self.apply_masking)
        mode_layout.addWidget(self.mask_none)
        
        self.mask_autocrop = QRadioButton("Auto-Crop (Detect Content)")
        self.mask_autocrop.toggled.connect(self.apply_masking)
        mode_layout.addWidget(self.mask_autocrop)
        
        self.mask_color = QRadioButton("Remove Color (Entire Image)")
        self.mask_color.toggled.connect(self.apply_masking)
        mode_layout.addWidget(self.mask_color)
        
        self.mask_border = QRadioButton("Remove Color (Borders Only)")
        self.mask_border.toggled.connect(self.apply_masking)
        mode_layout.addWidget(self.mask_border)
        
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        
        # Phase 19: Edge Handling (Seed Strategy & Protection)
        edge_layout = QHBoxLayout()
        edge_layout.addWidget(QLabel("Seed:"))
        
        self.seed_combo = QComboBox()
        self.seed_combo.addItems(["Corners (Default)", "Edges (All)", "Manual (Center)"])
        self.seed_combo.setToolTip("Where to sample the background color from.")
        self.seed_combo.currentIndexChanged.connect(self.apply_masking)
        edge_layout.addWidget(self.seed_combo)
        
        self.edge_pad_check = QCheckBox("Protect Edges")
        self.edge_pad_check.setToolTip("Adds temporary padding to prevent 'eating' full-bleed icons.")
        self.edge_pad_check.stateChanged.connect(self.apply_masking)
        edge_layout.addWidget(self.edge_pad_check)
        
        edge_layout.addStretch()
        layout.addLayout(edge_layout)
        
        # Color mask settings (The Masking Lab)
        # 1. Primary Key
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Primary Key:"))
        
        self.color_btn = QPushButton("🎨 Pick Color 1")
        self.color_btn.setFixedWidth(100)
        self.color_btn.clicked.connect(self.pick_color)
        color_layout.addWidget(self.color_btn)
        
        color_layout.addWidget(QLabel("Tolerance:"))
        self.tolerance_spin = QSpinBox()
        self.tolerance_spin.setRange(0, 255)
        self.tolerance_spin.setValue(30)
        self.tolerance_spin.setSuffix(" px")
        self.tolerance_spin.valueChanged.connect(self.apply_masking)
        color_layout.addWidget(self.tolerance_spin)
        
        color_layout.addStretch()
        layout.addLayout(color_layout)
        
        # 2. Secondary Key (Multi-Mask) - Phase 9
        color_2_layout = QHBoxLayout()
        self.enable_key_2 = QCheckBox("Secondary Key:")
        self.enable_key_2.toggled.connect(self.apply_masking)
        self.enable_key_2.toggled.connect(lambda c: self.color_btn_2.setEnabled(c))
        color_2_layout.addWidget(self.enable_key_2)
        
        self.color_btn_2 = QPushButton("🎨 Pick Color 2")
        self.color_btn_2.setFixedWidth(100)
        self.color_btn_2.setEnabled(False)
        self.color_btn_2.clicked.connect(self.pick_color_2)
        color_2_layout.addWidget(self.color_btn_2)
        
        color_2_layout.addWidget(QLabel("Tolerance:"))
        self.tolerance_spin_2 = QSpinBox()
        self.tolerance_spin_2.setRange(0, 255)
        self.tolerance_spin_2.setValue(30)
        self.tolerance_spin_2.setSuffix(" px")
        self.tolerance_spin_2.valueChanged.connect(self.apply_masking)
        color_2_layout.addWidget(self.tolerance_spin_2)
        
        color_2_layout.addStretch()
        layout.addLayout(color_2_layout)
        
        # 3. Mask Choke / Expand (Promoted to Main Panel)
        choke_layout = QHBoxLayout()
        choke_layout.addWidget(QLabel("Mask Choke:"))
        
        self.mask_choke_slider = QSlider(Qt.Orientation.Horizontal)
        self.mask_choke_slider.setRange(-5, 5)
        self.mask_choke_slider.setValue(0)
        self.mask_choke_slider.setFixedWidth(150)
        self.mask_choke_slider.setToolTip("Negative = Choke (Remove Fringe) | Positive = Expand")
        
        choke_label = QLabel("0 px")
        self.mask_choke_slider.valueChanged.connect(lambda v: choke_label.setText(f"{v} px"))
        self.mask_choke_slider.valueChanged.connect(self.apply_masking)
        
        choke_layout.addWidget(self.mask_choke_slider)
        choke_layout.addWidget(choke_label)
        
        choke_help = self.create_help_btn(
            "Mask Choke (Reduce Border)",
            "<b>Controls the mask boundary.</b><br><br>"
            "<ul>"
            "<li><b>Negative (-1 to -5):</b> Choke/Shrink. REMOVES halos and fringes.</li>"
            "<li><b>Positive (+1 to +5):</b> Expand/Grow. Recover lost edges.</li>"
            "</ul>"
        )
        choke_layout.addWidget(choke_help)
        choke_layout.addStretch()
        layout.addLayout(choke_layout)
        
        
        # Auto-crop after masking checkbox
        self.autocrop_after = QCheckBox("✂️ Auto-Crop After Masking (Crop to tight bounds after removing transparency)")
        self.autocrop_after.setChecked(True)  # Default ON for clean results
        self.autocrop_after.toggled.connect(self.apply_masking)
        layout.addWidget(self.autocrop_after)
        
        # Advanced edge processing
        
        # Header for Advanced Edge
        edge_header = QHBoxLayout()
        edge_label = QLabel("✨ Advanced Edge Processing (Optional)")
        edge_help = self.create_help_btn(
            "Advanced Edge Processing",
            "<b>Fine-tune edge quality.</b><br><br>"
            "<ul>"
            "<li><b>Defringe:</b> Removes color halos/fringing from transparent edges.</li>"
            "<li><b>Clean Edges:</b> Removes semi-transparent pixel debris.</li>"
            "<li><b>Edge Threshold:</b> Determines what opacity is considered 'solid'.</li>"
            "</ul>"
        )
        edge_header.addWidget(edge_label)
        edge_header.addWidget(edge_help)
        edge_header.addStretch()
        
        edge_group = QGroupBox()
        edge_group.setTitle("") # Custom header via layout
        edge_layout = QVBoxLayout()
        edge_layout.addLayout(edge_header)
        
        # Checkbox to enable group (simulated groupbox behavior)
        self.edge_group_check = QCheckBox("Enable Edge Processing")
        self.edge_group_check.setChecked(False)
        self.edge_group_check.toggled.connect(self.apply_masking)
        self.edge_group_check.toggled.connect(self.update_ui_state) # Update UI enable state
        edge_layout.addWidget(self.edge_group_check)
        
        # Container for controls
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        self.edge_controls = controls_widget # Store ref
        
        # Defringe checkbox
        self.defringe_check = QCheckBox("Defringe (Remove Color Halos)")
        self.defringe_check.setChecked(False)
        self.defringe_check.toggled.connect(self.apply_masking)
        controls_layout.addWidget(self.defringe_check)
        
        # Clean edges checkbox
        self.clean_edges_check = QCheckBox("Clean Edges (Remove Pixel Debris)")
        self.clean_edges_check.setChecked(True)
        self.clean_edges_check.toggled.connect(self.apply_masking)
        controls_layout.addWidget(self.clean_edges_check)
        
        # Edge threshold with spinbox
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Edge Threshold:"))
        
        self.edge_threshold_spin = QSpinBox()
        self.edge_threshold_spin.setRange(0, 50)
        self.edge_threshold_spin.setValue(10)
        self.edge_threshold_spin.setSuffix(" alpha")
        self.edge_threshold_spin.valueChanged.connect(self.apply_masking)
        threshold_layout.addWidget(self.edge_threshold_spin)
        
        threshold_layout.addStretch()
        controls_layout.addLayout(threshold_layout)
        
        edge_layout.addWidget(controls_widget)
        edge_group.setLayout(edge_layout)
        
        layout.addWidget(edge_group)
        self.edge_group = self.edge_group_check # Redirect reference for logic compatibility
        
        group.setLayout(layout)
        return group
    
    def create_export_panel(self):
        """Create export options panel with Output settings."""
        group = QGroupBox("Export Settings")
        layout = QVBoxLayout()
        
        # 1. Output Path & Name
        # Icon Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.icon_name_input = QLineEdit()
        self.icon_name_input.setPlaceholderText("Auto (Source Filename)")
        name_layout.addWidget(self.icon_name_input)
        layout.addLayout(name_layout)
        
        # Output Directory
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Output:"))
        self.output_path = QLineEdit(str(Path.home() / "Desktop" / "icons"))
        dir_layout.addWidget(self.output_path)
        browse_btn = QPushButton("...")
        browse_btn.setFixedWidth(30)
        browse_btn.clicked.connect(self.browse_output)
        dir_layout.addWidget(browse_btn)
        layout.addLayout(dir_layout)
        
        layout.addSpacing(10)
        
        # 2. Formats
        formats_label = QLabel("Formats:")
        formats_label.setObjectName("SubHeader")
        layout.addWidget(formats_label)
        
        formats_layout = QVBoxLayout() # Vertical stack for clean look
        
        self.export_windows = QCheckBox("Windows ICO (.ico)")
        self.export_windows.setChecked(True)
        formats_layout.addWidget(self.export_windows)
        
        self.export_mac = QCheckBox("Mac ICNS (.icns)")
        self.export_mac.setChecked(True)
        formats_layout.addWidget(self.export_mac)
        
        self.export_png = QCheckBox("PNG Set (16px - 1024px)")
        self.export_png.setChecked(True)
        formats_layout.addWidget(self.export_png)
        
        self.create_archive = QCheckBox("Create ZIP Archive")
        self.create_archive.setChecked(True)
        formats_layout.addWidget(self.create_archive)
        
        layout.addLayout(formats_layout)
        
        layout.addStretch()
        group.setLayout(layout)
        return group
        
    def create_help_btn(self, title: str, text: str):
        """Create a help button with popup info."""
        btn = QPushButton("?")
        btn.setFixedSize(20, 20)
        btn.setToolTip("Click for more info")
        btn.setStyleSheet("""
            QPushButton {
                border-radius: 10px;
                background-color: #ddd;
                color: #555;
                font-weight: bold;
                border: 1px solid #aaa;
            }
            QPushButton:hover {
                background-color: #4a90e2;
                color: white;
                border: 1px solid #357abd;
            }
        """)
        btn.clicked.connect(lambda: QMessageBox.information(self, title, text))
        return btn

    def create_composition_panel(self):
        """Create Composition Settings panel (Phase 16)."""
        group = QGroupBox("Smart Composition (Fit & Padding)")
        layout = QVBoxLayout()
        
        # 1. Fit Mode (Contain vs Cover)
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Fit Mode:")
        self.fit_contain = QRadioButton("Fit (Whole Image)")
        self.fit_contain.setChecked(True)
        self.fit_contain.setToolTip("Scale image to fit INSIDE the square (adds padding if needed).")
        
        self.fit_cover = QRadioButton("Fill (Crop)")
        self.fit_cover.setToolTip("Scale image to FILL the square (crops excess).")
        
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.fit_contain)
        mode_layout.addWidget(self.fit_cover)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        
        # 2. Scale / Padding Slider
        scale_layout = QHBoxLayout()
        self.scale_label = QLabel("Zoom / Scale: 100%")
        
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setRange(50, 150) # 50% to 150%
        self.scale_slider.setValue(100)
        self.scale_slider.setToolTip("Zoom out (<100%) to add border padding.\nZoom in (>100%) to crop.")
        
        self.scale_slider.valueChanged.connect(lambda v: self.scale_label.setText(f"Zoom / Scale: {v}%"))
        self.scale_slider.sliderReleased.connect(self.apply_masking) # Update on release to avoid lag
        
        scale_layout.addWidget(self.scale_slider)
        
        # Phase 19: Safe Margin Button
        self.btn_safe_margin = QPushButton("Safe Margin (90%)")
        self.btn_safe_margin.setToolTip("Shrink to 90% to prevent border clipping.")
        self.btn_safe_margin.setFixedWidth(120)
        
        def apply_safe_margin():
            self.scale_slider.setValue(90)
            self.apply_masking()
            
        self.btn_safe_margin.clicked.connect(apply_safe_margin)
        scale_layout.addWidget(self.btn_safe_margin)
        
        layout.addLayout(scale_layout)
        
        # Connect mode toggles
        self.fit_contain.toggled.connect(self.apply_masking)
        self.fit_cover.toggled.connect(self.apply_masking)
        
        group.setLayout(layout)
        return group
        
    def create_geometry_panel(self):
        """Create Geometry Settings panel (Phase 4)."""
        group = QGroupBox("Geometry Settings (Enforce Clean Lines)")
        layout = QHBoxLayout()
        
        # 1. Smoothing (Wart Removal)
        smooth_layout = QVBoxLayout()
        
        # Header with Help
        smooth_header = QHBoxLayout()
        smooth_label = QLabel("Smoothing (Wart Removal): 50")
        self.smooth_label = smooth_label # Store ref for update
        
        smooth_help = self.create_help_btn(
            "Geometry Smoothing (Wart Removal)",
            "<b>Controls the aggression of the Smart Edge engine.</b><br><br>"
            "<ul>"
            "<li><b>0-40 (Gentle):</b> Faithful to source. Good for organic shapes.</li>"
            "<li><b>50 (Standard):</b> Removes small pixel bumps while keeping curves.</li>"
            "<li><b>60-100 (Aggressive):</b> The 'Enforcer'. Eats away warts and protrusions. "
            "Forces lines to be straight. Use this for geometric icons with dirty edges.</li>"
            "</ul>"
        )
        smooth_header.addWidget(smooth_label)
        smooth_header.addWidget(smooth_help)
        smooth_header.addStretch()
        smooth_layout.addLayout(smooth_header)
        
        self.smooth_slider = QSlider(Qt.Orientation.Horizontal)
        self.smooth_slider.setRange(0, 100)
        self.smooth_slider.setValue(50)
        self.smooth_slider.setToolTip("Aggressiveness of bump removal. Higher = Straighter lines.")
        self.smooth_slider.valueChanged.connect(lambda v: self.smooth_label.setText(f"Smoothing (Wart Removal): {v}"))
        self.smooth_slider.sliderReleased.connect(self.apply_masking) # Live Update
        
        smooth_layout.addWidget(self.smooth_slider)
        layout.addLayout(smooth_layout)
        
        # Phase 20: Liquid Polish (KPT Style)
        polish_layout = QHBoxLayout()
        self.liquid_polish_check = QCheckBox("Liquid Polish (Super-Sampled)")
        self.liquid_polish_check.setToolTip("Upscale 4x -> Blur -> Sharpen. Creates vector-like smoothness.")
        self.liquid_polish_check.toggled.connect(self.apply_masking) # Live Update
        polish_layout.addWidget(self.liquid_polish_check)
        polish_layout.addStretch()
        layout.addLayout(polish_layout)
        
        # 2. Corner Sharpness
        sharp_layout = QVBoxLayout()
        
        # Header with Help
        sharp_header = QHBoxLayout()
        sharp_label = QLabel("Corner Sharpness: 50")
        self.sharp_label = sharp_label
        
        sharp_help = self.create_help_btn(
            "Corner Sharpness",
            "<b>Controls the rounding radius of corners.</b><br><br>"
            "<ul>"
            "<li><b>0-30 (Round):</b> Soft, friendly, rounded corners.</li>"
            "<li><b>50 (Standard):</b> Balanced anti-aliasing.</li>"
            "<li><b>80-100 (Razor):</b> Sharp, crisp corners with minimal blur. "
            "Perfect for modern, flat design.</li>"
            "</ul>"
        )
        sharp_header.addWidget(sharp_label)
        sharp_header.addWidget(sharp_help)
        sharp_header.addStretch()
        sharp_layout.addLayout(sharp_header)
        
        self.sharp_slider = QSlider(Qt.Orientation.Horizontal)
        self.sharp_slider.setRange(0, 100)
        self.sharp_slider.setValue(50)
        self.sharp_slider.setToolTip("0 = Round, 100 = Razor Sharp")
        self.sharp_slider.valueChanged.connect(lambda v: self.sharp_label.setText(f"Corner Sharpness: {v}"))
        self.sharp_slider.sliderReleased.connect(self.apply_masking) # Live Update
        
        sharp_layout.addWidget(self.sharp_slider)
        layout.addLayout(sharp_layout)
        
        group.setLayout(layout)
        return group
        
    def create_stroke_panel(self):
        """Phase 8 & 20: Create 'Stroke & Polish' panel."""
        group = QGroupBox("Stroke Engine & Polish")
        layout = QVBoxLayout()
        
        # Helper method for sliders
        def add_slider(name, min_val, max_val, default_val, tooltip, help_content):
            row = QHBoxLayout()
            lbl_layout = QHBoxLayout()
            label = QLabel(f"{name}: {default_val}")
            lbl_layout.addWidget(label)
            lbl_layout.addWidget(self.create_help_btn("Stroke Engine", help_content))
            lbl_layout.addStretch()
            row.addLayout(lbl_layout)
            
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(min_val, max_val)
            slider.setValue(default_val)
            slider.setToolTip(tooltip)
            slider.valueChanged.connect(lambda v: label.setText(f"{name}: {v}"))
            slider.sliderReleased.connect(self.apply_masking) # Live Update (on Release)
            layout.addLayout(row)
            layout.addWidget(slider)
            return slider, label

        # 1. Shape Weight (Dilate/Erode) - Was "Stroke Weight"
        self.stroke_slider, self.stroke_label = add_slider(
            "Shape Weight (Dilate/Erode)", -10, 10, 0,
            "Thicken or Thin the lines (Alpha Manipulation).",
            "<b>Shape Weight (-10 to +10):</b><br>Modifies the alpha channel directly.<br><ul><li><b>Positive (+):</b> Dilate/Grow (Bold).</li><li><b>Negative (-):</b> Erode (Thin).</li></ul>"
        )
        
        layout.addSpacing(10)
        
        # 2. Phase 20: Border Engine (Colored Stroke)
        self.border_group = QGroupBox("Border Engine")
        self.border_group.setCheckable(True)
        self.border_group.setChecked(False)
        self.border_group.toggled.connect(self.apply_masking) # Live Update
        border_layout = QVBoxLayout()
        
        # Color & Alignment Row
        row1 = QHBoxLayout()
        self.stroke_color_btn = QPushButton("🎨 Color")
        self.current_stroke_color = (0, 0, 0, 255) # Default Black
        self.stroke_color_btn.clicked.connect(self.pick_stroke_color)
        self.stroke_color_btn.setStyleSheet("background-color: black; color: white;")
        row1.addWidget(self.stroke_color_btn)
        
        row1.addWidget(QLabel("Align:"))
        self.stroke_align_combo = QComboBox()
        self.stroke_align_combo.addItems(["Outside", "Center", "Inside"])
        self.stroke_align_combo.currentIndexChanged.connect(self.apply_masking) # Live Update
        self.stroke_align_combo.setToolTip("Outside: Grows outward (clips if full bleed).\nCenter: Straddles edge.\nInside: Safe for full bleed.")
        row1.addWidget(self.stroke_align_combo)
        border_layout.addLayout(row1)
        
        # Thickness Slider
        t_label = QLabel("Thickness: 10px")
        border_layout.addWidget(t_label)
        self.stroke_width_slider = QSlider(Qt.Orientation.Horizontal)
        self.stroke_width_slider.setRange(1, 50)
        self.stroke_width_slider.setValue(10)
        self.stroke_width_slider.valueChanged.connect(lambda v: t_label.setText(f"Thickness: {v}px"))
        self.stroke_width_slider.sliderReleased.connect(self.apply_masking) # Live Update
        border_layout.addWidget(self.stroke_width_slider)
        
        self.border_group.setLayout(border_layout)
        layout.addWidget(self.border_group)
        
        layout.addSpacing(10)

        # 3. Post Sharpen (Resolution Snap)
        self.sharpen_slider, self.sharpen_label = add_slider(
            "Resolution Snap (Sharpen)", 0, 100, 0,
            "Contrast enhancement at edges for pixel-grid alignment.",
            "<b>Resolution Snap (0-100):</b><br>Applies Unsharp Mask.<br>Helps icon 'snap' to pixel grid."
        )
        
        group.setLayout(layout)
        return group
        
    def create_quick_enhance_panel(self):
        """Create Quick Enhancements panel (Checkbox Style)."""
        group = QGroupBox("Quick Enhancements (Prep)")
        # User requested: Enhance, Sharpen, Antialias, Despeckle, Equalize, Normalize
        layout = QHBoxLayout()
        
        # 1. Enhance (Auto Contrast - Cutoff 2%)
        self.chk_enhance = QCheckBox("Enhance")
        self.chk_enhance.setToolTip("Auto Contrast (Maximize Tone, 2% Cutoff)")
        self.chk_enhance.toggled.connect(self.apply_masking)
        layout.addWidget(self.chk_enhance)
        
        # 2. Sharpen
        self.chk_sharpen = QCheckBox("Sharpen")
        self.chk_sharpen.setToolTip("Basic Sharpen Filter")
        self.chk_sharpen.toggled.connect(self.apply_masking)
        layout.addWidget(self.chk_sharpen)
        
        # 3. Antialias (Smooth)
        self.chk_antialias = QCheckBox("Antialias")
        self.chk_antialias.setToolTip("Smooth jagged edges")
        self.chk_antialias.setChecked(False) # User source has checked? Let's leave unchecked for now to be safe
        self.chk_antialias.toggled.connect(self.apply_masking)
        layout.addWidget(self.chk_antialias)
        
        # 4. Despeckle (Median)
        self.chk_despeckle = QCheckBox("Despeckle")
        self.chk_despeckle.setToolTip("Remove noise (Median Filter)")
        self.chk_despeckle.toggled.connect(self.apply_masking)
        layout.addWidget(self.chk_despeckle)
        
        # 5. Equalize
        self.chk_equalize = QCheckBox("Equalize")
        self.chk_equalize.setToolTip("Histogram Equalization")
        self.chk_equalize.toggled.connect(self.apply_masking)
        layout.addWidget(self.chk_equalize)
        
        # 6. Normalize (Auto Contrast - Full Range)
        self.chk_normalize = QCheckBox("Normalize")
        self.chk_normalize.setToolTip("Stretch contrast to full range (No Cutoff)")
        self.chk_normalize.toggled.connect(self.apply_masking)
        layout.addWidget(self.chk_normalize)
        
        layout.addStretch()
        group.setLayout(layout)
        return group
    
    def update_ui_state(self):
        """Update UI state based on settings."""
        if hasattr(self, 'edge_controls') and hasattr(self, 'edge_group_check'):
            self.edge_controls.setEnabled(self.edge_group_check.isChecked())
            
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event."""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.load_image(file_path)
    
    def choose_file(self):
        """Open file dialog to choose image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.svg *.eps *.pdf *.ai)"
        )
        if file_path:
            self.load_image(file_path)
    
    def load_image(self, path: str):
        """Load an image file."""
        if self.processor.load_image(path):
            self.current_source_path = path
            file_name = Path(path).stem
            
            # Update Info Label
            w, h = self.processor.source_image.size
            self.filename_label.setText(file_name)
            self.res_label.setText(f"{w}x{h} px")
            
            self.load_source_preview()
            
            # Set default icon name (user can edit)
            self.icon_name_input.setText(file_name)
            
            # UI State Logic
            self.generate_btn.setEnabled(True)
            self.check_btn.setEnabled(True)
            if hasattr(self, 'reveal_btn'):
                self.reveal_btn.setEnabled(True)
                self.reload_btn.setEnabled(True)
                
            self.reset_ui_controls_after_commit()
            
            # Phase 11: Auto-Audit (Instant Feedback)
            # Phase 11: Auto-Audit (Instant Feedback)
            issues = IconAuditor.audit_image(self.processor.source_image)
            # Filter to relevant issues (Warning/Error)
            relevant_issues = [i for i in issues if i.severity in [IssueSeverity.WARNING, IssueSeverity.ERROR]]
            
            if hasattr(self, 'approval_status_label'):
                if not relevant_issues:
                    self.approval_status_label.setText("✅ Source is Clean")
                    self.approval_status_label.setStyleSheet("color: green; font-weight: bold;")
                else:
                    count = len(relevant_issues)
                    self.approval_status_label.setText(f"⚠️ {count} Issues Found")
                    self.approval_status_label.setStyleSheet("color: red; font-weight: bold;")
            
            # Phase 13: Update History
            if hasattr(self, 'populate_history_combo'):
                self.populate_history_combo(path)
            
            self.apply_masking()
            self.update_preview()

    def load_source_preview(self):
        """Cache the Source Inspector pixmap."""
        if not self.processor.source_image:
            return
            
        w, h = self.processor.source_image.size
        
        # Convert PIL to QPixmap
        src_img = self.processor.source_image.copy()
        if src_img.mode != 'RGBA':
            src_img = src_img.convert('RGBA')
            
        data = src_img.tobytes('raw', 'RGBA')
        qimage = QImage(data, w, h, QImage.Format.Format_RGBA8888)
        self.source_pixmap = QPixmap.fromImage(qimage)
        # We don't display it immediately anymore, 
        # unless View Mode is 'Source' (which set_view_mode handles)
            

    
    def apply_masking(self):
        """Apply selected masking mode."""
        if not self.processor.source_image:
            return
        
        # Reset to source
        self.processor.reset_to_source()
        img = self.processor.processed_image
        
        # 0. Quick Enhancements (Prep)
        # Applied BEFORE masking to improve separation
        if hasattr(self, 'chk_despeckle') and self.chk_despeckle.isChecked():
             img = FilterEngine.despeckle(img)
             
        if hasattr(self, 'chk_equalize') and self.chk_equalize.isChecked():
             img = FilterEngine.equalize(img)
             
        if hasattr(self, 'chk_enhance') and self.chk_enhance.isChecked():
             # Auto-Contrast with 2% cutoff
             img = FilterEngine.auto_contrast(img, cutoff=2)
             
        if hasattr(self, 'chk_normalize') and self.chk_normalize.isChecked():
             # Auto-Contrast with 0% cutoff (Full Range)
             img = FilterEngine.auto_contrast(img, cutoff=0)
        
        if hasattr(self, 'chk_sharpen') and self.chk_sharpen.isChecked():
             img = FilterEngine.sharpen(img)
             
        if hasattr(self, 'chk_antialias') and self.chk_antialias.isChecked():
             img = FilterEngine.smooth(img)
             
        if hasattr(self, 'chk_grayscale') and self.chk_grayscale.isChecked():
             img = FilterEngine.grayscale(img)
             
        # Apply changes to processor flow before masking
        # (This is tricky because processor.processed_image is what we're editing)
        # We just keep 'img' variable flowing.
        
        # Apply basic masking
        if self.mask_autocrop.isChecked():
            # Phase 19: Edge Protection
            # If enabled, add padding to ensure full-bleed content isn't eaten.
            if hasattr(self, 'edge_pad_check') and self.edge_pad_check.isChecked():
                # Add 5px transparent padding
                # Note: This is mainly useful if we were doing border masking. 
                # For basic Auto-Crop it might not matter unless crop is aggressive.
                from PIL import ImageOps
                img = ImageOps.expand(img, border=5, fill=(0,0,0,0))
                
            img = AutoCropper.crop_to_content(img, padding=5)
            
        elif self.mask_color.isChecked():
            # Multi-Key Logic (Phase 9)
            input_colors = [self.current_mask_color]
            
            if hasattr(self, 'enable_key_2') and self.enable_key_2.isChecked():
                input_colors.append(self.current_mask_color_2)
            
            tolerance = self.tolerance_spin.value()
            img = MaskingEngine.multi_color_mask(img, input_colors, tolerance)
            
            # Auto-crop after if enabled
            if self.autocrop_after.isChecked():
                img = AutoCropper.crop_to_content(img, padding=5)
        
        elif self.mask_border.isChecked():
            # Phase 19: Edge Protection (Padding) 
            # CRITICAL: Adds buffer so flood fill works around the image
            if hasattr(self, 'edge_pad_check') and self.edge_pad_check.isChecked():
                from PIL import ImageOps
                # Pad with TRANSPARENCY to stop the flood fill from reaching the icon
                pad_color = (0,0,0,0)
                img = ImageOps.expand(img, border=5, fill=pad_color)
            
            # Phase 19: Seed Strategy
            start_from_corners = True
            if hasattr(self, 'seed_combo'):
                idx = self.seed_combo.currentIndex()
                if idx == 1: # Edges (All)
                    start_from_corners = False
                elif idx == 2: # Manual
                    # Skip border masking? Or assume center is subject?
                    # For now treating Manual as "Don't Mask" or just corners
                    pass 

            # Border-only masking (Magic Wand style)
            tolerance = self.tolerance_spin.value()
            img = BorderMasking.flood_fill_from_edges(img, tolerance=tolerance, start_from_corners=start_from_corners)
            
            # Auto-crop after if enabled
            if self.autocrop_after.isChecked():
                img = AutoCropper.crop_to_content(img, padding=5)
        
        # Phase 16: Smart Composition (Fit & Padding)
        # We now have the "Core Content" (Masked & Cropped).
        # We must compose it onto the standard square canvas.
        img = self.apply_composition_step(img)
        
        # Phase 20: Shape Modification (Shape Weight)
        # Replaces old "Mask Choke" logic
        if hasattr(self, 'stroke_slider'):
            shape_weight = self.stroke_slider.value()
            if shape_weight < 0:
                 # Erode (Thin)
                 img = MaskingEngine.choke_mask(img, abs(shape_weight))
            elif shape_weight > 0:
                 # Dilate (Thick)
                 img = EdgeProcessor.expand_mask(img, pixels=shape_weight)
        
        # Phase 20: Border Engine (Colored Stroke)
        # Phase 20: Border Engine (Colored Stroke)
        # Check specific checkbox, not group (group just holds it)
        if hasattr(self, 'border_enabled_check') and self.border_enabled_check.isChecked():
            color = self.current_stroke_color
            if hasattr(self, 'stroke_width_slider'):
                width = self.stroke_width_slider.value()
                align_idx = self.stroke_align_combo.currentIndex()
                align_map = {0: 'outside', 1: 'center', 2: 'inside'}
                alignment = align_map.get(align_idx, 'outside')
                
                img = StrokeGenerator.apply_stroke(img, color, width, alignment)
            
        # Phase 20: Liquid Polish (Super-Sampled Smoothing)
        if hasattr(self, 'liquid_polish_check') and self.liquid_polish_check.isChecked():
            # Intensity could be a slider, but for now fixed high quality
            img = SuperPolisher.liquid_smooth(img, intensity=0.5)
            
        # Standard Cleanup (Clean Edges)
        # We use 'smooth_slider' (Geometry) to control the BLUR radius (Smoothness)
        # We use 'edge_threshold_spin' (Masking) to control the THRESHOLD (Tightness)
        
        blur_val = 0.3 # Default
        if hasattr(self, 'smooth_slider'):
            # Map 0-100 to 0.0-2.0
            blur_val = self.smooth_slider.value() / 50.0
            
        threshold = self.edge_threshold_spin.value() if hasattr(self, 'edge_threshold_spin') else 10
        img = EdgeProcessor.clean_edges(img, threshold=threshold, blur_radius=blur_val)
        
        # Geometry: Corner Sharpness (0-100)
        # 50 = Neutral. <50 = Round. >50 = Sharp.
        if hasattr(self, 'sharp_slider'):
             val = self.sharp_slider.value()
             if val < 50:
                 # Rounding: Blur -> Threshold (implied by clean_edges if we blur MORE?)
                 # Actually, clean_edges does blur+threshold.
                 # So maybe smooth_slider handles rounding?
                 # Let's make Sharp Slider < 50 add EXTRA blur before thresholding?
                 # Or just leave it as distinct feature?
                 # Let's use GaussianBlur for specific Rounding effect.
                 radius = (50 - val) / 10.0 # 0 to 5px
                 if radius > 0:
                      img = img.filter(ImageFilter.GaussianBlur(radius))
                      # Re-threshold to keep hard edge but rounded shape
                      # This effectively rounds corners
                      img = EdgeProcessor.clean_edges(img, threshold=128, blur_radius=0) 
                      
             elif val > 50:
                 # Sharpening: Unsharp Mask
                 amount = (val - 50) * 2 # 0 to 100
                 if amount > 0:
                     img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=int(amount*2), threshold=3))
        
        # Stroke Panel: Resolution Snap (Extra Sharpen)
        if hasattr(self, 'sharpen_slider'):
             val = self.sharpen_slider.value()
             if val > 0:
                 img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=int(val*1.5), threshold=3)) 

        self.processor.apply_processed_image(img)
        self.update_preview()
    
    def pick_color(self):
        """Open color picker dialog (Primary Key)."""
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_mask_color = (color.red(), color.green(), color.blue())
            self.color_btn.setStyleSheet(
                f"background-color: rgb({color.red()}, {color.green()}, {color.blue()});"
            )
            if self.mask_color.isChecked():
                self.apply_masking()

    def pick_color_2(self):
        """Open color picker dialog (Secondary Key)."""
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_mask_color_2 = (color.red(), color.green(), color.blue())
            self.color_btn_2.setStyleSheet(
                f"background-color: rgb({color.red()}, {color.green()}, {color.blue()});"
            )
            if self.mask_color.isChecked():
                self.apply_masking()
                
    def pick_stroke_color(self):
        """Pick color for Border Engine."""
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_stroke_color = (color.red(), color.green(), color.blue(), 255)
            # Adjust text color for contrast
            text_color = 'black' if color.lightness() > 128 else 'white'
            self.stroke_color_btn.setStyleSheet(
                f"background-color: {color.name()}; color: {text_color};"
            )
            self.apply_masking() # Live Update - No Commit
    
    def update_preview(self):
        """Update the preview image."""
        if not self.processor.processed_image:
            return
            
        preview = self.processor.processed_image.copy()
        
        # 1. Apply Backgrounds (for visualization only)
        if self.bg_white.isChecked():
            preview = MaskingEngine.add_background(preview, (255, 255, 255, 255))
        elif self.bg_black.isChecked():
            preview = MaskingEngine.add_background(preview, (0, 0, 0, 255))
        # Transparent (Checkerboard) is handled by the stylesheet on the label
            
        # 2. Apply Overlays (Visual Aids)
        
        # Mask Overlay (Show removed areas in Red)
        if self.show_mask_overlay.isChecked():
            # Create a semi-transparent red layer
            red_overlay = Image.new('RGBA', preview.size, (255, 0, 0, 100))
            
            # Create mask from current alpha (where alpha is 0/transp, we show red)
            # We invert the alpha channel of the processed image
            if preview.mode != 'RGBA':
                preview = preview.convert('RGBA')
            
            alpha = preview.split()[3]
            # Invert alpha: 0 (transp) -> 255 (opaque), 255 -> 0
            from PIL import ImageChops
            mask_inv = ImageChops.invert(alpha)
            
            # Composite red overlay using inverted alpha as mask
            # We want red ONLY where it is transparent
            preview.paste(red_overlay, (0,0), mask_inv)
            
        # Safe Zone Grid (10% Margin)
        if self.show_safe_zone.isChecked():
            from PIL import ImageDraw
            draw = ImageDraw.Draw(preview)
            w, h = preview.size
            margin = int(min(w, h) * 0.10) # 10%
            
            # Draw Rectangle
            # Outline color: Magenta (high visibility)
            outline_color = (255, 0, 255, 255)
            
            # Draw rectangle (1px width)
            draw.rectangle(
                (margin, margin, w - margin, h - margin),
                outline=outline_color,
                width=2
            )
            
            # Draw Center Crosshair (subtle)
            cx, cy = w // 2, h // 2
            draw.line((cx - 10, cy, cx + 10, cy), fill=outline_color, width=1)
            draw.line((cx, cy - 10, cx, cy + 10), fill=outline_color, width=1)
        
        # Convert to QPixmap
        preview_rgb = preview.convert('RGB')
        data = preview_rgb.tobytes('raw', 'RGB')
        qimage = QImage(data, preview.width, preview.height, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)
        
        # Phase 18: Viewport Zoom
        # Store the full-resolution pixmap (1024x1024)
        self.current_preview_pixmap = pixmap
        
        # Render viewport based on current zoom settings
        self.refresh_viewport()
    
    def browse_output(self):
        """Browse for output directory."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self.output_path.text()
        )
        if dir_path:
            self.output_path.setText(dir_path)
    
    
    def run_icon_audit(self):
        """Run the Icon Doctor audit."""
        if not self.processor.processed_image:
            return
            
        # Run standard audit
        issues = IconAuditor.audit_image(self.processor.processed_image)
        
        # Run Comparative Audit if Reference is loaded
        comp_stats = None
        if hasattr(self, 'reference_image') and self.reference_image:
            try:
                # 1. Analyze Both
                processed_img = self.processor.processed_image
                ref_img = self.reference_image.resize(processed_img.size, Image.Resampling.LANCZOS)
                
                stats_yours = IconAuditor.analyze_metrics(processed_img)
                stats_ref = IconAuditor.analyze_metrics(ref_img)
                
                # 2. Calculate Diffs
                comp_stats = {
                    'yours': stats_yours,
                    'ref': stats_ref,
                    'sharpness_diff': stats_yours['sharpness'] - stats_ref['sharpness'],
                    'contrast_diff': stats_yours['contrast'] - stats_ref['contrast']
                }
            except Exception as e:
                print(f"Comparison failed: {e}")
        
        # Show report
        dialog = AuditReportDialog(issues, comparison_stats=comp_stats, parent=self)
        if dialog.exec():
            # If user clicked "Auto-Fix All"
            # Apply Smart Edge Cleanup
            self.apply_smart_cleanup()
            
    def apply_smart_cleanup(self):
        """Apply Smart Edge Cleanup (Vector Reconstruction) with Auto-Commit."""
        if not self.processor.source_image:
            return
            
        # 1. Force Strong Defaults (Make the fix visible)
        # Using blockSignals to prevent intermediate updates if desired, 
        # but actually we want the update to happen so processed_image is ready.
        self.smooth_slider.setValue(5)
        self.sharp_slider.setValue(80)
        
        # 2. Logic is triggered by signals above, updating processed_image
        # But just in case signals are blocked or queued:
        # (The actual processing happens in update_preview which is connected to valueChanged)
        # We need to ensure update_preview finishes before committing?
        # Since this is single threaded UI, the signal should fire immediately.
        
        # 3. Auto-Commit (Phase 12)
        # This saves to history/, reloads the file, and resets the pipeline.
        self.promote_preview_to_source(confirm=False)
        
        QMessageBox.information(
            self, 
            "Auto-Fix Applied", 
            "✅ Fix Applied & Committed!\n\n"
            "1. Smoothing & Sharpening applied.\n"
            "2. Result saved as new Source.\n"
            "3. Pipeline reset for next step."
        )
        
    def promote_preview_to_source(self, confirm: bool = True):
        """Phase 10: Promote current preview to be the new source (Save & Reload)."""
        if not self.processor.processed_image:
            return
            
        # Check for changes (Phase 14)
        if self.processor.source_image:
            diff = ImageChops.difference(self.processor.source_image, self.processor.processed_image)
            if not diff.getbbox():
                if confirm:
                     QMessageBox.warning(self, "No Changes", "You haven't made any changes yet!")
                return 
            
        if confirm:
            reply = QMessageBox.question(
                self, 
                "Commit Changes?",
                "This will use your current preview as the new Original Source.\n\n"
                "1. A new version of the file will be saved to 'history/'.\n"
                "2. The app will reload this new file.\n"
                "3. All sliders and masks will be reset.\n\n"
                "Proceed?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            should_proceed = (reply == QMessageBox.StandardButton.Yes)
        else:
            should_proceed = True
        
        if should_proceed:
            # 1. Create History Directory
            history_dir = Path("history")
            history_dir.mkdir(exist_ok=True)
            
            # 2. Generate Unique Filename
            # {original_stem}_v{timestamp}.png
            original_stem = Path(self.current_source_path).stem
            # Remove existing version suffix if present to avoid v1_v2_v3 chains
            import re
            base_stem = re.sub(r'_v\d{14}$', '', original_stem) 
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            new_filename = f"{base_stem}_v{timestamp}.png"
            new_path = history_dir / new_filename
            
            # 3. Save Processed Image
            try:
                self.processor.processed_image.save(new_path)
            except Exception as e:
                QMessageBox.critical(self, "Error Saving", f"Could not save history file:\n{e}")
                return
            
            # 4. Reload as New Source (True Reset)
            # This triggers load_image -> resets masking, geometry, stroke -> updates UI
            self.load_image(str(new_path.absolute()))
            
            # 5. Toast
            QMessageBox.information(self, "Changes Committed", 
                                  f"Saved version: {new_filename}\n\n"
                                  "The pipeline has been reset. You are now working on the clean, committed version.")

    def reset_ui_controls_after_commit(self):
        """Reset all processing controls to neutral state."""
        # 1. Geometry (The Enforcer) - Reset to Neutral
        # We set smoothing to 0 because the image is ALREADY smoothed.
        self.smooth_slider.blockSignals(True)
        self.smooth_slider.setValue(0) # 0 = Faithful to the new source
        self.smooth_slider.blockSignals(False)
        self.smooth_label.setText("Smoothing (Wart Removal): 0")
        
        # Sharpness stays at 50 (Neutral/Standard)
        self.sharp_slider.blockSignals(True)
        self.sharp_slider.setValue(50) 
        self.sharp_slider.blockSignals(False)
        self.sharp_label.setText("Corner Sharpness: 50")
        
        # Stroke Engine - Reset to Neutral
        self.stroke_slider.blockSignals(True)
        self.stroke_slider.setValue(0)
        self.stroke_slider.blockSignals(False)
        self.stroke_label.setText("Stroke Weight (Boldness): 0")
        
        self.sharpen_slider.blockSignals(True)
        self.sharpen_slider.setValue(0)
        self.sharpen_slider.blockSignals(False)
        self.sharpen_label.setText("Resolution Snap (Sharpen): 0")
        
        # 2. Cleanup Tab - Reset
        self.mask_none.setChecked(True) # Disable masking
        
        # Reset Masking Lab
        self.mask_choke_slider.blockSignals(True)
        self.mask_choke_slider.setValue(0)
        self.mask_choke_slider.blockSignals(False)
        if hasattr(self, 'enable_key_2'):
            self.enable_key_2.setChecked(False)
            
        self.defringe_check.setChecked(False)
        self.edge_controls.setEnabled(False)
        
        # 3. Geometry Tab - Reset (Simulated)
        # We already reset sliders above

    def generate_icons(self):
        """Start icon generation."""
        if not self.processor.processed_image:
            return
            
        # Phase 21: Audit Check (Alert only at the end)
        # Phase 21: Audit Check (Alert only at the end)
        issues = IconAuditor.audit_image(self.processor.processed_image)
        # Filter to relevant issues (Warning/Error)
        relevant_issues = [i for i in issues if i.severity in [IssueSeverity.WARNING, IssueSeverity.ERROR]]
        
        if relevant_issues:
            count = len(relevant_issues)
            msg = f"Found {count} potential issues with your icon:\n\n"
            for issue in relevant_issues[:3]:
                msg += f"- {issue.message}\n"
            if count > 3:
                msg += f"...and {count-3} more.\n"
            msg += "\nDo you want to export anyway?"
            
            reply = QMessageBox.question(
                self, "Export Warning", msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Get icon name (use custom name if provided, otherwise use source filename)
        icon_name = self.icon_name_input.text().strip()
        if not icon_name:
            icon_name = Path(self.current_source_path).stem
        
        # Prepare settings
        settings = {
            'output_dir': self.output_path.text(),
            'icon_name': icon_name,
            'source_path': self.current_source_path,
            'export_windows': self.export_windows.isChecked(),
            'export_mac': self.export_mac.isChecked(),
            'export_png': self.export_png.isChecked(),
            'create_archive': self.create_archive.isChecked(),
            'create_zip': True
        }
        
        # Start generation thread
        self.generate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.worker = IconGeneratorThread(self.processor, settings)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.generation_finished)
        self.worker.start()
    
    def generation_finished(self, success: bool, message: str):
        """Handle generation completion."""
        self.generate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            QMessageBox.information(
                self,
                "Success",
                f"Icons generated successfully!\n\nOutput: {message}"
            )
        else:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate icons:\n{message}"
            )

    def reveal_source_file(self):
        """Reveal the current source file in Finder/Explorer (Escape Hatch)."""
        if not self.current_source_path:
            return
            
        path = str(Path(self.current_source_path).absolute())
        
        try:
            if sys.platform == 'darwin':
                import subprocess
                subprocess.run(['open', '-R', path])
            elif sys.platform == 'win32':
                import subprocess
                subprocess.run(['explorer', '/select,', path])
            else:
                # Linux fallback
                import subprocess
                subprocess.run(['xdg-open', str(Path(path).parent)])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not reveal file:\n{e}")

    def reload_source_file(self):
        """Reload the source file from disk (Pull Manual Edits)."""
        if not self.current_source_path:
            return
            
        # Verify file exists
        if not Path(self.current_source_path).exists():
            QMessageBox.warning(self, "Error", "Source file no longer exists!")
            return
            
        # Reload triggers full reset
        self.load_image(self.current_source_path)
        
        QMessageBox.information(self, "Reloaded", "File reloaded from disk.\nMasking and Filters have been reset to match the new pixels.")

    def create_source_inspector(self):
        """Create Compact Input Settings Panel."""
        group = QGroupBox("Input Source")
        layout = QVBoxLayout()
        
        # Row 1: File Info (Icon + Name + Resolution)
        info_layout = QHBoxLayout()
        
        self.source_icon_label = QLabel()
        self.source_icon_label.setFixedSize(32, 32)
        self.source_icon_label.setStyleSheet("background-color: #333; border-radius: 4px;")
        info_layout.addWidget(self.source_icon_label)
        
        meta_layout = QVBoxLayout()
        self.filename_label = QLabel("No File Loaded")
        self.filename_label.setStyleSheet("font-weight: bold; color: #ddd;")
        meta_layout.addWidget(self.filename_label)
        
        self.res_label = QLabel("Drag & Drop Image")
        self.res_label.setStyleSheet("color: #888; font-size: 11px;")
        meta_layout.addWidget(self.res_label)
        
        info_layout.addLayout(meta_layout)
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        layout.addSpacing(5)
        
        # Row 2: Actions
        action_layout = QHBoxLayout()
        
        btn_open = QPushButton("Open...")
        btn_open.setToolTip("Open Source File")
        btn_open.clicked.connect(self.choose_file)
        action_layout.addWidget(btn_open)
        
        self.reload_btn = QPushButton("Reload")
        self.reload_btn.setToolTip("Reload from Disk")
        self.reload_btn.setEnabled(False)
        self.reload_btn.clicked.connect(self.reload_source_file)
        action_layout.addWidget(self.reload_btn)
        
        self.check_btn = QPushButton("Audit")
        self.check_btn.setToolTip("Check for Issues")
        self.check_btn.setEnabled(False)
        self.check_btn.clicked.connect(self.run_icon_audit)
        action_layout.addWidget(self.check_btn)
        
        layout.addLayout(action_layout)
        
        # Row 3: History (Compact)
        history_layout = QHBoxLayout()
        history_layout.addWidget(QLabel("Ver:"))
        self.history_combo = QComboBox()
        self.history_combo.addItem("Latest")
        self.history_combo.setEnabled(False)
        self.history_combo.currentIndexChanged.connect(self.load_history_version)
        history_layout.addWidget(self.history_combo, 1)
        
        # Commit (Small Button)
        self.commit_btn = QPushButton("💾")
        self.commit_btn.setFixedSize(24, 24)
        self.commit_btn.setToolTip("Commit Current Preview as New Source")
        self.commit_btn.clicked.connect(self.promote_preview_to_source)
        history_layout.addWidget(self.commit_btn)
        
        layout.addLayout(history_layout)
        
        group.setLayout(layout)
        return group


    def populate_history_combo(self, current_path: str):
        """Populate history dropdown with ALL versions (Unified Timeline)."""
        if not hasattr(self, 'history_combo'):
            return
            
        self.history_combo.blockSignals(True)
        self.history_combo.clear()
        
        # 1. Identify Base Stem (Root of the Timeline)
        current_stem = Path(current_path).stem
        import re
        base_stem = re.sub(r'_v\d{14}$', '', current_stem)
        
        history_dir = Path("history")
        versions = []
        
        # 2. Add History Versions
        if history_dir.exists():
            for f in history_dir.glob(f"{base_stem}_v*.png"):
                try:
                    ts_str = f.stem.split('_v')[-1]
                    from datetime import datetime
                    dt = datetime.strptime(ts_str, "%Y%m%d%H%M%S")
                    display_time = dt.strftime("%H:%M:%S")
                    versions.append({
                        'path': str(f.absolute()),
                        'name': f"v.{ts_str[-6:]} ({display_time})", 
                        'ts': ts_str
                    })
                except:
                    continue
                    
        # Sort by timestamp descending (newest first)
        versions.sort(key=lambda x: x['ts'], reverse=True)
        
        # 3. Add Items to Combo (Unified List)
        # Scan list to find which one is "Current"
        current_idx = 0 
        found_active = False # Initialize explicitly 
        
        # Add matches
        # Add matches
        for i, v in enumerate(versions):
            item_name = v['name']
            item_path = v['path']
            self.history_combo.addItem(item_name, item_path)
            
            # Check if this is the current one
            if item_path == str(Path(current_path).absolute()):
                 self.history_combo.setCurrentIndex(i)
                 found_active = True
                 
        if not found_active:
             # Current file is likely the Original Source (root folder)
             # Add it at the END or START? Usually original is oldest.
             # But our list is Newest First.
             # If "Original" is active, maybe it's not in history folder.
             self.history_combo.addItem(f"Original Source (Active)", str(Path(current_path).absolute()))
             self.history_combo.setCurrentIndex(self.history_combo.count() - 1)
                 
        self.history_combo.setEnabled(True)
        self.history_combo.blockSignals(False)

    def load_history_version(self):
        """Load selected version from history."""
        # Get data from selected item
        path = self.history_combo.currentData()
        if path and Path(path).exists():
            # Load it (this triggers standard load pipeline)
            self.load_image(path)

    def apply_composition_step(self, image: Image.Image) -> Image.Image:
        """Apply Composition (Scale/Fit) to the image."""
        if not image:
            return None
            
        # 1. Get Settings
        scale_pct = self.scale_slider.value() # 50-150
        scale = scale_pct / 100.0
        
        fit_mode = 'contain' if self.fit_contain.isChecked() else 'cover'
        
        # 2. Compose
        # Default target size 1024 for internal processing
        # (Export will resize to specific targets later)
        return CompositionEngine.compose(image, target_size=1024, scale=scale, fit_mode=fit_mode)

    # =========================================================================
    # Phase 18: Viewport Zoom Logic
    # =========================================================================

    def toggle_fit_zoom(self):
        """Toggle 'Fit' mode."""
        if self.btn_fit.isChecked():
            self.zoom_label.setText("Fit")
            self.refresh_viewport()
        else:
            # Revert to current slider value
            self.update_zoom_from_slider(self.zoom_slider.value())

    def set_zoom_level(self, scale: float):
        """Set specific zoom level (e.g. 1.0 = 100%)."""
        self.btn_fit.setChecked(False)
        self.zoom_slider.setValue(int(scale * 100))
        # Slider change triggers update_zoom_from_slider -> refresh_viewport

    def update_zoom_from_slider(self, value):
        """Handle zoom slider changes."""
        if self.btn_fit.isChecked():
             self.btn_fit.setChecked(False)
             
        scale = value / 100.0
        self.zoom_label.setText(f"{value}%")
        self.refresh_viewport()

    def load_reference_image(self):
        """Load a reference image for comparison."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Reference Image", "", 
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if path:
            try:
                img = Image.open(path).convert('RGBA')
                self.reference_image = img
                # Pre-calculate pixmap
                w, h = img.size
                data = img.tobytes('raw', 'RGBA')
                qimage = QImage(data, w, h, QImage.Format.Format_RGBA8888)
                self.reference_pixmap = QPixmap.fromImage(qimage)
                
                # Enable Split View
                self.btn_view_split.setEnabled(True)
                self.btn_view_split.setChecked(True)
                self.set_view_mode("split")
                
                QMessageBox.information(self, "Reference Loaded", "Reference loaded!\nUse the slider to wipe between Reference (Left) and Result (Right).")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load reference: {str(e)}")

    def set_view_mode(self, mode: str):
        """Switch View Mode (Live, Source, Split)."""
        # Toggle buttons programmatically if needed
        if mode == "live":
            if not self.btn_view_live.isChecked(): self.btn_view_live.setChecked(True)
            self.split_slider.setVisible(False)
        elif mode == "source":
            if not self.btn_view_source.isChecked(): self.btn_view_source.setChecked(True)
            self.split_slider.setVisible(False)
        elif mode == "split":
            if not self.btn_view_split.isChecked(): self.btn_view_split.setChecked(True)
            self.split_slider.setVisible(True)
        
        self.refresh_viewport()

    def refresh_viewport(self):
        """Render the current preview pixmap at the correct zoom level."""
        # 0. Determine Content Source
        base_pixmap = None
        is_split = False
        
        if self.btn_view_source.isChecked():
            if hasattr(self, 'source_pixmap'):
                base_pixmap = self.source_pixmap
        elif self.btn_view_split.isChecked():
            # Split Mode
            is_split = True
            # Base is Live Result
            if hasattr(self, 'current_preview_pixmap'):
                base_pixmap = self.current_preview_pixmap
        else:
            # Live Mode (Default)
            if hasattr(self, 'current_preview_pixmap'):
                base_pixmap = self.current_preview_pixmap
        
        if not base_pixmap:
             self.preview_label.setText("No Image")
             return
        
        # 2. Determine Target Size (Fit vs Zoom) -> logic remains same per-pixmap
        if self.btn_fit.isChecked():
            viewport_size = self.preview_scroll.viewport().size()
            target_w = viewport_size.width() - 4
            target_h = viewport_size.height() - 4
            if target_w < 10: target_w = 300
            if target_h < 10: target_h = 300
            
            scaled_pixmap = base_pixmap.scaled(target_w, target_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        else:
            # Zoom Factor
            scale = self.zoom_slider.value() / 100.0
            w = int(base_pixmap.width() * scale)
            h = int(base_pixmap.height() * scale)
            scaled_pixmap = base_pixmap.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        # 3. Handle Split Rendering (If Split Mode)
        if is_split and self.reference_pixmap:
            # We need to compost Reference + Result based on slider
            # Reference is UNDER? Or Left?
            # "Wipe" means: Left part is Ref, Right part is Result.
            
            # Scale Reference to match Result's display size?
            # Or just scale it identically.
            # Let's scale reference to match `scaled_pixmap` dimensions for direct comparison
            ref_scaled = self.reference_pixmap.scaled(scaled_pixmap.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            # Create a composite QPixmap
            composite = QPixmap(scaled_pixmap.size())
            composite.fill(Qt.GlobalColor.transparent)
            
            from PyQt6.QtGui import QPainter
            painter = QPainter(composite)
            
            # Draw Reference (Full)
            # painter.drawPixmap(0, 0, ref_scaled)
            
            # Actually, Wipe:
            # Percentage
            split_x = int(scaled_pixmap.width() * (self.split_slider.value() / 100.0))
            
            # Left side = Reference
            # Draw Ref cropped to split_x
            painter.drawPixmap(0, 0, ref_scaled, 0, 0, split_x, ref_scaled.height())
            
            # Right side = Result
            # Draw Result cropped from split_x
            painter.drawPixmap(split_x, 0, scaled_pixmap, split_x, 0, scaled_pixmap.width() - split_x, scaled_pixmap.height())
            
            # Draw Divider Line
            painter.setPen(Qt.GlobalColor.white)
            painter.drawLine(split_x, 0, split_x, scaled_pixmap.height())
            
            painter.end()
            scaled_pixmap = composite

        self.preview_label.setPixmap(scaled_pixmap)
        self.preview_label.setText("")


