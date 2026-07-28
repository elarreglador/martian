"""Tray icon module: system tray application for Martian."""

import os
import subprocess
import sys

from ..keyboard import Keyboard, apply_mode
from ..modes import BUILTIN_MODES, load_modes
from ..protocol import find_hidraw

def _make_tray_icon():
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None
    s = 32
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Rocket body (cyan cone)
    d.polygon([(16, 1), (5, 22), (27, 22)], fill=(0, 180, 255, 255))
    # Window (white circle)
    d.ellipse([12, 8, 20, 16], fill=(255, 255, 255, 255))
    # Fins (orange)
    d.polygon([(5, 22), (1, 28), (7, 24)], fill=(255, 120, 0, 255))
    d.polygon([(27, 22), (31, 28), (25, 24)], fill=(255, 120, 0, 255))
    # Flame (yellow)
    d.polygon([(11, 22), (16, 31), (21, 22)], fill=(255, 200, 0, 255))
    return img

def _request_sudo():
    try:
        pwd = subprocess.check_output(
            ["zenity", "--password", "--title=Martian - Privilegios requeridos"]
        ).decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        print("Autenticación cancelada")
        sys.exit(1)
    proc = subprocess.Popen(
        ["sudo", "-E", "-S", sys.executable] + sys.argv,
        stdin=subprocess.PIPE, env=os.environ
    )
    proc.communicate(input=pwd.encode())
    sys.exit(0)

def cmd_tray():
    path = find_hidraw()
    if not path:
        print("Error: teclado no encontrado")
        sys.exit(1)
    try:
        fd = os.open(path, os.O_RDWR)
        os.close(fd)
    except PermissionError:
        _request_sudo()
        return

    if "--daemon" not in sys.argv:
        proc = subprocess.Popen(
            [sys.executable] + sys.argv + ["--daemon"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        print(f"Martian tray iniciado (PID {proc.pid})")
        return

    try:
        import pystray
    except ImportError:
        sys.exit(1)

    icon_img = _make_tray_icon()
    if icon_img is None:
        sys.exit(1)

    kbd = Keyboard()

    def _apply(name):
        if name in BUILTIN_MODES:
            kbd.set_hardware_mode(BUILTIN_MODES[name])
        else:
            modes = load_modes()
            if name in modes:
                apply_mode(kbd, modes[name])

    def _make_cb(name):
        return lambda icon, item: _apply(name)

    def _make_menu():
        modes = load_modes()
        flash_items = [
            pystray.MenuItem(n, _make_cb(n)) for n in sorted(modes)
        ]
        fw_items = [
            pystray.MenuItem(n, _make_cb(n)) for n in sorted(BUILTIN_MODES)
        ]
        flash_sub = pystray.Menu(
            *flash_items if flash_items else [pystray.MenuItem("(ninguno)", None, enabled=False)]
        )
        fw_sub = pystray.Menu(*fw_items)
        return pystray.Menu(
            pystray.MenuItem("Flash Modes", flash_sub),
            pystray.MenuItem("Firmware Modes", fw_sub),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("LEDs Off", lambda icon, item: kbd.set_mode_off()),
            pystray.MenuItem("Salir", lambda icon, item: icon.stop()),
        )

    icon = pystray.Icon("martian", icon_img, "Martian Flash Controller", _make_menu())
    icon.run()
