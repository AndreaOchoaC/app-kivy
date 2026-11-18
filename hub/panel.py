"""El «contrato» que cumple cada panel para integrarse en la app.

Cada panel es una carpeta dentro de `panels/` con tres cosas:

  1. `__init__.py`  define `PANEL = PanelInfo(...)`: nombre, color, autor. Es lo único que la
                    app lee para saber que tu panel existe.
  2. `panel.py`     una clase que hereda de `PanelScreen` (tu lógica en Python).
  3. `panel.kv`     el aspecto de tu panel en lenguaje KV (se carga solo).

`PanelScreen` se encarga de lo común, para que tú solo programes lo tuyo:
  * la barra superior con el botón de volver (y el botón «atrás» de Android / la tecla Esc),
  * el fondo, los márgenes seguros del iPhone y las animaciones de entrada y salida,
  * llamar a tus «ganchos» en el momento justo (on_build, on_show, on_hide, update),
  * guardar datos de tu panel (self.save / self.load),
  * atrapar los errores de tu código para que NO tumben el resto de la app.

Mira panels/_template/ para ver un ejemplo mínimo que funciona.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from kivy.clock import Clock
from kivy.properties import (
    BooleanProperty,
    ColorProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen

from hub import theme
from hub.kvloader import load_kv
from hub.widgets import KV_DIR

# Minúsculas, números y guion bajo. (Puede empezar con _ porque la plantilla es «_template».)
_ID_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")


@dataclass(frozen=True)
class PanelInfo:
    """Datos de un panel. Se declaran en el `__init__.py` del panel como `PANEL = PanelInfo(...)`.

    id            nombre corto en minúsculas. DEBE ser igual al nombre de la carpeta.
    title         nombre que se muestra en la tarjeta y en la barra superior.
    subtitle      una o dos frases sobre qué hace tu panel.
    author        quién lo hizo.
    color         color de la tarjeta, en hexadecimal (por ejemplo "#FF5E8A").
    screen_class  la clase de tu panel (hereda de PanelScreen).
    color2        segundo color del degradado (opcional; si no lo pones se calcula solo).
    version       versión de tu panel (libre).
    order         posición en la lista (menor = antes). Si hay empate, por título.
    header        True: la app te da una barra superior con el botón de volver.
                  False: pantalla completa (ideal para juegos); aparece solo un botón «<» flotante.
    """

    id: str
    title: str
    subtitle: str
    author: str
    color: str
    screen_class: type
    color2: str | None = None
    version: str = "0.1.0"
    order: int = 100
    header: bool = True

    def __post_init__(self):
        if not _ID_PATTERN.match(self.id):
            raise ValueError(
                f"id '{self.id}' no es válido: usa solo minúsculas, números y _ (sin espacios)"
            )
        for name in ("color", "color2"):
            value = getattr(self, name)
            if value is None and name == "color2":
                continue
            if not (isinstance(value, str) and value.startswith("#") and len(value) in (4, 7)):
                raise ValueError(f"{name} '{value}' no es válido: usa formato '#RRGGBB'")

    @property
    def accent(self) -> tuple:
        return theme.hx(self.color)

    @property
    def accent2(self) -> tuple:
        return theme.hx(self.color2) if self.color2 else theme.companion(self.accent)


class PanelFrame(FloatLayout):
    """Marco del panel: fondo, barra superior y el área `content` donde va TU diseño."""

    content = ObjectProperty(None)
    title = StringProperty("")
    accent = ColorProperty(theme.ACCENT)
    show_bar = BooleanProperty(True)
    inset_top = NumericProperty(0)
    inset_bottom = NumericProperty(0)


class PanelScreen(Screen):
    """Clase base de todos los paneles. Tu panel hereda de ella.

    Lo que puedes usar:

      Ganchos (escribe estos métodos en tu clase; todos son opcionales)
        on_build(self)    se ejecuta UNA vez, cuando tu panel ya tiene su diseño (.kv).
        on_show(self)     cada vez que tu panel aparece en pantalla.
        on_hide(self)     cada vez que sale de pantalla (o la app pasa a segundo plano).
        update(self, dt)  ~60 veces por segundo mientras tu panel está visible, si pones
                          `run_update = True`. `dt` son los segundos desde la vez anterior.
        handle_back(self) el usuario pulsó «atrás». Devuelve True si lo manejaste tú;
                          por defecto vuelve al inicio.

      Herramientas
        self.save("clave", valor) / self.load("clave", por_defecto)   datos que se recuerdan
        self.toast("mensaje")                                          aviso corto abajo
        self.go_home()                                                 volver al inicio
        self.asset("foto.png")                                         ruta a tu carpeta assets/
        self.ids.nombre                                                widgets con `id:` del .kv
        self.content                                                   el área donde va tu diseño
    """

    info = ObjectProperty(None, allownone=True)
    title = StringProperty("")
    author = StringProperty("")
    subtitle = StringProperty("")
    accent = ColorProperty(theme.ACCENT)
    show_bar = BooleanProperty(True)

    # Ponlo en True en tu clase (`run_update = True`) para recibir update(dt) cada cuadro.
    run_update = False

    def __init__(self, info: PanelInfo | None = None, storage=None, **kwargs):
        self._frame = None
        self._tick_event = None
        self._memory: dict = {}          # datos de respaldo cuando no hay Storage (pruebas)
        self.storage = storage
        if info is not None:
            kwargs.setdefault("name", info.id)
            kwargs.setdefault("title", info.title)
            kwargs.setdefault("author", info.author)
            kwargs.setdefault("subtitle", info.subtitle)
            kwargs.setdefault("accent", info.accent)
            kwargs.setdefault("show_bar", info.header)
        kwargs["info"] = info
        super().__init__(**kwargs)
        self.on_build()

    # ------------------------------------------------------------------ estructura
    @property
    def content(self):
        """El área donde va el diseño de tu panel (lo que escribes en tu .kv va aquí dentro)."""
        return self._frame.content if self._frame is not None else self

    def add_widget(self, widget, *args, **kwargs):
        # El marco (PanelFrame) se añade al Screen; TODO lo demás (lo de tu .kv o lo que añadas
        # con self.add_widget) va dentro del área de contenido, debajo de la barra superior.
        if isinstance(widget, PanelFrame):
            self._frame = widget
            return super().add_widget(widget, *args, **kwargs)
        if self._frame is None:
            return super().add_widget(widget, *args, **kwargs)
        return self._frame.content.add_widget(widget, *args, **kwargs)

    def clear_widgets(self, children=None):
        if children is None and self._frame is not None:
            return self._frame.content.clear_widgets()
        return super().clear_widgets(children)

    # ------------------------------------------------------------------ ganchos para el alumno
    def on_build(self):
        """Gancho: se ejecuta una vez, con el diseño del .kv ya creado."""

    def on_show(self):
        """Gancho: el panel aparece en pantalla."""

    def on_hide(self):
        """Gancho: el panel sale de pantalla."""

    def update(self, dt):
        """Gancho: se llama cada cuadro si `run_update` es True."""

    def handle_back(self) -> bool:
        """Gancho: botón «atrás». Devuelve True si lo manejaste (por ejemplo, con una subpantalla)."""
        self.go_home()
        return True

    # ------------------------------------------------------------------ herramientas
    def save(self, key: str, value):
        """Guarda un dato (texto, número, lista o diccionario) en el espacio de TU panel."""
        if self.storage is not None:
            self.storage.set(self.name, key, value)
        else:
            self._memory[key] = value

    def load(self, key: str, default=None):
        """Lee un dato guardado con save(). Si nunca se guardó, devuelve `default`."""
        if self.storage is not None:
            return self.storage.get(self.name, key, default)
        return self._memory.get(key, default)

    def toast(self, message: str):
        """Muestra un aviso corto en la parte baja de la pantalla."""
        app = _running_app()
        if app is not None:
            app.toast(message)

    def go_home(self):
        """Vuelve a la pantalla de inicio."""
        app = _running_app()
        if app is not None:
            app.go_home()

    def asset(self, filename: str) -> str:
        """Ruta completa de un archivo de la carpeta `assets/` de tu panel (imágenes, sonidos...)."""
        module = sys.modules[type(self).__module__]
        return str(Path(module.__file__).resolve().parent / "assets" / filename)

    # ------------------------------------------------------------------ ciclo de vida (no tocar)
    def on_enter(self, *_args):
        self.on_show()
        if self.run_update:
            self.start_updates()

    def on_leave(self, *_args):
        self.stop_updates()
        self.on_hide()

    def start_updates(self):
        if self._tick_event is None:
            self._tick_event = Clock.schedule_interval(self._tick, 1 / 60.0)

    def stop_updates(self):
        if self._tick_event is not None:
            self._tick_event.cancel()
            self._tick_event = None

    def _tick(self, dt):
        self.update(dt)


def _running_app():
    from kivy.app import App

    return App.get_running_app()


load_kv(KV_DIR / "panel.kv")
