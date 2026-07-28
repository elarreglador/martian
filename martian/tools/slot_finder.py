"""Slot finder: detect keyboard LED slots by pressing keys."""

import os
import sys

from ..protocol import find_keyboard_hidraw
from slots import HID_TO_SLOT, HID_TO_SLOT_AMBIGUOUS, MODIFIER_SLOTS

def cmd_slot_find():
    """Espera una pulsación de tecla y muestra su número de slot."""
    kb_path = find_keyboard_hidraw()
    if not kb_path:
        print("Error: no se encuentra la interfaz de teclado")
        print("Asegúrate de que el teclado está conectado y tienes permisos.")
        sys.exit(1)

    # Comprobar si el descriptor usa Report ID 1
    base = os.path.dirname(os.path.dirname(kb_path))
    uevent_path = os.path.join(base, "device", "report_descriptor")
    has_report_id = False
    try:
        with open(uevent_path.replace("/dev/hidraw", "/sys/class/hidraw/hidraw"), "rb") as f:
            desc = f.read()
        has_report_id = bytes([0x85, 0x01]) in desc
    except OSError:
        pass

    offset = 1 if has_report_id else 0  # Byte de modifier en el reporte

    fd = os.open(kb_path, os.O_RDONLY)
    print("Pulsa una tecla...")
    try:
        while True:
            data = os.read(fd, 64)
            if len(data) < offset + 3:
                continue

            modifier_byte = data[offset]
            keycodes = [k for k in data[offset + 2:offset + 8] if k != 0]

            if not keycodes and modifier_byte == 0:
                continue  # Ninguna tecla pulsada

            resultados = []

            # Buscar en keycodes estándar
            for kc in keycodes:
                if kc in HID_TO_SLOT:
                    slot = HID_TO_SLOT[kc]
                    if slot not in resultados:
                        resultados.append(slot)
                if kc in HID_TO_SLOT_AMBIGUOUS:
                    for slot in HID_TO_SLOT_AMBIGUOUS[kc]:
                        if slot not in resultados:
                            resultados.append(slot)

            # Buscar en modifier byte
            if modifier_byte:
                for bit, slot in MODIFIER_SLOTS.items():
                    if modifier_byte & bit:
                        if slot not in resultados:
                            resultados.append(slot)

            if resultados:
                if len(resultados) == 1:
                    print(f"Slot: {resultados[0]}")
                else:
                    print(f"Slots: {', '.join(str(s) for s in resultados)}")
            else:
                codigos = ', '.join(f'0x{kc:02X}' for kc in keycodes)
                if modifier_byte:
                    codigos += f' mod=0x{modifier_byte:02X}'
                print(f"Tecla no reconocida: {codigos}")

            return
    finally:
        os.close(fd)
