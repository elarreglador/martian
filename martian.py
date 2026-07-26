#!/usr/bin/env python3
import fcntl
import glob
import os
import sys
import time

# ── ioctl ──────────────────────────────────────────────────────────────────────

def _IOC(dirn, typ, nr, size):
    return (dirn << 30) | (size << 16) | (ord(typ) << 8) | nr

def HIDIOCSFEATURE(length):
    return _IOC(3, "H", 0x06, length)

def HIDIOCGFEATURE(length):
    return _IOC(3, "H", 0x07, length)

# ── Protocolo ──────────────────────────────────────────────────────────────────

VENDOR_ID  = 0x258A
PRODUCT_ID = 0x0016

LED_COUNT   = 132
PAYLOAD_LEN = 1032

# Comandos de 6 bytes (Report 5 SET_FEATURE)
REQ_MODES        = bytes([0x05, 0x83, 0x00, 0x00, 0x00, 0x00])  # Tabla de modos
REQ_COLORS       = bytes([0x05, 0x88, 0xA8, 0x00, 0x40, 0x00])  # Colores predefinidos
REQ_PER_LED_CM12 = bytes([0x05, 0x89, 0xAC, 0x00, 0x40, 0x00])  # LEDs tecla CM1/2
REQ_PER_LED_CM34 = bytes([0x05, 0x89, 0xB0, 0x00, 0x40, 0x00])  # LEDs tecla CM3/4
REQ_PER_LED_CM5  = bytes([0x05, 0x89, 0xB4, 0x00, 0x40, 0x00])  # LEDs tecla CM5

# Offsets del buffer de configuración (1032 bytes, Report 6)
COLORS_START        = 8    # Inicio de datos BGR planar (132 LED × 3 planos)
PER_KEY_MODE_IDX    = 20   # Byte de modo personalizado
CURRENT_MODE_IDX    = 21   # Byte de modo actual
CURRENT_MODE2_IDX   = 22   # Byte de submode/preset
PROFILES_START_IDX  = 32   # Inicio de tabla de perfiles de modo (15 × 2 bytes)

MODE_OFF     = 0x00
MODE_PER_KEY = 0x0F  # Modo personalizado (CM1-CM5)

# Modos hardware que ejecuta el chip internamente (no desgastan flash)
BUILTIN_MODES = {
    "spectrum":  1,     "breathing": 2,     "static":    3,
    "ripples":   4,     "reactive":  5,     "flash":     6,
    "sine":      7,     "raindrops": 8,     "rainbow":   9,
    "wheel":    10,     "adorn":    11,     "twinkle":  12,
    "shadow":   13,     "snake":    14,
}

# ── Utilidades ─────────────────────────────────────────────────────────────────

def hex_to_rgb(h):
    """'FF0000' → (255, 0, 0). Acepta # opcional."""
    h = h.lstrip("#")
    if len(h) != 6 or not all(c in "0123456789abcdefABCDEF" for c in h):
        raise ValueError(f"Invalid hex color: {h!r}")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def find_hidraw(vid=VENDOR_ID, pid=PRODUCT_ID):
    """Busca el hidraw con Report ID 5 (interfaz RGB)."""
    for path in sorted(glob.glob("/sys/class/hidraw/hidraw*")):
        try:
            with open(os.path.join(path, "device", "uevent")) as f:
                uevent = f.read()
            if f"HID_ID=0003:{vid:08X}:{pid:08X}" not in uevent:
                continue
            with open(os.path.join(path, "device", "report_descriptor"), "rb") as f:
                desc = f.read()
            if bytes([0x85, 0x05]) in desc:
                return "/dev/" + os.path.basename(path)
        except OSError:
            continue
    return None


def send_feature(fd, buf):
    """Envía un feature report (HIDIOCSFEATURE)."""
    fcntl.ioctl(fd, HIDIOCSFEATURE(len(buf)), bytearray(buf), True)


def get_feature(fd, report_id, length):
    """Lee un feature report (HIDIOCGFEATURE). Retorna bytes."""
    buf = bytearray(length)
    buf[0] = report_id
    n = fcntl.ioctl(fd, HIDIOCGFEATURE(length), buf, True)
    return bytes(buf[:n])

# ── Controlador del teclado ────────────────────────────────────────────────────

