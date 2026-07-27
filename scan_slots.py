#!/usr/bin/env python3
"""scan_slots.py — Build HID_TO_SLOT mapping on MK-Revo Pro from scratch.

Usage: sudo python3 scan_slots.py

Lights up each slot with a colored circle, asks what key it
illuminates, and generates the correct slot map at the end.
"""

import time

from martian import Keyboard, LED_COUNT, COLORS_START, \
    PER_KEY_MODE_IDX, CURRENT_MODE_IDX, CURRENT_MODE2_IDX, MODE_PER_KEY
from slots import WIDE_KEY_PAIRS, HID_TO_SLOT, HID_TO_SLOT_AMBIGUOUS

COLOR_CIRCLES = ["\U0001f534", "\U0001f535", "\U0001f7e1", "\U0001f7e2", "\U0001f7e3"]
COLOR_RGB = [
    (255, 50, 50),     # 🔴
    (50, 50, 255),     # 🔵
    (255, 255, 50),    # 🟡
    (50, 255, 50),     # 🟢
    (200, 50, 255),    # 🟣
]

SLOT_TO_KEY = {
    0: "Esc", 2: "F1", 3: "F2", 4: "F3", 5: "F4",
    7: "F5", 8: "F6", 9: "F7", 10: "F8", 11: "F9",
    12: "F10", 13: "F11", 14: "F12", 15: "PrtSc", 16: "ScrLk", 17: "Pause",
    18: "Num7", 19: "Num8", 20: "Num9",
    22: "`", 23: "1", 24: "2", 25: "3", 26: "4", 27: "5",
    28: "6", 29: "7", 30: "8", 31: "9", 32: "0", 33: "-", 34: "=",
    36: "BkSp", 37: "Ins", 38: "Home", 39: "PgUp",
    40: "Num4", 41: "Num5", 42: "Num6", 43: "Num-",
    44: "Tab", 45: "Q", 46: "W", 47: "E", 48: "R", 49: "T",
    50: "Y", 51: "U", 52: "I", 53: "O", 54: "P",
    55: "[", 56: "]", 57: "\\",
    59: "Del", 60: "End", 61: "PgDn",
    62: "Num1", 63: "Num2", 64: "Num3",
    66: "Caps", 67: "A", 68: "S", 69: "D", 70: "F",
    71: "G", 72: "H", 73: "J", 74: "K", 75: "L",
    76: ";", 77: "'", 78: "\\", 79: "Enter",
    84: "Num0", 85: "Num5", 86: "Num.", 87: "Num+",
    65: "Num+",
    88: "LShift", 90: "Z", 91: "X", 92: "C", 93: "V",
    94: "B", 95: "N", 96: "M", 97: ",", 98: ".", 99: "/",
    102: "RShift", 104: "Up",
    # 106/107/108 previously called Num1/2/3 but found APAGADO
    110: "LCtrl", 111: "LWin", 112: "LAlt",
    115: "Space", 118: "RAlt", 119: "RFn", 120: "RWin", 122: "RCtrl",
    125: "Left", 126: "Down", 127: "Right",
    # 128/130 previously called Num0/Num. but found APAGADO
    109: "NumEnter", 131: "NumEnter",
}

