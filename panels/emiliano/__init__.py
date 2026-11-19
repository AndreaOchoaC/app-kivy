"""Datos del panel de Emiliano. Este archivo es lo único que la app lee para saber que el panel existe.

El código del juego está en panel.py, los dibujos en art.py y el diseño en panel.kv.
"""

from hub.panel import PanelInfo

from .panel import EmilianoPanel

PANEL = PanelInfo(
    # El id debe ser igual al nombre de la carpeta. Aquí se toma solo de ella,
    # así que NO tienes que cambiarlo.
    id=__name__.rsplit(".", 1)[-1],
    title="Emiliano",
    subtitle="Flappy Bird",
    author="Emiliano",
    color="#2FB8FF",             # color de tu tarjeta (formato "#RRGGBB")
    screen_class=EmilianoPanel,     # la clase de panel.py (si le cambias el nombre, cámbialo aquí)
    header=False,                # pantalla completa (sin barra superior): ideal para juegos
    order=20,                    # posición en la lista de inicio (menor = antes)
)
