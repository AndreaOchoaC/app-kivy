"""Datos del panel de Jorge. Este archivo es lo único que la app lee para saber que el panel existe.

El código del juego está en panel.py, los dibujos en art.py y el diseño en panel.kv.
"""

from hub.panel import PanelInfo

from .panel import JorgePanel

PANEL = PanelInfo(
    # El id debe ser igual al nombre de la carpeta. Aquí se toma solo de ella,
    # así que NO tienes que cambiarlo.
    id=__name__.rsplit(".", 1)[-1],
    title="Jorge",
    subtitle="Flappy Bird",
    author="Jorge",
    color="#FBBF24",             # color de tu tarjeta (formato "#RRGGBB")
    screen_class=JorgePanel,     # la clase de panel.py (si le cambias el nombre, cámbialo aquí)
    header=False,                # pantalla completa (sin barra superior): ideal para juegos
    order=30,                    # posición en la lista de inicio (menor = antes)
)