# Standard HID keycodes for all keyboard keys
KEY_TO_HID = {
    "esc": 0x29, "f1": 0x3a, "f2": 0x3b, "f3": 0x3c, "f4": 0x3d,
    "f5": 0x3e, "f6": 0x3f, "f7": 0x40, "f8": 0x41, "f9": 0x42,
    "f10": 0x43, "f11": 0x44, "f12": 0x45,
    "prtsc": 0x46, "scrlk": 0x47, "pause": 0x48,
    "ins": 0x49, "home": 0x4a, "pgup": 0x4b,
    "del": 0x4c, "end": 0x4d, "pgdn": 0x4e,
    "numlk": 0x53, "num/": 0x54, "num*": 0x55, "num-": 0x56,
    "num7": 0x59, "num8": 0x5a, "num9": 0x5b,
    "num4": 0x5c, "num5": 0x5d, "num6": 0x5e,
    "num1": 0x5f, "num2": 0x60, "num3": 0x61,
    "num0": 0x62, "num.": 0x63, "num+": 0x57, "numenter": 0x58,
    "tab": 0x2b, "caps": 0x39, "enter": 0x28, "intro": 0x28,
    "lshift": 0xe1, "rshift": 0xe5,
    "lctrl": 0xe0, "rctrl": 0xe4,
    "lalt": 0xe2, "ralt": 0xe6,
    "lwin": 0xe3, "rwin": 0xe7,
    "space": 0x2c, "bksp": 0x2a,
    "up": 0x52, "down": 0x51, "left": 0x50, "right": 0x4f,
    "`": 0x35, "-": 0x2d, "=": 0x2e,
    "[": 0x2f, "]": 0x30, "\\": 0x31,
    ";": 0x33, "'": 0x34, ",": 0x36, ".": 0x37, "/": 0x38,
    "q": 0x14, "w": 0x1a, "e": 0x08, "r": 0x15, "t": 0x17,
    "y": 0x1c, "u": 0x18, "i": 0x0c, "o": 0x12, "p": 0x13,
    "a": 0x04, "s": 0x16, "d": 0x07, "f": 0x09, "g": 0x0a,
    "h": 0x0b, "j": 0x0d, "k": 0x0e, "l": 0x0f,
    "z": 0x1d, "x": 0x1b, "c": 0x06, "v": 0x19, "b": 0x05,
    "n": 0x11, "m": 0x10,
    "0": 0x27, "1": 0x1e, "2": 0x1f, "3": 0x20, "4": 0x21,
    "5": 0x22, "6": 0x23, "7": 0x24, "8": 0x25, "9": 0x26,
}

MODIFIER_MAP = {
    "lctrl": 0x01, "lshift": 0x02, "lalt": 0x04, "lwin": 0x08,
    "rctrl": 0x10, "rshift": 0x20, "ralt": 0x40, "rwin": 0x80,
}

