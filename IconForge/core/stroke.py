"""
Stroke Generation and Polishing Logic (Phase 20).
"""

from PIL import Image, ImageFilter, ImageOps, ImageChops
import numpy as np

class StrokeGenerator:
    """Handles advanced stroke generation with alignment."""
    
    @staticmethod
    def apply_stroke(image: Image.Image, color, width: int, alignment: str = 'outside') -> Image.Image:
        """
        Apply a stroke (border) of a specific width and alignment.
        
        Args:
            image: Source RGBA image.
            color: Stroke color (tuple).
            width: Stroke width in pixels.
            alignment: 'outside', 'center', 'inside'.
        """
        if width <= 0 or image.mode != 'RGBA':
            return image
            
        r, g, b, a = image.split()
        
        # We work with the alpha channel mask
        mask = a
        
        # Prepare filters
        # Note: MaxFilter/MinFilter is square kernel. 
        # For smoother circles, maybe Gaussian blur + threshold?
        # Sticking to MaxFilter for now for "Hard" stroke.
        # Ideally we use distance transform for perfect rounded strokes, but PIL is limited.
        # We can simulate rounded stroke by iterating MaxFilter(3) which approximates circle?
        # Or just use MaxFilter(size). MaxFilter(5) is square.
        # Let's use MaxFilter for now.
        
        outer_mask = None
        inner_mask = None
        
        # Calculate Masks based on alignment
        if alignment == 'outside':
            # Dilate by Width
            # MaxFilter takes Kernel Size (odd int). Radius = (Disk - 1)/2
            # Size = 2*Radius + 1.
            # Here width is effectively radius of expansion.
            kernel_size = (width * 2) + 1
            outer_mask = mask.filter(ImageFilter.MaxFilter(kernel_size))
            inner_mask = mask # Original
            
        elif alignment == 'inside':
            # Erode by Width
            kernel_size = (width * 2) + 1
            outer_mask = mask # Original
            inner_mask = mask.filter(ImageFilter.MinFilter(kernel_size))
            
        elif alignment == 'center':
            # Dilate/Erode by Half Width
            half_w = width // 2
            if half_w < 1: half_w = 1
            kernel_size = (half_w * 2) + 1
            
            outer_mask = mask.filter(ImageFilter.MaxFilter(kernel_size))
            inner_mask = mask.filter(ImageFilter.MinFilter(kernel_size))
            
        # Stroke Area = Outer - Inner
        # If Outside: Dilated - Original
        # If Inside: Original - Eroded
        # If Center: Dilated - Eroded
        
        stroke_mask = ImageChops.subtract(outer_mask, inner_mask)
        
        # Create Stroke Layer
        stroke_layer = Image.new('RGBA', image.size, color)
        stroke_layer.putalpha(stroke_mask)
        
        # Composite
        # Result = Stroke over Image?
        # If 'Inside', Stroke covers edge of image.
        # If 'Outside', Stroke is behind? Usually strokes are on top?
        # Actually, "Outside Alignment" usually implies Stroke is BEHIND the subject.
        # "Inside Alignment" implies Stroke is ON TOP of the subject (masking it).
        # "Center Alignment" implies ON TOP (straddling).
        
        # Standard vector behavior:
        # Outside: Behind.
        # Inside: Inteferes (On Top).
        # Center: Straddles (On Top).
        
        if alignment == 'outside':
            # Paste image OVER stroke
            result = Image.alpha_composite(stroke_layer, image)
        else:
            # Paste stroke OVER image
            result = Image.alpha_composite(image, stroke_layer)
            
        return result


class SuperPolisher:
    """Implements 'Liquid Polish' (KPT-style super-sampling)."""
    
    @staticmethod
    def liquid_smooth(image: Image.Image, intensity: float = 0.5) -> Image.Image:
        """
        Upscale -> Blur -> Levels -> Downscale.
        
        Args:
            image: Source RGBA image.
            intensity: Strength of the effect (0-1).
        """
        if intensity <= 0 or image.mode != 'RGBA':
            return image
            
        w, h = image.size
        
        # 1. Supersample (4x)
        # We need massive resolution to blur effectively without losing shape
        factor = 4
        big_w, big_h = w * factor, h * factor
        
        # Use Bicubic for smooth upscale (Lanczos might ring)
        supersampled = image.resize((big_w, big_h), Image.Resampling.BICUBIC)
        
        # 2. Gaussian Blur (Melt)
        # Radius depends on intensity.
        # 4x upscale means 1px blur becomes 4px.
        # Start low.
        blur_radius = 2 + (intensity * 8) # 2 to 10px
        
        blurred = supersampled.filter(ImageFilter.GaussianBlur(blur_radius))
        
        # 3. Threshold / Levels (Harden)
        # We want to sharpen the alpha channel.
        # Split alpha
        r, g, b, a = blurred.split()
        
        # Apply "Levels" to Alpha: 
        # Push standard gray (128) to edges (0 or 255).
        # Using point lookup table.
        # Sigmoid function or steep step.
        
        def levels_curve(x):
            # Midpoint 128.
            # Steepness depends on... we want it VERY sharp for "Vector" look.
            # If x < 100 -> 0. If x > 150 -> 255.
            # Smooth transition in between.
            
            if x < 100: return 0
            if x > 180: return 255
            # Linear interp
            return int((x - 100) / 80 * 255)
            
        a_sharp = a.point(levels_curve)
        
        # Re-merge
        polished_big = Image.merge('RGBA', (r, g, b, a_sharp))
        
        # 4. Downscale (Lanczos)
        result = polished_big.resize((w, h), Image.Resampling.LANCZOS)
        
        return result
