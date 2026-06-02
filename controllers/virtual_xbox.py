"""Virtual Xbox360 controller management."""
import logging
import struct
from typing import Optional
from dataclasses import dataclass

try:
    import vgamepad as vg
    VGAMEPAD_AVAILABLE = True
except ImportError:
    VGAMEPAD_AVAILABLE = False
    logging.warning("vgamepad not available. Virtual controller features disabled.")

logger = logging.getLogger(__name__)


@dataclass
class VirtualControllerConfig:
    """Configuration for virtual controller."""
    dead_zone: float = 0.15
    trigger_threshold: float = 0.1
    invert_y_stick: bool = False
    invert_x_stick: bool = False


class VirtualXbox360:
    """Manages a virtual Xbox360 controller."""

    def __init__(self, config: Optional[VirtualControllerConfig] = None):
        """Initialize virtual Xbox360 controller.
        
        Args:
            config: Configuration for the virtual controller
        """
        if not VGAMEPAD_AVAILABLE:
            logger.error("vgamepad not available. Install with: pip install vgamepad")
            self.gamepad = None
            return

        self.config = config or VirtualControllerConfig()
        self.gamepad: Optional[vg.VX360Gamepad] = None
        self._connected = False

        try:
            self.gamepad = vg.VX360Gamepad()
            self._connected = True
            logger.info("Virtual Xbox360 controller created successfully")
        except Exception as e:
            logger.error(f"Failed to create virtual Xbox360 controller: {e}")
            logger.error("Make sure ViGEmBus is installed: https://github.com/ViGEm/ViGEmBus/releases")

    def is_connected(self) -> bool:
        """Check if virtual controller is connected.
        
        Returns:
            True if connected, False otherwise
        """
        return self._connected and self.gamepad is not None

    def _normalize_stick(self, x: float, y: float) -> tuple[float, float]:
        """Normalize stick input to -1.0 to 1.0 range.
        
        Args:
            x: X axis value
            y: Y axis value
            
        Returns:
            Normalized (x, y) tuple
        """
        x = max(-1.0, min(1.0, x))
        y = max(-1.0, min(1.0, y))
        
        if self.config.invert_x_stick:
            x = -x
        if self.config.invert_y_stick:
            y = -y
            
        return (x, y)

    def _normalize_trigger(self, value: float) -> float:
        """Normalize trigger input to 0.0 to 1.0 range.
        
        Args:
            value: The trigger value
            
        Returns:
            Normalized value
        """
        value = max(0.0, min(1.0, value))
        
        if value < self.config.trigger_threshold:
            return 0.0
            
        return value

    def update_left_stick(self, x: float, y: float):
        """Update left analog stick.
        
        Args:
            x: X axis value (-1.0 to 1.0)
            y: Y axis value (-1.0 to 1.0)
        """
        if not self.is_connected():
            return

        try:
            x, y = self._normalize_stick(x, y)
            self.gamepad.left_joystick_float(x, y)
        except Exception as e:
            logger.error(f"Error updating left stick: {e}")

    def update_right_stick(self, x: float, y: float):
        """Update right analog stick.
        
        Args:
            x: X axis value (-1.0 to 1.0)
            y: Y axis value (-1.0 to 1.0)
        """
        if not self.is_connected():
            return

        try:
            x, y = self._normalize_stick(x, y)
            self.gamepad.right_joystick_float(x, y)
        except Exception as e:
            logger.error(f"Error updating right stick: {e}")

    def update_triggers(self, left: float, right: float):
        """Update both triggers.
        
        Args:
            left: Left trigger value (0.0 to 1.0)
            right: Right trigger value (0.0 to 1.0)
        """
        if not self.is_connected():
            return

        try:
            left = self._normalize_trigger(left)
            right = self._normalize_trigger(right)
            self.gamepad.left_trigger_float(left)
            self.gamepad.right_trigger_float(right)
        except Exception as e:
            logger.error(f"Error updating triggers: {e}")

    def press_button(self, button: str):
        """Press a button.
        
        Args:
            button: Button name (A, B, X, Y, LB, RB, Back, Start, LS, RS, Guide)
        """
        if not self.is_connected():
            return

        try:
            button_map = {
                "A": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
                "B": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
                "X": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
                "Y": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
                "LB": vg.XUSB_BUTTON.XUSB_GAMEPAD_LB,
                "RB": vg.XUSB_BUTTON.XUSB_GAMEPAD_RB,
                "Back": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
                "Start": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
                "LS": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
                "RS": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
                "Guide": vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
            }
            
            if button in button_map:
                self.gamepad.press_button_number(button_map[button].value)
        except Exception as e:
            logger.error(f"Error pressing button {button}: {e}")

    def release_button(self, button: str):
        """Release a button.
        
        Args:
            button: Button name
        """
        if not self.is_connected():
            return

        try:
            button_map = {
                "A": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
                "B": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
                "X": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
                "Y": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
                "LB": vg.XUSB_BUTTON.XUSB_GAMEPAD_LB,
                "RB": vg.XUSB_BUTTON.XUSB_GAMEPAD_RB,
                "Back": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
                "Start": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
                "LS": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
                "RS": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
                "Guide": vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
            }
            
            if button in button_map:
                self.gamepad.release_button_number(button_map[button].value)
        except Exception as e:
            logger.error(f"Error releasing button {button}: {e}")

    def press_dpad(self, direction: str):
        """Press a D-pad direction.
        
        Args:
            direction: Direction (UP, DOWN, LEFT, RIGHT)
        """
        if not self.is_connected():
            return

        try:
            direction_map = {
                "UP": vg.XUSB_GAMEPAD_DPAD_DIRECTIONS.XUSB_GAMEPAD_DPAD_UP,
                "DOWN": vg.XUSB_GAMEPAD_DPAD_DIRECTIONS.XUSB_GAMEPAD_DPAD_DOWN,
                "LEFT": vg.XUSB_GAMEPAD_DPAD_DIRECTIONS.XUSB_GAMEPAD_DPAD_LEFT,
                "RIGHT": vg.XUSB_GAMEPAD_DPAD_DIRECTIONS.XUSB_GAMEPAD_DPAD_RIGHT,
            }
            
            if direction in direction_map:
                self.gamepad.press_button_number(direction_map[direction].value)
        except Exception as e:
            logger.error(f"Error pressing D-pad {direction}: {e}")

    def release_dpad(self, direction: str = None):
        """Release a D-pad direction or all.
        
        Args:
            direction: Direction to release, or None to release all
        """
        if not self.is_connected():
            return

        try:
            if direction is None:
                # Release all D-pad
                self.gamepad.press_button_number(vg.XUSB_GAMEPAD_DPAD_DIRECTIONS.XUSB_GAMEPAD_DPAD_OFF.value)
            else:
                direction_map = {
                    "UP": vg.XUSB_GAMEPAD_DPAD_DIRECTIONS.XUSB_GAMEPAD_DPAD_UP,
                    "DOWN": vg.XUSB_GAMEPAD_DPAD_DIRECTIONS.XUSB_GAMEPAD_DPAD_DOWN,
                    "LEFT": vg.XUSB_GAMEPAD_DPAD_DIRECTIONS.XUSB_GAMEPAD_DPAD_LEFT,
                    "RIGHT": vg.XUSB_GAMEPAD_DPAD_DIRECTIONS.XUSB_GAMEPAD_DPAD_RIGHT,
                }
                
                if direction in direction_map:
                    self.gamepad.release_button_number(direction_map[direction].value)
        except Exception as e:
            logger.error(f"Error releasing D-pad: {e}")

    def reset(self):
        """Reset all controller inputs to neutral state."""
        if not self.is_connected():
            return

        try:
            self.gamepad.left_joystick_float(0.0, 0.0)
            self.gamepad.right_joystick_float(0.0, 0.0)
            self.gamepad.left_trigger_float(0.0)
            self.gamepad.right_trigger_float(0.0)
            self.gamepad.update()
        except Exception as e:
            logger.error(f"Error resetting controller: {e}")

    def update(self):
        """Send pending updates to the virtual controller."""
        if not self.is_connected():
            return

        try:
            self.gamepad.update()
        except Exception as e:
            logger.error(f"Error updating virtual controller: {e}")

    def shutdown(self):
        """Shutdown the virtual controller."""
        if self.gamepad:
            try:
                self.reset()
                self.gamepad.update()
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
        logger.info("Virtual Xbox360 controller shutdown")