GROUPS = [
    ("Function row",
     [0, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]),

    ("Number row + nav",
     [22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 36,
      37, 38, 39, 40, 41, 42, 43]),

    ("QWERTY row + mid nav",
     [44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57,
      59, 60, 61, 62, 63, 64, 65]),

    ("Home row + numpad 4-6",
     [66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 84, 85, 86]),

    ("Shift row + numpad 1-3 + Up",
     [88, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 102, 104, 106, 107, 108]),

    ("Bottom row + cursors + numpad bottom",
     [110, 111, 112, 115, 118, 120, 122, 125, 126, 127, 128, 130, 109]),

    ("Remaining slots",
     [1, 6, 18, 19, 20, 21, 35, 58, 78, 79, 80, 81, 82, 83, 87,
      89, 100, 101, 103, 105, 113, 114, 116, 117, 119, 121, 123,
      124, 129, 131]),
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


def _detect_indent(text, marker):
    idx = text.find(marker)
    if idx == -1:
        return "    "
    line_start = text.rfind("\n", 0, idx) + 1
    indent = ""
    for ch in text[line_start:]:
        if ch in " \t":
            indent += ch
        else:
            break
    return indent if indent else "    "


def _replace_dict_block(text, dict_name, new_dict, indent="    "):
    start_marker = f"{dict_name} = {{"
    start = text.find(start_marker)
    if start == -1:
        return None

    depth = 0
    found_open = False
    end = start
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
            found_open = True
        elif text[i] == '}':
            depth -= 1
            if found_open and depth == 0:
                end = i + 1
                break
    if end == start:
        return None

    lines = [f"{dict_name} = {{\n"]
    for kc in sorted(new_dict.keys()):
        slot = new_dict[kc]
        name = SLOT_TO_KEY.get(slot, "")
        comment = f"  # {name}" if name else ""
        lines.append(f"    {hex(kc):>6s}: {slot:3d},{comment}\n")
    lines.append("}\n")
    return text[:start] + "".join(lines) + text[end:]


def _replace_ambiguous_block(text, new_dict, indent="    "):
    start_marker = "HID_TO_SLOT_AMBIGUOUS = {"
    start = text.find(start_marker)
    if start == -1:
        return text

    depth = 0
    found_open = False
    end = start
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
            found_open = True
        elif text[i] == '}':
            depth -= 1
            if found_open and depth == 0:
                end = i + 1
                break
    if end == start:
        return text

    if not new_dict:
        empty_block = "HID_TO_SLOT_AMBIGUOUS = {\n}\n\n"
        return text[:start] + empty_block + text[end:]

    lines = ["HID_TO_SLOT_AMBIGUOUS = {\n"]
    for kc in sorted(new_dict.keys()):
        slots = new_dict[kc]
        slist = ", ".join(str(s) for s in slots)
        names = [SLOT_TO_KEY.get(s, "") for s in slots]
        comment = f"  # {', '.join(filter(None, names))}"
        lines.append(f"    {hex(kc):>6s}: [{slist}],{comment}\n")
    lines.append("}\n\n")
    return text[:start] + "".join(lines) + text[end:]


def _replace_wide_pairs(text, new_pairs, indent="    "):
    start_marker = "WIDE_KEY_PAIRS = {"
    start = text.find(start_marker)
    if start == -1:
        return text

    depth = 0
    found_open = False
    end = start
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
            found_open = True
        elif text[i] == '}':
            depth -= 1
            if found_open and depth == 0:
                end = i + 1
                break
    if end == start:
        return text

    if not new_pairs:
        empty_block = "WIDE_KEY_PAIRS = {\n}\n"
        return text[:start] + empty_block + text[end:]

    lines = ["WIDE_KEY_PAIRS = {\n"]
    pair_set = set()
    for a, b in new_pairs:
        if a not in pair_set and b not in pair_set:
            name_a = SLOT_TO_KEY.get(a, "")
            name_b = SLOT_TO_KEY.get(b, "")
            comment = f"  # {name_a} / {name_b}" if name_a or name_b else ""
            lines.append(f"    {a:3d}: {b:3d},{comment}\n")
            lines.append(f"    {b:3d}: {a:3d},\n")
            pair_set.add(a)
            pair_set.add(b)
    lines.append("}\n")
    return text[:start] + "".join(lines) + text[end:]


def _replace_modifier_slots(text, new_dict, indent="    "):
    start_marker = "MODIFIER_SLOTS = {"
    start = text.find(start_marker)
    if start == -1:
        return text

    depth = 0
    found_open = False
    end = start
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
            found_open = True
        elif text[i] == '}':
            depth -= 1
            if found_open and depth == 0:
                end = i + 1
                break
    if end == start:
        return text

    lines = ["MODIFIER_SLOTS = {\n"]
    for mask_str in sorted(new_dict.keys(), key=lambda x: int(x, 16)):
        slot = new_dict[mask_str]
        name = SLOT_TO_KEY.get(slot, "")
        comment = f"  # {name}" if name else ""
        lines.append(f"    {mask_str:>4s}: {slot:3d},{comment}\n")
    lines.append("}\n")
    return text[:start] + "".join(lines) + text[end:]


def _update_slots(scan_results):
    hid_to_slot = {}
    ambiguous = {}
    modifier = {}
    pairs = []

    key_to_slots = {}
    for slot, key_name in scan_results.items():
        if key_name in ("APAGADO", "DESCONOCIDO"):
            continue
        kn = key_name.strip().lower()
        key_to_slots.setdefault(kn, []).append(slot)

    for kn, slots in key_to_slots.items():
        if kn not in KEY_TO_HID:
            continue
        hc = KEY_TO_HID[kn]
        if len(slots) == 1:
            if hc not in hid_to_slot:
                hid_to_slot[hc] = slots[0]
        elif len(slots) == 2:
            ambiguous[hc] = slots
            pairs.append((slots[0], slots[1]))

    known_modifiers = {
        "lctrl": 0x01, "lshift": 0x02, "lalt": 0x04, "lwin": 0x08,
        "rctrl": 0x10, "rshift": 0x20, "ralt": 0x40, "rwin": 0x80,
    }
    for kn, mask in known_modifiers.items():
        if kn in key_to_slots:
            slot = key_to_slots[kn][0]
            modifier[f"0x{mask:02X}"] = slot

    try:
        with open("slots.py") as f:
            text = f.read()
    except OSError:
        print("  Error: no se puede leer slots.py")
        return False

    new_text = _replace_dict_block(text, "HID_TO_SLOT", hid_to_slot)
    if new_text is None:
        print("  Error: no se pudo reemplazar HID_TO_SLOT")
        return False

    new_text = _replace_ambiguous_block(new_text, ambiguous)
    new_text = _replace_wide_pairs(new_text, pairs)
    new_text = _replace_modifier_slots(new_text, modifier)

    try:
        with open("slots.py", "w") as f:
            f.write(new_text)
    except OSError:
        print("  Error: no se puede escribir slots.py")
        return False

    mapped = len([k for k in scan_results.values() if k not in ("APAGADO", "DESCONOCIDO")])
    total = len(scan_results)
    print(f"  {mapped}/{total} slots mapeados")
    print(f"  {len(hid_to_slot)} entradas en HID_TO_SLOT")
    print(f"  {len(ambiguous)} entradas ambiguas")
    print(f"  {len(pairs)} pares anchos")
    print(f"  {len(modifier)} modificadores")
    print("  slots.py actualizado.")
    return True


def run():
    kbd = Keyboard()

    print("Setting per-key mode...")
    cfg = bytearray(kbd.read_modes())
    cfg[PER_KEY_MODE_IDX] = 1
    cfg[CURRENT_MODE_IDX] = MODE_PER_KEY
    cfg[CURRENT_MODE2_IDX] = 0x20
    kbd._send_config(cfg)
    time.sleep(0.25)

    print()
    print("  Para cada slot, escribe qu\u00e9 tecla se ilumina.")
    print("  Si no se ilumina nada, escribe: apagado")
    print("  Si no reconoces la tecla, escribe: desconocido")
    print()

    batches = make_batches(GROUPS)
    total = len(batches)
    scan = {}
    all_ok = 0
    all_slots = 0

    for bnum, (label, full_slots, slots) in enumerate(batches, 1):
        attempt = 0
        batch_ok = 0

        while True:
            rgb = rotate_list(COLOR_RGB, attempt)
            circles = rotate_list(COLOR_CIRCLES, attempt)

            buf = bytearray(kbd.read_per_led(0))
            clear_colors(buf)
            for i, slot in enumerate(slots):
                set_color_in_buf(buf, slot, *rgb[i])
            kbd._send_config(buf)
            time.sleep(0.20)

            print()
            print("=" * 65)
            print(f"  Lote {bnum}/{total}  \u2014  {label}")
            print("=" * 65)
            print(f"  Teclas disponibles: {format_available(full_slots)}")
            print()

            seq = " ".join(circles[:len(slots)])
            print(f"  Colores: {seq}")
            print()

            batch_keys = {}
            batch_ok = 0

            for i, slot in enumerate(slots):
                prompt = (f"    {circles[i]} Slot {slot:3d}\n"
                          f"      \u00bfQu\u00e9 tecla? (o apagado/desconocido): ")
                try:
                    raw = input(prompt).strip()
                except (EOFError, KeyboardInterrupt):
                    print()
                    kbd.set_mode_off()
                    kbd.close()
                    return

                if raw.lower() in ("apagado", ""):
                    print("      (apagado - sin LED)")
                    batch_keys[slot] = "APAGADO"
                elif raw.lower() == "desconocido":
                    print("      (desconocido)")
                    batch_keys[slot] = "DESCONOCIDO"
                else:
                    batch_keys[slot] = raw
                    batch_ok += 1

            print()
            print(f"  Lote: {batch_ok}/{len(slots)} detectados")
            confirm = input("  \u00bfTodo correcto? (s/n): ").strip().lower()

            if confirm in ("s", "si", "s\u00ed", "yes", ""):
                scan.update(batch_keys)
                all_ok += batch_ok
                all_slots += len(slots)
                break
            else:
                attempt += 1
                print("  Repitiendo lote con colores rotados...")

    kbd.set_mode_off()
    kbd.close()

    print()
    print("=" * 65)
    print("  REPORTE FINAL")
    print("=" * 65)
    print()
    print(f"  {all_ok}/{all_slots} slots detectados")

    apagados = [s for s, k in scan.items() if k == "APAGADO"]
    conocidos = [(s, k) for s, k in scan.items() if k not in ("APAGADO", "DESCONOCIDO")]
    desconocidos = [s for s, k in scan.items() if k == "DESCONOCIDO"]

    if conocidos:
        print()
        print(f"  MAPEADOS ({len(conocidos)}):")
        for s, k in sorted(conocidos):
            print(f"    Slot {s:3d} \u2192 {k}")
    if apagados:
        print()
        print(f"  SIN LED ({len(apagados)}):")
        for s in sorted(apagados):
            print(f"    Slot {s:3d}")

    if conocidos:
        print()
        upd = input("  \u00bfActualizar slots.py? (s/n): ").strip().lower()
        if upd in ("s", "si", "s\u00ed", "yes"):
            print()
            _update_slots(scan)


if __name__ == "__main__":
    run()
