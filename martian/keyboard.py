"""Keyboard class: high-level interface to MK-Revo Pro keyboard."""

import os
import time

from .protocol import (
    send_feature, get_feature, find_hidraw,
    LED_COUNT, PAYLOAD_LEN, COLORS_START,
    PER_KEY_MODE_IDX, CURRENT_MODE_IDX, CURRENT_MODE2_IDX,
    MODE_OFF, MODE_PER_KEY,
    REQ_MODES, REQ_PER_LED_CM12, REQ_COLORS
)
from .colors import hex_to_rgb
from .modes import BUILTIN_MODES
from slots import HID_TO_SLOT, HID_TO_SLOT_AMBIGUOUS, WIDE_KEY_PAIRS, KEY_TO_HID

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
                REQ_PER_LED_CM12, REQ_PER_LED_CM12,
                REQ_PER_LED_CM12]
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
        slots = {slot}
        if slot in WIDE_KEY_PAIRS:
            slots.add(WIDE_KEY_PAIRS[slot])
        c = COLORS_START
        for s in slots:
            buf[c + s] = b
            buf[c + LED_COUNT + s] = g
            buf[c + LED_COUNT * 2 + s] = r
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

        mode_ptr = 32 + mode_id * 2  # PROFILES_START_IDX
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

def apply_mode(kb, mode):
    """Aplica un modo personalizado al teclado."""
    buf = bytearray(kb.read_per_led(0))
    c = COLORS_START

    if mode["bg"]:
        r, g, b = hex_to_rgb(mode["bg"])
        for i in range(LED_COUNT):
            buf[c + i] = b
            buf[c + LED_COUNT + i] = g
            buf[c + LED_COUNT * 2 + i] = r

    for key_name, color in mode["keys"].items():
        hc = KEY_TO_HID[key_name]
        r, g, b = hex_to_rgb(color)
        if hc in HID_TO_SLOT:
            slots = [HID_TO_SLOT[hc]]
        elif hc in HID_TO_SLOT_AMBIGUOUS:
            slots = HID_TO_SLOT_AMBIGUOUS[hc]
        else:
            continue
        for slot in slots:
            buf[c + slot] = b
            buf[c + LED_COUNT + slot] = g
            buf[c + LED_COUNT * 2 + slot] = r
            if slot in WIDE_KEY_PAIRS:
                p = WIDE_KEY_PAIRS[slot]
                buf[c + p] = b
                buf[c + LED_COUNT + p] = g
                buf[c + LED_COUNT * 2 + p] = r

    kb.set_mode_off()
    cfg = bytearray(kb.read_modes())
    cfg[PER_KEY_MODE_IDX] = 1
    cfg[CURRENT_MODE_IDX] = MODE_PER_KEY
    cfg[CURRENT_MODE2_IDX] = 0x20
    kb._send_config(cfg)
    time.sleep(0.25)

    kb._send_config(buf)
