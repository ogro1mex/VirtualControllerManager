"""Tracking Tab - Visual Object Detection and Tracking."""
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel,
    QGroupBox, QCheckBox, QSpinBox, QDoubleSpinBox, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
import numpy as np

from ...tracking.visual_capture import VisualCapture, CaptureConfig
from ...tracking.object_tracker import ObjectTracker, TrackerConfig, Detection

logger = logging.getLogger(__name__)


class TrackingTab(QWidget):
    """Tab for visual tracking."""
    
    target_updated = pyqtSignal(tuple)

    def __init__(self, app_context):
        """Initialize tracking tab."""
        super().__init__()
        self.app_context = app_context
        self.visual_capture = None
        self.object_tracker = None
        self.tracking_enabled = False
        
        self._setup_ui()
        self._init_tracking()

    def _setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        
        # Camera Configuration
        camera_group = QGroupBox("Camera Configuration")
        camera_layout = QGridLayout()
        
        camera_layout.addWidget(QLabel("Camera:"), 0, 0)
        self.camera_combo = QComboBox()
        self.camera_combo.addItems(["Camera 0", "Camera 1", "Camera 2"])
        camera_layout.addWidget(self.camera_combo, 0, 1)
        
        camera_layout.addWidget(QLabel("Resolution:"), 1, 0)
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["640x480", "1280x720", "1920x1080"])
        self.resolution_combo.setCurrentText("1280x720")
        camera_layout.addWidget(self.resolution_combo, 1, 1)
        
        camera_layout.addWidget(QLabel("FPS:"), 2, 0)
        self.fps_spin = QSpinBox()
        self.fps_spin.setMinimum(15)
        self.fps_spin.setMaximum(60)
        self.fps_spin.setValue(30)
        camera_layout.addWidget(self.fps_spin, 2, 1)
        
        camera_group.setLayout(camera_layout)
        layout.addWidget(camera_group)
        
        # Tracking Configuration
        tracking_group = QGroupBox("Tracking Configuration")
        tracking_layout = QGridLayout()
        
        self.tracking_toggle_btn = QPushButton("▶ Start Tracking")
        self.tracking_toggle_btn.setObjectName("greenButton")
        self.tracking_toggle_btn.clicked.connect(self._toggle_tracking)
        tracking_layout.addWidget(self.tracking_toggle_btn, 0, 0, 1, 2)
        
        tracking_layout.addWidget(QLabel("Track Object:"), 1, 0)
        self.target_class_combo = QComboBox()
        self.target_class_combo.addItems(["person", "car", "dog", "cat"])
        tracking_layout.addWidget(self.target_class_combo, 1, 1)
        
        tracking_layout.addWidget(QLabel("Confidence:"), 2, 0)
        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setMinimum(0.1)
        self.confidence_spin.setMaximum(1.0)
        self.confidence_spin.setValue(0.5)
        tracking_layout.addWidget(self.confidence_spin, 2, 1)
        
        self.persistent_check = QCheckBox("Persistent Tracking")
        self.persistent_check.setChecked(True)
        tracking_layout.addWidget(self.persistent_check, 3, 0, 1, 2)
        
        self.aim_assist_check = QCheckBox("Aim Assist to Right Stick")
        self.aim_assist_check.setChecked(True)
        tracking_layout.addWidget(self.aim_assist_check, 4, 0, 1, 2)
        
        tracking_group.setLayout(tracking_layout)
        layout.addWidget(tracking_group)
        
        # Detection Info
        display_group = QGroupBox("Detection Info")
        display_layout = QVBoxLayout()
        
        self.detection_label = QLabel(
            "Detections: 0\n"
            "Target: None\n"
            "Position: (--, --)\n"
            "Confidence: --%"
        )
        self.detection_label.setStyleSheet("font-family: monospace; background-color: #2d2d2d; padding: 10px;")
        display_layout.addWidget(self.detection_label)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        layout.addStretch()

    def _init_tracking(self):
        """Initialize tracking."""
        try:
            capture_config = CaptureConfig(
                camera_index=0,
                width=1280,
                height=720,
                fps=30
            )
            self.visual_capture = VisualCapture(capture_config)
            
            tracker_config = TrackerConfig(
                model_path="models/yolov8_320x320.onnx",
                confidence_threshold=0.5
            )
            self.object_tracker = ObjectTracker(tracker_config)
        except Exception as e:
            logger.error(f"Error initializing tracking: {e}")

    def _toggle_tracking(self):
        """Toggle tracking."""
        if self.tracking_enabled:
            self._stop_tracking()
        else:
            self._start_tracking()

    def _start_tracking(self):
        """Start tracking."""
        if not self.visual_capture or not self.object_tracker:
            logger.error("Tracking not initialized")
            return
        
        res_text = self.resolution_combo.currentText()
        width, height = map(int, res_text.split('x'))
        
        self.visual_capture.config.width = width
        self.visual_capture.config.height = height
        self.visual_capture.config.fps = self.fps_spin.value()
        
        if self.visual_capture.start():
            self.tracking_enabled = True
            self.tracking_toggle_btn.setText("⏹ Stop Tracking")
            logger.info("Tracking started")

    def _stop_tracking(self):
        """Stop tracking."""
        if self.visual_capture:
            self.visual_capture.stop()
        
        self.tracking_enabled = False
        self.tracking_toggle_btn.setText("▶ Start Tracking")
        logger.info("Tracking stopped")

    def shutdown(self):
        """Shutdown."""
        self._stop_tracking()
        if self.object_tracker:
            self.object_tracker.shutdown()
