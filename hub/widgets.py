"""Widgets reutilizables: tarjetas, botones, textos, avatar, avisos...

Cada widget tiene dos partes:
  * la clase de Python (sus propiedades y su lógica), aquí, y
  * su aspecto, escrito en lenguaje KV, en hub/kv/widgets.kv.

Cualquier panel puede usarlos en su .kv sin importar nada (por ejemplo `PillButton:` o `Card:`).
La lista completa con ejemplos está en docs/CONTEXTO_IA.md.
"""

from pathlib import Path

from kivy.animation import Animation
from kivy.metrics import dp
from kivy.properties import (
    ColorProperty,
    NumericProperty,
    OptionProperty,
    StringProperty,
)
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from hub import theme
from hub.kvloader import load_kv

KV_DIR = Path(__file__).resolve().parent / "kv"


# ---------------------------------------------------------------------------- textos
class Heading(Label):
    """Título grande."""


class Title(Label):
    """Título mediano (nombre de una tarjeta, de una sección...)."""


class Body(Label):
    """Texto de lectura. Se ajusta solo al ancho y crece en alto según el texto."""


class Caption(Label):
    """Texto pequeño y apagado (notas, etiquetas, pies de foto)."""


# ---------------------------------------------------------------------------- superficies
class Card(BoxLayout):
    """Tarjeta con esquinas redondeadas, borde finísimo y sombra suave.

    Es un BoxLayout: dentro le pones lo que quieras. Propiedades: bg (color), radius.
    """

    bg = ColorProperty(theme.SURFACE)
    radius = NumericProperty(22)     # en dp; el .kv lo convierte
    scale = NumericProperty(1.0)     # 1 = tamaño normal (PressCard lo anima al tocarla)
    offset_y = NumericProperty(0.0)  # desplazamiento vertical (animación de entrada)


class PressCard(ButtonBehavior, Card):
    """Tarjeta que se puede tocar: se encoge un poco al presionarla (como en iOS)."""

    def on_state(self, _widget, state):
        Animation.cancel_all(self, "scale")
        Animation(scale=0.965 if state == "down" else 1.0, d=0.12, t="out_quad").start(self)


class PillButton(ButtonBehavior, Label):
    """Botón en forma de píldora. `kind`: "primary" (degradado), "secondary" o "ghost"."""

    kind = OptionProperty("primary", options=["primary", "secondary", "ghost"])
    accent = ColorProperty(theme.ACCENT)
    scale = NumericProperty(1.0)

    def on_state(self, _widget, state):
        Animation.cancel_all(self, "scale")
        Animation(scale=0.96 if state == "down" else 1.0, d=0.1, t="out_quad").start(self)


class Chip(Label):
    """Etiqueta pequeña con fondo de color suave."""

    tint = ColorProperty(theme.ACCENT)


class Avatar(Widget):
    """Círculo con degradado y una letra (la inicial del nombre)."""

    text = StringProperty("?")
    accent = ColorProperty(theme.ACCENT)
    accent2 = ColorProperty(theme.ACCENT_2)


class Swatch(ButtonBehavior, Widget):
    """Círculo de color que se puede tocar (para elegir colores). `value` es el color."""

    value = ColorProperty(theme.ACCENT)
    selected = NumericProperty(0)  # 1 si es el elegido: dibuja un aro alrededor


class Divider(Widget):
    """Línea fina horizontal."""


# ---------------------------------------------------------------------------- barras
class BackButton(ButtonBehavior, Widget):
    """Botón redondo con una flecha « < » dibujada (no usa fuentes de iconos)."""


class TopBar(BoxLayout):
    """Barra superior de un panel: botón de volver y título."""

    title = StringProperty("")
    accent = ColorProperty(theme.ACCENT)


class Toast(Label):
    """Aviso corto flotante. Se usa con `app.toast("mensaje")`."""


class ErrorSheet(FloatLayout):
    """Hoja que aparece cuando el código de un panel falla: explica qué pasó sin cerrar la app."""

    title = StringProperty("Algo falló en tu panel")
    message = StringProperty("")
    where = StringProperty("")

    def set_buttons(self, buttons):
        """`buttons` es una lista de (texto, función, tipo) con tipo "primary" o "secondary"."""
        box = self.ids.buttons
        box.clear_widgets()
        for text, callback, kind in buttons:
            btn = PillButton(text=text, kind=kind, size_hint_y=None, height=dp(52))
            btn.bind(on_release=lambda *_args, cb=callback: cb())
            box.add_widget(btn)

    # Es modal: consume todos los toques para que no lleguen al panel de abajo.
    def on_touch_down(self, touch):
        super().on_touch_down(touch)
        return True

    def on_touch_move(self, touch):
        super().on_touch_move(touch)
        return True

    def on_touch_up(self, touch):
        super().on_touch_up(touch)
        return True


class Aurora(Widget):
    """Fondo animado: un degradado oscuro con luces de colores que flotan despacio."""

    phase = NumericProperty(0.0)  # va de 0 a 1 y vuelve; el .kv mueve las luces con él

    def on_parent(self, _widget, parent):
        Animation.cancel_all(self, "phase")
        if parent is not None:
            anim = Animation(phase=1.0, d=22) + Animation(phase=0.0, d=22)
            anim.repeat = True
            anim.start(self)


load_kv(KV_DIR / "widgets.kv")
