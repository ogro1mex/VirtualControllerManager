"""Detects and manages physical game controller input."""
import pygame
import threading
import logging
from typing import Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ControllerType(Enum):
    """Types of game controllers supported."""
    XBOX = "xbox"
    PLAYSTATION4 = "ps4"
    PLAYSTATION5 = "ps5"
    SWITCH = "switch"
    GENERIC = "generic"


@dataclass
class ControllerState:
    """Current state of a game controller."""
    left_stick: Tuple[float, float] = (0.0, 0.0)
    right_stick: Tuple[float, float] = (0.0, 0.0)
    left_trigger: float = 0.0
    right_trigger: float = 0.0
    buttons: Dict[str, bool] = None
    dpad: Tuple[int, int] = (0, 0)  # (-1, 0, 1), (-1, 0, 1)

    def __post_init__(self):
        if self.buttons is None:
            self.buttons = {}


class InputDetector:
    """Detects and manages physical game controller input."""

    def __init__(self, dead_zone: float = 0.15):
        """Initialize the input detector."
        
        Args:
            dead_zone: Threshold for stick input to be considered as movement (0.0-1.0)
        """
        pygame.init()
        pygame.joystick.init()
        
        self.dead_zone = dead_zone
        self.controllers: Dict[int, pygame.joystick.Joystick] = {}
        self.controller_states: Dict[int, ControllerState] = {}
        self.controller_names: Dict[int, str] = {}
        self.controller_types: Dict[int, ControllerType] = {}
        
        self.running = False
        self.input_thread: Optional[threading.Thread] = None
        self.input_callback: Optional[Callable] = None
        self.connection_callback: Optional[Callable] = None
        
        self._init_connected_controllers()

    def _init_connected_controllers(self):
        """Initialize all currently connected controllers."""
        for i in range(pygame.joystick.get_count()):
            self._register_controller(i)

    def _register_controller(self, device_id: int):
        """Register a new controller.
        
        Args:
            device_id: The device ID from pygame
        """
        try:
            joystick = pygame.joystick.Joystick(device_id)
            joystick.init()
            
            self.controllers[device_id] = joystick
            self.controller_names[device_id] = joystick.get_name()
            self.controller_types[device_id] = self._detect_controller_type(joystick)
            self.controller_states[device_id] = ControllerState()
            
            logger.info(f"Controller registered: {self.controller_names[device_id]} (Type: {self.controller_types[device_id].value})")
            
            if self.connection_callback:
                self.connection_callback(device_id, True, self.controller_names[device_id])
                
        except Exception as e:
            logger.error(f"Error registering controller {device_id}: {e}")

    def _detect_controller_type(self, joystick: pygame.joystick.Joystick) -> ControllerType:
        """Detect the type of controller based on its properties.
        
        Args:
            joystick: The pygame joystick object
            
        Returns:
            The detected controller type
        """
        name = joystick.get_name().lower()
        
        if "xbox" in name or "x-input" in name:
            return ControllerType.XBOX
        elif "playstation" in name or "ps5" in name or "dualsense" in name:
            return ControllerType.PLAYSTATION5
        elif "ps4" in name or "dualshock4" in name:
            return ControllerType.PLAYSTATION4
        elif "switch" in name or "pro controller" in name:
            return ControllerType.SWITCH
        else:
            return ControllerType.GENERIC

    def start_polling(self):
        """Start polling for controller input."""
        if self.running:
            return
            
        self.running = True
        self.input_thread = threading.Thread(target=self._polling_loop, daemon=True)
        self.input_thread.start()
        logger.info("Input polling started")

    def stop_polling(self):
        """Stop polling for controller input."""
        self.running = False
        if self.input_thread:
            self.input_thread.join(timeout=2.0)
        logger.info("Input polling stopped")

    def _polling_loop(self):
        """Main polling loop for controller input."""
        clock = pygame.time.Clock()
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.JOYDEVICEADDED:
                    self._register_controller(event.device_index)
                elif event.type == pygame.JOYDEVICEREMOVED:
                    self._unregister_controller(event.device_index)
            
            # Update all controller states
            for device_id, joystick in list(self.controllers.items()):
                self.controller_states[device_id] = self._read_controller_state(joystick)
                
                if self.input_callback:
                    self.input_callback(device_id, self.controller_states[device_id])
            
            clock.tick(125)  # 125 Hz polling rate

    def _read_controller_state(self, joystick: pygame.joystick.Joystick) -> ControllerState:
        """Read the current state of a controller.
        
        Args:
            joystick: The pygame joystick object
            
        Returns:
            The current controller state
        """
        state = ControllerState()
        
        # Read analog sticks
        if joystick.get_numaxes() >= 4:
            lx = self._apply_dead_zone(joystick.get_axis(0))
            ly = self._apply_dead_zone(joystick.get_axis(1))
            rx = self._apply_dead_zone(joystick.get_axis(2))
            ry = self._apply_dead_zone(joystick.get_axis(3))
            
            state.left_stick = (lx, ly)
            state.right_stick = (rx, ry)
        
        # Read triggers
        if joystick.get_numaxes() >= 6:
            lt = max(0, joystick.get_axis(4))
            rt = max(0, joystick.get_axis(5))
            state.left_trigger = lt
            state.right_trigger = rt
        
        # Read buttons
        for i in range(joystick.get_numbuttons()):
            button_name = self._get_button_name(i)
            state.buttons[button_name] = joystick.get_button(i)
        
        # Read D-pad
        if joystick.get_numhats() > 0:
            hat = joystick.get_hat(0)
            state.dpad = hat
        
        return state

    def _apply_dead_zone(self, value: float, threshold: float = None) -> float:
        """Apply dead zone to an analog input value.
        
        Args:
            value: The raw input value (-1.0 to 1.0)
            threshold: The dead zone threshold (uses self.dead_zone if None)
            
        Returns:
            The processed value with dead zone applied
        """
        if threshold is None:
            threshold = self.dead_zone
            
        if abs(value) < threshold:
            return 0.0
        
        # Scale the value to 0-1 range after dead zone
        if value > 0:
            return (value - threshold) / (1.0 - threshold)
        else:
            return (value + threshold) / (1.0 - threshold)

    def _get_button_name(self, button_id: int) -> str:
        """Get the name of a button based on its ID.
        
        Args:
            button_id: The button ID
            
        Returns:
            The button name
        """
        button_names = {
            0: "A", 1: "B", 2: "X", 3: "Y",
            4: "LB", 5: "RB",
            6: "Back", 7: "Start",
            8: "LS", 9: "RS",
            10: "Guide"
        }
        return button_names.get(button_id, f"Button_{button_id}")

    def _unregister_controller(self, device_id: int):
        """Unregister a disconnected controller.
        
        Args:
            device_id: The device ID from pygame
        """
        if device_id in self.controllers:
            name = self.controller_names.get(device_id, "Unknown")
            del self.controllers[device_id]
            del self.controller_states[device_id]
            del self.controller_names[device_id]
            del self.controller_types[device_id]
            
            logger.info(f"Controller disconnected: {name}")
            
            if self.connection_callback:
                self.connection_callback(device_id, False, name)

    def set_input_callback(self, callback: Callable[[int, ControllerState], None]):
        """Set a callback function for controller input events.
        
        Args:
            callback: Function that receives (device_id, controller_state)
        """
        self.input_callback = callback

    def set_connection_callback(self, callback: Callable[[int, bool, str], None]):
        """Set a callback function for controller connection/disconnection events.
        
        Args:
            callback: Function that receives (device_id, connected, name)
        """
        self.connection_callback = callback

    def get_controller_list(self) -> List[Dict]:
        """Get a list of connected controllers.
        
        Returns:
            List of controller information dictionaries
        """
        return [
            {
                "device_id": device_id,
                "name": self.controller_names[device_id],
                "type": self.controller_types[device_id].value,
                "state": self.controller_states[device_id]
            }
            for device_id in self.controllers.keys()
        ]

    def get_controller_state(self, device_id: int) -> Optional[ControllerState]:
        """Get the current state of a specific controller.
        
        Args:
            device_id: The device ID
            
        Returns:
            The controller state or None if device not found
        """
        return self.controller_states.get(device_id)

    def shutdown(self):
        """Shutdown the input detector and clean up resources."""
        self.stop_polling()
        pygame.quit()
        logger.info("Input detector shutdown complete")
