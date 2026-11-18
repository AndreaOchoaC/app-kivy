"""Pantalla de inicio: portada de la app con una tarjeta por cada panel del equipo."""

from __future__ import annotations

from datetime import datetime

from kivy.animation import Animation
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ColorProperty, NumericProperty, StringProperty
from kivy.uix.screenmanager import Screen

from hub import theme
from hub.build_info import BRANCH, COMMIT
from hub.config import APP_NAME, APP_TAGLINE, APP_VERSION
from hub.device import safe_insets
from hub.kvloader import load_kv
from hub.widgets import KV_DIR, PressCard


class PanelCard(PressCard):
    """Tarjeta de un panel en la pantalla de inicio. Si el panel falló, muestra el error."""

    panel_id = StringProperty("")
    title = StringProperty("")
    subtitle = StringProperty("")
    author = StringProperty("")
    initial = StringProperty("?")
    accent = ColorProperty(theme.ACCENT)
    accent2 = ColorProperty(theme.ACCENT_2)
    ok = BooleanProperty(True)


def greeting(now: datetime | None = None) -> str:
    """«Buenos días», «Buenas tardes» o «Buenas noches» según la hora."""
    hour = (now or datetime.now()).hour
    if hour < 6:
        return "Buenas noches"
    if hour < 13:
        return "Buenos días"
    if hour < 20:
        return "Buenas tardes"
    return "Buenas noches"


class HomeScreen(Screen):
    """Portada: título, resumen del equipo y la lista de paneles."""

    app_name = StringProperty(APP_NAME)
    tagline = StringProperty(APP_TAGLINE)
    greeting = StringProperty("")
    count_text = StringProperty("")
    version_text = StringProperty("")
    credits = StringProperty("")
    inset_top = NumericProperty(0)
    inset_bottom = NumericProperty(0)

    def __init__(self, **kwargs):
        self._intro_done = False
        super().__init__(**kwargs)
        self.inset_top, self.inset_bottom = safe_insets()
        self.greeting = greeting()
        self.version_text = f"v{APP_VERSION} · {BRANCH}" + (f" · {COMMIT[:7]}" if COMMIT else "")

    # ------------------------------------------------------------------ contenido
    def populate(self, entries):
        """Crea una tarjeta por cada panel (los que fallaron salen en rojo, con el motivo)."""
        grid = self.ids.grid
        grid.clear_widgets()
        authors = []
        for entry in entries:
            if entry.ok:
                info = entry.info
                card = PanelCard(
                    panel_id=info.id,
                    title=info.title,
                    subtitle=info.subtitle,
                    author=info.author,
                    initial=(info.author or info.title or "?").strip()[:1].upper(),
                    accent=info.accent,
                    accent2=info.accent2,
                )
                if info.author and info.author not in authors:
                    authors.append(info.author)
            else:
                card = PanelCard(
                    panel_id=entry.folder,
                    title=entry.folder,
                    subtitle=f"No se pudo cargar: {entry.error}",
                    initial="!",
                    accent=theme.DANGER,
                    accent2=theme.DANGER,
                    ok=False,
                )
            grid.add_widget(card)
        good = sum(1 for e in entries if e.ok)
        self.count_text = f"{good} PANEL" + ("" if good == 1 else "ES")
        self.credits = _join_names(authors)

    # ------------------------------------------------------------------ animación de entrada
    def on_enter(self, *_args):
        if self._intro_done:
            return
        self._intro_done = True
        for index, card in enumerate(reversed(self.ids.grid.children)):
            card.opacity = 0
            card.offset_y = -dp(28)
            appear = Animation(opacity=1, offset_y=0, d=0.5, t="out_cubic")
            (Animation(d=0.08 * index + 0.05) + appear).start(card)  # cada tarjeta, un poco después


def _join_names(names):
    if not names:
        return ""
    if len(names) == 1:
        return f"Hecho por {names[0]}"
    return "Hecho por " + ", ".join(names[:-1]) + " y " + names[-1]


load_kv(KV_DIR / "home.kv")
