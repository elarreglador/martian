"""Color conversion utilities."""

import re

HEX_RE = re.compile(r'^[0-9a-fA-F]{6}$')

def hex_to_rgb(h):
    """'FF0000' → (255, 0, 0). Acepta # opcional."""
    h = h.lstrip("#")
    if len(h) != 6 or not all(c in "0123456789abcdefABCDEF" for c in h):
        raise ValueError(f"Invalid hex color: {h!r}")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r, g, b):
    """(255, 0, 0) → 'FF0000'."""
    return f"{r:02X}{g:02X}{b:02X}"
