"""Tray icon module: system tray application for Martian."""

import os
import subprocess
import sys
from tkinter import colorchooser
import tkinter as tk

from ..keyboard import Keyboard, apply_mode
from ..colors import hex_to_rgb
from ..modes import BUILTIN_MODES, load_modes
from ..protocol import find_hidraw

# Color palettes based on CSS color standards
COLOR_PALETTES = {
    "Basics": [
        ("Red", "FF0000"),
        ("Green", "008000"),
        ("Blue", "0000FF"),
        ("Yellow", "FFFF00"),
        ("Cyan", "00FFFF"),
        ("Magenta", "FF00FF"),
        ("White", "FFFFFF"),
        ("Black", "000000"),
    ],
    "Pastel": [
        ("Pastel Pink", "FFB3BA"),
        ("Pastel Orange", "FFDFBA"),
        ("Pastel Yellow", "FFFFBA"),
        ("Pastel Green", "BAE1BA"),
        ("Pastel Blue", "BAC7FF"),
        ("Pastel Purple", "E1BAFF"),
        ("Pastel Peach", "FFD6BA"),
        ("Pastel Mint", "BAFFBA"),
    ],
    "Cool": [
        ("Sky Blue", "87CEEB"),
        ("Deep Sky Blue", "00BFFF"),
        ("Dodger Blue", "1E90FF"),
        ("Cornflower Blue", "6495ED"),
        ("Turquoise", "40E0D0"),
        ("Dark Turquoise", "00CED1"),
        ("Cyan", "00FFFF"),
        ("Medium Slate Blue", "7B68EE"),
    ],
    "Warm": [
        ("Red", "FF0000"),
        ("Orange Red", "FF4500"),
        ("Orange", "FFA500"),
        ("Dark Orange", "FF8C00"),
        ("Tomato", "FF6347"),
        ("Coral", "FF7F50"),
        ("Light Salmon", "FFA07A"),
        ("Gold", "FFD700"),
    ],
}

def _make_tray_icon(size=32):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None
    k = size / 32.0
    s = size
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Rocket body (cyan cone)
    d.polygon([(16*k, 1*k), (5*k, 22*k), (27*k, 22*k)], fill=(0, 180, 255, 255))
    # Window (white circle)
    d.ellipse([12*k, 8*k, 20*k, 16*k], fill=(255, 255, 255, 255))
    # Fins (orange)
    d.polygon([(5*k, 22*k), (1*k, 28*k), (7*k, 24*k)], fill=(255, 120, 0, 255))
    d.polygon([(27*k, 22*k), (31*k, 28*k), (25*k, 24*k)], fill=(255, 120, 0, 255))
    # Flame (yellow)
    d.polygon([(11*k, 22*k), (16*k, 31*k), (21*k, 22*k)], fill=(255, 200, 0, 255))
    return img

def _apply_color_hex(kbd, hex_color):
    """Aplica un color en formato hex al teclado."""
    try:
        r, g, b = hex_to_rgb(hex_color)
        kbd.set_color(r, g, b)
    except Exception:
        pass

def _make_color_callback(kbd, hex_color):
    """Crea un callback para aplicar un color específico."""
    return lambda icon, item: _apply_color_hex(kbd, hex_color)

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

    def _pick_color():
        """Abre un diálogo de selección de color nativo."""
        root = tk.Tk()
        root.withdraw()
        color = colorchooser.askcolor(color="#FF0000", title="Select Color")
        root.destroy()
        if color[1]:
            _apply_color_hex(kbd, color[1].lstrip("#"))

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

        # Build One Color submenu with palette selector
        palette_items = [pystray.MenuItem("Palette", lambda icon, item: _pick_color())]
        palette_items.append(pystray.Menu.SEPARATOR)

        for palette_name in ["Basics", "Pastel", "Cool", "Warm"]:
            colors = COLOR_PALETTES[palette_name]
            color_items = [
                pystray.MenuItem(name, _make_color_callback(kbd, hex_val))
                for name, hex_val in colors
            ]
            palette_items.append(
                pystray.MenuItem(palette_name, pystray.Menu(*color_items))
            )

        one_color_menu = pystray.Menu(*palette_items)

        def _show_about():
            import webbrowser
            from .. import __version__

            win = tk.Tk()
            win.title("Acerca de Martian")
            win.resizable(False, False)
            win.attributes("-type", "dialog")

            frame = tk.Frame(win, padx=15, pady=15)
            frame.pack()

            img = _make_tray_icon()
            if img:
                from PIL import ImageTk
                photo = ImageTk.PhotoImage(img)
                tk.Label(frame, image=photo).pack(pady=(0, 5))

            tk.Label(frame, text=f"Martian v{__version__}",
                     font=("", 12, "bold")).pack()
            tk.Label(frame, text="por David Moreno Bolívar\n(elarreglador)",
                     justify="center").pack(pady=(5, 0))

            link = tk.Label(frame, text="github.com/elarreglador/martian",
                            fg="#0066CC", cursor="hand2", font=("", 9))
            link.pack(pady=(5, 10))
            link.bind("<Button-1>", lambda e: webbrowser.open(
                "https://github.com/elarreglador/martian"))

            tk.Button(frame, text="Cerrar", command=win.destroy,
                      padx=20, cursor="hand2").pack()

            win.update_idletasks()
            x = (win.winfo_screenwidth() - win.winfo_reqwidth()) // 2
            y = (win.winfo_screenheight() - win.winfo_reqheight()) // 2
            win.geometry(f"+{x}+{y}")

            win.mainloop()

        return pystray.Menu(
            pystray.MenuItem("Flash Modes", flash_sub),
            pystray.MenuItem("Firmware Modes", fw_sub),
            pystray.MenuItem("One Color", one_color_menu),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("LEDs Off", lambda icon, item: kbd.set_mode_off()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("About", lambda icon, item: _show_about()),
            pystray.MenuItem("Exit", lambda icon, item: icon.stop()),
        )

    icon = pystray.Icon("martian", icon_img, "Martian Flash Controller", _make_menu())
    icon.run()
