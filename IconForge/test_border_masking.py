#!/usr/bin/env python3
"""
Test border masking functionality.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core import ImageProcessor, BorderMasking
from PIL import Image


def test_border_masking():
    """Test border-only color removal."""
    print("=" * 60)
    print("Testing Border Masking (Magic Wand Style)")
    print("=" * 60)
    
    processor = ImageProcessor()
    # Replace with path to your test image
    test_image = "path/to/your/test_image.png"
    
    if not Path(test_image).exists():
        print("⚠️  Test image not found")
        return False
    
    processor.load_image(test_image)
    img = processor.source_image
    
    output_dir = Path("test_output/border_tests")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save original
    img.save(output_dir / "1_original.png")
    print("✓ Saved original")
    
    # Test flood fill from corners with different tolerances
    for tolerance in [10, 30, 50]:
        result = BorderMasking.flood_fill_from_edges(img, tolerance=tolerance, start_from_corners=True)
        result.save(output_dir / f"2_flood_fill_tol{tolerance}.png")
        print(f"✓ Saved flood fill (tolerance={tolerance})")
    
    # Test simple border removal
    simple = BorderMasking.remove_border_color_simple(img, sample_corners=True, tolerance=30)
    simple.save(output_dir / "3_simple_border_removal.png")
    print("✓ Saved simple border removal")
    
    print(f"\n✓ All border masking tests completed!")
    print(f"  Output: {output_dir}")
    
    return True


if __name__ == "__main__":
    test_border_masking()
