"""
Auto-cropping functionality for Icon Factory.
Detects and crops to tight borders around content.
"""

from PIL import Image
import numpy as np
from typing import Tuple, Optional


class AutoCropper:
    """Handles automatic cropping to content bounds."""
    
    @staticmethod
    def get_content_bounds(image: Image.Image, 
                          padding: int = 0,
                          alpha_threshold: int = 0) -> Optional[Tuple[int, int, int, int]]:
        """
        Get the bounding box of non-transparent content.
        
        Args:
            image: RGBA image
            padding: Additional padding around content (in pixels)
            alpha_threshold: Minimum alpha value to consider as content (0-255)
            
        Returns:
            Tuple of (left, top, right, bottom) or None if no content
        """
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Get alpha channel
        alpha = np.array(image.split()[3])
        
        # Find rows and columns with content
        rows = np.any(alpha > alpha_threshold, axis=1)
        cols = np.any(alpha > alpha_threshold, axis=0)
        
        if not np.any(rows) or not np.any(cols):
            return None
        
        # Get bounds
        row_indices = np.where(rows)[0]
        col_indices = np.where(cols)[0]
        
        top = max(0, row_indices[0] - padding)
        bottom = min(image.height, row_indices[-1] + 1 + padding)
        left = max(0, col_indices[0] - padding)
        right = min(image.width, col_indices[-1] + 1 + padding)
        
        return (left, top, right, bottom)
    
    @staticmethod
    def crop_to_content(image: Image.Image, 
                       padding: int = 0,
                       alpha_threshold: int = 0) -> Image.Image:
        """
        Crop image to tight bounds around content.
        
        Args:
            image: Source image
            padding: Additional padding around content
            alpha_threshold: Minimum alpha to consider as content
            
        Returns:
            Cropped image
        """
        bounds = AutoCropper.get_content_bounds(image, padding, alpha_threshold)
        
        if bounds is None:
            return image
        
        return image.crop(bounds)
    
    @staticmethod
    def get_crop_info(image: Image.Image, padding: int = 0) -> dict:
        """
        Get information about the crop operation.
        
        Args:
            image: Source image
            padding: Padding to use
            
        Returns:
            Dictionary with crop information
        """
        bounds = AutoCropper.get_content_bounds(image, padding)
        
        if bounds is None:
            return {
                "has_content": False,
                "original_size": image.size,
                "cropped_size": image.size,
                "waste_percent": 0.0
            }
        
        left, top, right, bottom = bounds
        original_area = image.width * image.height
        cropped_area = (right - left) * (bottom - top)
        waste_percent = ((original_area - cropped_area) / original_area) * 100
        
        return {
            "has_content": True,
            "original_size": image.size,
            "cropped_size": (right - left, bottom - top),
            "bounds": bounds,
            "waste_percent": waste_percent
        }
        
    @staticmethod
    def apply_safe_zone(image: Image.Image, margin_percent: float = 10.0) -> Image.Image:
        """
        Enforce a 'Safe Zone' by scaling content to fit within a margin.
        Ensures uniform borders and prevents clipping using industry standards.
        (e.g., Apple uses ~10-15% margin, Google ~8%)
        
        Args:
            image: Source image (likely tightly cropped)
            margin_percent: Percentage of canvas to use as margin (per side)
            
        Returns:
            Square image with content centered and padded respecting the safe zone
        """
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
            
        # 1. Get tight content bounds first (ignore existing whitespace)
        bounds = AutoCropper.get_content_bounds(image, padding=0)
        if not bounds:
            return image
            
        content = image.crop(bounds)
        content_w, content_h = content.size
        
        # 2. Determine container size (Square)
        # We want the content to fit within (100% - 2*margin) of the container
        # Let's use the larger dimension of content as baseline
        max_dim = max(content_w, content_h)
        
        # Calculate canvas size
        # effective_width = canvas_size * (1 - 2*margin/100)
        # canvas_size = effective_width / (1 - 2*margin/100)
        # canvas_size = max_dim / (1 - 2*margin/100)
        
        safe_factor = 1.0 - (2.0 * margin_percent / 100.0)
        canvas_size = int(max_dim / safe_factor)
        
        # Enforce minimum size (optional, but good for anti-aliasing)
        canvas_size = max(canvas_size, 512) 
        
        # Create new square canvas
        canvas = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
        
        # 3. Center content
        paste_x = (canvas_size - content_w) // 2
        paste_y = (canvas_size - content_h) // 2
        
        canvas.paste(content, (paste_x, paste_y), content)
        
        return canvas
