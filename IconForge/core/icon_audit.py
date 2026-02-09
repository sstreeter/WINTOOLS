"""
Icon Auditor module.
Analyzes icons for design flaws and quality issues.
Provides a 'report card' with actionable fixes.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
from PIL import Image, ImageStat
import numpy as np
from enum import Enum

class IssueSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    PASS = "pass"

@dataclass
class AuditIssue:
    check_name: str
    severity: IssueSeverity
    message: str
    fix_available: bool = False
    fix_action: str = ""

class IconAuditor:
    """Analyzes icon quality and visual integrity."""
    
    @staticmethod
    def audit_image(image: Image.Image) -> List[AuditIssue]:
        """Run comprehensive audit on an image."""
        issues = []
        
        # Ensure RGBA
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
            
        width, height = image.size
        
        # 1. Resolution Check
        if width != height:
            issues.append(AuditIssue(
                "Aspect Ratio", 
                IssueSeverity.ERROR, 
                f"Image is not square ({width}x{height}). Icons must be square.",
                fix_available=True,
                fix_action="crop_square"
            ))
        else:
            issues.append(AuditIssue("Aspect Ratio", IssueSeverity.PASS, "Image is square"))
            
        if width < 512:
             issues.append(AuditIssue(
                "Resolution", 
                IssueSeverity.WARNING, 
                f"Resolution is low ({width}px). Recommended: 1024px for best quality.",
                fix_available=False
            ))
        else:
            issues.append(AuditIssue("Resolution", IssueSeverity.PASS, f"High resolution ({width}px)"))

        # 2. Alpha/Edge Analysis
        alpha = np.array(image.split()[3])
        
        # Check if fully opaque
        if np.min(alpha) == 255:
            issues.append(AuditIssue(
                "Transparency",
                IssueSeverity.INFO,
                "Image is fully opaque. Use 'Masking Options' to remove background if this is a logo/icon.",
                fix_available=False
            ))
        elif np.std(alpha) > 0: # If not fully opaque/transparent
            # Check for hard, aliased edges (binary alpha transitions without smoothing)
            # Count pixels with intermediate alpha (1-254)
            intermediate_pixels = np.sum((alpha > 0) & (alpha < 255))
            total_edge_pixels = np.sum(alpha > 0)
            
            smoothing_ratio = intermediate_pixels / total_edge_pixels if total_edge_pixels > 0 else 0
            
            if smoothing_ratio < 0.01: # Less than 1% smoothing - likely aliased
                issues.append(AuditIssue(
                    "Edge Quality",
                    IssueSeverity.ERROR,
                    "Edges appear jagged/aliased (pixelated).",
                    fix_available=True,
                    fix_action="smart_cleanup"
                ))
            elif smoothing_ratio > 0.2: # Too much smoothing - blurry
                 issues.append(AuditIssue(
                    "Edge Quality",
                    IssueSeverity.WARNING,
                    "Edges appear blurry/soft.",
                    fix_available=True,
                    fix_action="sharpen"
                ))
            else:
                 issues.append(AuditIssue("Edge Quality", IssueSeverity.PASS, "Edges look smooth and clean"))
        
        # 3. Contrast / "Dirty Pixel" Check
        # Check for very faint pixels (alpha < 10) that are effectively invisible but dirty
        dirty_pixels = np.sum((alpha > 0) & (alpha < 10))
        if dirty_pixels > 10:
             issues.append(AuditIssue(
                "Cleanliness",
                IssueSeverity.WARNING,
                f"Found {dirty_pixels} stray/dirty pixels.",
                fix_available=True,
                fix_action="clean_debris"
            ))
        else:
             issues.append(AuditIssue("Cleanliness", IssueSeverity.PASS, "No dirty pixels detected"))
             
        return issues
