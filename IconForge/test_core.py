#!/usr/bin/env python3
"""
Test script for Icon Factory core functionality.
Tests without GUI to verify all modules work correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core import ImageProcessor, AutoCropper, MaskingEngine, IconExporter
from utils import ArchiveManager


def test_image_processing():
    """Test image loading and processing."""
    print("Testing Image Processing...")
    
    processor = ImageProcessor()
    
    # Load test image
    # Replace with path to your test image
    test_image = "path/to/your/test_image.png"
    if not Path(test_image).exists():
        print(f"  ⚠️  Test image not found: {test_image}")
        return False
    
    if not processor.load_image(test_image):
        print("  ❌ Failed to load image")
        return False
    
    print(f"  ✓ Loaded image: {processor.get_image_info()}")
    
    # Generate sizes
    images = processor.generate_all_sizes([16, 32, 48, 256])
    print(f"  ✓ Generated {len(images)} sizes")
    
    return True


def test_auto_crop():
    """Test auto-cropping."""
    print("\nTesting Auto-Crop...")
    
    processor = ImageProcessor()
    # Replace with path to your test image
    test_image = "path/to/your/test_image.png"
    
    if not Path(test_image).exists():
        print("  ⚠️  Test image not found")
        return False
    
    processor.load_image(test_image)
    
    # Get crop info
    crop_info = AutoCropper.get_crop_info(processor.source_image, padding=5)
    print(f"  Original size: {crop_info['original_size']}")
    print(f"  Cropped size: {crop_info['cropped_size']}")
    print(f"  Waste: {crop_info['waste_percent']:.1f}%")
    
    # Apply crop
    cropped = AutoCropper.crop_to_content(processor.source_image, padding=5)
    print(f"  ✓ Cropped to: {cropped.size}")
    
    return True


def test_masking():
    """Test masking operations."""
    print("\nTesting Masking...")
    
    processor = ImageProcessor()
    # Replace with path to your test image
    test_image = "path/to/your/test_image.png"
    
    if not Path(test_image).exists():
        print("  ⚠️  Test image not found")
        return False
    
    processor.load_image(test_image)
    
    # Test binary alpha
    binary = MaskingEngine.binary_alpha(processor.source_image)
    print(f"  ✓ Binary alpha: {binary.size}")
    
    # Test glow
    glow = MaskingEngine.add_glow(processor.source_image)
    print(f"  ✓ Glow effect: {glow.size}")
    
    # Test background detection
    bg_color = MaskingEngine.get_dominant_background_color(processor.source_image)
    print(f"  ✓ Detected background color: RGB{bg_color}")
    
    return True


def test_export():
    """Test icon export."""
    print("\nTesting Export...")
    
    processor = ImageProcessor()
    # Replace with path to your test image
    test_image = "path/to/your/test_image.png"
    
    if not Path(test_image).exists():
        print("  ⚠️  Test image not found")
        return False
    
    processor.load_image(test_image)
    images = processor.generate_all_sizes([16, 32, 48, 256])
    
    # Create test output directory
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    # Test ICO export
    ico_path = output_dir / "test.ico"
    if IconExporter.export_ico(images, str(ico_path)):
        print(f"  ✓ Exported ICO: {ico_path}")
    else:
        print("  ❌ Failed to export ICO")
        return False
    
    # Test PNG set export
    png_dir = output_dir / "png"
    if IconExporter.export_png_set(images, str(png_dir)):
        print(f"  ✓ Exported PNG set: {png_dir}")
    else:
        print("  ❌ Failed to export PNG set")
        return False
    
    # Test ICNS export (macOS only)
    icns_path = output_dir / "test.icns"
    if IconExporter.export_icns_macos(images, str(icns_path)):
        print(f"  ✓ Exported ICNS: {icns_path}")
    else:
        print("  ⚠️  ICNS export skipped (macOS iconutil not available)")
    
    return True


def test_archive():
    """Test archive management."""
    print("\nTesting Archive Management...")
    
    output_dir = Path("test_output")
    
    # Create organized structure
    icon_dir = ArchiveManager.create_organized_structure(
        str(output_dir),
        "test_icon",
        "path/to/your/test_image.png"
    )
    print(f"  ✓ Created structure: {icon_dir}")
    
    # Create ZIP
    zip_path = output_dir / "test_icon.zip"
    if ArchiveManager.create_zip_archive(str(icon_dir), str(zip_path)):
        print(f"  ✓ Created ZIP: {zip_path}")
    else:
        print("  ❌ Failed to create ZIP")
        return False
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Icon Factory - Core Functionality Tests")
    print("=" * 60)
    
    tests = [
        test_image_processing,
        test_auto_crop,
        test_masking,
        test_export,
        test_archive
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Test failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("✓ All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
