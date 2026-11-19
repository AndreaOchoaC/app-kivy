"""Constantes generales de la app. No importa Kivy: se puede usar desde cualquier lado."""

APP_NAME = "App"

# Paquete de Python donde viven los paneles (la carpeta panels/).
PANELS_PACKAGE = "panels"

# Tamaño de la ventana (en píxeles) SOLO al probar en el PC: imita un teléfono vertical.
# Es pequeño a propósito: con la escala de Windows al 150 % una ventana más alta no cabe
# en un monitor de 1080p. Se puede estirar con el ratón para probar otros tamaños.
DEV_WINDOW = (390, 760)
DEV_WINDOW_MIN = (300, 520)
