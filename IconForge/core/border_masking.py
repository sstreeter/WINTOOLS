"""
Border-based masking for Icon Factory.
Implements flood-fill style masking from edges (like Magic Wand/Paint Bucket).
"""

from PIL import Image
import numpy as np
from typing import Tuple, Set
from collections import deque


class BorderMasking:
    """Border-based color removal (flood fill from edges)."""
    
    @staticmethod
    def flood_fill_from_edges(image: Image.Image,
                              tolerance: int = 30,
                              start_from_corners: bool = True) -> Image.Image:
        """
        Remove color from borders using flood fill (like Magic Wand).
        Only removes colors connected to the edges, preserving interior colors.
        
        Args:
            image: Source RGBA image
            tolerance: Color matching tolerance (0-255)
            start_from_corners: If True, start from corners; if False, from all edges
            
        Returns:
            Image with border colors removed
        """
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        data = np.array(image)
        height, width = data.shape[:2]
        
        # Create mask for pixels to remove
        remove_mask = np.zeros((height, width), dtype=bool)
        visited = np.zeros((height, width), dtype=bool)
        
        # Get starting points (edge pixels)
        start_points = []
        
        if start_from_corners:
            # Start from corners only
            start_points = [
                (0, 0),
                (0, width - 1),
                (height - 1, 0),
                (height - 1, width - 1)
            ]
        else:
            # Start from all edge pixels
            # Top and bottom edges
            for x in range(width):
                start_points.append((0, x))
                start_points.append((height - 1, x))
            # Left and right edges
            for y in range(1, height - 1):
                start_points.append((y, 0))
                start_points.append((y, width - 1))
        
        # Flood fill from each starting point
        for start_y, start_x in start_points:
            if visited[start_y, start_x]:
                continue
            
            # Get the color at this starting point
            start_color = data[start_y, start_x, :3]
            
            # Skip if already transparent
            if data[start_y, start_x, 3] == 0:
                continue
            
            # Flood fill
            queue = deque([(start_y, start_x)])
            visited[start_y, start_x] = True
            
            while queue:
                y, x = queue.popleft()
                
                # Check if this pixel matches the start color
                current_color = data[y, x, :3]
                color_distance = np.sqrt(np.sum((current_color.astype(float) - start_color.astype(float)) ** 2))
                
                if color_distance <= tolerance:
                    remove_mask[y, x] = True
                    
                    # Add neighbors to queue
                    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < height and 0 <= nx < width and not visited[ny, nx]:
                            visited[ny, nx] = True
                            queue.append((ny, nx))
        
        # Apply mask
        result = data.copy()
        result[remove_mask, 3] = 0  # Set alpha to 0 for removed pixels
        
        return Image.fromarray(result, 'RGBA')
    
    @staticmethod
    def remove_border_color_simple(image: Image.Image,
                                   sample_corners: bool = True,
                                   tolerance: int = 30) -> Image.Image:
        """
        Simplified border color removal.
        Samples corner/edge colors and removes matching colors from entire border region.
        
        Args:
            image: Source RGBA image
            sample_corners: Sample from corners vs all edges
            tolerance: Color matching tolerance
            
        Returns:
            Image with border colors removed
        """
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        data = np.array(image)
        height, width = data.shape[:2]
        
        # Sample border colors
        if sample_corners:
            # Sample from corners
            sample_points = [
                (0, 0),
                (0, width - 1),
                (height - 1, 0),
                (height - 1, width - 1)
            ]
        else:
            # Sample from edges
            sample_points = []
            # Top edge
            for x in range(0, width, max(1, width // 10)):
                sample_points.append((0, x))
            # Bottom edge
            for x in range(0, width, max(1, width // 10)):
                sample_points.append((height - 1, x))
            # Left edge
            for y in range(0, height, max(1, height // 10)):
                sample_points.append((y, 0))
            # Right edge
            for y in range(0, height, max(1, height // 10)):
                sample_points.append((y, width - 1))
        
        # Get unique border colors
        border_colors = set()
        for y, x in sample_points:
            if data[y, x, 3] > 0:  # Not already transparent
                color = tuple(data[y, x, :3])
                border_colors.add(color)
        
        # Remove matching colors from border region only
        # Define border region (outer 10% of image)
        border_width = max(1, min(width, height) // 10)
        
        result = data.copy()
        
        for border_color in border_colors:
            bc = np.array(border_color)
            
            # Check all pixels in border region
            for y in range(height):
                for x in range(width):
                    # Check if in border region
                    in_border = (y < border_width or y >= height - border_width or
                               x < border_width or x >= width - border_width)
                    
                    if in_border:
                        pixel_color = result[y, x, :3]
                        distance = np.sqrt(np.sum((pixel_color.astype(float) - bc.astype(float)) ** 2))
                        
                        if distance <= tolerance:
                            result[y, x, 3] = 0
        
        return Image.fromarray(result, 'RGBA')
