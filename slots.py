# USB HID keycode → slot LED del MK-Revo Pro
# Los keycodes están definidos en USB HID Usage Tables (página 0x07 Keyboard/Keypad)
# Las posiciones están mapeadas desde el matrix_map del OpenRGB (Sinowealth)

HID_TO_SLOT = {
    # Fila 0 — Function keys
    0x29:   0,  # Escape
    0x3A:   2,  # F1
    0x3B:   3,  # F2
    0x3C:   4,  # F3
    0x3D:   5,  # F4
    0x3E:   7,  # F5
    0x3F:   8,  # F6
    0x40:   9,  # F7
    0x41:  10,  # F8
    0x42:  11,  # F9
    0x43:  12,  # F10
    0x44:  13,  # F11
    0x45:  14,  # F12
    0x46:  15,  # PrtSc
    0x47:  16,  # ScrLk
    0x48:  17,  # Pause
    # Fila 1 — Números
    0x35:  22,  # `~
    0x1E:  23,  # 1
    0x1F:  24,  # 2
    0x20:  25,  # 3
    0x21:  26,  # 4
    0x22:  27,  # 5
    0x23:  28,  # 6
    0x24:  29,  # 7
    0x25:  30,  # 8
    0x26:  31,  # 9
    0x27:  32,  # 0
    0x2D:  33,  # -
    0x2E:  34,  # =
    0x2A:  36,  # BkSp
    # Fila 1 — Navegación superior
    0x49:  37,  # Ins
    0x4A:  38,  # Home
    0x4B:  39,  # PgUp
    # Fila 1 — Keypad superior
    0x53:  40,  # NumLk
    0x54:  41,  # / (numpad)
    0x55:  42,  # * (numpad)
    0x56:  43,  # - (numpad)
    # Fila 2 — QWERTY
    0x2B:  44,  # Tab
    0x14:  45,  # Q
    0x1A:  46,  # W
    0x08:  47,  # E
    0x15:  48,  # R
    0x17:  49,  # T
    0x1C:  50,  # Y
    0x18:  51,  # U
    0x0C:  52,  # I
    0x12:  53,  # O
    0x13:  54,  # P
    0x2F:  55,  # [
    0x30:  56,  # ]
    0x31:  57,  # \
    # Fila 2 — Navegación media
    0x4C:  59,  # Del
    0x4D:  60,  # End
    0x4E:  61,  # PgDn
    # Fila 2 — Keypad fila 7-9
    0x5F:  62,  # 7 (numpad)
    0x60:  63,  # 8 (numpad)
    0x61:  64,  # 9 (numpad)
    # Fila 3 — Home row
    0x39:  66,  # Caps
    0x04:  67,  # A
    0x16:  68,  # S
    0x07:  69,  # D
    0x09:  70,  # F
    0x0A:  71,  # G
    0x0B:  72,  # H
    0x0D:  73,  # J
    0x0E:  74,  # K
    0x0F:  75,  # L
    0x33:  76,  # ;
    0x34:  77,  # '
    0x28:  79,  # Enter (principal)
    # Fila 3 — Keypad fila 4-6
    0x5C:  84,  # 4 (numpad)
    0x5D:  85,  # 5 (numpad)
    0x5E:  86,  # 6 (numpad)
    # Fila 4 — Shift row
    0xE1:  88,  # LShift
    0x1D:  90,  # Z
    0x1B:  91,  # X
    0x06:  92,  # C
    0x19:  93,  # V
    0x05:  94,  # B
    0x11:  95,  # N
    0x10:  96,  # M
    0x36:  97,  # ,
    0x37:  98,  # .
    0x38:  99,  # /
    0xE5: 102,  # RShift
    # Fila 4 — Cursor arriba
    0x52: 104,  # ↑
    # Fila 4 — Keypad fila 1-3
    0x59: 106,  # 1 (numpad)
    0x5A: 107,  # 2 (numpad)
    0x5B: 108,  # 3 (numpad)
    # Fila 5 — Bottom row
    0xE0: 110,  # LCtrl
    0xE3: 111,  # LWin
    0xE2: 112,  # LAlt
    0x2C: 115,  # Space
    0xE6: 118,  # RAlt
    0xE7: 120,  # RWin
    0xE4: 122,  # RCtrl
    # Fila 5 — Cursores
    0x50: 125,  # ←
    0x51: 126,  # ↓
    0x4F: 127,  # →
    # Fila 5 — Keypad fila inferior
    0x62: 128,  # 0 (numpad)
    0x63: 130,  # . (numpad)
}

# Teclas que aparecen en dos posiciones LED distintas
# con el mismo keycode HID
HID_TO_SLOT_AMBIGUOUS = {
    0x57: [65, 87],    # Numpad + (arriba y medio)
    0x58: [109, 131],  # Numpad Enter (derecha y abajo)
}

# Byte de modifier HID → slot
# Bit 7=RCtrl, 6=RAlt, 5=RShift, 4=RWin, 3=?, 2=LAlt, 1=LShift, 0=LCtrl
MODIFIER_SLOTS = {
    0x01: 110,  # LCtrl
    0x02: 88,   # LShift
    0x04: 112,  # LAlt
    0x08: 111,  # LWin
    0x10: 122,  # RCtrl
    0x20: 102,  # RShift
    0x40: 118,  # RAlt
    0x80: 120,  # RWin
}
