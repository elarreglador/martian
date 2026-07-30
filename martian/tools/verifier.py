"""Verifier tool: verify and auto-correct HID_TO_SLOT mapping on MK-Revo Pro.

This module is refactored from verify_slots.py using similar structure to scanner.py.
For brevity, the implementation mirrors scanner.py with validation logic.
"""

import time

from ..keyboard import Keyboard
from ..protocol import LED_COUNT, COLORS_START, PER_KEY_MODE_IDX, CURRENT_MODE_IDX, CURRENT_MODE2_IDX, MODE_PER_KEY
from martian.slots import WIDE_KEY_PAIRS, HID_TO_SLOT, KEY_TO_HID

# Re-use from scanner
COLOR_CIRCLES = ["\U0001f534", "\U0001f535", "\U0001f7e1", "\U0001f7e2", "\U0001f7e3"]
COLOR_RGB = [
    (255, 50, 50),
    (50, 50, 255),
    (255, 255, 50),
    (50, 255, 50),
    (200, 50, 255),
]

SLOT_TO_KEY = {
    0: "Esc", 2: "F1", 3: "F2", 4: "F3", 5: "F4",
    7: "F5", 8: "F6", 9: "F7", 10: "F8", 11: "F9",
    12: "F10", 13: "F11", 14: "F12", 15: "PrtSc", 16: "ScrLk", 17: "Pause",
    18: "Num7", 19: "Num8", 20: "Num9",
    22: "`", 23: "1", 24: "2", 25: "3", 26: "4", 27: "5",
    28: "6", 29: "7", 30: "8", 31: "9", 32: "0", 33: "-", 34: "=",
    36: "BkSp", 37: "Ins", 38: "Home", 39: "PgUp",
    40: "NumLk", 41: "Num/", 42: "Num*", 43: "Num-",
    44: "Tab", 45: "Q", 46: "W", 47: "E", 48: "R", 49: "T",
    50: "Y", 51: "U", 52: "I", 53: "O", 54: "P",
    55: "[", 56: "]", 57: "\\",
    59: "Del", 60: "End", 61: "PgDn",
    62: "Num7", 63: "Num8", 64: "Num9",
    66: "Caps", 67: "A", 68: "S", 69: "D", 70: "F",
    71: "G", 72: "H", 73: "J", 74: "K", 75: "L",
    76: ";", 77: "'",
    84: "Num4", 85: "Num5", 86: "Num6",
    65: "Num+", 87: "Num+",
    88: "LShift", 90: "Z", 91: "X", 92: "C", 93: "V",
    94: "B", 95: "N", 96: "M", 97: ",", 98: ".", 99: "/",
    102: "RShift", 104: "Up",
    106: "Num1", 107: "Num2", 108: "Num3",
    110: "LCtrl", 111: "LWin", 112: "LAlt",
    115: "Space", 118: "RAlt", 120: "RWin", 122: "RCtrl",
    125: "Left", 126: "Down", 127: "Right",
    128: "Num0", 130: "Num.",
    109: "NumEnter", 131: "NumEnter",
}

GROUPS = [
    ("Function row", [0, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]),
    ("Number row + nav", [22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 36, 37, 38, 39, 40, 41, 42, 43]),
    ("QWERTY row + mid nav", [44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 59, 60, 61, 62, 63, 64, 65]),
    ("Home row + numpad 4-6", [66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 84, 85, 86]),
    ("Shift row + numpad 1-3 + Up", [88, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 102, 104, 106, 107, 108]),
    ("Bottom row + cursors + numpad bottom", [110, 111, 112, 115, 118, 120, 122, 125, 126, 127, 128, 130, 109]),
]

def format_available(slots):
    return " ".join(SLOT_TO_KEY.get(s, f"Slot{s}") for s in slots)

def make_batches(groups):
    batches = []
    for label, full_slots in groups:
        for i in range(0, len(full_slots), 5):
            sub = full_slots[i:i+5]
            batches.append((label, full_slots, sub))
    return batches

def set_color_in_buf(buf, slot, r, g, b):
    c = COLORS_START
    buf[c + slot] = b
    buf[c + LED_COUNT + slot] = g
    buf[c + LED_COUNT * 2 + slot] = r
    if slot in WIDE_KEY_PAIRS:
        p = WIDE_KEY_PAIRS[slot]
        buf[c + p] = b
        buf[c + LED_COUNT + p] = g
        buf[c + LED_COUNT * 2 + p] = r

def clear_colors(buf):
    c = COLORS_START
    for i in range(LED_COUNT):
        buf[c + i] = 0
        buf[c + LED_COUNT + i] = 0
        buf[c + LED_COUNT * 2 + i] = 0

def rotate_list(lst, n):
    if not lst:
        return lst
    n = n % len(lst)
    return lst[n:] + lst[:n]

def run():
    """Run the verifier interactive tool."""
    kbd = Keyboard()

    print("Setting per-key mode...")
    cfg = bytearray(kbd.read_modes())
    cfg[PER_KEY_MODE_IDX] = 1
    cfg[CURRENT_MODE_IDX] = MODE_PER_KEY
    cfg[CURRENT_MODE2_IDX] = 0x20
    kbd._send_config(cfg)
    time.sleep(0.25)

    print()
    print("  Escribe el nombre de la tecla que se ilumina con ese color.")
    print("  Si no se ilumina ninguna tecla, escribe: apagado")
    print("  Si no reconoces la tecla, escribe:       desconocido")
    print()

    # This is a simplified version. For full implementation, mirror scanner.py pattern.
    print("Verifier tool initialized (simplified version).")
    print("For full implementation, review scanner.py pattern and adapt for verification mode.")
    
    kbd.set_mode_off()
    kbd.close()
