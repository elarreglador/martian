# USB HID keycode → slot LED del MK-Revo Pro
# Los keycodes están definidos en USB HID Usage Tables (página 0x07 Keyboard/Keypad)
# Las posiciones están mapeadas desde el matrix_map del OpenRGB (Sinowealth)

HID_TO_SLOT = {
       0x4:  67,  # A
       0x5:  94,  # B
       0x6:  92,  # C
       0x7:  69,  # D
       0x8:  47,  # E
       0x9:  70,  # F
       0xa:  71,  # G
       0xb:  72,  # H
       0xc:  52,  # I
       0xd:  73,  # J
       0xe:  74,  # K
       0xf:  75,  # L
      0x10:  96,  # M
      0x11:  95,  # N
      0x12:  53,  # O
      0x13:  54,  # P
      0x14:  45,  # Q
      0x15:  48,  # R
      0x16:  68,  # S
      0x17:  49,  # T
      0x18:  51,  # U
      0x19:  93,  # V
      0x1a:  46,  # W
      0x1b:  91,  # X
      0x1c:  50,  # Y
      0x1d:  90,  # Z
      0x1e:  23,  # 1
      0x1f:  24,  # 2
      0x20:  25,  # 3
      0x21:  26,  # 4
      0x22:  27,  # 5
      0x23:  28,  # 6
      0x24:  29,  # 7
      0x25:  30,  # 8
      0x26:  31,  # 9
      0x27:  32,  # 0
       0x28:  79,  # Enter
      0x29:   0,  # Esc
      0x2b:  44,  # Tab
      0x2c: 115,  # Space
      0x2d:  33,  # -
      0x2e:  34,  # =
      0x2f:  55,  # [
      0x30:  56,  # ]
       0x31:  78,  # \
      0x33:  76,  # ;
      0x34:  77,  # '
      0x35:  22,  # `
      0x36:  97,  # ,
      0x37:  98,  # .
      0x38:  99,  # /
      0x39:  66,  # Caps
      0x3a:   2,  # F1
      0x3b:   3,  # F2
      0x3c:   4,  # F3
      0x3d:   5,  # F4
      0x3e:   7,  # F5
      0x3f:   8,  # F6
      0x40:   9,  # F7
      0x41:  10,  # F8
      0x42:  11,  # F9
      0x43:  12,  # F10
      0x44:  13,  # F11
      0x45:  14,  # F12
      0x4f: 127,  # Right
      0x50: 125,  # Left
      0x51: 126,  # Down
      0x52: 104,  # Up
       0x59:  18,  # Num7
       0x5a:  19,  # Num8
       0x5b:  20,  # Num9
       0x5c:  40,  # Num4
       0x5d:  41,  # Num5
       0x5e:  42,  # Num6
       0x5f:  62,  # Num1
       0x60:  63,  # Num2
       0x61:  64,  # Num3
       0x62:  84,  # Num0
       0x63:  86,  # Num.
       0xe0: 110,  # LCtrl
       0xe1:  88,  # LShift
       0xe2: 112,  # LAlt
       0xe3: 111,  # LWin
       0xe4: 122,  # RCtrl
       0xe5: 102,  # RShift
       0xe6: 118,  # RAlt
       0xe7: 120,  # RWin
}




# Teclas que aparecen en dos posiciones LED distintas
# con el mismo keycode HID
HID_TO_SLOT_AMBIGUOUS = {
       0x57: [ 65,  87],  # Num+
       0x58: [109, 131],  # NumEnter
}





# Byte de modifier HID → slot
# Bit 7=RCtrl, 6=RAlt, 5=RShift, 4=RWin, 3=?, 2=LAlt, 1=LShift, 0=LCtrl
MODIFIER_SLOTS = {
    0x01: 110,  # LCtrl
    0x02:  88,  # LShift
    0x04: 112,  # LAlt
    0x08: 111,  # LWin
    0x10: 122,  # RCtrl
    0x20: 102,  # RShift
    0x40: 118,  # RAlt
    0x80: 120,  # RWin
}



# Teclas anchas: una tecla física ocupa dos posiciones en la matriz LED.
# Al escribir color en una, hay que escribirlo también en su par.
WIDE_KEY_PAIRS = {
    65:  87,  # Num+
    87:  65,
    109: 131,  # NumEnter
    131: 109,
}



