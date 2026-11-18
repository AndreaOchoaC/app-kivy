"""PLANTILLA de panel. NO la edites: crea la tuya con   python dev.py new <tu_nombre>

Este archivo es lo único que la app lee para saber que tu panel existe: aquí van los
DATOS de tu panel (título, color, autor). El código va en panel.py y el diseño en panel.kv.
"""

from hub.panel import PanelInfo

from .panel import EmilianoPanel

PANEL = PanelInfo(
    # El id debe ser igual al nombre de la carpeta. Aquí se toma solo de ella,
    # así que NO tienes que cambiarlo.
    id=__name__.rsplit(".", 1)[-1],
    title="Panel de Emiliano",
    subtitle="Aquí vive lo que yo construyo: un juego, una app o varias ventanas.",
    author="Emiliano",
    color="#2FB8FF",             # color de tu tarjeta (formato "#RRGGBB")
    screen_class=EmilianoPanel,  # la clase de panel.py (si le cambias el nombre, cámbialo aquí)
    # header=False,              # quita la barra superior: pantalla completa (ideal para juegos)
    order=20,                 # posición en la lista de inicio (menor = antes)
)
