from PyQt6.QtWidgets import QLabel, QWidget
from PyQt6.QtGui import QPainter, QColor, QPixmap, QPaintEvent
from PyQt6.QtCore import Qt, QRect

class TransparencyLabel(QLabel):
    """
    A QLabel that draws a checkerboard background behind its pixmap 
    to properly visualize transparency.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pixmap = None
        self.check_size = 10
        self.check_color_1 = QColor(240, 240, 240) # Light gray
        self.check_color_2 = QColor(200, 200, 200) # Darker gray
        
    def setPixmap(self, pixmap: QPixmap):
        """Override setPixmap to store it and trigger repaint."""
        self._pixmap = pixmap
        super().setPixmap(pixmap)
        
    def paintEvent(self, event: QPaintEvent):
        """Draw checkerboard then the pixmap."""
        painter = QPainter(self)
        
        # 1. Draw Checkerboard Background
        w = self.width()
        h = self.height()
        
        # We draw the checkerboard over the entire widget
        # Optimization: We could pre-render this to a pixmap if performance is an issue,
        # but for a UI label it's likely fine.
        
        rows = h // self.check_size + 1
        cols = w // self.check_size + 1
        
        for r in range(rows):
            for c in range(cols):
                if (r + c) % 2 == 0:
                    painter.fillRect(
                        c * self.check_size, 
                        r * self.check_size, 
                        self.check_size, 
                        self.check_size, 
                        self.check_color_1
                    )
                else:
                    painter.fillRect(
                        c * self.check_size, 
                        r * self.check_size, 
                        self.check_size, 
                        self.check_size, 
                        self.check_color_2
                    )
                    
        if self._pixmap and not self._pixmap.isNull():
            # Calculate centered position
            pw = self._pixmap.width()
            ph = self._pixmap.height()
            
            x = (w - pw) // 2
            y = (h - ph) // 2
            
            painter.drawPixmap(x, y, self._pixmap)
        else:
            # Draw Text if no pixmap (e.g. "Drop Here")
            text = self.text()
            if text:
                painter.setPen(QColor(100, 100, 100))
                painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)
            
        # 3. Draw Border (1px Solid Gray)
        painter.setPen(QColor(160, 160, 160))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(0, 0, w - 1, h - 1)
        
        # We do NOT call super().paintEvent() because we handled the drawing.
