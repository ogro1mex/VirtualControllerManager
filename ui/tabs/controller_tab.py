"""Controller Tab - Physical and Virtual Controller Management."""
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QGroupBox, QCheckBox, QSpinBox, QDoubleSpinBox,
    QComboBox, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from ...controllers.input_detector import InputDetector, ControllerState
from ...controllers.virtual_xbox import VirtualXbox360, VirtualControllerConfig

logger = logging.getLogger(__name__)


class ControllerTab(QWidget):
    """Tab for managing controllers."""
    
    controller_connected = pyqtSignal(int, str)
    controller_disconnected = pyqtSignal(int, str)

    def __init__(self, app_context):
        """Initialize controller tab."""
        super().__init__()
        self.app_context = app_context
        self.input_detector = None
        self.virtual_xbox = None
        
        self._setup_ui()
        self._init_controllers()

    def _setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        
        # Physical Controllers
        physical_group = QGroupBox("Physical Controllers")
        physical_layout = QVBoxLayout()
        
        self.controllers_table = QTableWidget()
        self.controllers_table.setColumnCount(4)
        self.controllers_table.setHorizontalHeaderLabels(["ID", "Name", "Type", "Status"])
        self.controllers_table.setMaximumHeight(200)
        physical_layout.addWidget(self.controllers_table)
        
        refresh_btn = QPushButton("🔄 Refresh Controllers")
        refresh_btn.clicked.connect(self._refresh_controllers)
        physical_layout.addWidget(refresh_btn)
        
        physical_group.setLayout(physical_layout)
        layout.addWidget(physical_group)
        
        # Virtual Controller
        virtual_group = QGroupBox("Virtual Xbox360 Controller")
        virtual_layout = QGridLayout()
        
        virtual_layout.addWidget(QLabel("Status:"), 0, 0)
        self.virtual_status_label = QLabel("❌ Disconnected")
        virtual_layout.addWidget(self.virtual_status_label, 0, 1)
        
        self.virtual_toggle_btn = QPushButton("🎮 Enable Virtual Controller")
        self.virtual_toggle_btn.setObjectName("greenButton")
        self.virtual_toggle_btn.clicked.connect(self._toggle_virtual_controller)
        virtual_layout.addWidget(self.virtual_toggle_btn, 1, 0, 1, 2)
        
        virtual_group.setLayout(virtual_layout)
        layout.addWidget(virtual_group)
        
        # Settings
        settings_group = QGroupBox("Input Configuration")
        settings_layout = QGridLayout()
        
        settings_layout.addWidget(QLabel("Dead Zone:"), 0, 0)
        self.dead_zone_spin = QDoubleSpinBox()
        self.dead_zone_spin.setMinimum(0.0)
        self.dead_zone_spin.setMaximum(1.0)
        self.dead_zone_spin.setValue(0.15)
        settings_layout.addWidget(self.dead_zone_spin, 0, 1)
        
        self.mirror_input_check = QCheckBox("Mirror Input to Virtual Controller")
        settings_layout.addWidget(self.mirror_input_check, 1, 0, 1, 2)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Input Display
        display_group = QGroupBox("Current Input")
        display_layout = QVBoxLayout()
        
        self.input_display = QLabel("No input")
        self.input_display.setStyleSheet("font-family: monospace; background-color: #2d2d2d; padding: 10px;")
        display_layout.addWidget(self.input_display)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        layout.addStretch()

    def _init_controllers(self):
        """Initialize controllers."""
        try:
            self.input_detector = InputDetector(dead_zone=0.15)
            self.input_detector.set_connection_callback(self._on_connection)
            self.input_detector.set_input_callback(self._on_input)
            self.input_detector.start_polling()
            
            self.virtual_xbox = VirtualXbox360()
            self._refresh_controllers()
        except Exception as e:
            logger.error(f"Error initializing controllers: {e}")

    def _refresh_controllers(self):
        """Refresh controllers list."""
        if not self.input_detector:
            return
        
        controllers = self.input_detector.get_controller_list()
        self.controllers_table.setRowCount(len(controllers))
        
        for row, ctrl in enumerate(controllers):
            self.controllers_table.setItem(row, 0, QTableWidgetItem(str(ctrl['device_id'])))
            self.controllers_table.setItem(row, 1, QTableWidgetItem(ctrl['name']))
            self.controllers_table.setItem(row, 2, QTableWidgetItem(ctrl['type']))
            status_item = QTableWidgetItem("✓ Connected")
            status_item.setForeground(QColor(100, 200, 100))
            self.controllers_table.setItem(row, 3, status_item)

    def _toggle_virtual_controller(self):
        """Toggle virtual controller."""
        if self.virtual_xbox.is_connected():
            self.virtual_xbox.shutdown()
            self.virtual_status_label.setText("❌ Disconnected")
            self.virtual_toggle_btn.setText("🎮 Enable Virtual Controller")
        else:
            self.virtual_xbox = VirtualXbox360()
            if self.virtual_xbox.is_connected():
                self.virtual_status_label.setText("✓ Connected")
                self.virtual_toggle_btn.setText("🎮 Disable Virtual Controller")

    def _on_connection(self, device_id: int, connected: bool, name: str):
        """Handle connection."""
        self._refresh_controllers()

    def _on_input(self, device_id: int, state: ControllerState):
        """Handle input."""
        buttons_text = ", ".join([n for n, p in state.buttons.items() if p]) or "None"
        self.input_display.setText(
            f"Left: ({state.left_stick[0]:.2f}, {state.left_stick[1]:.2f})\n"
            f"Right: ({state.right_stick[0]:.2f}, {state.right_stick[1]:.2f})\n"
            f"Triggers: L={state.left_trigger:.2f} R={state.right_trigger:.2f}\n"
            f"Buttons: {buttons_text}"
        )
        
        if self.mirror_input_check.isChecked() and self.virtual_xbox.is_connected():
            self.virtual_xbox.update_left_stick(state.left_stick[0], state.left_stick[1])
            self.virtual_xbox.update_right_stick(state.right_stick[0], state.right_stick[1])
            self.virtual_xbox.update_triggers(state.left_trigger, state.right_trigger)
            self.virtual_xbox.update()

    def shutdown(self):
        """Shutdown."""
        if self.input_detector:
            self.input_detector.shutdown()
        if self.virtual_xbox:
            self.virtual_xbox.shutdown()
