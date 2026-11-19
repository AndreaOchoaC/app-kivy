"""Pantalla de inicio: el nombre de la app y una tarjeta por cada panel del equipo."""

from __future__ import annotations

from kivy.animation import Animation
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ColorProperty, NumericProperty, StringProperty
from kivy.uix.screenmanager import Screen

from hub import theme
from hub.config import APP_NAME
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


class HomeScreen(Screen):
    """Portada: el nombre de la app y la lista de paneles."""

    app_name = StringProperty(APP_NAME)
    inset_top = NumericProperty(0)
    inset_bottom = NumericProperty(0)

    def __init__(self, **kwargs):
        self._intro_done = False
        super().__init__(**kwargs)
        self.inset_top, self.inset_bottom = safe_insets()

    # ------------------------------------------------------------------ contenido
    def populate(self, entries):
        """Crea una tarjeta por cada panel (los que fallaron salen en rojo, con el motivo)."""
        grid = self.ids.grid
        grid.clear_widgets()
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


load_kv(KV_DIR / "home.kv")
