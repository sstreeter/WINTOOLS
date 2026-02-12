"""
Image processing core functionality for Icon Factory.
Handles image loading, resizing, and format conversion.
"""

from PIL import Image
from typing import List, Tuple, Optional
from pathlib import Path


class ImageProcessor:
    """Handles all image processing operations."""
    
    # Standard icon sizes for different platforms
    WINDOWS_SIZES = [16, 32, 48, 256]
    MAC_SIZES = [16, 32, 64, 128, 256, 512, 1024]
    WEB_SIZES = [100]  # Common for forms and web applications
    ALL_SIZES = sorted(list(set(WINDOWS_SIZES + MAC_SIZES + WEB_SIZES)))
    
    def __init__(self):
        self.source_image: Optional[Image.Image] = None
        self.processed_image: Optional[Image.Image] = None
        
    def load_image(self, path: str) -> bool:
        """
        Load an image from file path.
        Supports: PNG, JPG, BMP, GIF, SVG, EPS, PDF, AI.
        
        Args:
            path: Path to image file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            p = Path(path)
            ext = p.suffix.lower()
            
            # --- Vector Logic ---
            if ext == '.svg':
                # SVG Support via svglib (Pure Python)
                from svglib.svglib import svg2rlg
                from reportlab.graphics import renderPM
                from io import BytesIO
                
                # Convert SVG to ReportLab Drawing
                drawing = svg2rlg(path)
                
                # Render to high-res PNG in memory (1024x1024 target)
                # We need to scale it up if it's small defined in SVG
                # But svglib renders at defined size. Let's render at 4x scale for quality?
                # Actually renderPM allows scaling.
                
                # Get native size
                # width = drawing.width
                # height = drawing.height
                
                # Render to PNG buffer
                img_data = BytesIO()
                renderPM.drawToFile(drawing, img_data, fmt="PNG", dpi=300) # High DPI
                img_data.seek(0)
                
                self.source_image = Image.open(img_data).convert("RGBA")
                
            elif ext in ['.eps', '.pdf', '.ai']:
                # EPS/PDF Support via Ghostscript (PIL)
                # PIL Image.open lazy loads, so strictly it doesn't fail until rasterized.
                # However, for Vectors we want HIGH RES.
                # PIL defaults to 72 DPI which is bad for icons.
                
                # We need to use Ghostscript CLI directly or PIL with 'scale' param?
                # PIL EpsImagePlugin updates:
                img = Image.open(path)
                
                # Force high resolution rasterization
                # If we just convert(), PIL uses default DPI.
                # We need to reload with scale.
                img.load(scale=4) # Load at 4x resolution (High Quality)
                
                self.source_image = img.convert("RGBA")
                
            else:
                # Standard Raster Images
                self.source_image = Image.open(path).convert("RGBA")
                
            self.processed_image = self.source_image.copy()
            return True
            
        except Exception as e:
            print(f"Error loading image: {e}")
            return False
    
    def get_image_info(self) -> dict:
        """Get information about the loaded image."""
        if not self.source_image:
            return {}
        
        return {
            "size": self.source_image.size,
            "mode": self.source_image.mode,
            "format": self.source_image.format,
            "has_transparency": self.source_image.mode in ("RGBA", "LA", "P")
        }
    
    def resize_to_square(self, image: Image.Image, size: int, 
                        maintain_aspect: bool = True,
                        sharpen_params: dict = None) -> Image.Image:
        """
        Resize image to square dimensions.
        
        Args:
            image: Source image
            size: Target size (width and height)
            maintain_aspect: If True, pad to square; if False, stretch
            sharpen_params: Optional dict with 'radius', 'percent', 'threshold' for UnsharpMask
            
        Returns:
            Resized image
        """
        if maintain_aspect:
            # Calculate padding to make square
            width, height = image.size
            max_dim = max(width, height)
            
            # Create square canvas
            square = Image.new('RGBA', (max_dim, max_dim), (0, 0, 0, 0))
            
            # Paste image centered
            offset_x = (max_dim - width) // 2
            offset_y = (max_dim - height) // 2
            square.paste(image, (offset_x, offset_y))
            
            # Resize to target size
            resized = square.resize((size, size), Image.Resampling.LANCZOS)
        else:
            # Stretch to fit
            resized = image.resize((size, size), Image.Resampling.LANCZOS)
            
        # Apply Smart Sharpening
        if sharpen_params:
            from PIL import ImageFilter
            # UnsharpMask parameters: radius, percent, threshold
            radius = sharpen_params.get('radius', 0.5)
            percent = sharpen_params.get('percent', 100)
            threshold = sharpen_params.get('threshold', 3)
            
            # Apply to RGB channels mostly, but PIL UnsharpMask works on all.
            # However, sharpening alpha can created jagged edges.
            # Best practice: Sharpen RGB, keep Alpha clean or sharpen lightly.
            # For icons, "snapping" alpha is actually desired for crispness.
            resized = resized.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=threshold))
            
        return resized
    
    def generate_all_sizes(self, sizes: List[int] = None) -> dict:
        """
        Generate all icon sizes from the processed image.
        
        Args:
            sizes: List of sizes to generate (defaults to ALL_SIZES)
            
        Returns:
            Dictionary mapping size to Image object
        """
        if not self.processed_image:
            return {}
        
        if sizes is None:
            sizes = self.ALL_SIZES
        
        result = {}
        for size in sizes:
            # Determine Smart Sharpen parameters based on size
            sharpen_params = None
            if size <= 32:
                # Aggressive sharpen for tiny icons (16, 32)
                sharpen_params = {'radius': 0.5, 'percent': 150, 'threshold': 2}
            elif size <= 64:
                # Mild sharpen for medium icons (48, 64)
                sharpen_params = {'radius': 0.5, 'percent': 100, 'threshold': 3}
            # > 64: No sharpening (LANCZOS is sufficient and looks natural)
            
            result[size] = self.resize_to_square(self.processed_image, size, 
                                                 sharpen_params=sharpen_params)
        
        return result
    
    def get_preview(self, size: int = 256) -> Optional[Image.Image]:
        """
        Get a preview of the processed image.
        
        Args:
            size: Preview size
            
        Returns:
            Preview image or None
        """
        if not self.processed_image:
            return None
        
        return self.resize_to_square(self.processed_image, size)
    
    def apply_processed_image(self, image: Image.Image):
        """Update the processed image (used after masking/cropping)."""
        self.processed_image = image.copy()
    
    def reset_to_source(self):
        """Reset processed image to original source."""
        if self.source_image:
            self.processed_image = self.source_image.copy()