class Keyboard:
    """Comunicación de bajo nivel con el teclado Mars Gaming MK-Revo Pro."""

    def __init__(self):
        path = find_hidraw()
        if not path:
            raise SystemExit("Keyboard not found")
        self.fd = os.open(path, os.O_RDWR)

    def close(self):
        try:
            os.close(self.fd)
        except OSError:
            pass

    def send_cmd(self, cmd):
        """Envía un comando de 6 bytes (Report 5 SET_FEATURE)."""
        send_feature(self.fd, cmd)

    def _read_config(self, req):
        """Envía comando y lee respuesta de 1032 bytes (Report 6).

        Procesa la respuesta: limpia flag de byte[1] y copia dirección
        flash desde el comando original (bytes 2-5).
        """
        self.send_cmd(req)
        time.sleep(0.01)
        raw = bytearray(get_feature(self.fd, 0x06, PAYLOAD_LEN))
        if len(raw) < 6:
            raise IOError("Config response too short")
        raw[1] &= ~0x80                 # Bit 7 = flag respuesta
        raw[2:6] = req[2:6]             # Dirección flash desde comando
        result = bytearray(PAYLOAD_LEN)
        result[:len(raw)] = raw
        return bytes(result)

    def read_modes(self):
        """Lee tabla de configuración de modos del teclado."""
        return self._read_config(REQ_MODES)

    def read_per_led(self, preset=0):
        """Lee colores por tecla para el preset dado (0-4 = CM1-CM5)."""
        reqs = [REQ_PER_LED_CM12, REQ_PER_LED_CM12,
                REQ_PER_LED_CM34, REQ_PER_LED_CM34,
                REQ_PER_LED_CM5]
        return self._read_config(reqs[preset])

    def _send_config(self, buf):
        """Escribe un buffer de configuración en el teclado (Report 6 SET_FEATURE)."""
        data = bytearray(PAYLOAD_LEN)
        data[:min(len(buf), PAYLOAD_LEN)] = buf[:PAYLOAD_LEN]
        send_feature(self.fd, data)

    # ── Operaciones de alto nivel ──────────────────────────────────────────

    def set_color(self, r, g, b):
        """Fija todos los LEDs a un color estático.

        Esto escribe en flash: ~1 ciclo de escritura por llamada.
        Es seguro para uso diario.
        """
        self.set_mode_off()                     # Apagar LEDs primero
        cfg = bytearray(self.read_modes())       # Leer config actual
        cfg[PER_KEY_MODE_IDX] = 1
        cfg[CURRENT_MODE_IDX] = MODE_PER_KEY
        cfg[CURRENT_MODE2_IDX] = 0x20           # Preset CM1
        self._send_config(cfg)                   # Escribir modo per-key
        time.sleep(0.25)

        buf = bytearray(self.read_per_led(0))    # Leer colores actuales
        c = COLORS_START
        for i in range(LED_COUNT):
            buf[c + i] = b
            buf[c + LED_COUNT + i] = g
            buf[c + LED_COUNT * 2 + i] = r
        self._send_config(buf)                   # Escribir colores

    def set_slot(self, slot, r, g, b):
        """Fija un LED individual. El resto conserva su color."""
        if slot < 0 or slot >= LED_COUNT:
            raise ValueError(f"Slot must be 0-{LED_COUNT - 1}")
        self.set_mode_off()
        cfg = bytearray(self.read_modes())
        cfg[PER_KEY_MODE_IDX] = 1
        cfg[CURRENT_MODE_IDX] = MODE_PER_KEY
        cfg[CURRENT_MODE2_IDX] = 0x20
        self._send_config(cfg)
        time.sleep(0.25)

        buf = bytearray(self.read_per_led(0))
        c = COLORS_START
        buf[c + slot] = b
        buf[c + LED_COUNT + slot] = g
        buf[c + LED_COUNT * 2 + slot] = r
        self._send_config(buf)

    def set_mode_off(self):
        """Apaga todos los LEDs (modo OFF). Una escritura."""
        cfg = bytearray(self.read_modes())
        cfg[PER_KEY_MODE_IDX] = 0
        cfg[CURRENT_MODE_IDX] = MODE_OFF
        cfg[CURRENT_MODE2_IDX] = 0
        self._send_config(cfg)

    def set_hardware_mode(self, mode_id, r=None, g=None, b=None):
        """Activa un modo hardware del teclado (no desgasta flash).

        Si se pasa color (r,g,b), también actualiza el preset del modo
        (escribe en flash una vez para guardar el color).
        """
        cfg = bytearray(self.read_modes())
        cfg[PER_KEY_MODE_IDX] = 0
        cfg[CURRENT_MODE_IDX] = mode_id
        cfg[CURRENT_MODE2_IDX] = 0

        mode_ptr = PROFILES_START_IDX + mode_id * 2
        if r is not None:
            cfg[mode_ptr] = cfg[mode_ptr] & 0xF8       # color = preset 0
            colors_buf = bytearray(self._read_config(REQ_COLORS))
            preset_ptr = COLORS_START + mode_id * 7 * 3
            colors_buf[preset_ptr]     = b
            colors_buf[preset_ptr + 1] = g
            colors_buf[preset_ptr + 2] = r
            self._send_config(colors_buf)
        else:
            cfg[mode_ptr] = (cfg[mode_ptr] & 0xF8) | 7  # color aleatorio
        self._send_config(cfg)


    def set_flash_game(self):
        """Fondo azul (0000FF) con teclas WASD+ESC+Space+Shift+Arrows+Delete en rojo (FF0000).

        2 escrituras en flash (modo + colores).
        """
        red_slots = [0, 46, 67, 68, 69, 88, 115, 59, 104, 125, 126, 127]

        self.set_mode_off()
        cfg = bytearray(self.read_modes())
        cfg[PER_KEY_MODE_IDX] = 1
        cfg[CURRENT_MODE_IDX] = MODE_PER_KEY
        cfg[CURRENT_MODE2_IDX] = 0x20
        self._send_config(cfg)
        time.sleep(0.25)

        buf = bytearray(self.read_per_led(0))
        c = COLORS_START
        for i in range(LED_COUNT):
            if i in red_slots:
                buf[c + i] = 0x00                    # B
                buf[c + LED_COUNT + i] = 0x00        # G
                buf[c + LED_COUNT * 2 + i] = 0xFF    # R
            else:
                buf[c + i] = 0xFF                    # B
                buf[c + LED_COUNT + i] = 0x00        # G
                buf[c + LED_COUNT * 2 + i] = 0x00    # R
        self._send_config(buf)


