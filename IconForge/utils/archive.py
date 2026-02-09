"""
Archive management for Icon Factory.
Handles organizing and packaging icon outputs.
"""

from pathlib import Path
import json
import zipfile
from datetime import datetime
from typing import Dict, Optional
import shutil


class ArchiveManager:
    """Manages icon output organization and archiving."""
    
    @staticmethod
    def create_organized_structure(base_path: str,
                                   icon_name: str,
                                   source_path: Optional[str] = None,
                                   metadata: Optional[dict] = None) -> Path:
        """
        Create organized directory structure for icon outputs.
        
        Args:
            base_path: Base output directory
            icon_name: Name for the icon
            source_path: Path to source image (optional)
            metadata: Additional metadata to save
            
        Returns:
            Path to created structure
        """
        # Create main directory
        icon_dir = Path(base_path) / icon_name
        icon_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (icon_dir / "source").mkdir(exist_ok=True)
        (icon_dir / "windows").mkdir(exist_ok=True)
        (icon_dir / "mac").mkdir(exist_ok=True)
        (icon_dir / "png").mkdir(exist_ok=True)
        
        # Copy source file if provided
        if source_path:
            source_file = Path(source_path)
            if source_file.exists():
                shutil.copy2(source_file, icon_dir / "source" / source_file.name)
        
        # Create metadata file
        meta = {
            "icon_name": icon_name,
            "created": datetime.now().isoformat(),
            "source_file": str(source_path) if source_path else None,
        }
        
        if metadata:
            meta.update(metadata)
        
        with open(icon_dir / "metadata.json", "w") as f:
            json.dump(meta, f, indent=2)
        
        return icon_dir
    
    @staticmethod
    def create_zip_archive(source_dir: str, output_path: str) -> bool:
        """
        Create a ZIP archive of the icon directory.
        
        Args:
            source_dir: Directory to archive
            output_path: Output ZIP file path
            
        Returns:
            True if successful
        """
        try:
            source = Path(source_dir)
            
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in source.rglob('*'):
                    if file.is_file():
                        arcname = file.relative_to(source.parent)
                        zipf.write(file, arcname)
            
            return True
        except Exception as e:
            print(f"Error creating ZIP archive: {e}")
            return False
    
    @staticmethod
    def get_output_paths(base_dir: Path, icon_name: str) -> Dict[str, Path]:
        """
        Get standardized output paths for different formats.
        
        Args:
            base_dir: Base directory
            icon_name: Icon name
            
        Returns:
            Dictionary of format to path
        """
        return {
            "ico_full_alpha": base_dir / "windows" / f"{icon_name}_full_alpha.ico",
            "ico_binary_alpha": base_dir / "windows" / f"{icon_name}_binary_alpha.ico",
            "ico_with_glow": base_dir / "windows" / f"{icon_name}_with_glow.ico",
            "icns": base_dir / "mac" / f"{icon_name}.icns",
            "png_dir": base_dir / "png"
        }
