"""
Advanced masking and edge processing for Icon Factory.
Includes defringe, edge cleanup, and mask expansion/contraction.
"""

from PIL import Image, ImageFilter, ImageChops
import numpy as np
from typing import Tuple


class EdgeProcessor:
    """Advanced edge processing and cleanup."""
    
    @staticmethod
    def defringe(image: Image.Image, 
                 radius: int = 1,
                 threshold: int = 30) -> Image.Image:
        """
        Remove color fringing from edges (like Photoshop's Defringe).
        This removes colored halos around transparent edges.
        
        Args:
            image: Source RGBA image
            radius: Defringe radius in pixels
            threshold: Alpha threshold for edge detection
            
        Returns:
            Defringed image
        """
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        data = np.array(image, dtype=np.float32)
        r, g, b, a = data[:, :, 0], data[:, :, 1], data[:, :, 2], data[:, :, 3]
        
        # Find edge pixels (semi-transparent)
        edge_mask = (a > 0) & (a < 255 - threshold)
        
        # For edge pixels, blend with nearby opaque pixels
        if np.any(edge_mask):
            # Create a mask of fully opaque pixels
            opaque_mask = a >= 255 - threshold
            
            # Dilate the opaque mask to find nearby opaque pixels
            from scipy import ndimage
            dilated_opaque = ndimage.binary_dilation(opaque_mask, iterations=radius)
            
            # For each edge pixel, average with nearby opaque pixels
            for channel in [r, g, b]:
                # Create weighted average based on alpha
                channel_copy = channel.copy()
                channel[edge_mask] = channel_copy[edge_mask] * 0.3 + \
                                    np.mean(channel_copy[dilated_opaque]) * 0.7
        
        # Reconstruct image
        result = np.stack([r, g, b, a], axis=2).astype(np.uint8)
        return Image.fromarray(result, 'RGBA')
    
    @staticmethod
    def defringe_simple(image: Image.Image, strength: float = 0.5) -> Image.Image:
        """
        Simplified defringe that doesn't require scipy.
        Removes color from semi-transparent edges.
        
        Args:
            image: Source RGBA image
            strength: Defringe strength (0-1)
            
        Returns:
            Defringed image
        """
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        data = np.array(image, dtype=np.float32)
        r, g, b, a = data[:, :, 0], data[:, :, 1], data[:, :, 2], data[:, :, 3]
        
        # Find semi-transparent pixels
        edge_mask = (a > 0) & (a < 200)
        
        # Reduce color intensity on edges based on alpha
        alpha_factor = (a / 255.0) ** (1.0 + strength)
        
        r = r * alpha_factor
        g = g * alpha_factor
        b = b * alpha_factor
        
        result = np.stack([r, g, b, a], axis=2).astype(np.uint8)
        return Image.fromarray(result, 'RGBA')
    
    @staticmethod
    def expand_mask(image: Image.Image, pixels: int = 1) -> Image.Image:
        """
        Expand the alpha mask outward (choke/spread).
        
        Args:
            image: Source RGBA image
            pixels: Number of pixels to expand (positive) or contract (negative)
            
        Returns:
            Image with expanded mask
        """
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Extract alpha channel
        alpha = image.split()[3]
        
        if pixels > 0:
            # Expand (dilate)
            for _ in range(pixels):
                alpha = alpha.filter(ImageFilter.MaxFilter(3))
        elif pixels < 0:
            # Contract (erode)
            for _ in range(abs(pixels)):
                alpha = alpha.filter(ImageFilter.MinFilter(3))
        
        # Apply modified alpha
        result = image.copy()
        result.putalpha(alpha)
        
        return result
    
    @staticmethod
    def clean_edges(image: Image.Image, 
                   threshold: int = 10,
                   blur_radius: float = 0.5) -> Image.Image:
        """
        Clean up edge artifacts and pixel debris.
        
        Args:
            image: Source RGBA image
            threshold: Minimum alpha to keep (removes very faint pixels)
            blur_radius: Slight blur to smooth edges
            
        Returns:
            Cleaned image
        """
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        data = np.array(image)
        alpha = data[:, :, 3]
        
        # Remove pixels below threshold (debris)
        alpha[alpha < threshold] = 0
        
        # Apply slight blur to smooth edges
        if blur_radius > 0:
            alpha_img = Image.fromarray(alpha, 'L')
            alpha_img = alpha_img.filter(ImageFilter.GaussianBlur(blur_radius))
            alpha = np.array(alpha_img)
        
        data[:, :, 3] = alpha
        
        return Image.fromarray(data, 'RGBA')
    
    @staticmethod
    def remove_matte(image: Image.Image, 
                     matte_color: Tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
        """
        Remove color matte from semi-transparent edges.
        Useful when image was composited on a colored background.
        
        Args:
            image: Source RGBA image
            matte_color: RGB color of the matte to remove
            
        Returns:
            Image with matte removed
        """
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        data = np.array(image, dtype=np.float32)
        r, g, b, a = data[:, :, 0], data[:, :, 1], data[:, :, 2], data[:, :, 3]
        
        # Normalize alpha
        alpha_norm = a / 255.0
        alpha_norm = np.maximum(alpha_norm, 0.001)  # Avoid division by zero
        
        # Remove matte color
        mr, mg, mb = matte_color
        
        r = (r - mr * (1 - alpha_norm)) / alpha_norm
        g = (g - mg * (1 - alpha_norm)) / alpha_norm
        b = (b - mb * (1 - alpha_norm)) / alpha_norm
        
        # Clamp values
        r = np.clip(r, 0, 255)
        g = np.clip(g, 0, 255)
        b = np.clip(b, 0, 255)
        
        result = np.stack([r, g, b, a], axis=2).astype(np.uint8)
        return Image.fromarray(result, 'RGBA')
    
    @staticmethod
    def sharpen_edges(image: Image.Image, strength: float = 1.0) -> Image.Image:
        """
        Sharpen edges while preserving transparency.
        
        Args:
            image: Source RGBA image
            strength: Sharpening strength
            
        Returns:
            Sharpened image
        """
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Extract alpha
        alpha = image.split()[3]
        
        # Sharpen RGB
        rgb = image.convert('RGB')
        sharpened = rgb.filter(ImageFilter.UnsharpMask(
            radius=1.0,
            percent=int(150 * strength),
            threshold=3
        ))
        
        # Recombine with alpha
        result = sharpened.convert('RGBA')
        result.putalpha(alpha)
        
        return result

    @staticmethod
    def smart_cleanup(image: Image.Image, 
                     smoothing_strength: int = 50, 
                     corner_sharpness: int = 50,
                     stroke_weight: int = 0,
                     sharpen_amount: int = 0) -> Image.Image:
        """
        Reconstruct jagged edges using Super-Sampling technique.
        Synthesizes vector-like quality from pixelated/jagged sources.
        
        Args:
            image: Source RGBA image
            smoothing_strength: 0-100 (0=Faithful, 100=Geometric/Abstract)
            corner_sharpness: 0-100 (0=Round, 100=Sharp)
            stroke_weight: -10 to +10 (Negative=Thin, Positive=Bold)
            sharpen_amount: 0-100 (Contrast at edges)
            
        Returns:
            Reconstructed 'clean' image
        """
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
            
        original_size = image.size
        
        # 0. Pad image to prevent border artifacts
        # Add 10px padding on all sides to give the kernels room to work
        padding = 10
        padded_w = original_size[0] + (padding * 2)
        padded_h = original_size[1] + (padding * 2)
        padded_img = Image.new('RGBA', (padded_w, padded_h), (0,0,0,0))
        padded_img.paste(image, (padding, padding))
        
        # 1. Pipeline: High-Res Processing
        # Upscale 4x for sub-pixel precision
        scale = 4
        high_res = padded_img.resize(
            (padded_w * scale, padded_h * scale), 
            resample=Image.Resampling.LANCZOS
        )
        
        # Split channels
        r, g, b, a = high_res.split()
        
        # 2. Hard Threshold on Alpha (Create Vector Shape)
        # Anything > 128 becomes opaque, else transparent. Snap to grid.
        a_arr = np.array(a)
        a_arr = np.where(a_arr > 127, 255, 0).astype(np.uint8)
        a_binary = Image.fromarray(a_arr, 'L')
        
        # 3. Morphological Opening (Wart Removal / Smoothing)
        # Calculate kernel size based on strength (0-100 -> 0-25px)
        struct_size = int(smoothing_strength * 0.25)
        
        # MinFilter/MaxFilter require odd integer size >= 3
        if struct_size < 3:
            if smoothing_strength > 0:
                struct_size = 3
            else:
                struct_size = 0
        elif struct_size % 2 == 0:
            struct_size += 1
            
        if struct_size >= 3:
            # Erode (MinFilter): Eats away small protrusions ("warts")
            # Dilate (MaxFilter): Grows back the main shape
            a_eroded = a_binary.filter(ImageFilter.MinFilter(struct_size))
            a_opened = a_eroded.filter(ImageFilter.MaxFilter(struct_size))
        else:
            a_opened = a_binary
        
        # 3b. Stroke Weight (Boldness) - Phase 8
        # Execute after smoothing but before blur
        # stroke_weight: -10 to +10 (Negative=Thin/Erode, Positive=Bold/Dilate)
        if stroke_weight != 0:
            # Map abstract weight (1-10) to valid kernel size (odd >= 3)
            # Weight 1 -> Size 3
            # Weight 2 -> Size 5
            # ...
            kernel_size = (int(abs(stroke_weight)) * 2) + 1
            
            if stroke_weight > 0:
                # Positive = Bold = Dilate (MaxFilter)
                a_opened = a_opened.filter(ImageFilter.MaxFilter(kernel_size))
            else:
                # Negative = Thin = Erode (MinFilter)
                a_opened = a_opened.filter(ImageFilter.MinFilter(kernel_size))

        # 4. Soft Anti-Aliasing (Corner Sharpness)
        # Calculate blur radius based on sharpness (0-100 -> 4.0-0.0px)
        # Sharpness 50 -> 2.0px (Current default)
        blur_radius = 4.0 * (1.0 - (corner_sharpness / 100.0))
        # Ensure minimum tiny blur to prevent aliasing
        blur_radius = max(blur_radius, 0.5)
        
        # Blur slightly at high res to create smooth transition
        a_smooth = a_opened.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        
        # 5. Final Polish (Sharpening) - Phase 8
        # Apply UnsharpMask to the Alpha channel to "snap" the edges
        if sharpen_amount > 0:
            # Map 0-100 to Percent 0-200 usually works well
            percent = int(sharpen_amount * 2) 
            a_smooth = a_smooth.filter(ImageFilter.UnsharpMask(radius=2, percent=percent, threshold=3))
        
        # Recombine high-res image
        high_res_clean = Image.merge('RGBA', (r, g, b, a_smooth))
        
        # 5. Downscale to original padded size
        result_padded = high_res_clean.resize((padded_w, padded_h), resample=Image.Resampling.LANCZOS)
        
        # 6. Unpad (Crop back to original size)
        result = result_padded.crop((padding, padding, padding + original_size[0], padding + original_size[1]))
        
        # 7. Border Guard (Wipe outer 1px to fix ringing artifacts)
        result = EdgeProcessor.wipe_borders(result, pixels=1)
        
        return result
        
    @staticmethod
    def wipe_borders(image: Image.Image, pixels: int = 1) -> Image.Image:
        """
        Border Guard: Explicitly wipe the outer perimeter of the image to transparent.
        Fixes 'ringing' artifacts and dirty lines caused by resampling at the edges.
        
        Args:
            image: Source RGBA image
            pixels: Number of pixels to wipe from the edge
            
        Returns:
            Cleaned image with transparent border
        """
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
            
        w, h = image.size
        
        # Create a mask that is opaque in the center and transparent at edges
        mask = Image.new('L', (w, h), 0)
        
        # Draw opaque rectangle in center
        from PIL import ImageDraw
        draw = ImageDraw.Draw(mask)
        draw.rectangle((pixels, pixels, w - pixels - 1, h - pixels - 1), fill=255)
        
        # Apply mask to alpha channel
        data = np.array(image)
        alpha = data[:, :, 3]
        mask_arr = np.array(mask)
        
        # Multiply alpha by mask (where mask is 0, alpha becomes 0)
        # Using simple boolean masking since mask is binary
        alpha[mask_arr == 0] = 0
        
        data[:, :, 3] = alpha
        
        return Image.fromarray(data, 'RGBA')