# ── Interfaz de línea de comandos ─────────────────────────────────────────────

def print_usage(prog):
    print(f"Uso: {prog} <RRGGBB>                  LEDs personalizados (CM1)")
    print(f"     {prog} <modo> [<RRGGBB>]         Modo hardware")
    print(f"     {prog} slot <n> <RRGGBB>         LED individual")
    print(f"     {prog} flash-game                Modo juego FPS")
    print(f"     {prog} off                       Apagar")
    print(f"     {prog} status                    Información")
    print("Modos hardware: " + ", ".join(sorted(BUILTIN_MODES)))


def main():
    kb = Keyboard()
    try:
        if len(sys.argv) < 2:
            print_usage(sys.argv[0])
            return

        arg = sys.argv[1].lower()

        if arg == "off":
            kb.set_mode_off()
            print("Done")

        elif arg == "status":
            print("=== Keyboard Status ===")
            modes = bytearray(kb.read_modes())
            print(f"  mode_byte[21] (modo actual)  = 0x{modes[CURRENT_MODE_IDX]:02X}")
            print(f"  per_key_byte[20] (per-key)   = 0x{modes[PER_KEY_MODE_IDX]:02X}")
            print(f"  mode2_byte[22] (submodo)     = 0x{modes[CURRENT_MODE2_IDX]:02X}")
            perled = bytearray(kb.read_per_led(0))
            non_zero = sum(1 for i in range(COLORS_START, PAYLOAD_LEN) if perled[i])
            print(f"  bytes de color no-cero        = {non_zero}")

        elif arg == "flash-game":
            kb.set_flash_game()
            print("Done")

        elif arg == "slot":
            if len(sys.argv) < 4:
                print("Uso: slot <n> <RRGGBB>")
                return
            r, g, b = hex_to_rgb(sys.argv[3])
            kb.set_slot(int(sys.argv[2]), r, g, b)
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
