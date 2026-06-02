"""Object tracking module using ONNX models."""
import logging
import cv2
import numpy as np
import threading
from typing import Optional, List, Tuple, Callable
from dataclasses import dataclass
from pathlib import Path

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    logging.warning("onnxruntime not available")

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """A detected object."""
    class_id: int
    class_name: str
    confidence: float
    x: float
    y: float
    width: float
    height: float
    center_x: float = 0.0
    center_y: float = 0.0
    
    def __post_init__(self):
        self.center_x = self.x + self.width / 2
        self.center_y = self.y + self.height / 2


@dataclass
class TrackerConfig:
    """Configuration for object tracker."""
    model_path: str = "models/yolov8_320x320.onnx"
    input_size: int = 320
    confidence_threshold: float = 0.5
    iou_threshold: float = 0.45
    enable_cuda: bool = True


class ObjectTracker:
    """Tracks objects in video frames using ONNX models."""

    def __init__(self, config: Optional[TrackerConfig] = None):
        """Initialize object tracker.
        
        Args:
            config: Tracker configuration
        """
        if not ONNX_AVAILABLE:
            logger.error("onnxruntime not available")
            self.session = None
            return

        self.config = config or TrackerConfig()
        self.session: Optional[ort.InferenceSession] = None
        self.input_name: Optional[str] = None
        self.output_names: List[str] = []
        self.class_names: List[str] = []
        self.detections: List[Detection] = []
        self.tracking_enabled = False
        self.target_object: Optional[Detection] = None
        self.tracking_callback: Optional[Callable] = None
        
        self._load_model()

    def _load_model(self):
        """Load the ONNX model."""
        try:
            model_path = Path(self.config.model_path)
            
            if not model_path.exists():
                logger.error(f"Model file not found: {model_path}")
                return
            
            providers = [
                'CUDAExecutionProvider' if self.config.enable_cuda else None,
                'CPUExecutionProvider'
            ]
            providers = [p for p in providers if p is not None]
            
            self.session = ort.InferenceSession(
                str(model_path),
                providers=providers
            )
            
            # Get input/output information
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [output.name for output in self.session.get_outputs()]
            
            # Default class names (customize for your model)
            self.class_names = self._get_class_names()
            
            logger.info(f"Model loaded successfully: {model_path}")
            logger.info(f"Input: {self.input_name}")
            logger.info(f"Outputs: {self.output_names}")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.session = None

    def _get_class_names(self) -> List[str]:
        """Get class names for the model.
        
        Returns:
            List of class names
        """
        # COCO classes (80 classes) - customize for your model
        coco_classes = [
            'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck',
            'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
            'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe',
            'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis',
            'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
            'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
            'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
            'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
            'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
            'remote', 'keyboard', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator',
            'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
        ]
        return coco_classes

    def is_ready(self) -> bool:
        """Check if tracker is ready to use.
        
        Returns:
            True if model is loaded, False otherwise
        """
        return self.session is not None

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """Detect objects in a frame.
        
        Args:
            frame: Input frame (BGR format)
            
        Returns:
            List of detections
        """
        if not self.is_ready():
            return []
        
        try:
            # Prepare input
            input_tensor = self._prepare_input(frame)
            
            # Run inference
            outputs = self.session.run(self.output_names, {self.input_name: input_tensor})
            
            # Parse outputs
            self.detections = self._parse_output(outputs, frame.shape)
            
            return self.detections
            
        except Exception as e:
            logger.error(f"Error during detection: {e}")
            return []

    def _prepare_input(self, frame: np.ndarray) -> np.ndarray:
        """Prepare frame for model input.
        
        Args:
            frame: Input frame
            
        Returns:
            Preprocessed tensor
        """
        # Resize to model input size
        img = cv2.resize(frame, (self.config.input_size, self.config.input_size))
        
        # Convert BGR to RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Normalize to 0-1
        img = img.astype(np.float32) / 255.0
        
        # Add batch dimension
        img = np.expand_dims(img, axis=0)
        
        # Transpose to CHW format if needed
        if img.shape[-1] == 3:
            img = np.transpose(img, (0, 3, 1, 2))
        
        return img

    def _parse_output(self, outputs: List[np.ndarray], frame_shape: Tuple) -> List[Detection]:
        """Parse model outputs into detections.
        
        Args:
            outputs: Model output arrays
            frame_shape: Original frame shape
            
        Returns:
            List of detections
        """
        detections = []
        frame_height, frame_width = frame_shape[:2]
        
        try:
            # Assuming output format: [N, 85] for YOLO (x, y, w, h, conf, class_probs)
            output = outputs[0]
            
            if output.ndim == 3:
                output = output[0]
            
            for detection in output:
                confidence = float(detection[4])
                
                if confidence < self.config.confidence_threshold:
                    continue
                
                # Get class with highest probability
                class_scores = detection[5:]
                class_id = int(np.argmax(class_scores))
                class_confidence = float(class_scores[class_id])
                
                if class_confidence < self.config.confidence_threshold:
                    continue
                
                # Get bounding box (YOLO format: center_x, center_y, width, height)
                x_center = float(detection[0]) * frame_width
                y_center = float(detection[1]) * frame_height
                width = float(detection[2]) * frame_width
                height = float(detection[3]) * frame_height
                
                x = x_center - width / 2
                y = y_center - height / 2
                
                detection_obj = Detection(
                    class_id=class_id,
                    class_name=self.class_names[class_id] if class_id < len(self.class_names) else "Unknown",
                    confidence=class_confidence,
                    x=x,
                    y=y,
                    width=width,
                    height=height
                )
                
                detections.append(detection_obj)
        
        except Exception as e:
            logger.error(f"Error parsing output: {e}")
        
        return detections

    def track_object(self, class_name: str = None, class_id: int = None) -> Optional[Detection]:
        """Track a specific object type.
        
        Args:
            class_name: Name of class to track
            class_id: ID of class to track
            
        Returns:
            The best detection match or None
        """
        if not self.detections:
            self.target_object = None
            return None
        
        # Filter detections
        matches = self.detections
        
        if class_name:
            matches = [d for d in matches if d.class_name.lower() == class_name.lower()]
        elif class_id is not None:
            matches = [d for d in matches if d.class_id == class_id]
        
        if not matches:
            self.target_object = None
            return None
        
        # Get detection with highest confidence
        target = max(matches, key=lambda d: d.confidence)
        self.target_object = target
        
        if self.tracking_callback:
            self.tracking_callback(target)
        
        return target

    def get_center_offset(self, frame_width: int, frame_height: int) -> Tuple[float, float]:
        """Get offset from frame center to target center.
        
        Args:
            frame_width: Width of the frame
            frame_height: Height of the frame
            
        Returns:
            (offset_x, offset_y) normalized to -1.0 to 1.0
        """
        if not self.target_object:
            return (0.0, 0.0)
        
        center_x = frame_width / 2
        center_y = frame_height / 2
        
        offset_x = (self.target_object.center_x - center_x) / (frame_width / 2)
        offset_y = (self.target_object.center_y - center_y) / (frame_height / 2)
        
        # Clamp to -1.0 to 1.0
        offset_x = max(-1.0, min(1.0, offset_x))
        offset_y = max(-1.0, min(1.0, offset_y))
        
        return (offset_x, offset_y)

    def set_tracking_callback(self, callback: Callable[[Detection], None]):
        """Set callback for tracking updates.
        
        Args:
            callback: Function to call with detected target
        """
        self.tracking_callback = callback

    def shutdown(self):
        """Shutdown the tracker."""
        if self.session:
            del self.session
            self.session = None
        logger.info("Object tracker shutdown")
