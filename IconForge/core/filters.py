
"""
Image enhancement filters for Icon Factory.
Provides simple checkbox-style enhancements (Sharpen, Contrast, etc.).
"""

from PIL import Image, ImageOps, ImageFilter

class FilterEngine:
    """Handles general image enhancements."""
    
    @staticmethod
    def auto_contrast(image: Image.Image, cutoff: int = 0) -> Image.Image:
        """Maximize image contrast."""
        if image.mode != 'RGB':
            rgb = image.convert('RGB')
            # changing to RGB loses alpha, need to preserve it
            alpha = image.split()[3] if 'A' in image.mode else None
            
            enhanced = ImageOps.autocontrast(rgb, cutoff=cutoff)
            
            if alpha:
                enhanced = enhanced.convert('RGBA')
                enhanced.putalpha(alpha)
            return enhanced
        else:
            return ImageOps.autocontrast(image, cutoff=cutoff)

    @staticmethod
    def equalize(image: Image.Image) -> Image.Image:
        """Equalize image histogram."""
        if image.mode != 'RGB':
            rgb = image.convert('RGB')
            alpha = image.split()[3] if 'A' in image.mode else None
            
            enhanced = ImageOps.equalize(rgb)
            
            if alpha:
                enhanced = enhanced.convert('RGBA')
                enhanced.putalpha(alpha)
            return enhanced
        else:
            return ImageOps.equalize(image)
            
    @staticmethod
    def sharpen(image: Image.Image) -> Image.Image:
        """Apply basic sharpening filter."""
        return image.filter(ImageFilter.SHARPEN)
        
    @staticmethod
    def smooth(image: Image.Image) -> Image.Image:
        """Apply smoothing (antialias) filter."""
        return image.filter(ImageFilter.SMOOTH)
        
    @staticmethod
    def grayscale(image: Image.Image) -> Image.Image:
        """Convert to grayscale."""
        return ImageOps.grayscale(image).convert('RGBA')
        
    @staticmethod
    def saturate(image: Image.Image, factor: float = 1.5) -> Image.Image:
        """Increase saturation."""
        from PIL import ImageEnhance
        converter = ImageEnhance.Color(image)
        return converter.enhance(factor)

    @staticmethod
    def despeckle(image: Image.Image) -> Image.Image:
        """Remove speckles (Median Filter)."""
        return image.filter(ImageFilter.MedianFilter(size=3))
