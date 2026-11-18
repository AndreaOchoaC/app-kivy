"""EJEMPLO: un panel con VARIAS ventanas dentro (un ScreenManager propio)."""

from hub.panel import PanelInfo

from .panel import VariasVentanasPanel

PANEL = PanelInfo(
    id=__name__.rsplit(".", 1)[-1],
    title="Varias ventanas",
    subtitle="Un panel puede tener su propio menú y sus propias pantallas internas.",
    author="Ejemplo",
    color="#A78BFA",
    screen_class=VariasVentanasPanel,
)
