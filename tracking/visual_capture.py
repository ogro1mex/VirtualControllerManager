"""Visual capture module for accessing camera feeds."""
import cv2
import logging
import threading
import numpy as np
from typing import Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CaptureConfig:
    """Configuration for visual capture."""
    camera_index: int = 0
    width: int = 1280
    height: int = 720
    fps: int = 30
    flip_horizontal: bool = False
    flip_vertical: bool = False


class VisualCapture:
    """Captures video from camera feeds."""

    def __init__(self, config: Optional[CaptureConfig] = None):
        """Initialize visual capture.
        
        Args:
            config: Capture configuration
        """
        self.config = config or CaptureConfig()
        self.cap: Optional[cv2.VideoCapture] = None
        self.running = False
        self.capture_thread: Optional[threading.Thread] = None
        self.frame_callback: Optional[Callable] = None
        self.current_frame: Optional[np.ndarray] = None
        self.frame_count = 0

    def start(self) -> bool:
        """Start capturing video.
        
        Returns:
            True if successful, False otherwise
        """
        if self.running:
            return True

        try:
            self.cap = cv2.VideoCapture(self.config.camera_index)
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera {self.config.camera_index}")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.config.fps)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer
            
            self.running = True
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
            logger.info(f"Camera {self.config.camera_index} started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting camera: {e}")
            return False

    def stop(self):
        """Stop capturing video."""
        self.running = False
        
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        logger.info("Camera capture stopped")

    def _capture_loop(self):
        """Main capture loop."""
        while self.running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            
            if not ret:
                logger.warning("Failed to read frame from camera")
                continue
            
            # Apply flips if configured
            if self.config.flip_horizontal:
                frame = cv2.flip(frame, 1)
            if self.config.flip_vertical:
                frame = cv2.flip(frame, 0)
            
            self.current_frame = frame
            self.frame_count += 1
            
            if self.frame_callback:
                try:
                    self.frame_callback(frame)
                except Exception as e:
                    logger.error(f"Error in frame callback: {e}")

    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get the current frame.
        
        Returns:
            Current frame or None if not available
        """
        return self.current_frame

    def get_frame_info(self) -> dict:
        """Get information about the current frame.
        
        Returns:
            Dictionary with frame information
        """
        if self.current_frame is None:
            return {}
        
        return {
            "height": self.current_frame.shape[0],
            "width": self.current_frame.shape[1],
            "channels": self.current_frame.shape[2] if len(self.current_frame.shape) > 2 else 1,
            "frame_count": self.frame_count,
        }

    def set_frame_callback(self, callback: Callable[[np.ndarray], None]):
        """Set a callback for frame updates.
        
        Args:
            callback: Function to call with each frame
        """
        self.frame_callback = callback

    def is_running(self) -> bool:
        """Check if capture is running.
        
        Returns:
            True if running, False otherwise
        """
        return self.running and self.cap is not None and self.cap.isOpened()

    def list_available_cameras(self) -> list:
        """List available camera devices.
        
        Returns:
            List of available camera indices
        """
        available_cameras = []
        
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append(i)
                cap.release()
        
        return available_cameras
