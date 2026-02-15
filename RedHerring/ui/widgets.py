"""
Custom Widgets for RedHerring.
"""
from PyQt6.QtWidgets import QLabel, QWidget, QMenu, QSizePolicy, QToolButton, QVBoxLayout, QFrame, QHBoxLayout, QToolTip
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF, QSize, QSizeF, QRect, QPropertyAnimation, QAbstractAnimation, QParallelAnimationGroup, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QCursor, QPixmap, QImage, QIcon, QAction

class InteractiveImageLabel(QLabel):
    # Signals
    selectionChanged = pyqtSignal(QRect) # Emits rect in IMAGE coordinates
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # State
        self.source_pixmap = None     # The full-res image
        self.scaled_pixmap = None     # The displayed image (fitted to widget)
        self.scale_factor = 1.0       # Ratio: displayed / source
        self.offset = QPointF(0, 0)   # Top-left of painted image in widget coords
        
        self.selection_rect = QRectF() # In IMAGE coordinates (0,0 to w,h)
        
        # Interaction
        self.is_dragging = False
        self.drag_mode = None         # 'move', 'nw', 'ne', 'sw', 'se', 'n', 's', 'e', 'w'
        self.drag_start_pos = QPointF()
        self.drag_start_rect = QRectF()
        
        # Settings
        self.aspect_ratio_mode = "Free" # "Free", "Original", "Square"
        self.handle_size = 8
        self.min_selection_size = 10
        
        # Marching Ants
        self.dash_offset = 0
        from PyQt6.QtCore import QTimer
        self.ant_timer = QTimer(self)
        self.ant_timer.timeout.connect(self.animate_ants)
        self.ant_timer.start(100) # 100ms interval
        
    def animate_ants(self):
        self.dash_offset -= 1
        if self.dash_offset < 0: self.dash_offset = 15 # Wrap around (dash len approx)
        self.update()
            
    def set_image(self, pixmap: QPixmap):
        """Set the source image and reset selection to full."""
        self.source_pixmap = pixmap
        if pixmap:
            w, h = pixmap.width(), pixmap.height()
            self.selection_rect = QRectF(0, 0, w, h)
            self.update_geometry_cache()
        else:
            self.selection_rect = QRectF()
            self.scaled_pixmap = None
            
        self.update()
        if self.selection_rect.isValid():
            self.selectionChanged.emit(self.selection_rect.toRect())
            
    def set_selection(self, rect: QRect):
        """Programmatically set selection (e.g. from spinboxes)."""
        if not self.source_pixmap: return
        
        # Clamp to image bounds
        img_rect = QRectF(0, 0, self.source_pixmap.width(), self.source_pixmap.height())
        new_rect = QRectF(rect).intersected(img_rect)
        
        if new_rect != self.selection_rect:
            self.selection_rect = new_rect
            self.update()
            
    def set_aspect_ratio_mode(self, mode: str):
        """Set aspect ratio constraint: 'Free', 'Original', 'Square'."""
        self.aspect_ratio_mode = mode
        # Re-apply constraint to current selection if needed
        if mode != "Free" and self.source_pixmap:
            self.constrain_selection(self.selection_rect)
            self.update()
            self.selectionChanged.emit(self.selection_rect.toRect())

    def update_geometry_cache(self):
        """Calculate scale factor and offset based on widget size."""
        if not self.source_pixmap: return
        
        w_widget, h_widget = self.width(), self.height()
        w_img, h_img = self.source_pixmap.width(), self.source_pixmap.height()
        
        if w_img == 0 or h_img == 0: return

        # Fit image in widget (Contain)
        scale_w = w_widget / w_img
        scale_h = h_widget / h_img
        self.scale_factor = min(scale_w, scale_h)
        
        disp_w = w_img * self.scale_factor
        disp_h = h_img * self.scale_factor
        
        self.scaled_pixmap = self.source_pixmap.scaled(
            int(disp_w), int(disp_h), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Center the image
        off_x = (w_widget - disp_w) / 2
        off_y = (h_widget - disp_h) / 2
        self.offset = QPointF(off_x, off_y)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_geometry_cache()
        
    def paintEvent(self, event):
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.scaled_pixmap:
            # Draw Checkerboard Background
            self.draw_checkerboard(painter)
            
            # Draw Image
            painter.drawPixmap(self.offset.toPoint(), self.scaled_pixmap)
            
            # Darken overlay outside selection
            self.draw_overlay(painter)
            
            # Draw Selection Border
            self.draw_selection(painter)
        else:
            # If no image, maybe draw placeholder text?
            # Handled by parent label text usually
            pass

    def draw_checkerboard(self, painter):
        """Draw a checkerboard pattern behind the image area."""
        # We only need to draw where the image is
        x = int(self.offset.x())
        y = int(self.offset.y())
        w = self.scaled_pixmap.width()
        h = self.scaled_pixmap.height()
        
        # Grid Size
        size = 10
        light = QColor(255, 255, 255)
        dark = QColor(204, 204, 204)
        
        # Optimize: Draw a tiled pixmap or just loops?
        # Loops are fine for typical icon sizes.
        
        # Clip to image area
        painter.save()
        painter.setClipRect(x, y, w, h)
        
        # Fill background first
        painter.fillRect(x, y, w, h, light)
        
        cols = w // size + 1
        rows = h // size + 1
        
        painter.setBrush(dark)
        painter.setPen(Qt.PenStyle.NoPen)
        
        for r in range(rows):
            for c in range(cols):
                if (r + c) % 2 == 1:
                    painter.drawRect(x + c * size, y + r * size, size, size)
                    
        painter.restore()

    def draw_overlay(self, painter):
        """Draw semi-transparent overlay excluding selection."""
        if not self.selection_rect.isValid(): return
        
        # Widget Rect
        w, h = self.width(), self.height()
        
        # Selection in Widget Coords
        sel = self.map_from_image(self.selection_rect)
        
        painter.setBrush(QColor(0, 0, 0, 150))
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Top
        painter.drawRect(0, 0, w, int(sel.top()))
        # Bottom
        painter.drawRect(0, int(sel.bottom()), w, h - int(sel.bottom()))
        # Left (between top/bottom)
        painter.drawRect(0, int(sel.top()), int(sel.left()), int(sel.height()))
        # Right
        painter.drawRect(int(sel.right()), int(sel.top()), w - int(sel.right()), int(sel.height()))

    def draw_selection(self, painter):
        """Draw border handles and grid."""
        sel = self.map_from_image(self.selection_rect)
        
        # Border
        # Marching Ants Effect: Black and White dashes moving?
        # Standard approach: White dash on top of Black solid? Or just White dash with offset?
        # Let's try 2-tone for visibility on all backgrounds.
        
        # 1. Black solid base (slightly wider?) or contrast
        # actually, standard marching ants usually just single dashed line.
        # But to be visible on white/black, alternating colors is good.
        # Let's just animate the dash for now as requested.
        
        pen = QPen(Qt.GlobalColor.white, 1, Qt.PenStyle.CustomDashLine)
        pen.setDashPattern([4, 4]) # 4px dash, 4px gap
        pen.setDashOffset(self.dash_offset)
        
        # Draw outlines to ensure visibility?
        # Or just Draw once with white, maybe shadow?
        # Simple animated dash:
        
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(sel)
        
        # Optional: Secondary contrast line (black) with different offset?
        # pen2 = QPen(Qt.GlobalColor.black, 1, Qt.PenStyle.CustomDashLine)
        # pen2.setDashPattern([4, 4])
        # pen2.setDashOffset(self.dash_offset + 4) 
        # painter.setPen(pen2)
        # painter.drawRect(sel)
        
        # Handles (Corners)
        painter.setBrush(Qt.GlobalColor.white)
        painter.setPen(Qt.GlobalColor.black)
        
        hs = self.handle_size
        handles = [
            sel.topLeft(), sel.topRight(), sel.bottomLeft(), sel.bottomRight(),
            QPointF(sel.center().x(), sel.top()),    # N
            QPointF(sel.center().x(), sel.bottom()), # S
            QPointF(sel.left(), sel.center().y()),   # W
            QPointF(sel.right(), sel.center().y())   # E
        ]
        
        for pt in handles:
            painter.drawRect(QRectF(pt.x() - hs/2, pt.y() - hs/2, hs, hs))

    # --- Coordinate Mapping ---
    def map_to_image(self, pos: QPointF) -> QPointF:
        """Widget -> Image Coords"""
        x = (pos.x() - self.offset.x()) / self.scale_factor
        y = (pos.y() - self.offset.y()) / self.scale_factor
        return QPointF(x, y)

    def map_from_image(self, rect: QRectF) -> QRectF:
        """Image -> Widget Coords"""
        x = rect.x() * self.scale_factor + self.offset.x()
        y = rect.y() * self.scale_factor + self.offset.y()
        w = rect.width() * self.scale_factor
        h = rect.height() * self.scale_factor
        return QRectF(x, y, w, h)
        
    # --- Mouse Interaction ---
    def mousePressEvent(self, event):
        if not self.source_pixmap: return
        
        pos = event.position()
        sel = self.map_from_image(self.selection_rect)
        hs = self.handle_size
        
        # Check handles
        # NW, NE, SW, SE
        if (pos - sel.topLeft()).manhattanLength() < hs*2: self.drag_mode = 'nw'
        elif (pos - sel.topRight()).manhattanLength() < hs*2: self.drag_mode = 'ne'
        elif (pos - sel.bottomLeft()).manhattanLength() < hs*2: self.drag_mode = 'sw'
        elif (pos - sel.bottomRight()).manhattanLength() < hs*2: self.drag_mode = 'se'
        # Inside -> Move
        elif sel.contains(pos): self.drag_mode = 'move'
        else:
            # Outside -> Start new selection? Or ignore?
            # Let's ignore for now to keep it simple, or 'move' could re-center
            self.drag_mode = None
            return

        self.is_dragging = True
        self.drag_start_pos = pos
        self.drag_start_rect = self.selection_rect # In Image Coords

    def mouseMoveEvent(self, event):
        if not self.source_pixmap: return
        
        pos = event.position()
        
        # Cursor Update
        sel = self.map_from_image(self.selection_rect)
        hs = self.handle_size
        
        cursor = Qt.CursorShape.ArrowCursor
        if (pos - sel.topLeft()).manhattanLength() < hs*2: cursor = Qt.CursorShape.SizeFDiagCursor
        elif (pos - sel.topRight()).manhattanLength() < hs*2: cursor = Qt.CursorShape.SizeBDiagCursor
        elif (pos - sel.bottomLeft()).manhattanLength() < hs*2: cursor = Qt.CursorShape.SizeBDiagCursor
        elif (pos - sel.bottomRight()).manhattanLength() < hs*2: cursor = Qt.CursorShape.SizeFDiagCursor
        elif sel.contains(pos): cursor = Qt.CursorShape.SizeAllCursor
        
        self.setCursor(cursor)
        
        if not self.is_dragging or not self.drag_mode: return
        
        # Calculate delta in IMAGE Coords
        start_img = self.map_to_image(self.drag_start_pos)
        curr_img = self.map_to_image(pos)
        dx = curr_img.x() - start_img.x()
        dy = curr_img.y() - start_img.y()
        
        new_rect = QRectF(self.drag_start_rect)
        
        # Apply Delta based on mode
        if self.drag_mode == 'move':
            new_rect.translate(dx, dy)
        elif self.drag_mode == 'nw':
            new_rect.setTopLeft(new_rect.topLeft() + QPointF(dx, dy))
        elif self.drag_mode == 'ne':
            new_rect.setTopRight(new_rect.topRight() + QPointF(dx, dy))
        elif self.drag_mode == 'sw':
            new_rect.setBottomLeft(new_rect.bottomLeft() + QPointF(dx, dy))
        elif self.drag_mode == 'se':
            new_rect.setBottomRight(new_rect.bottomRight() + QPointF(dx, dy))
            
        # Constrain Aspect Ratio if needed
        new_rect = self.constrain_selection(new_rect, self.drag_mode)
            
        # Clamp to Image Bounds
        img_w, img_h = self.source_pixmap.width(), self.source_pixmap.height()
        new_rect = new_rect.intersected(QRectF(0, 0, img_w, img_h))
        
        # Enforce Min Size
        if new_rect.width() < self.min_selection_size: new_rect.setWidth(self.min_selection_size)
        if new_rect.height() < self.min_selection_size: new_rect.setHeight(self.min_selection_size)
        
        self.selection_rect = new_rect
        self.update()
        self.selectionChanged.emit(self.selection_rect.toRect())

    def mouseReleaseEvent(self, event):
        self.is_dragging = False
        self.drag_mode = None

    def constrain_selection(self, rect: QRectF, mode=None) -> QRectF:
        """Adjust rect to match aspect ratio constraint."""
        if self.aspect_ratio_mode == "Free": return rect
        
        target_ratio = 1.0
        if self.aspect_ratio_mode == "Square":
            target_ratio = 1.0
        elif self.aspect_ratio_mode == "Original":
             if self.source_pixmap:
                 target_ratio = self.source_pixmap.width() / self.source_pixmap.height()
             else:
                 return rect
        
        # Adjust width or height to match ratio
        # Simple approach: fix width, adjust height (unless primarily dragging height)
        # For corners, we usually take the larger dimension change
        
        w, h = rect.width(), rect.height()
        
        if w/h > target_ratio:
            # Too wide, reduce width (or increase height?)
            # Standard interaction: set height based on width?
            h = w / target_ratio
        else:
            w = h * target_ratio
            
        rect.setSize(QSizeF(w, h))
        return rect

class CollapsibleBox(QWidget):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        
        self.toggle_button = QToolButton(text=title, checkable=True, checked=False)
        self.toggle_button.setStyleSheet("QToolButton { border: none; font-weight: bold; }")
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.ArrowType.RightArrow)
        self.toggle_button.clicked.connect(self.on_pressed)

        self.toggle_animation = QParallelAnimationGroup(self)

        self.content_area = QWidget()
        self.content_area.setMaximumHeight(0)
        self.content_area.setMinimumHeight(0)
        
        lay = QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)
        
        self.animation = QPropertyAnimation(self.content_area, b"maximumHeight")
        self.animation.setDuration(300)
        self.animation.setStartValue(0)
        self.animation.setEndValue(0)
        
        self.toggle_animation.addAnimation(self.animation)
        
        # Determine content height
        # We need a layout in content_area to measure it
        self.content_layout = QVBoxLayout(self.content_area)
        
    def setContentLayout(self, layout):
        # Instead of replacing, add to existing layout
        self.content_layout.addLayout(layout)

    def on_pressed(self):
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)
        self.toggle_animation.setDirection(QAbstractAnimation.Direction.Forward if checked else QAbstractAnimation.Direction.Backward)
        
        # Recalculate height
        content_height = self.content_area.layout().sizeHint().height()
        self.animation.setEndValue(content_height)
        
        self.toggle_animation.start()
        
    def expand(self):
        self.toggle_button.setChecked(True)
        self.on_pressed()
        
    def collapse(self):
        self.toggle_button.setChecked(False)
        self.on_pressed()

class InfoLabel(QWidget):
    def __init__(self, text, tooltip="", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        label = QLabel(text)
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)
        
        if tooltip:
            info_btn = QToolButton()
            info_btn.setText("ⓘ") # Unicode info icon
            info_btn.setToolTip(tooltip)
            info_btn.setStyleSheet("QToolButton { border: none; color: #666; font-weight: bold; } QToolButton:hover { color: #007bff; }")
            info_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(info_btn)
            
        layout.addStretch()
