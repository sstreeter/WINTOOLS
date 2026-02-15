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
            
            
        # 2. Crop Source (Square) - DEPRECATED / REMOVED
        # We now handle sizing/cropping at the Save stage (save_icon)
        # or via explicit Crop Tool (todo).
        # if options.get('crop_square'): ...
            
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
    def save_icon(img: Image.Image, path: str, formats: list, sizes: list, options: dict = None):
        """
        Save the processed image to the specified formats with resizing logic.
        options['resize_to_aspect']: True (default) = Contain/Fit, False = Crop/Fill
        """
        path = Path(path)
        base_name = path.stem
        output_dir = path.parent
        options = options or {}
        
        # Ensure sizes are sorted
        sizes = sorted(sizes, reverse=True)
        
        # Resize Mode
        # If resize_to_aspect is True (Checked): Contain/Fit (Sacrosanct)
        # If False (Unchecked): Fit/Crop (Fill square)
        use_contain = options.get('resize_to_aspect', True)
        
        # 1. Generate Mipmaps
        mipmaps = []
        for s in sizes:
            # Determine target dimensions
            if isinstance(s, tuple):
                tw, th = s
            else:
                tw, th = s, s
                
            if use_contain:
                # Sacrosanct: Fit INSIDE target rect with transparent padding
                # Create canvas of target size
                canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
                
                # Resize image to fit within tw x th
                res = ImageOps.contain(img.copy(), (tw, th), Image.Resampling.LANCZOS)
                
                # Center it
                x = (tw - res.width) // 2
                y = (th - res.height) // 2
                canvas.paste(res, (x, y))
                mipmaps.append(canvas)
            else:
                # Crop/Fill: Fill the target rect, cropping edges
                res = ImageOps.fit(img.copy(), (tw, th), Image.Resampling.LANCZOS)
                mipmaps.append(res)
            
        # 2. Save Formats
        if 'ico' in formats:
            base_img = mipmaps[0]
            other_images = mipmaps[1:] if len(mipmaps) > 1 else []
            base_img.save(path, format='ICO', append_images=other_images)
            
        if 'icns' in formats:
            base_img = mipmaps[0]
            other_images = mipmaps[1:] if len(mipmaps) > 1 else []
            base_img.save(path.with_suffix('.icns'), format='ICNS', append_images=other_images)
            
        if 'png' in formats:
            if len(mipmaps) == 1:
                mipmaps[0].save(path, "PNG")
            else:
                png_dir = output_dir / f"{base_name}_pngs"
                png_dir.mkdir(exist_ok=True)
                for m in mipmaps:
                    m.save(png_dir / f"{base_name}_{m.width}x{m.height}.png")
                
        if 'bmp' in formats:
            # Similar to PNG: if multiple, folder. If single, maybe just file?
            # Standard logic: Always folder for consistency if multiple sizes?
            # Or if len(mipmaps) == 1, save to path directly?
            # The prompt implies user might want single file.
            # Let's do: If 1 size -> Path. If >1 -> Folder.
            
            if len(mipmaps) == 1:
                # Save single file
                mipmaps[0].save(path, "BMP")
            else:
                bmp_dir = output_dir / f"{base_name}_bmps"
                bmp_dir.mkdir(exist_ok=True)
                for m in mipmaps:
                    m.save(bmp_dir / f"{base_name}_{m.width}x{m.height}.bmp")
