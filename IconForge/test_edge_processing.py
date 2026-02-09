#!/usr/bin/env python3
"""
Test advanced edge processing features.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core import ImageProcessor, EdgeProcessor
from PIL import Image


def test_edge_processing():
    """Test edge processing features."""
    print("=" * 60)
    print("Testing Advanced Edge Processing")
    print("=" * 60)
    
    processor = ImageProcessor()
    # Replace with path to your test image
    test_image = "path/to/your/test_image.png"
    
    if not Path(test_image).exists():
        print("⚠️  Test image not found")
        return False
    
    processor.load_image(test_image)
    img = processor.source_image
    
    output_dir = Path("test_output/edge_tests")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save original
    img.save(output_dir / "1_original.png")
    print("✓ Saved original")
    
    # Test defringe
    defringed = EdgeProcessor.defringe_simple(img, strength=0.7)
    defringed.save(output_dir / "2_defringed.png")
    print("✓ Saved defringed")
    
    # Test clean edges
    cleaned = EdgeProcessor.clean_edges(img, threshold=10, blur_radius=0.3)
    cleaned.save(output_dir / "3_cleaned_edges.png")
    print("✓ Saved cleaned edges")
    
    # Test mask expansion
    expanded = EdgeProcessor.expand_mask(img, pixels=2)
    expanded.save(output_dir / "4_mask_expanded.png")
    print("✓ Saved expanded mask")
    
    # Test mask contraction
    contracted = EdgeProcessor.expand_mask(img, pixels=-2)
    contracted.save(output_dir / "5_mask_contracted.png")
    print("✓ Saved contracted mask")
    
    # Test combined processing
    combined = img.copy()
    combined = EdgeProcessor.defringe_simple(combined, strength=0.7)
    combined = EdgeProcessor.clean_edges(combined, threshold=10, blur_radius=0.3)
    combined.save(output_dir / "6_combined.png")
    print("✓ Saved combined processing")
    
    print(f"\n✓ All edge processing tests completed!")
    print(f"  Output: {output_dir}")
    
    return True


if __name__ == "__main__":
    test_edge_processing()
