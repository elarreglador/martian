"""Protocol layer for Mars Gaming MK-Revo Pro keyboard HID communication."""

import fcntl
import glob
import os

# ── ioctl ──────────────────────────────────────────────────────────────────────

def _IOC(dirn, typ, nr, size):
    return (dirn << 30) | (size << 16) | (ord(typ) << 8) | nr

def HIDIOCSFEATURE(length):
    return _IOC(3, "H", 0x06, length)

def HIDIOCGFEATURE(length):
    return _IOC(3, "H", 0x07, length)

# ── Constantes ──────────────────────────────────────────────────────────────────

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

# ── Funciones de bajo nivel ─────────────────────────────────────────────────────

def send_feature(fd, buf):
    """Envía un feature report (HIDIOCSFEATURE)."""
    fcntl.ioctl(fd, HIDIOCSFEATURE(len(buf)), bytearray(buf), True)

def get_feature(fd, report_id, length):
    """Lee un feature report (HIDIOCGFEATURE). Retorna bytes."""
    buf = bytearray(length)
    buf[0] = report_id
    n = fcntl.ioctl(fd, HIDIOCGFEATURE(length), buf, True)
    return bytes(buf[:n])

# ── Detección de dispositivo ────────────────────────────────────────────────────

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

def find_keyboard_hidraw(vid=VENDOR_ID, pid=PRODUCT_ID):
    """Busca el hidraw de la interfaz de teclado (no la RGB).

    El teclado tiene dos interfaces:
    - Interfaz 0: teclado HID estándar (sin Report ID 5)
    - Interfaz 1: RGB vendor-specific (con Report ID 5)
    """
    for path in sorted(glob.glob("/sys/class/hidraw/hidraw*")):
        try:
            with open(os.path.join(path, "device", "uevent")) as f:
                uevent = f.read()
            if f"HID_ID=0003:{vid:08X}:{pid:08X}" not in uevent:
                continue
            with open(os.path.join(path, "device", "report_descriptor"), "rb") as f:
                desc = f.read()
            # La interfaz de teclado no tiene Report ID 5
            if bytes([0x85, 0x05]) not in desc and b'\x09\x06' in desc:
                return "/dev/" + os.path.basename(path)
        except OSError:
            continue
    return None
