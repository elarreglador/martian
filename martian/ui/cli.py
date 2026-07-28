"""Command-line interface for Martian."""

import sys

from ..keyboard import Keyboard, apply_mode
from ..colors import hex_to_rgb
from ..modes import BUILTIN_MODES, load_modes
from ..protocol import find_hidraw

def print_usage(prog, custom_modes=None):
    print(f"Uso: {prog} <RRGGBB>                  LEDs personalizados (CM1)")
    print(f"     {prog} <modo> [<RRGGBB>]         Modo hardware")
    print(f"     {prog} slot <n> <RRGGBB>         LED individual")
    print(f"     {prog} slot                      Detectar slot al pulsar tecla")
    print(f"     {prog} tray                      Icono en bandeja")
    print(f"     {prog} off                       Apagar")
    print(f"     {prog} status                    Información")
    print("Modos hardware: " + ", ".join(sorted(BUILTIN_MODES)))
    if custom_modes:
        print("Modos personalizados: " + " ".join(sorted(custom_modes)))

def main():
    """Main CLI dispatcher."""
    from .tray import cmd_tray
    from ..tools.slot_finder import cmd_slot_find
    
    custom_modes = load_modes()

    if len(sys.argv) < 2:
        print_usage(sys.argv[0], custom_modes)
        return

    arg = sys.argv[1].lower()

    if arg == "slot" and len(sys.argv) == 2:
        cmd_slot_find()
        return

    if arg == "tray":
        cmd_tray()
        return

    kb = Keyboard()
    try:
        if arg == "off":
            kb.set_mode_off()
            print("Done")

        elif arg == "status":
            print("=== Keyboard Status ===")
            modes = bytearray(kb.read_modes())
            from ..protocol import CURRENT_MODE_IDX, PER_KEY_MODE_IDX, CURRENT_MODE2_IDX
            print(f"  mode_byte[21] (modo actual)  = 0x{modes[CURRENT_MODE_IDX]:02X}")
            print(f"  per_key_byte[20] (per-key)   = 0x{modes[PER_KEY_MODE_IDX]:02X}")
            print(f"  mode2_byte[22] (submodo)     = 0x{modes[CURRENT_MODE2_IDX]:02X}")
            from ..protocol import PAYLOAD_LEN
            perled = bytearray(kb.read_per_led(0))
            from ..protocol import COLORS_START
            non_zero = sum(1 for i in range(COLORS_START, PAYLOAD_LEN) if perled[i])
            print(f"  bytes de color no-cero        = {non_zero}")

        elif arg == "slot":
            if len(sys.argv) < 4:
                print("Uso: slot <n> <RRGGBB>")
                return
            r, g, b = hex_to_rgb(sys.argv[3])
            kb.set_slot(int(sys.argv[2]), r, g, b)
            print("Done")

        elif arg in custom_modes:
            apply_mode(kb, custom_modes[arg])
            print("Done")

        elif arg in BUILTIN_MODES:
            color = sys.argv[2] if len(sys.argv) > 2 else None
            if color:
                r, g, b = hex_to_rgb(color)
                kb.set_hardware_mode(BUILTIN_MODES[arg], r, g, b)
            else:
                kb.set_hardware_mode(BUILTIN_MODES[arg])
            print("Done")

        else:
            r, g, b = hex_to_rgb(arg)
            kb.set_color(r, g, b)
            print("Done")

    except (ValueError, IOError, OSError) as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        kb.close()

if __name__ == "__main__":
    main()
