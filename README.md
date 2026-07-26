# Martian — Mars Gaming MK-Revo Pro RGB Controller for Linux

Controlador RGB para teclado **Mars Gaming MK-Revo Pro** (PID 258a:0016, MCU Sinowealth SH68F90).

## Estado

✅ **Funcional** — Control completo de LEDs por software mediante protocolo flash-save.

| Comando | Estado |
|---------|--------|
| `<RRGGBB>` | ✅ LEDs personalizados (CM1) |
| `<modo> [<RRGGBB>]` | ✅ Modo hardware integrado |
| `slot <n> <RRGGBB>` | ✅ LED individual |
| `off` | ✅ Apagar |
| `status` | ✅ Info |

## Protocolo

### Hardware

- **VID/PID**: `258a:0016` ("BY Tech Usb Gaming Keyboard")
- **MCU**: Sinowealth SH68F90 (8051)
- **Interfaz HID**: 2 interfaces:
  - Interface 0 (`/dev/hidraw1`): Teclado estándar (Report 1)
  - Interface 1 (`/dev/hidraw2`): RGB, Usage Page 0xFF00 (Reports 3, 5, 6, 7)
- **LEDs**: 132 (formato BGR planar), matriz 6×22
- **Modos**: 14 hardware + 5 personalizados (Custom CM1–CM5)

### ioctl

| Función | Dirección | Tipo | NR | Fórmula |
|---------|-----------|------|----|---------|
| `HIDIOCSFEATURE(len)` | 3 (WRITE\|READ) | `'H'` (0x48) | 0x06 | `(3<<30) \| (len<<16) \| (0x48<<8) \| 0x06` |
| `HIDIOCGFEATURE(len)` | 3 (WRITE\|READ) | `'H'` (0x48) | 0x07 | `(3<<30) \| (len<<16) \| (0x48<<8) \| 0x07` |

**Importante**: Ambos ioctl requieren `dir=3` (WRITE|READ). Usar `dir=2` (HIDIOCGFEATURE) o `dir=1` (HIDIOCSFEATURE) produce EINVAL.

### Comandos (6 bytes, Report 5 SET_FEATURE)

| Comando | Bytes | Descripción |
|---------|-------|-------------|
| Leer modos | `05 83 00 00 00 00` | Tabla de modos (~80 bytes respuesta) |
| Leer presets color | `05 88 A8 00 40 00` | Colores predefinidos por modo (1032 bytes) |
| Leer per-led CM1/2 | `05 89 AC 00 40 00` | Colores por tecla CM1/2 (1032 bytes) |
| Leer per-led CM3/4 | `05 89 B0 00 40 00` | Colores por tecla CM3/4 (1032 bytes) |
| Leer per-led CM5 | `05 89 B4 00 40 00` | Colores por tecla CM5 (1032 bytes) |

**Init** (`05 01 AA BB 2F 3E`) no se usa — resetea el teclado a ISP bootloader.

### Secuencia

```
1. SET_FEATURE(Report 5, cmd=6 bytes)   → comando
2. GET_FEATURE(Report 6, 1032 bytes)    ← leer configuración actual
3. Modificar bytes en el buffer
4. SET_FEATURE(Report 6, 1032 bytes)    → escribir configuración modificada
```

### Buffer (1032 bytes, Report 6)

| Offset | Tamaño | Descripción |
|--------|--------|-------------|
| 0 | 1 | Report ID (0x06) |
| 1 | 1 | Status (bit 7 = flag, **limpiar** antes de reenviar) |
| 2–5 | 4 | Dirección flash (copiar del comando original) |
| 6–7 | 2 | ? (rellenar con 0) |
| 8+ | 396 | Colores BGR planar (132 LEDs × 3) |

CM2/CM4 usan segunda mitad del array de colores (offset 8 + 396).

Colores: `buf[8 + i] = Blue[i]`, `buf[8 + 132 + i] = Green[i]`, `buf[8 + 264 + i] = Red[i]`

### Mapeo modo personalizado

