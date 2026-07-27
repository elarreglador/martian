#!/usr/bin/env python3
"""verify_slots.py — Verify and auto-correct HID_TO_SLOT mapping on MK-Revo Pro.

Usage: sudo python3 verify_slots.py
"""

import re
import time

from martian import Keyboard, LED_COUNT, COLORS_START, \
    PER_KEY_MODE_IDX, CURRENT_MODE_IDX, CURRENT_MODE2_IDX, MODE_PER_KEY
from slots import WIDE_KEY_PAIRS, HID_TO_SLOT

COLOR_CIRCLES = ["\U0001f534", "\U0001f535", "\U0001f7e1", "\U0001f7e2", "\U0001f7e3"]
COLOR_RGB = [
    (255, 50, 50),     # 🔴 red
    (50, 50, 255),     # 🔵 blue
    (255, 255, 50),    # 🟡 yellow
    (50, 255, 50),     # 🟢 green
    (200, 50, 255),    # 🟣 purple
]

SLOT_TO_KEY = {
    0: "Esc", 2: "F1", 3: "F2", 4: "F3", 5: "F4",
    7: "F5", 8: "F6", 9: "F7", 10: "F8", 11: "F9",
    12: "F10", 13: "F11", 14: "F12", 15: "PrtSc", 16: "ScrLk", 17: "Pause",
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


def _replace_dict_block(text, dict_name, new_dict):
    start_marker = f"{dict_name} = {{"
    start = text.find(start_marker)
    if start == -1:
        return None

    pos = start + len(start_marker) - 1
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
    new_block = "".join(lines)
    return text[:start] + new_block + text[end:]


def _auto_correct(all_errors):
    if not all_errors:
        return False

    key_to_hid = {}
    for kc, slot in HID_TO_SLOT.items():
        name = SLOT_TO_KEY.get(slot)
        if name:
            key_to_hid[name.lower()] = kc

    new_hid = dict(HID_TO_SLOT)
    removed = 0
    corrected = 0
    pending = set()

    for slot, expected, received in all_errors:
        if received == "APAGADO":
            for kc, s in list(new_hid.items()):
                if s == slot:
                    del new_hid[kc]
                    removed += 1
                    break
        elif received == "DESCONOCIDO":
            pending.add(expected)
        else:
            recv_norm = received.strip().lower()
            if recv_norm in key_to_hid:
                kc = key_to_hid[recv_norm]
                if new_hid.get(kc) != slot:
                    new_hid[kc] = slot
                    corrected += 1
            else:
                pending.add(received)

    try:
        with open("slots.py") as f:
            text = f.read()
    except OSError:
        print("  Error: no se puede leer slots.py")
        return False

    new_text = _replace_dict_block(text, "HID_TO_SLOT", new_hid)
    if new_text is None:
        print("  Error: no se pudo reemplazar HID_TO_SLOT")
        return False

    if removed:
        new_text = _replace_dict_block(new_text, "WIDE_KEY_PAIRS", {
            k: v for k, v in WIDE_KEY_PAIRS.items()
            if k in new_hid.values() or v in new_hid.values()
        }) or new_text

    try:
        with open("slots.py", "w") as f:
            f.write(new_text)
    except OSError:
        print("  Error: no se puede escribir slots.py")
        return False

    print(f"  Eliminados: {removed} slots APAGADO")
    print(f"  Corregidos: {corrected} mapeos")
    if pending:
        print(f"  Pendientes (usa 'python3 martian.py slot'):")
        print(f"    {', '.join(pending)}")
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
    print("  Escribe el nombre de la tecla que se ilumina con ese color.")
    print("  Si no se ilumina ninguna tecla, escribe: apagado")
    print("  Si no reconoces la tecla, escribe:       desconocido")
    print()

    batches = make_batches(GROUPS)
    total = len(batches)
    all_errors = []
    all_ok = 0
    all_total = 0

    for bnum, (label, full_slots, slots) in enumerate(batches, 1):
        attempt = 0
        batch_errors = []
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

            batch_errors = []
            batch_ok = 0

            for i, slot in enumerate(slots):
                name = SLOT_TO_KEY.get(slot, f"Slot{slot}")
                prompt = (f"    {circles[i]} Slot {slot:3d} ({name})\n"
                          f"      Tecla (o apagado/desconocido): ")
                try:
                    raw = input(prompt).strip()
                except (EOFError, KeyboardInterrupt):
                    print()
                    kbd.set_mode_off()
                    kbd.close()
                    return

                lower_in = raw.lower()
                if lower_in == name.lower():
                    print("      \u2713")
                    batch_ok += 1
                elif lower_in == "apagado":
                    print(f"      \u2717 (apagado, esperado: {name})")
                    batch_errors.append((slot, name, "APAGADO"))
                elif lower_in == "desconocido":
                    print(f"      \u2717 (desconocido, esperado: {name})")
                    batch_errors.append((slot, name, "DESCONOCIDO"))
                else:
                    print(f"      \u2717 (esperado: {name})")
                    batch_errors.append((slot, name, raw))

            print()
            ok_count = len(slots) - len(batch_errors)
            print(f"  Lote: {ok_count}/{len(slots)} correctos")
            confirm = input("  \u00bfTodo correcto? (s/n): ").strip().lower()

            if confirm in ("s", "si", "sí", "yes", ""):
                all_errors.extend(batch_errors)
                all_ok += batch_ok
                all_total += len(slots)
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
    print(f"  \u2713 {all_ok}/{all_total} correctos")
    print(f"  \u2717 {len(all_errors)} error(es) encontrados:")

    apagados = [(s, e) for s, e, r in all_errors if r == "APAGADO"]
    wrong = [(s, e, r) for s, e, r in all_errors if r not in ("APAGADO", "DESCONOCIDO")]
    unknown = [(s, e) for s, e, r in all_errors if r == "DESCONOCIDO"]

    if apagados:
        print()
        print(f"  APAGADO ({len(apagados)}):")
        for s, e in apagados:
            print(f"    Slot {s}: {e}")
    if wrong:
        print()
        print(f"  MAPEO INCORRECTO ({len(wrong)}):")
        for s, e, r in wrong:
            print(f"    Slot {s}: esperado {e}, recibido {r}")
    if unknown:
        print()
        print(f"  DESCONOCIDO ({len(unknown)}):")
        for s, e in unknown:
            print(f"    Slot {s}: {e}")

    if all_errors:
        print()
        auto = input("  \u00bfCorregir slots.py? (s/n): ").strip().lower()
        if auto in ("s", "si", "sí", "yes"):
            print()
            _auto_correct(all_errors)


if __name__ == "__main__":
    run()
