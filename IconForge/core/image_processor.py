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
        
        Args:
            path: Path to image file
            
        Returns:
            True if successful, False otherwise
        """
        try:
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
                        maintain_aspect: bool = True) -> Image.Image:
        """
        Resize image to square dimensions.
        
        Args:
            image: Source image
            size: Target size (width and height)
            maintain_aspect: If True, pad to square; if False, stretch
            
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
            return square.resize((size, size), Image.Resampling.LANCZOS)
        else:
            # Stretch to fit
            return image.resize((size, size), Image.Resampling.LANCZOS)
    
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
            result[size] = self.resize_to_square(self.processed_image, size)
        
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