| Byte | Valor | Significado |
|------|-------|-------------|
| `[20]` | `0x01` | Per-key activado |
| `[21]` | `0x0F` | `MODE_PER_KEY` |
| `[22]` | `0x20 \| preset` | preset 0–4 = CM1–CM5 |

## Instalación

### 1. Requisitos

- Python 3.8+
- Permisos de escritura en `/dev/hidraw2` (ver udev más abajo)

### 2. Descargar

```bash
git clone <repo> ~/dev/martian
cd ~/dev/martian
```

### 3. Regla udev (opcional, para evitar sudo)

```bash
sudo cp 60-mkrevopro.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Cierra sesión y vuelve a entrar (o ejecuta `newgrp plugdev`) para que el grupo `plugdev` tenga efecto.

## Uso

### Color estático (uso principal)

```bash
python3 mkrevopro.py FF0000    # Rojo
python3 mkrevopro.py 00FF00    # Verde
python3 mkrevopro.py 0000FF    # Azul
python3 mkrevopro.py FFFFFF    # Blanco
python3 mkrevopro.py FF8800    # Naranja
python3 mkrevopro.py FF00FF    # Magenta
python3 mkrevopro.py 00FFFF    # Cian
```

Cada cambio escribe en flash ~2-3 veces. Despreciable para uso diario.

### LED individual

```bash
python3 mkrevopro.py slot 0 FF0000    # Escape rojo
python3 mkrevopro.py slot 2 00FF00    # F1 verde
python3 mkrevopro.py slot 27 FF8800   # Tecla 5 naranja
python3 mkrevopro.py slot 45 0000FF   # W azul
python3 mkrevopro.py slot 52 FF0000   # Barra espaciadora roja
```

El resto de teclas conservan el último color que tenían.

### Apagar

```bash
python3 mkrevopro.py off
```

### Información

```bash
python3 mkrevopro.py status
```

### Modos hardware (no desgastan flash)

Estos modos los ejecuta el propio chip del teclado. No escriben en flash repetidamente:

```bash
python3 mkrevopro.py spectrum              # Ciclo de colores
python3 mkrevopro.py breathing             # Respiro
python3 mkrevopro.py breathing FF0000      # Respiro rojo
python3 mkrevopro.py rainbow               # Arcoíris
python3 mkrevopro.py snake                 # Serpiente
python3 mkrevopro.py reactive              # Reacción a teclas
python3 mkrevopro.py twinkle               # Estrellas
```

Modos disponibles: `spectrum`, `breathing`, `static`, `ripples`, `reactive`, `flash`, `sine`, `raindrops`, `rainbow`, `wheel`, `adorn`, `twinkle`, `shadow`, `snake`.

### Sin regla udev

```bash
sudo python3 mkrevopro.py FF0000
```

## Limitaciones

### Flash-save: cada cambio desgasta la memoria flash

El teclado **no tiene memoria RAM para los LEDs**. La iluminación se guarda en **memoria flash NOR** interna del microcontrolador SH68F90.

Esto significa que **cada vez que se cambia un color, brillo o modo, se escribe en la flash**. Una escritura en flash:

- Tarda ~50-80ms (el teclado no responde durante ese tiempo)
- Consume uno de los ~10 000 ciclos de borrado/escritura de la flash

**Consecuencias prácticas**:

| Uso | Escrituras por cambio | Impacto |
|-----|-----------------------|---------|
| Color estático (`python3 mkrevopro.py FF0000`) | ~2-3 escrituras | Despreciable. 10 000 cambios ≈ 27 años si cambias una vez al día |
| Animación software (1 FPS, 132 LEDs) | 132 escrituras por frame | **130 000 escrituras/día si corre 8h → flash muerta en ~77 días** |
| Animación software (10 FPS) | 1320 escrituras/s | Flash muerta en **~7 segundos** |

Por eso **las animaciones por software están desactivadas**. No es un bug del código — es una limitación física del hardware.

### Sin modo directo (real-time)

Algunos teclados gaming tienen un modo "directo" donde los LEDs se controlan por RAM y los cambios no persisten ni desgastan la flash. Este teclado **no implementa ese modo**. Todas las operaciones pasan por flash.

### No enviar comando Init (`05 01 AA BB 2F 3E`)

Inicia el bootloader ISP, no una inicialización normal. El teclado deja de funcionar como HID hasta que se desconecte y reconecte.

### OpenRGB CLI bug

`DeviceUpdateMode()` en OpenRGB sobreescribe los colores con `GetPerLedColors()`, anulando el parámetro `-c`.

## OpenRGB

El fork de [glooom](https://gitlab.com/glooom/OpenRGB) detecta el teclado con `-DUSE_HID_USAGE`.
Los cambios de modo funcionan, pero los colores por LED requieren usar la GUI (no la CLI).

## Tests

```bash
python3 -m unittest test_martian -v
```

24 tests, cero dependencias externas (solo `unittest` de la stdlib). No requieren el teclado conectado.

### `TestHexToRgb` — 16 tests

Prueba `hex_to_rgb(h)`, que convierte un string hex a tupla `(R, G, B)`.

**11 casos válidos**, cada uno verifica con `assertEqual`:

| Test | Entrada | Esperado | Qué prueba |
|------|---------|----------|------------|
| `test_red` | `FF0000` | `(255, 0, 0)` | Sólo canal R |
| `test_green` | `00FF00` | `(0, 255, 0)` | Sólo canal G |
| `test_blue` | `0000FF` | `(0, 0, 255)` | Sólo canal B |
| `test_white` | `FFFFFF` | `(255, 255, 255)` | Todos al máximo |
| `test_black` | `000000` | `(0, 0, 0)` | Todos a 0 |
| `test_orange` | `FF8800` | `(255, 136, 0)` | Valor intermedio |
| `test_magenta` | `FF00FF` | `(255, 0, 255)` | Sólo R y B |
| `test_cyan` | `00FFFF` | `(0, 255, 255)` | Sólo G y B |
| `test_lowercase` | `ff0000` | `(255, 0, 0)` | Minúsculas |
| `test_mixed_case` | `FfAa00` | `(255, 170, 0)` | Mayúsculas + minúsculas |
| `test_with_hash` | `#FF0000` | `(255, 0, 0)` | `#` opcional |

