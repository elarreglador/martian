#!/usr/bin/env python3
"""Generate the Martian app icon (hand-drawn rocket) as a PNG."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from martian.ui.tray import _make_tray_icon


def main():
    if len(sys.argv) != 2:
        print(f"Uso: {sys.argv[0]} <output.png>")
        sys.exit(1)
    out_path = sys.argv[1]
    img = _make_tray_icon(128)
    if img is None:
        print("Error: PIL no disponible")
        sys.exit(1)
    img.save(out_path)
    print(f"Icon generated: {out_path}")


if __name__ == "__main__":
    main()
