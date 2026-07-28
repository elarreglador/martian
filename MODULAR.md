# Arquitectura modular de Martian

## Cambios principales

La refactorización separa el código monolítico original (619 líneas en `martian.py`) en módulos especializados para mejorar:

- **Mantenibilidad**: cambios en protocolo no afectan CLI
- **Testabilidad**: cada módulo se prueba aisladamente
- **Reutilización**: la clase `Keyboard` se importa en otros proyectos
- **Extensibilidad**: fácil añadir nuevas UIs o modos

## Estructura de directorios

```
martian/
├── martian/
│   ├── __init__.py              # Punto de entrada del paquete
│   ├── protocol.py              # Comunicación HID (ioctl, constantes)
│   ├── colors.py                # Conversión hex ↔ RGB
│   ├── modes.py                 # Modos (hardware + personalizados)
│   ├── keyboard.py              # Clase Keyboard de alto nivel
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── cli.py               # Interfaz de línea de comandos
│   │   └── tray.py              # Icono en bandeja del sistema
│   └── tools/
│       ├── __init__.py
│       ├── scanner.py           # Herramienta: mapeo de slots
│       ├── verifier.py          # Herramienta: verificación de slots
│       └── slot_finder.py       # Herramienta: detectar slots al pulsar
├── martian.py                   # Punto de entrada (wrapper)
├── scan_slots.py                # Wrapper para scanner
├── verify_slots.py              # Wrapper para verifier
└── slots.py                     # (sin cambios) Mapeos estáticos
```

## Módulos

### `protocol.py`
Comunicación de bajo nivel con el dispositivo HID.

**Contenido:**
- Macros ioctl: `_IOC()`, `HIDIOCSFEATURE()`, `HIDIOCGFEATURE()`
- Constantes del protocolo: `VENDOR_ID`, `PRODUCT_ID`, `LED_COUNT`, etc.
- Offsets del buffer: `COLORS_START`, `PER_KEY_MODE_IDX`, etc.
- Comandos HID: `REQ_MODES`, `REQ_COLORS`, etc.
- Funciones primitivas: `send_feature()`, `get_feature()`
- Detección de dispositivo: `find_hidraw()`, `find_keyboard_hidraw()`

### `colors.py`
Utilidades de color.

**Contenido:**
- `hex_to_rgb()` — convierte "FF0000" → (255, 0, 0)
- `rgb_to_hex()` — convierte (255, 0, 0) → "FF0000"
- `HEX_RE` — expresión regular para validación

### `modes.py`
Gestión de modos de iluminación.

**Contenido:**
- `BUILTIN_MODES` — diccionario de 14 modos hardware
- `MODE_OFF`, `MODE_PER_KEY` — constantes de modo
- `parse_mode_file()` — parsea archivos `.txt` de modo personalizado
- `load_modes()` — carga todos los modos desde `modes/`

### `keyboard.py`
Interfaz de alto nivel con el teclado.

**Contenido:**
- Clase `Keyboard` — interfaz de lectura/escritura
  - `set_color(r, g, b)` — todos los LEDs a un color
  - `set_slot(slot, r, g, b)` — LED individual
  - `set_mode_off()` — apaga LEDs
  - `set_hardware_mode(mode_id, r, g, b)` — modo del chip
  - `read_modes()`, `read_per_led()` — lectura de configuración
- Función `apply_mode()` — aplica modo personalizado

### `ui/cli.py`
Interfaz de línea de comandos.

**Contenido:**
- `main()` — dispatcher principal de comandos
- `print_usage()` — ayuda
- Manejo de argumentos: color, slot, modo, off, status, tray

### `ui/tray.py`
Aplicación de icono en bandeja del sistema.

**Contenido:**
- `cmd_tray()` — lógica principal
- `_make_tray_icon()` — genera icono PIL
- `_request_sudo()` — solicita privilegios con zenity
- Menús dinámicos de modos

### `tools/slot_finder.py`
Herramienta para detectar slots por pulsación de teclas.

