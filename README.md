# Martian — RGB para tu Mars Gaming MK-Revo Pro en Linux

Martian controla la iluminación LED del teclado **Mars Gaming MK-Revo Pro**
(258a:0016) desde Linux. Sin software de Windows, sin OpenRGB, sin vueltas.

## ⚡ Inicio rápido

```bash
git clone https://github.com/elarreglador/martian.git ~/dev/martian
cd ~/dev/martian
sudo cp 60-mkrevopro.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
```

Cierra sesión y vuelve a entrar (o `newgrp plugdev`). Ya puedes usar el
teclado sin sudo.

##  Uso básico

```bash
python3 martian.py FF0000    # Todo en rojo
python3 martian.py 00FF00    # Todo en verde
python3 martian.py 0000FF    # Todo en azul
python3 martian.py FF8800    # Naranja
python3 martian.py FFFFFF    # Blanco
```

Cada cambio escribe en la memoria flash del teclado (~2-3 escrituras).
Para uso normal (cambiar el color de vez en cuando) no hay problema.

### Modos hardware (no desgastan flash)

Estos los ejecuta el propio chip del teclado. No escriben en flash:

```bash
python3 martian.py spectrum
python3 martian.py breathing
python3 martian.py breathing FF0000   # respiro en rojo
python3 martian.py rainbow
python3 martian.py snake
python3 martian.py reactive
python3 martian.py twinkle
```

Modos disponibles: `spectrum`, `breathing`, `static`, `ripples`, `reactive`,
`flash`, `sine`, `raindrops`, `rainbow`, `wheel`, `adorn`, `twinkle`,
`shadow`, `snake`.

### LED individual

```bash
python3 martian.py slot 0 FF0000    # Escape en rojo
python3 martian.py slot 2 00FF00    # F1 en verde
python3 martian.py slot 45 0000FF   # Q en azul
python3 martian.py slot 115 FF0000  # Barra espaciadora en rojo
```

### Detectar qué tecla es cada slot

```bash
python3 martian.py slot
```

Pulsa una tecla y te dice su número de slot. Sirve para averiguar qué número
usar con `slot <n> <RRGGBB>`.

### Apagar

```bash
python3 martian.py off
```

### Información del teclado

```bash
python3 martian.py status
```

### Icono en la bandeja del sistema

```bash
python3 martian.py tray
```

Pone un icono (cohete  ) en la bandeja con menús para cambiar de modo y
apagar LEDs. Requiere `pystray` y `Pillow`:

```bash
pip install pystray Pillow
```

En GNOME Wayland necesitas la extensión
[AppIndicator](https://extensions.gnome.org/extension/615/appindicator-support/).

##  Modos personalizados (archivos .txt)

Puedes crear tus propias configuraciones de color en la carpeta `modes/`.
Cada archivo `.txt` es un modo nuevo que aparece como comando.

### Modos incluidos

| Modo | Descripción |
|------|-------------|
| `flash-game` | Fondo azul, WASD/cursores/Shift/Espace/Supr en rojo |
| `flash-term` | Terminal clásica: fondo negro, letras verde fosforito |
| `flash-vscode` | Tema oscuro VS Code: azul código, números cálidos |
| `flash-opencode` | Tema oscuro opencode: cian, coral, amarillo |
| `flash-writer` | Fondo rojo, letras azules, cursores naranja |

### Crear un modo propio

Crea `modes/mi-modo.txt`:

```txt
# Mi modo chulo
bg=1E1E1E

w=FF0000
a=00FF00
s=0000FF
d=FFFFFF

enter=FF8800
space=FF8800
```

- `bg=RRGGBB` — color de fondo (todas las teclas no listadas)
- `tecla=RRGGBB` — color para una tecla concreta
- Los nombres de tecla válidos son los del diccionario KEY_TO_HID
- Las líneas con `#` son comentarios

Al ejecutar `python3 martian.py mi-modo` se aplica automáticamente.

## ⚠️ Lo que hay que saber

### Cada cambio desgasta la flash

Este teclado **no tiene RAM para LEDs**. La iluminación se guarda en memoria
flash NOR. Cada cambio de color es una escritura en flash (~50-80ms).

**Consecuencias prácticas**:
- Cambiar el color una vez al día: **27 años** de vida útil
- Animaciones software que cambien LEDs constantemente: **la flash muere en
  días o segundos**
- Por eso no hay animaciones por software. No es una limitación del código,
  es física del hardware.

### No tiene modo directo

Algunos teclados tienen un modo "directo" donde los LEDs se controlan por
RAM. Este no lo implementa. Todas las operaciones pasan por flash.

### No ejecutar el comando Init

Si ves código por ahí que envía `05 01 AA BB 2F 3E`, **no lo uses**. Eso
inicia el bootloader ISP y el teclado deja de funcionar hasta que lo
desconectes y reconectes.

##  Para desarrolladores

Si quieres entender el protocolo, el mapeo de teclas, o contribuir al
código, mira la documentación técnica:

→ [TECH-README.md](TECH-README.md)
