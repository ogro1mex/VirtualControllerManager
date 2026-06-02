"""Macros Tab - Macro Recording and Execution."""
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QGroupBox, QCheckBox, QSpinBox, QGridLayout,
    QLineEdit, QListWidget, QListWidgetItem, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from ...macros.macro_engine import MacroEngine, Macro, MacroAction, ActionType

logger = logging.getLogger(__name__)


class MacrosTab(QWidget):
    """Tab for macro management."""
    
    macro_executed = pyqtSignal(str)

    def __init__(self, app_context):
        """Initialize macros tab."""
        super().__init__()
        self.app_context = app_context
        self.macro_engine = MacroEngine()
        
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        
        # Recording Section
        record_group = QGroupBox("Macro Recording")
        record_layout = QGridLayout()
        
        record_layout.addWidget(QLabel("Macro Name:"), 0, 0)
        self.macro_name_input = QLineEdit()
        self.macro_name_input.setPlaceholderText("Enter macro name")
        record_layout.addWidget(self.macro_name_input, 0, 1)
        
        record_layout.addWidget(QLabel("Trigger Button:"), 1, 0)
        self.trigger_button_combo = QComboBox()
        self.trigger_button_combo.addItems(["None", "A", "B", "X", "Y", "LB", "RB", "Start", "Back"])
        record_layout.addWidget(self.trigger_button_combo, 1, 1)
        
        self.record_toggle_btn = QPushButton("● Start Recording")
        self.record_toggle_btn.setObjectName("greenButton")
        self.record_toggle_btn.clicked.connect(self._toggle_recording)
        record_layout.addWidget(self.record_toggle_btn, 2, 0, 1, 2)
        
        record_group.setLayout(record_layout)
        layout.addWidget(record_group)
        
        # Macros List
        list_group = QGroupBox("Recorded Macros")
        list_layout = QVBoxLayout()
        
        self.macros_list = QListWidget()
        list_layout.addWidget(self.macros_list)
        
        button_layout = QHBoxLayout()
        
        self.execute_btn = QPushButton("▶ Execute")
        self.execute_btn.clicked.connect(self._execute_selected)
        button_layout.addWidget(self.execute_btn)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self._stop_macro)
        button_layout.addWidget(self.stop_btn)
        
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.clicked.connect(self._delete_selected)
        button_layout.addWidget(delete_btn)
        
        list_layout.addLayout(button_layout)
        
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        # Settings
        settings_group = QGroupBox("Macro Settings")
        settings_layout = QGridLayout()
        
        settings_layout.addWidget(QLabel("Max Macro Length:"), 0, 0)
        self.max_length_spin = QSpinBox()
        self.max_length_spin.setMinimum(10)
        self.max_length_spin.setMaximum(500)
        self.max_length_spin.setValue(100)
        settings_layout.addWidget(self.max_length_spin, 0, 1)
        
        self.auto_trigger_check = QCheckBox("Auto-trigger on button press")
        settings_layout.addWidget(self.auto_trigger_check, 1, 0, 1, 2)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        
        self._refresh_macro_list()

    def _connect_signals(self):
        """Connect signals."""
        self.macro_executed.connect(self._on_macro_executed)

    def _toggle_recording(self):
        """Toggle macro recording."""
        if self.macro_engine.recording:
            macro = self.macro_engine.stop_recording()
            if macro:
                self._refresh_macro_list()
                QMessageBox.information(self, "Success", f"Macro '{macro.name}' recorded with {len(macro.actions)} actions")
            
            self.record_toggle_btn.setText("● Start Recording")
            self.record_toggle_btn.setObjectName("greenButton")
        else:
            macro_name = self.macro_name_input.text().strip()
            if not macro_name:
                QMessageBox.warning(self, "Error", "Please enter a macro name")
                return
            
            trigger_btn = self.trigger_button_combo.currentText()
            trigger_btn = None if trigger_btn == "None" else trigger_btn
            
            self.macro_engine.start_recording(macro_name, trigger_btn)
            
            self.record_toggle_btn.setText("⏺️ Stop Recording")
            self.record_toggle_btn.setObjectName("redButton")
        
        self.record_toggle_btn.style().polish(self.record_toggle_btn)

    def _execute_selected(self):
        """Execute selected macro."""
        current_item = self.macros_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "Please select a macro")
            return
        
        macro_name = current_item.text()
        self.macro_engine.execute_macro(macro_name)
        self.macro_executed.emit(macro_name)

    def _stop_macro(self):
        """Stop all macros."""
        self.macro_engine.stop_all_macros()

    def _delete_selected(self):
        """Delete selected macro."""
        current_item = self.macros_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "Please select a macro")
            return
        
        macro_name = current_item.text()
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete macro '{macro_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.macro_engine.remove_macro(macro_name)
            self._refresh_macro_list()

    def _refresh_macro_list(self):
        """Refresh macros list."""
        self.macros_list.clear()
        for macro_name in self.macro_engine.list_macros():
            macro = self.macro_engine.get_macro(macro_name)
            actions_count = len(macro.actions) if macro else 0
            item_text = f"{macro_name} ({actions_count} actions)"
            self.macros_list.addItem(item_text)

    def _on_macro_executed(self, macro_name: str):
        """Handle macro executed."""
        logger.info(f"Macro executed: {macro_name}")

    def shutdown(self):
        """Shutdown."""
        self.macro_engine.stop_all_macros()
