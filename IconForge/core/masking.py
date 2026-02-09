"""
Masking functionality for Icon Factory.
Supports color-based masking, perimeter detection, and alpha manipulation.
"""

from PIL import Image, ImageFilter
import numpy as np
from typing import Tuple, Optional


class MaskingEngine:
    """Handles various masking operations."""
    
    @staticmethod
    def color_mask(image: Image.Image, 
                   target_color: Tuple[int, int, int],
                   tolerance: int = 30) -> Image.Image:
        """
        Remove a specific color from the image (make it transparent).
        
        Args:
            image: Source image
            target_color: RGB color to remove
            tolerance: Color matching tolerance (0-255)
            
        Returns:
            Image with color masked to transparent
        """
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Convert to numpy for faster processing
        data = np.array(image)
        
        # Extract RGB channels
        r, g, b, a = data[:, :, 0], data[:, :, 1], data[:, :, 2], data[:, :, 3]
        
        # Calculate color distance
        target_r, target_g, target_b = target_color
        distance = np.sqrt(
            (r.astype(float) - target_r) ** 2 +
            (g.astype(float) - target_g) ** 2 +
            (b.astype(float) - target_b) ** 2
        )
        
        # Create mask where color matches
        mask = distance <= tolerance
        
        # Set alpha to 0 where mask is True
        data[:, :, 3] = np.where(mask, 0, a)
        
        return Image.fromarray(data, 'RGBA')
    
    @staticmethod
    def binary_alpha(image: Image.Image, threshold: int = 128) -> Image.Image:
        """
        Convert gradual alpha to binary (fully transparent or fully opaque).
        Better for Windows ICO compatibility.
        
        Args:
            image: Source image
            threshold: Alpha threshold (0-255)
            
        Returns:
            Image with binary alpha
        """
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        data = np.array(image)
        alpha = data[:, :, 3]
        
        # Binary threshold
        data[:, :, 3] = np.where(alpha > threshold, 255, 0)
        
        return Image.fromarray(data, 'RGBA')
    
    @staticmethod
    def add_glow(image: Image.Image,
                 glow_color: Tuple[int, int, int, int] = (0, 0, 0, 180),
                 blur_radius: int = 3) -> Image.Image:
        """
        Add a subtle glow/shadow around the image content.
        
        Args:
            image: Source image
            glow_color: RGBA color for glow
            blur_radius: Blur amount for glow
            
        Returns:
            Image with glow effect
        """
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Extract alpha channel
        alpha = image.split()[3]
        
        # Blur alpha to create glow
        glow_alpha = alpha.filter(ImageFilter.GaussianBlur(blur_radius))
        
        # Create glow layer
        glow_layer = Image.new('RGBA', image.size, glow_color)
        glow_layer.putalpha(glow_alpha)
        
        # Composite glow behind original
        result = Image.alpha_composite(glow_layer, image)
        
        return result
    
    @staticmethod
    def add_background(image: Image.Image,
                      bg_color: Tuple[int, int, int, int] = (255, 255, 255, 255)) -> Image.Image:
        """
        Add a solid background color (removes transparency).
        
        Args:
            image: Source image
            bg_color: RGBA background color
            
        Returns:
            Image with solid background
        """
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        background = Image.new('RGBA', image.size, bg_color)
        return Image.alpha_composite(background, image)
    
    @staticmethod
    def get_dominant_background_color(image: Image.Image) -> Tuple[int, int, int]:
        """
        Detect the dominant background color (useful for auto color masking).
        Samples corners and edges.
        
        Args:
            image: Source image
            
        Returns:
            RGB tuple of dominant color
        """
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Sample corner pixels
        width, height = image.size
        corners = [
            image.getpixel((0, 0)),
            image.getpixel((width - 1, 0)),
            image.getpixel((0, height - 1)),
            image.getpixel((width - 1, height - 1))
        ]
        
        # Get RGB only (ignore alpha)
        corner_colors = [(r, g, b) for r, g, b, a in corners]
        
        # Find most common color (simple mode)
        from collections import Counter
        color_counts = Counter(corner_colors)
        dominant = color_counts.most_common(1)[0][0]
        
        return dominant

    @staticmethod
    def choke_mask(image: Image.Image, radius: int = 1) -> Image.Image:
        """
        Shrink the opaque area of the mask (Erode).
        Essential for removing 'halos' or fringes around keyed subjects.
        
        Args:
            image: Source RGBA image
            radius: Amount to shrink in pixels
            
        Returns:
            Image with eroded alpha channel
        """
        if radius <= 0:
            return image
            
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
            
        # Extract alpha
        r, g, b, a = image.split()
        
        # Erode alpha (MinFilter)
        # 1px radius means looking at 3x3 window (radius=1)
        # PIL MinFilter takes integer size (3, 5, 7...)
        kernel_size = (int(radius) * 2) + 1
        a_choked = a.filter(ImageFilter.MinFilter(kernel_size))
        
        return Image.merge('RGBA', (r, g, b, a_choked))

    @staticmethod
    def multi_color_mask(image: Image.Image, 
                         target_colors: list[Tuple[int, int, int]],
                         tolerance: int = 30) -> Image.Image:
        """
        Remove multiple specific colors from the image.
        
        Args:
            image: Source image
            target_colors: List of RGB colors to remove
            tolerance: Color matching tolerance
            
        Returns:
            Image with colors masked to transparent
        """
        if not target_colors:
            return image
            
        img = image
        for color in target_colors:
            img = MaskingEngine.color_mask(img, color, tolerance)
            
        return img
