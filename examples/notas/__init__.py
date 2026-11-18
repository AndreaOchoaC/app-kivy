"""EJEMPLO: una app de notas que recuerda lo que escribes (TextInput + lista + guardado)."""

from hub.panel import PanelInfo

from .panel import NotasPanel

PANEL = PanelInfo(
    id=__name__.rsplit(".", 1)[-1],
    title="Mis notas",
    subtitle="Escribe ideas y se guardan solas, aunque cierres la app.",
    author="Ejemplo",
    color="#34D399",
    screen_class=NotasPanel,
)
