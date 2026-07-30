"""Mode management for keyboard LED configurations."""

import os
import sys

from .colors import HEX_RE
from slots import KEY_TO_HID

# Modos hardware que ejecuta el chip internamente (no desgastan flash)
BUILTIN_MODES = {
    "spectrum":  1,     "breathing": 2,     "static":    3,
    "ripples":   4,     "reactive":  5,     "flash":     6,
    "sine":      7,     "raindrops": 8,     "rainbow":   9,
    "wheel":    10,     "adorn":    11,     "twinkle":  12,
    "shadow":   13,     "snake":    14,
}

MODE_OFF     = 0x00
MODE_PER_KEY = 0x0F

def parse_mode_file(lines):
    """Parsea un archivo de modo personalizado.
    
    Formato esperado:
        # Comentarios con #
        bg=RRGGBB
        tecla=RRGGBB
    """
    bg = None
    keys = {}
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.rsplit("=", 1)
        k = k.strip().lower()
        v = v.strip()
        if k == "bg":
            if not HEX_RE.match(v):
                raise ValueError(f"Invalid bg color: {v!r}")
            bg = v
        elif k in KEY_TO_HID:
            if not HEX_RE.match(v):
                raise ValueError(f"Invalid color {v!r} for key {k!r}")
            keys[k] = v
        else:
            raise ValueError(f"Unknown key: {k!r}")
    return {"bg": bg, "keys": keys}

def load_modes():
    """Carga todos los modos personalizados desde la carpeta modes/."""
    modes_dir = os.path.join(os.path.dirname(__file__), "modes")
    if not os.path.isdir(modes_dir):
        return {}
    modes = {}
    for fn in os.listdir(modes_dir):
        if not fn.endswith(".txt"):
            continue
        name = fn[:-4]
        path = os.path.join(modes_dir, fn)
        try:
            with open(path) as f:
                mode = parse_mode_file(f)
            modes[name] = mode
        except (ValueError, OSError) as e:
            print(f"Warning: cannot load mode '{name}': {e}", file=sys.stderr)
    return modes