**5 casos inválidos**, cada uno verifica que lanza `ValueError` con `assertRaises`:

| Test | Entrada | Por qué falla |
|------|---------|---------------|
| `test_invalid_short` | `FFF` | 3 caracteres, no 6 |
| `test_invalid_long` | `FFFFFFFF` | 8 caracteres, no 6 |
| `test_invalid_chars` | `ZZZZZZ` | `Z` no es hex |
| `test_empty` | `` | Vacío |
| `test_only_hash` | `#` | Sólo `#`, sin dígitos |

### `TestConstants` — 8 tests

Verifica que las constantes del protocolo sean coherentes en el código fuente:

| Test | Qué comprueba |
|------|---------------|
| `test_builtin_modes_count` | `BUILTIN_MODES` tiene exactamente 14 entradas |
| `test_builtin_modes_have_all_ids` | Todos los IDs están entre 1 y 14 |
| `test_builtin_modes_no_duplicates` | Ningún ID se repite |
| `test_payload_led_fit` | Los 132 LEDs en BGR caben en 1032 bytes |
| `test_led_count_positive` | `LED_COUNT > 0` |
| `test_payload_large_enough` | `PAYLOAD_LEN >= 256` (mínimo razonable) |
| `test_colors_start_aligned` | `COLORS_START >= 8` (espacio para cabecera) |
| `test_all_mode_names_lowercase` | Todos los nombres están en minúsculas (coinciden con `input.lower()` en CLI) |

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `martian.py` | Controlador Python independiente |
| `test_martian.py` | Tests unitarios (24 tests) |
| `60-mkrevopro.rules` | Regla udev para acceso sin root |
