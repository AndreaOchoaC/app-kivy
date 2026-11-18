"""Punto de entrada de la app.

    python main.py            abre la app completa
    python main.py pilar      abre SOLO el panel «pilar» (cámbialo por el nombre de tu carpeta)

Android (buildozer) e iOS (kivy-ios) buscan exactamente este archivo: main.py en la raíz.
En el PC la ventana imita un teléfono vertical para que se vea como en el móvil.
"""

import sys

# Si pasaste el nombre de un panel, lo guardamos y lo quitamos de sys.argv: Kivy lee los
# argumentos al importarse y no entendería una palabra suelta.
ONLY_PANEL = None
if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
    ONLY_PANEL = sys.argv[1]
    del sys.argv[1:]

from kivy.config import Config  # noqa: E402
from kivy.utils import platform  # noqa: E402

# Esta configuración debe ir ANTES de importar Window (o sea, antes de importar la app).
if platform not in ("android", "ios"):
    from hub.config import DEV_WINDOW, DEV_WINDOW_MIN

    Config.set("graphics", "width", str(DEV_WINDOW[0]))
    Config.set("graphics", "height", str(DEV_WINDOW[1]))
    Config.set("graphics", "minimum_width", str(DEV_WINDOW_MIN[0]))
    Config.set("graphics", "minimum_height", str(DEV_WINDOW_MIN[1]))
    # Con clic derecho Kivy dibuja puntos rojos (multitoque simulado): no los queremos.
    Config.set("input", "mouse", "mouse,disable_multitouch")
# Esc NO cierra la app: lo usamos como botón «atrás» (igual que en Android).
Config.set("kivy", "exit_on_escape", "0")

from hub.app import HubApp  # noqa: E402

if __name__ == "__main__":
    HubApp(only=ONLY_PANEL).run()