**Contenido:**
- `cmd_slot_find()` — escucha reportes HID
- Mapeo de keycode + modifier byte → slot LED

### `tools/scanner.py`
Herramienta: mapeo de slots desde cero.

**Contenido:**
- `run()` — loop interactivo principal
- Funciones auxiliares: `set_color_in_buf()`, `clear_colors()`, `rotate_list()`
- `_update_slots()` — actualiza `slots.py`
- Constantes: `GROUPS`, `SLOT_TO_KEY`, `COLOR_RGB`

### `tools/verifier.py`
Herramienta: verificación de mapeo de slots.

**Contenido:**
- `run()` — loop interactivo de verificación
- Similar a scanner pero para validación
- Nota: versión simplificada; puede expandirse mirando scanner.py

## Dependencias entre módulos

```
protocol.py         (sin dependencias internas)
colors.py           (sin dependencias internas)
modes.py            → colors.py, slots.py
keyboard.py         → protocol.py, colors.py, modes.py, slots.py
ui/cli.py           → keyboard.py, colors.py, modes.py, tools/slot_finder
ui/tray.py          → keyboard.py, modes.py
tools/slot_finder.py → protocol.py, slots.py
tools/scanner.py    → keyboard.py, protocol.py, slots.py
tools/verifier.py   → keyboard.py, protocol.py, slots.py
```

**Patrón de dependencias:** Las dependencias fluyen hacia los módulos de protocolo y datos, nunca hacia atrás. Esto facilita el testing y la reutilización.

## Uso desde Python

```python
from martian import Keyboard, hex_to_rgb, BUILTIN_MODES, load_modes

# Crear instancia del teclado
kbd = Keyboard()

# Cambiar a rojo
r, g, b = hex_to_rgb("FF0000")
kbd.set_color(r, g, b)

# Activar modo breathing
kbd.set_hardware_mode(BUILTIN_MODES["breathing"])

# Cargar modos personalizados
custom = load_modes()
# ...

kbd.close()
```

## Puntos de entrada

### `martian.py` (CLI principal)
```bash
python3 martian.py FF0000            # Color rojo
python3 martian.py breathing         # Modo hardware
python3 martian.py slot 45 0000FF    # LED individual
python3 martian.py off               # Apagar
python3 martian.py status            # Información
python3 martian.py tray              # Icono en bandeja
```

### `scan_slots.py` (herramienta de escaneo)
```bash
sudo python3 scan_slots.py
```

### `verify_slots.py` (herramienta de verificación)
```bash
sudo python3 verify_slots.py
```

## Testing

```bash
python3 -m unittest test_martian -v
```

51 tests, sin dependencias externas, sin requerir dispositivo conectado.

## Migración de código existente

Si usabas el código anterior monolítico:

**Antes:**
```python
from martian import Keyboard, hex_to_rgb
```

**Ahora (equivalente):**
```python
from martian import Keyboard, hex_to_rgb
# Las importaciones públicas se re-exportan en martian/__init__.py
```

O puedes ser más específico:
```python
from martian.keyboard import Keyboard
from martian.colors import hex_to_rgb
```

## Ventajas de la refactorización

1. **Separación de responsabilidades**: cada módulo tiene un propósito claro
2. **Tests independientes**: `test_martian.py` continúa funcionando sin cambios
3. **Facilidad de extensión**: añadir una nueva UI (GUI, web, etc.) no requiere tocar protocolo
4. **Mantenimiento**: bugs en un módulo no afectan al resto
5. **Reutilización**: otros proyectos pueden importar solo `Keyboard` sin cargar CLI

## Próximos pasos (opcionales)

- Expandir `tools/verifier.py` con la funcionalidad completa de `verify_slots.py`
- Añadir logging en `protocol.py` para debug
- Crear API REST (nuevo módulo `api/`)
- Crear GUI (nuevo módulo `ui/gui.py`)
- Configuración persistente (nuevo módulo `config.py`)
