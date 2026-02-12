"""
Core Conversion Logic for RedHerring.
Handles Pillow operations for resizing, styling, and saving icons.
"""
from PIL import Image, ImageDraw, ImageOps
from pathlib import Path

class IconConverter:
    @staticmethod
    def process_image(img: Image.Image, options: dict) -> Image.Image:
        """
        Apply transformations: Rotate -> Crop -> Style -> Resize.
        """
        processed = img.copy()
        
        # 1. Edit (Rotate/Flip would happen here if stored in options)
        # For now, we assume the UI handles rotation on the source object directly
        # or we pass it in options. Let's assume options has 'rotation'.
        if options.get('rotate'):
            processed = processed.rotate(options['rotate'], expand=True)
            
        if options.get('flip_h'):
            processed = ImageOps.mirror(processed)
            
        # 2. Crop Source (Square)
        if options.get('crop_square'):
            min_side = min(processed.size)
            left = (processed.width - min_side) // 2
            top = (processed.height - min_side) // 2
            processed = processed.crop((left, top, left + min_side, top + min_side))
            
        # 3. Resize to largest needed size (e.g. 1024) for high quality downscaling
        # But first, apply background/roundness
        
        # 4. Background Fill
        # If 'fill_background' is true, we create a new image with that color
        if options.get('fill_background'):
            bg_color = options.get('background_color', (255, 255, 255))
            bg = Image.new("RGBA", processed.size, bg_color + (255,))
            # Composite: Paste processed over background
            # If processed has alpha, use it as mask
            bg.alpha_composite(processed)
            processed = bg
            
        # 5. Rounded Corners
        radius_percent = options.get('radius', 0)
        if radius_percent > 0:
            # Create mask
            mask = Image.new('L', processed.size, 0)
            draw = ImageDraw.Draw(mask)
            
            w, h = processed.size
            # Radius is percentage of half-width (0-100 -> 0-w/2)
            r = int((min(w, h) / 2) * (radius_percent / 100))
            
            draw.rounded_rectangle([(0, 0), (w, h)], radius=r, fill=255)
            
            # Apply mask
            # If image already has alpha, we must multiply
            if 'A' in processed.getbands():
                current_alpha = processed.getchannel('A')
                # Intersection of both masks
                # Easy way: putalpha replaces it. We want: min(current, new)
                # But typically rounding cuts into it.
                processed.putalpha(mask) # This replaces existing alpha
            else:
                processed.putalpha(mask)
                
        return processed

    @staticmethod
    def save_icon(img: Image.Image, path: str, formats: list, sizes: list):
        """
        Save the processed image to the specified formats.
        """
        path = Path(path)
        base_name = path.stem
        output_dir = path.parent
        
        # Ensure sizes are sorted
        sizes = sorted(sizes, reverse=True)
        
        # 1. Generate Mipmaps
        mipmaps = []
        for s in sizes:
            # High quality resize
            res = img.resize((s, s), Image.Resampling.LANCZOS)
            mipmaps.append(res)
            
        # 2. Save Formats
        if 'ico' in formats:
            # Pillow saves ICO natively. It expects a list of images or (usually) just the biggest one 
            # and 'sizes' param, but passing a list to 'append_images' is safer for specific control.
            # Actually, img.save(..., sizes=[...]) re-generates them. 
            # Let's try passing the image and letting Pillow generate sizes.
            # Better strategy for high control:
            img.save(output_dir / f"{base_name}.ico", format='ICO', sizes=[(s, s) for s in sizes])
            
        if 'icns' in formats:
            # Pillow supports ICNS read/write
            img.save(output_dir / f"{base_name}.icns", format='ICNS', sizes=[(s, s) for s in sizes])
            
        if 'png' in formats:
            # Save bundle
            png_dir = output_dir / f"{base_name}_pngs"
            png_dir.mkdir(exist_ok=True)
            for m in mipmaps:
                m.save(png_dir / f"{base_name}_{m.width}x{m.height}.png")
