"""
Composition Engine for Icon Factory.
Handles "Smart Composition" - fitting images into square canvases with padding/crop logic.
"""

from PIL import Image, ImageOps

class CompositionEngine:
    """Handles image composition, scaling, and padding."""
    
    @staticmethod
    def compose(image: Image.Image, 
                target_size: int = 1024, 
                scale: float = 1.0, 
                fit_mode: str = 'contain',
                anchor: str = 'center') -> Image.Image:
        """
        Compose the image onto a square canvas.
        
        Args:
            image: Source image (PIL)
            target_size: Output square size (default 1024)
            scale: Zoom factor (1.0 = 100%, 0.9 = 90% size / 10% padding)
            fit_mode: 'contain' (Show all, adding bars) or 'cover' (Fill square, cropping)
            anchor: 'center' (default) - future expansion for alignment
            
        Returns:
            Square RGBA Image
        """
        if not image:
            return Image.new('RGBA', (target_size, target_size), (0,0,0,0))
            
        # 1. Base Canvas
        canvas = Image.new('RGBA', (target_size, target_size), (0, 0, 0, 0))
        
        # 2. Calculate Scaled Dimensions
        # First, resize image to fit the target box according to fit_mode
        src_w, src_h = image.size
        ratio_w = target_size / src_w
        ratio_h = target_size / src_h
        
        if fit_mode == 'cover':
            # Scale to FILL (max ratio)
            base_scale = max(ratio_w, ratio_h)
        else:
            # Scale to FIT (min ratio) -> 'contain'
            base_scale = min(ratio_w, ratio_h)
            
        # Apply user Zoom/Padding scale
        final_scale = base_scale * scale
        
        new_w = int(src_w * final_scale)
        new_h = int(src_h * final_scale)
        
        # 3. Resize Source
        # check for 0 dimensions
        if new_w < 1: new_w = 1
        if new_h < 1: new_h = 1
        
        resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # 4. Paste Centered
        offset_x = (target_size - new_w) // 2
        offset_y = (target_size - new_h) // 2
        
        # Handle crop if 'cover' made it larger than canvas
        if fit_mode == 'cover' and (new_w > target_size or new_h > target_size):
            # We need to crop the center
            left = (new_w - target_size) // 2
            top = (new_h - target_size) // 2
            right = left + target_size
            bottom = top + target_size
            resized = resized.crop((left, top, right, bottom))
            offset_x = 0
            offset_y = 0
            
        # Paste
        # Use mask if image has alpha
        if resized.mode == 'RGBA':
            canvas.paste(resized, (offset_x, offset_y), resized)
        else:
            canvas.paste(resized, (offset_x, offset_y))
            
        return canvas
