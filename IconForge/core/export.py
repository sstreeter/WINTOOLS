"""
Icon export functionality for Icon Factory.
Handles .ico, .icns, and PNG set exports.
"""

from PIL import Image
from pathlib import Path
from typing import List, Dict, Optional
import subprocess
import shutil
import tempfile


class IconExporter:
    """Handles exporting icons in various formats."""
    
    @staticmethod
    def export_ico(images: Dict[int, Image.Image],
                   output_path: str,
                   variant: str = "full_alpha") -> bool:
        """
        Export Windows ICO file.
        
        Args:
            images: Dictionary mapping size to Image
            output_path: Output file path
            variant: "full_alpha", "binary_alpha", or "with_glow"
            
        Returns:
            True if successful
        """
        try:
            # Get standard Windows sizes
            sizes = [16, 32, 48, 256]
            icon_images = [images.get(s) for s in sizes if s in images]
            
            if not icon_images:
                return False
            
            # Save ICO
            icon_images[0].save(
                output_path,
                format="ICO",
                sizes=[(img.width, img.height) for img in icon_images],
                append_images=icon_images[1:]
            )
            
            return True
        except Exception as e:
            print(f"Error exporting ICO: {e}")
            return False
    
    @staticmethod
    def export_icns_macos(images: Dict[int, Image.Image],
                         output_path: str) -> bool:
        """
        Export macOS ICNS file using iconutil (macOS only).
        
        Args:
            images: Dictionary mapping size to Image
            output_path: Output file path
            
        Returns:
            True if successful
        """
        try:
            # Check if iconutil is available (macOS only)
            if shutil.which('iconutil') is None:
                print("iconutil not found (macOS only)")
                return False
            
            # Create temporary iconset directory
            with tempfile.TemporaryDirectory() as tmpdir:
                iconset_path = Path(tmpdir) / "icon.iconset"
                iconset_path.mkdir()
                
                # ICNS requires specific naming convention
                size_mapping = {
                    16: [("icon_16x16.png", 16)],
                    32: [("icon_16x16@2x.png", 32), ("icon_32x32.png", 32)],
                    64: [("icon_32x32@2x.png", 64)],
                    128: [("icon_128x128.png", 128)],
                    256: [("icon_128x128@2x.png", 256), ("icon_256x256.png", 256)],
                    512: [("icon_256x256@2x.png", 512), ("icon_512x512.png", 512)],
                    1024: [("icon_512x512@2x.png", 1024)]
                }
                
                # Save images with proper naming
                for size, img in images.items():
                    if size in size_mapping:
                        for filename, _ in size_mapping[size]:
                            img.save(iconset_path / filename, "PNG")
                
                # Convert to ICNS using iconutil
                result = subprocess.run(
                    ["iconutil", "-c", "icns", str(iconset_path), "-o", output_path],
                    capture_output=True,
                    text=True
                )
                
                return result.returncode == 0
                
        except Exception as e:
            print(f"Error exporting ICNS: {e}")
            return False
    
    @staticmethod
    def export_png_set(images: Dict[int, Image.Image],
                      output_dir: str) -> bool:
        """
        Export set of PNG files at different sizes.
        
        Args:
            images: Dictionary mapping size to Image
            output_dir: Output directory path
            
        Returns:
            True if successful
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            for size, img in images.items():
                filename = f"icon_{size}.png"
                img.save(output_path / filename, "PNG")
            
            return True
        except Exception as e:
            print(f"Error exporting PNG set: {e}")
            return False
