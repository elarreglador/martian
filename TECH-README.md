# Martian — Documentación técnica

## Hardware

- **VID/PID**: `258a:0016` ("BY Tech Usb Gaming Keyboard")
- **MCU**: Sinowealth SH68F90 (8051)
- **LEDs**: 132 (formato BGR planar), matriz 6×22
- **Modos**: 14 hardware + 5 personalizados (CM1–CM5)

### Interfaces HID

| Interfaz | Dispositivo | Uso |
|----------|-------------|-----|
| 0 | `/dev/hidraw1` | Teclado estándar (Report 1) |
| 1 | `/dev/hidraw2` | RGB, Usage Page 0xFF00 (Reports 3, 5, 6, 7) |

## ioctl

| Función | Dirección | Tipo | NR | Fórmula |
|---------|-----------|------|----|---------|
| `HIDIOCSFEATURE(len)` | 3 (WRITE\|READ) | `'H'` (0x48) | 0x06 | `(3<<30) \| (len<<16) \| (0x48<<8) \| 0x06` |
| `HIDIOCGFEATURE(len)` | 3 (WRITE\|READ) | `'H'` (0x48) | 0x07 | `(3<<30) \| (len<<16) \| (0x48<<8) \| 0x07` |

Ambos ioctl requieren `dir=3` (WRITE\|READ). Usar `dir=2` (HIDIOCGFEATURE) o
`dir=1` (HIDIOCSFEATURE) produce EINVAL.

## Comandos (6 bytes, Report 5 SET_FEATURE)

| Comando | Bytes | Descripción |
|---------|-------|-------------|
| Leer modos | `05 83 00 00 00 00` | Tabla de modos (~80 bytes respuesta) |
| Leer presets color | `05 88 A8 00 40 00` | Colores predefinidos por modo (1032 bytes) |
| Leer per-led CM1/2 | `05 89 AC 00 40 00` | Colores por tecla CM1/2 (1032 bytes) |
| Leer per-led CM3/4 | `05 89 B0 00 40 00` | Colores por tecla CM3/4 (1032 bytes) |
| Leer per-led CM5 | `05 89 B4 00 40 00` | Colores por tecla CM5 (1032 bytes) |

**Init** (`05 01 AA BB 2F 3E`) **no debe usarse** — resetea el teclado a ISP
bootloader (deja de funcionar como HID hasta desconectar/reconectar).

## Secuencia de operación

```
1. SET_FEATURE(Report 5, cmd=6 bytes)   → comando de lectura
2. GET_FEATURE(Report 6, 1032 bytes)    ← leer configuración actual
3. Modificar bytes en el buffer
4. SET_FEATURE(Report 6, 1032 bytes)    → escribir configuración modificada
```

## Buffer (1032 bytes, Report 6)

| Offset | Tamaño | Descripción |
|--------|--------|-------------|
| 0 | 1 | Report ID (0x06) |
| 1 | 1 | Status (bit 7 = flag, **limpiar** antes de reenviar) |
| 2–5 | 4 | Dirección flash (copiar del comando original) |
| 6–7 | 2 | ? (rellenar con 0) |
| 8+ | 396 | Colores BGR planar (132 LEDs × 3) |

CM2/CM4 usan segunda mitad del array de colores (offset 8 + 396).

### Formato BGR planar

Los 132 LEDs se dividen en tres planos de 132 bytes cada uno:
```
buf[8 + i]           = Blue[i]
buf[8 + 132 + i]     = Green[i]
buf[8 + 264 + i]     = Red[i]
```

### Mapeo modo personalizado

Para activar modo per-key (CM1–CM5):

| Byte | Valor | Significado |
|------|-------|-------------|
| `[20]` | `0x01` | Per-key activado |
| `[21]` | `0x0F` | `MODE_PER_KEY` |
| `[22]` | `0x20 \| preset` | preset 0–4 = CM1–CM5 |

## Mapeo de slots

### HID_TO_SLOT (keycode → slot LED)

```
0x04 →  67 (A)     0x05 →  94 (B)     0x06 →  92 (C)
0x07 →  69 (D)     0x08 →  47 (E)     0x09 →  70 (F)
0x0A →  71 (G)     0x0B →  72 (H)     0x0C →  52 (I)
0x0D →  73 (J)     0x0E →  74 (K)     0x0F →  75 (L)
0x10 →  96 (M)     0x11 →  95 (N)     0x12 →  53 (O)
0x13 →  54 (P)     0x14 →  45 (Q)     0x15 →  48 (R)
0x16 →  68 (S)     0x17 →  49 (T)     0x18 →  51 (U)
0x19 →  93 (V)     0x1A →  46 (W)     0x1B →  91 (X)
0x1C →  50 (Y)     0x1D →  90 (Z)     0x1E →  23 (1)
0x1F →  24 (2)     0x20 →  25 (3)     0x21 →  26 (4)
0x22 →  27 (5)     0x23 →  28 (6)     0x24 →  29 (7)
0x25 →  30 (8)     0x26 →  31 (9)     0x27 →  32 (0)
0x28 →  79 (Enter) 0x29 →   0 (Esc)   0x2B →  44 (Tab)
0x2C → 115 (Space) 0x2D →  33 (-)    0x2E →  34 (=)
0x2F →  55 ([)     0x30 →  56 (])    0x31 →  78 (\)
0x33 →  76 (;)     0x34 →  77 (')    0x35 →  22 (`)
0x36 →  97 (,)     0x37 →  98 (.)    0x38 →  99 (/)
0x39 →  66 (Caps)  0x3A →   2 (F1)   0x3B →   3 (F2)
0x3C →   4 (F3)    0x3D →   5 (F4)   0x3E →   7 (F5)
0x3F →   8 (F6)    0x40 →   9 (F7)   0x41 →  10 (F8)
0x42 →  11 (F9)    0x43 →  12 (F10)  0x44 →  13 (F11)
0x45 →  14 (F12)   0x4F → 127 (→)    0x50 → 125 (←)
0x51 → 126 (↓)     0x52 → 104 (↑)

    0x59 →  18 (Num7)    0x5A →  19 (Num8)    0x5B →  20 (Num9)
    0x5C →  40 (Num4)    0x5D →  41 (Num5)    0x5E →  42 (Num6)
    0x5F →  62 (Num1)    0x60 →  63 (Num2)    0x61 →  64 (Num3)
    0x62 →  84 (Num0)    0x63 →  86 (Num.)

    0xE0 → 110 (LCtrl)   0xE1 →  88 (LShift)
    0xE2 → 112 (LAlt)    0xE3 → 111 (LWin)
    0xE4 → 122 (RCtrl)   0xE5 → 102 (RShift)
    0xE6 → 118 (RAlt)    0xE7 → 120 (RWin)
