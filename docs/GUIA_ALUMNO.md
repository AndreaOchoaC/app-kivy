# Guía del alumno: cómo hacer TU panel

Tu trabajo es **un panel**: una ventana de la app que tú diseñas y programas. Puede ser un juego, una app
útil (notas, calculadora, un diario...) o varias ventanas. No tienes que tocar la portada ni los paneles de tus
compañeros: tu panel vive en **tu carpeta** dentro de `panels/`.

> Primero haz la instalación del [README](../README.md#1-instalar-solo-la-primera-vez) y comprueba que
> `python dev.py run` abre la app.

---

## 1. Tu carpeta

```text
panels/pilar/
├── __init__.py    ← los DATOS de tu panel: título, color, autor, descripción
├── panel.py       ← el CÓDIGO (Python): qué pasa cuando tocas un botón, la lógica del juego...
├── panel.kv       ← el DISEÑO (lenguaje KV): cómo se ve, qué widgets hay y dónde
├── art.py         ← los dibujos del juego (tubos, suelo, ciudad), hechos con código
└── assets/        ← tus imágenes y sonidos (créala si no existe)
```

- **`__init__.py`**: aquí cambias el título, la descripción y el color de **tu tarjeta** en la portada.
  Es lo único que la app lee para saber que tu panel existe. **No cambies el `id`.**
- **`panel.py`** y **`panel.kv`** trabajan juntos. El `.kv` dice *cómo se ve*; el `.py` dice *qué hace*.
  Se conectan por el **nombre de la clase**: si en `panel.py` tienes `class PilarPanel(PanelScreen)`, en el
  `.kv` la regla empieza con `<PilarPanel>:`.
- Los archivos `.kv` de tu carpeta **se cargan solos**. No hace falta escribir nada para cargarlos.

Pruébalo siempre con tu panel solo (más rápido) y recarga con **F5**:

```bash
python dev.py panel pilar
```

---

## 2. El lenguaje KV en 5 minutos

KV describe widgets (cosas que se ven) y sus propiedades. Se escribe **por indentación** (4 espacios):

```kv
<PilarPanel>:                    # la regla de TU panel (mismo nombre que la clase de Python)
    BoxLayout:                   # un contenedor que apila cosas...
        orientation: "vertical"  # ...hacia abajo
        padding: dp(20)          # margen interior (dp = tamaño que se ve igual en todos los celulares)
        spacing: dp(12)          # espacio entre widgets

        Heading:                 # un widget DENTRO del BoxLayout (más indentado)
            text: "Hola, soy Pilar"
        PillButton:
            text: "Tócame"
            on_release: root.saludar()   # cuando lo sueltas, llama al método saludar() de Python
```

Lo que tienes que saber:

| En KV | Significa |
|---|---|
| `root` | **Tu panel** (la clase de `panel.py`). `root.count` lee la propiedad `count`; `root.saludar()` llama al método `saludar`. |
| `self` | El widget en el que estás escribiendo. `height: self.texture_size[1]` = «mi alto es el alto de mi texto». |
| `id: boton` | Le pone nombre a un widget. Desde Python: `self.ids.boton`. Desde otro lugar del `.kv`: `boton.text`. |
| `on_release: ...` | Qué hacer cuando se suelta un botón. También existen `on_press`, `on_text`, `on_touch_down`... |
| `dp(20)` y `"16sp"` | Tamaños. `dp` para anchos/altos/márgenes, `sp` para tamaño de letra. Así se ve bien en cualquier pantalla. |
| `size_hint: 1, None` | Ancho = 100 % del padre, alto = el que tú digas con `height`. |
| `pos_hint: {"center_x": .5}` | Centrar horizontalmente. |
| `# comentario` | Lo que el programa ignora. |

**Lo mágico de KV:** si una línea usa una Property (`text: str(root.count)`), **se actualiza sola** cuando
`count` cambia. No tienes que «redibujar» nada.

**Contenedores más usados:** `BoxLayout` (apila en fila o columna), `GridLayout` (cuadrícula: `cols: 3`),
`FloatLayout` (colocas cosas libremente con `pos_hint`), `ScrollView` (con scroll), `ScreenManager` (varias ventanas).

### Los widgets bonitos que ya existen (úsalos, se ven igual que el resto de la app)

| Widget | Qué es | Propiedades útiles |
|---|---|---|
| `Heading` · `Title` · `Body` · `Caption` | Textos de 4 tamaños (se ajustan solos al ancho) | `text`, `color` |
| `Card` | Tarjeta con sombra y bordes redondeados; dentro pones lo que quieras | `bg` (color), `radius` |
| `PillButton` | Botón redondo | `text`, `kind` (`"primary"`, `"secondary"`, `"ghost"`), `accent` (color) |
| `Chip` | Etiqueta pequeña de color | `text`, `tint` |
| `Avatar` | Círculo con degradado y una letra | `text`, `accent`, `accent2` |
| `Swatch` | Círculo de color que se puede tocar | `value`, `selected` |
| `Divider` | Línea fina | |

También puedes usar **todos los widgets de Kivy**: `Label`, `Image`, `TextInput`, `Slider`, `Switch`, `ProgressBar`,
`CheckBox`, `Button`, `Spinner`... Los colores del tema están en `theme` (`#:import theme hub.theme` arriba del `.kv`):
`theme.TEXT`, `theme.MUTED`, `theme.SURFACE`, `theme.ACCENT`, `theme.SUCCESS`, `theme.WARNING`, `theme.DANGER`...

El color de **tu panel** está en `root.accent` (lo eliges en `__init__.py`, con `color="#RRGGBB"`).

---

## 3. Python: las piezas de tu `panel.py`

```python
from kivy.properties import NumericProperty
from hub.panel import PanelScreen

class PilarPanel(PanelScreen):
    count = NumericProperty(0)        # una Property: variable «viva» que el .kv puede mostrar

    def on_build(self):               # una vez, al crear el panel
        self.count = self.load("count", 0)

    def add(self, amount):            # un método que el .kv llama con on_release: root.add(1)
        self.count += amount
        self.save("count", self.count)
```

**Tipos de Property:** `NumericProperty`, `StringProperty`, `BooleanProperty`, `ListProperty`, `DictProperty`,
`ColorProperty`, `ObjectProperty`.

**Ganchos** (métodos que Kivy llama en el momento justo; todos opcionales):

| Gancho | Cuándo se llama |
|---|---|
| `on_build(self)` | Una vez, cuando tu panel ya tiene su diseño |
| `on_show(self)` / `on_hide(self)` | Cada vez que tu panel aparece / sale de pantalla |
| `update(self, dt)` | ~60 veces por segundo **si pones `run_update = True`** en tu clase (para juegos y animaciones) |
| `handle_back(self)` | El usuario pulsó «atrás». Devuelve `True` si lo manejaste tú (por ejemplo, con una subpantalla) |

**Herramientas ya hechas** (disponibles con `self.`):

| Herramienta | Qué hace |
|---|---|
| `self.save("clave", valor)` / `self.load("clave", por_defecto)` | Recordar datos aunque se cierre la app (textos, números, listas, diccionarios). Cada panel tiene su espacio: nadie se pisa. |
| `self.toast("mensaje")` | Aviso corto abajo |
| `self.go_home()` | Volver a la portada |
| `self.asset("foto.png")` | Ruta de un archivo de tu carpeta `assets/` |
| `self.ids.nombre` | Un widget del `.kv` por su `id` |
| `self.accent` | El color de tu panel (puedes cambiarlo en vivo) |

---

## 4. Recetas (copia y adapta)

### Cambiar textos y colores
En `panel.kv` cambia `text: "..."`. En `__init__.py` cambia `title`, `subtitle` y `color`. Pulsa **F5**.

### Poner una imagen
Guarda `foto.png` en `panels/<tu_carpeta>/assets/` y en el `.kv`:
```kv
Image:
    source: root.asset("foto.png")
    size_hint_y: None
    height: dp(200)
```

### Reproducir un sonido
```python
from kivy.core.audio import SoundLoader

def on_build(self):
    self.sonido = SoundLoader.load(self.asset("click.wav"))   # .wav, .ogg o .mp3 en assets/

def sonar(self):
    if self.sonido:
        self.sonido.play()
```

### Animar algo
```python
from kivy.animation import Animation

def aparecer(self):
    widget = self.ids.caja
    widget.opacity = 0
    Animation(opacity=1, d=0.6, t="out_cubic").start(widget)   # d = segundos, t = tipo de suavizado
```
(No uses el nombre `t` para una de tus propias propiedades: en `Animation`, `t` significa «transición».)

### Tu panel ya trae un juego: Flappy Bird
Abre `panel.py` y juega con las constantes de arriba (`GRAVITY`, `FLAP_SPEED`, `GAP_START`, `BIRD_BODY`...): cambian cómo se siente el juego.
`python dev.py panel pilar` lo abre solo; **F5** recarga después de guardar. Las herramientas para dibujar, partículas y sonidos están en `hub/gamekit.py`.

### Hacer un juego desde cero
Activa `run_update = True` y mueve cosas en `update(dt)` con `posición += velocidad * dt`.
**Mira el ejemplo completo en [`examples/juego_estrella/`](../examples/juego_estrella/).**
```python
class PilarPanel(PanelScreen):
    run_update = True

    def update(self, dt):
        self.ids.bola.x += 200 * dt        # 200 píxeles por segundo, en cualquier celular
```
Para que sea de pantalla completa (sin barra superior), en `__init__.py` pon `header=False`.
Para detectar toques, escribe `on_touch_down(self, touch)` como en el ejemplo.

### Hacer una app con campos de texto y lista
**Mira [`examples/notas/`](../examples/notas/):** `TextInput`, una lista que se redibuja sola y guardado de datos.

### Tener varias ventanas dentro de tu panel
**Mira [`examples/varias_ventanas/`](../examples/varias_ventanas/):** un `ScreenManager` propio y `handle_back()`
para que «atrás» vuelva primero al menú de tu panel.

### Probar un ejemplo
```bash
# Windows (PowerShell):  Copy-Item -Recurse examples\juego_estrella panels\
# Mac / Linux:           cp -r examples/juego_estrella panels/
python dev.py panel juego_estrella
```
Si te gusta, **úsalo como punto de partida de tu panel** (copia el contenido a tu carpeta y cambia los nombres de
las clases) o bórralo cuando termines de estudiarlo (`panels/juego_estrella/`).

---

## 5. Imágenes, sonidos y archivos

- Ponlos **dentro de tu carpeta** `panels/<tu_nombre>/assets/` y úsalos con `self.asset("nombre.ext")` / `root.asset("nombre.ext")`.
- Formatos que se empaquetan en la app: `png`, `jpg`, `jpeg`, `kv`, `json`, `txt`, `ttf`, `otf`, `wav`, `ogg`, `mp3`.
- No uses rutas como `C:\Users\...`: no existen en el celular.
- Imágenes pesadas = app lenta. Mantén las fotos por debajo de 1–2 MB.

---

## 6. Agregar una librería nueva

La app solo trae **Kivy**. Si tu idea necesita otra librería de Python:

1. Instálala en tu entorno: `.venv\Scripts\pip install nombre` (Windows) / `.venv/bin/pip install nombre` (Mac/Linux).
2. Agrégala en **`requirements.txt`** (una línea: `nombre==1.2.3`).
3. Agrégala en **`buildozer.spec`**, en la línea `requirements = python3,kivy,nombre` (sin versión).
4. Haz `python dev.py check`: una prueba te avisa si las dos listas no coinciden.

⚠️ **No todas las librerías funcionan en el celular.** Las de Python puro (como `requests` o `plyer`) suelen
funcionar; las que tienen código compilado (como `numpy`, `pandas`, `opencv`) solo funcionan si existe una
«receta» para móviles. Si el build de Android o iOS falla después de agregar una librería, **es la causa más probable**.
Consulta con el profesor antes de usar librerías pesadas.

---

## 7. Git paso a paso (resumen)

```bash
git status                            # ¿qué cambié?
git add .                             # prepara TODOS tus cambios
git commit -m "Lo que hice hoy"       # los guarda en tu rama (un «punto de guardado»)
git push                              # los sube a GitHub (¡y se generan el APK y el IPA!)
```

- **Siempre en tu rama** (`git branch` te muestra cuál es; la activa tiene `*`). Nunca en `main`.
- Si `git push` dice «no upstream branch», ejecuta lo que te sugiere: `git push -u origin panel/<tu_nombre>`.
- Traer lo nuevo de `main`: `git fetch origin` y luego `git merge origin/main`.
- Si Git dice que hay un **conflicto**, no entres en pánico: avisa al profesor.

---

## 8. Errores frecuentes

| Qué ves | Qué significa y qué hacer |
|---|---|
| Hoja roja «Algo falló en tu panel» | Hay un error en **tu** código. Lee el mensaje y el archivo/línea. Arréglalo, guarda y pulsa **F5** (o «Reintentar»). El detalle completo está en la terminal. |
| Tu tarjeta sale en rojo en la portada | Tu panel no pudo cargar. Lee el motivo en la tarjeta. Suele ser un error de sintaxis o que `id` ≠ nombre de la carpeta. |
| `AttributeError: 'NoneType' object has no attribute 'ids'` | Estás usando `self.ids` demasiado pronto o el `.kv` no cargó. Usa `on_build` (no `__init__`). |
| `KeyError: 'nombre'` en `self.ids` | Ese `id:` no existe en tu `.kv`, o está escrito distinto. |
| `ParserException` | El `.kv` tiene mal la indentación o falta un `:`. Cuenta los espacios (siempre de 4 en 4). |
| El cambio del `.kv` «no hace nada» | ¿Guardaste el archivo? ¿Pulsaste **F5**? ¿El nombre de la regla `<...>:` es igual al de la clase de `panel.py`? |
| `dp` o `sp` «no está definido» | Al principio del `.kv` falta `#:import dp kivy.metrics.dp`. |
| Los widgets se salen de la pantalla | Usa `ScrollView` o `size_hint` en lugar de anchos fijos grandes. Pruébalo con la ventana angosta. |
| Funciona en PC pero no en el celular | Revisa: ¿usas una librería nueva? ¿rutas de tu computadora? ¿archivos con extensión no empaquetada? ¿emojis en los textos (algunos celulares no los muestran)? |

---

## 9. Lista de revisión antes de unir tu panel

- [ ] Mi panel se abre con `python dev.py panel <mi_carpeta>` y funciona de principio a fin.
- [ ] Probé con la ventana angosta y ancha (estirando con el ratón).
- [ ] `python dev.py check` pasa sin errores.
- [ ] Probé el **APK / IPA de mi rama** en un celular.
- [ ] Mi tarjeta tiene buen título, descripción y color en `__init__.py`.
- [ ] Solo modifiqué mi carpeta de `panels/` (o avisé qué más cambié).
