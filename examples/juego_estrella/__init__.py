"""EJEMPLO: un juego con bucle de actualización (update) y pantalla completa."""

from hub.panel import PanelInfo

from .panel import JuegoEstrellaPanel

PANEL = PanelInfo(
    id=__name__.rsplit(".", 1)[-1],
    title="Atrapa la estrella",
    subtitle="Toca la estrella antes de que se acabe el tiempo. ¡Cada toque la hace más rápida!",
    author="Ejemplo",
    color="#FBBF24",
    screen_class=JuegoEstrellaPanel,
    header=False,        # pantalla completa: sin barra superior (queda un botón «<» flotante)
)