```

Fuente: `slots.py`, mapeado desde el `matrix_map` de OpenRGB (Sinowealth).

### Teclas ambiguas (mismo keycode, dos slots)

| Keycode | Slots | Tecla |
|---------|-------|-------|
| `0x57` | 65, 87 | Num+ |
| `0x58` | 109, 131 | NumEnter |

### Byte de modifier HID → slot

| Bit | Keycode | Slot | Tecla |
|-----|---------|------|-------|
| 0x01 | 0xE0 | 110 | LCtrl |
| 0x02 | 0xE1 | 88 | LShift |
| 0x04 | 0xE2 | 112 | LAlt |
| 0x08 | 0xE3 | 111 | LWin |
| 0x10 | 0xE4 | 122 | RCtrl |
| 0x20 | 0xE5 | 102 | RShift |
| 0x40 | 0xE6 | 118 | RAlt |
| 0x80 | 0xE7 | 120 | RWin |

### Teclas anchas (ocupan dos slots LED)

| Slot | Pareja | Tecla |
|------|--------|-------|
| 65 | 87 | Num+ |
| 109 | 131 | NumEnter |

Al escribir en una tecla ancha, el color se replica automáticamente en su
pareja.

## Modos hardware (BUILTIN_MODES)

| Nombre | ID |
|--------|----|
| spectrum | 1 |
| breathing | 2 |
| static | 3 |
| ripples | 4 |
| reactive | 5 |
| flash | 6 |
| sine | 7 |
| raindrops | 8 |
| rainbow | 9 |
| wheel | 10 |
| adorn | 11 |
| twinkle | 12 |
| shadow | 13 |
| snake | 14 |

## KEY_TO_HID (nombres de tecla → keycode)

Diccionario completo en `slots.py`. Los nombres se usan en:

- Archivos de modo en `modes/*.txt`
- `scan_slots.py` para testeo de slots
- La CLI acepta cualquier clave de este diccionario

## Archivos del proyecto

| Archivo | Descripción |
|---------|-------------|
| `martian.py` | Controlador principal: CLI, Keyboard class, modos, tray icon |
| `slots.py` | Diccionario HID keycode → slot LED, KEY_TO_HID, teclas ambiguas/anchas/modifier |
| `scan_slots.py` | Herramienta para mapear slots desde cero (132 slots, 30 batches) |
| `verify_slots.py` | Verificación visual de slots con círculos de colores |
| `test_martian.py` | Tests unitarios (51 tests) |
| `60-mkrevopro.rules` | Regla udev para acceso sin root |
| `modes/*.txt` | Modos personalizados en formato `key=RRGGBB` |

## Tests

```bash
python3 -m unittest test_martian -v
```

51 tests, cero dependencias externas. No requieren el teclado conectado.

### TestHexToRgb (16 tests)
Conversión de string hex a tupla RGB: 11 casos válidos (colores,
minúsculas, mayúsculas, `#` opcional), 5 casos inválidos (longitud, chars
no hex).

### TestConstants (8 tests)
Verifica coherencia de constantes: 14 modos, IDs 1–14 sin duplicados,
tamaño del payload, offset de colores, nombres en minúsculas.

### TestKeyboard (12 tests)
Operaciones de alto nivel sobre `Keyboard` mockeado: `set_color`,
`set_slot`, `set_mode_off`, `set_hardware_mode`, lectura de modos/per-led,
gestión de teclas anchas, modos personalizados desde archivo, errores
(slot inválido, tecla desconocida, color inválido).

### TestSlotFind (5 tests)
Parseo de reportes HID: extracción de keycode y modifier byte, mapeo a
slot, resolución de teclas ambiguas (Num+, NumEnter).

### TestCommandTray (5 tests)
Flujo completo de `cmd_tray()`: icono creado con PIL, submenú de modos
personalizados, aplicación de modo, verificación de keyboard mockeado y
subprocess para daemon.

### TestPlugins (3 tests)
Carga de modos desde `modes/*.txt`, parseo de archivo (`bg` + teclas),
aplicación contra `Keyboard` mockeado con manejo de teclas anchas.

### TestLoadModes (2 tests)
Carga de archivos `.txt` y archivos no `.txt` desde directorio temporal.

## OpenRGB

El fork de [glooom](https://gitlab.com/glooom/OpenRGB) detecta el teclado
con `-DUSE_HID_USAGE`. Los cambios de modo funcionan, pero los colores por
LED requieren usar la GUI (no la CLI), porque `DeviceUpdateMode()` en
OpenRGB sobreescribe los colores con `GetPerLedColors()`, anulando el
parámetro `-c`.
