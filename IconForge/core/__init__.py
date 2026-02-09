"""
Core __init__ file for icon-factory core modules.
"""

from .image_processor import ImageProcessor
from .cropping import AutoCropper
from .masking import MaskingEngine
from .export import IconExporter
from .edge_processing import EdgeProcessor
from .border_masking import BorderMasking
from .composition import CompositionEngine

__all__ = ['ImageProcessor', 'AutoCropper', 'MaskingEngine', 'IconExporter', 'EdgeProcessor', 'BorderMasking', 'CompositionEngine']
