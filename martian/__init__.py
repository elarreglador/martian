"""Martian: RGB controller for Mars Gaming MK-Revo Pro keyboard on Linux."""

__version__ = "1.1.1"

from .keyboard import Keyboard, apply_mode
from .colors import hex_to_rgb, rgb_to_hex
from .modes import BUILTIN_MODES, load_modes, parse_mode_file
from .protocol import (
    LED_COUNT, PAYLOAD_LEN, VENDOR_ID, PRODUCT_ID,
    find_hidraw, find_keyboard_hidraw
)

__all__ = [
    "Keyboard", "apply_mode",
    "hex_to_rgb", "rgb_to_hex",
    "BUILTIN_MODES", "load_modes", "parse_mode_file",
    "LED_COUNT", "PAYLOAD_LEN", "VENDOR_ID", "PRODUCT_ID",
    "find_hidraw", "find_keyboard_hidraw",
]
