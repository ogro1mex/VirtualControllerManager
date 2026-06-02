"""Macro engine for recording and executing button sequences."""
import logging
import threading
import time
from typing import List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of macro actions."""
    BUTTON_PRESS = "button_press"
    BUTTON_RELEASE = "button_release"
    STICK_MOVE = "stick_move"
    TRIGGER_PRESS = "trigger_press"
    DPAD_PRESS = "dpad_press"
    DELAY = "delay"
    REPEAT = "repeat"


@dataclass
class MacroAction:
    """A single action in a macro sequence."""
    action_type: ActionType
    value: any = None
    duration: float = 0.0  # For delays
    
    def to_dict(self):
        return {
            "action_type": self.action_type.value,
            "value": self.value,
            "duration": self.duration
        }
    
    @staticmethod
    def from_dict(data: dict):
        return MacroAction(
            action_type=ActionType(data["action_type"]),
            value=data.get("value"),
            duration=data.get("duration", 0.0)
        )


@dataclass
class Macro:
    """A macro sequence of actions."""
    name: str
    actions: List[MacroAction] = field(default_factory=list)
    trigger_button: Optional[str] = None  # Button that triggers this macro
    loop: bool = False
    
    def add_action(self, action: MacroAction):
        """Add an action to the macro.
        
        Args:
            action: The action to add
        """
        self.actions.append(action)
    
    def to_dict(self):
        return {
            "name": self.name,
            "actions": [a.to_dict() for a in self.actions],
            "trigger_button": self.trigger_button,
            "loop": self.loop
        }
    
    @staticmethod
    def from_dict(data: dict):
        macro = Macro(
            name=data["name"],
            trigger_button=data.get("trigger_button"),
            loop=data.get("loop", False)
        )
        macro.actions = [MacroAction.from_dict(a) for a in data.get("actions", [])]
        return macro


class MacroEngine:
    """Engine for managing and executing macros."""

    def __init__(self, max_macro_length: int = 100):
        """Initialize macro engine.
        
        Args:
            max_macro_length: Maximum number of actions per macro
        """
        self.macros: dict[str, Macro] = {}
        self.max_macro_length = max_macro_length
        self.recording = False
        self.current_recording: Optional[Macro] = None
        self.recording_start_time = 0.0
        self.executing_macros: set[str] = set()
        self.execution_threads: dict[str, threading.Thread] = {}
        self.execute_callback: Optional[Callable] = None
        self.should_stop_macro: dict[str, bool] = {}

    def start_recording(self, macro_name: str, trigger_button: Optional[str] = None):
        """Start recording a macro sequence.
        
        Args:
            macro_name: Name for the macro
            trigger_button: Optional button that triggers this macro
        """
        if self.recording:
            logger.warning("Already recording a macro")
            return
        
        self.recording = True
        self.current_recording = Macro(name=macro_name, trigger_button=trigger_button)
        self.recording_start_time = time.time()
        logger.info(f"Started recording macro: {macro_name}")

    def stop_recording(self) -> Optional[Macro]:
        """Stop recording and save the macro.
        
        Returns:
            The recorded macro or None if nothing was recorded
        """
        if not self.recording:
            return None
        
        self.recording = False
        macro = self.current_recording
        self.current_recording = None
        
        if macro and len(macro.actions) > 0:
            self.macros[macro.name] = macro
            logger.info(f"Recorded macro: {macro.name} with {len(macro.actions)} actions")
            return macro
        
        return None

    def add_action_to_recording(self, action: MacroAction):
        """Add an action to the current recording.
        
        Args:
            action: The action to add
        """
        if not self.recording or not self.current_recording:
            return
        
        if len(self.current_recording.actions) >= self.max_macro_length:
            logger.warning(f"Macro length limit reached ({self.max_macro_length})")
            return
        
        self.current_recording.add_action(action)

    def add_macro(self, macro: Macro) -> bool:
        """Add a macro to the engine.
        
        Args:
            macro: The macro to add
            
        Returns:
            True if added successfully, False otherwise
        """
        if len(macro.actions) > self.max_macro_length:
            logger.error(f"Macro exceeds maximum length ({self.max_macro_length})")
            return False
        
        self.macros[macro.name] = macro
        logger.info(f"Macro added: {macro.name}")
        return True

    def remove_macro(self, macro_name: str) -> bool:
        """Remove a macro from the engine.
        
        Args:
            macro_name: Name of the macro to remove
            
        Returns:
            True if removed, False if not found
        """
        if macro_name in self.macros:
            del self.macros[macro_name]
            logger.info(f"Macro removed: {macro_name}")
            return True
        return False

    def get_macro(self, macro_name: str) -> Optional[Macro]:
        """Get a macro by name.
        
        Args:
            macro_name: Name of the macro
            
        Returns:
            The macro or None if not found
        """
        return self.macros.get(macro_name)

    def list_macros(self) -> List[str]:
        """Get list of all macro names.
        
        Returns:
            List of macro names
        """
        return list(self.macros.keys())

    def execute_macro(self, macro_name: str):
        """Execute a macro sequence.
        
        Args:
            macro_name: Name of the macro to execute
        """
        macro = self.get_macro(macro_name)
        if not macro:
            logger.error(f"Macro not found: {macro_name}")
            return
        
        if macro_name in self.executing_macros:
            logger.warning(f"Macro already executing: {macro_name}")
            return
        
        self.should_stop_macro[macro_name] = False
        
        # Stop any existing thread for this macro
        if macro_name in self.execution_threads:
            thread = self.execution_threads[macro_name]
            if thread.is_alive():
                self.should_stop_macro[macro_name] = True
                thread.join(timeout=2.0)
        
        # Start new execution thread
        thread = threading.Thread(
            target=self._execute_macro_thread,
            args=(macro,),
            daemon=True
        )
        self.execution_threads[macro_name] = thread
        thread.start()

    def _execute_macro_thread(self, macro: Macro):
        """Execute macro in a separate thread.
        
        Args:
            macro: The macro to execute
        """
        macro_name = macro.name
        
        try:
            self.executing_macros.add(macro_name)
            
            loop_count = 0
            while True:
                for action in macro.actions:
                    if self.should_stop_macro.get(macro_name, False):
                        break
                    
                    if self.execute_callback:
                        self.execute_callback(action)
                    
                    # Add delay for timing
                    if action.action_type == ActionType.DELAY:
                        time.sleep(action.duration)
                    else:
                        time.sleep(0.01)  # Small delay between actions
                
                if not macro.loop or self.should_stop_macro.get(macro_name, False):
                    break
                
                loop_count += 1
            
            logger.info(f"Macro executed: {macro_name} (loops: {loop_count})")
            
        except Exception as e:
            logger.error(f"Error executing macro: {e}")
        finally:
            self.executing_macros.discard(macro_name)

    def stop_macro(self, macro_name: str):
        """Stop execution of a macro.
        
        Args:
            macro_name: Name of the macro to stop
        """
        if macro_name in self.executing_macros:
            self.should_stop_macro[macro_name] = True
            logger.info(f"Macro stop requested: {macro_name}")

    def stop_all_macros(self):
        """Stop all executing macros."""
        for macro_name in list(self.executing_macros):
            self.stop_macro(macro_name)

    def set_execute_callback(self, callback: Callable[[MacroAction], None]):
        """Set callback for macro action execution.
        
        Args:
            callback: Function to call with each macro action
        """
        self.execute_callback = callback

    def save_macros(self, filepath: str):
        """Save all macros to a JSON file.
        
        Args:
            filepath: Path to save the macros to
        """
        try:
            data = {"macros": [m.to_dict() for m in self.macros.values()]}
            
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Macros saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving macros: {e}")

    def load_macros(self, filepath: str) -> bool:
        """Load macros from a JSON file.
        
        Args:
            filepath: Path to load the macros from
            
        Returns:
            True if successful, False otherwise
        """
        try:
            path = Path(filepath)
            
            if not path.exists():
                logger.warning(f"Macros file not found: {filepath}")
                return False
            
            with open(path, 'r') as f:
                data = json.load(f)
            
            self.macros = {}
            for macro_data in data.get("macros", []):
                macro = Macro.from_dict(macro_data)
                self.macros[macro.name] = macro
            
            logger.info(f"Loaded {len(self.macros)} macros from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error loading macros: {e}")
            return False
