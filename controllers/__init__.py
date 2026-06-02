"""Controllers module for managing physical and virtual game controllers."""
from .input_detector import InputDetector
from .virtual_xbox import VirtualXbox360

__all__ = ['InputDetector', 'VirtualXbox360']
