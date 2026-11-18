"""Paleta de colores y tipografía de la app (colores RGBA de Kivy: 4 números entre 0 y 1).

Se usa desde Python (`theme.ACCENT`) y desde los archivos .kv (`#:import theme hub.theme`).
Los paneles pueden usarla para verse coherentes con el resto de la app.

Los colores son TUPLAS (no listas) para poder usarlos como clave de caché.
"""

import colorsys

from kivy.utils import get_color_from_hex


def hx(value: str, alpha: float = 1.0) -> tuple:
    """'#RRGGBB' -> (r, g, b, a). Ejemplo: hx('#FF0000', 0.5) es rojo al 50 %."""
    r, g, b, _ = get_color_from_hex(value)
    return (r, g, b, alpha)


def with_alpha(color, alpha: float) -> tuple:
    """El mismo color con otra transparencia."""
    return (color[0], color[1], color[2], alpha)


def mix(a, b, t: float) -> tuple:
    """Mezcla dos colores: t=0 es `a`, t=1 es `b`."""
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(4))


def companion(color) -> tuple:
    """Segundo color para degradados: el mismo color, un poco más oscuro y desplazado hacia el violeta.

    Así el amarillo se vuelve naranja, el rosa se vuelve magenta y el azul se vuelve índigo.
    """
    h, s, v = colorsys.rgb_to_hsv(color[0], color[1], color[2])
    diff = ((0.74 - h + 0.5) % 1.0) - 0.5          # camino más corto hacia el violeta (0.74)
    h = (h + max(-0.09, min(0.09, diff))) % 1.0
    r, g, b = colorsys.hsv_to_rgb(h, min(1.0, s * 1.05), v * 0.80)
    return (r, g, b, color[3] if len(color) > 3 else 1.0)


# --- Fondos y superficies (de más oscuro a más claro) ------------------------------------
BG = hx("#08080F")          # fondo general
BG_TOP = hx("#14142A")      # parte alta del degradado de fondo
SURFACE = hx("#16161F")     # tarjetas y paneles
SURFACE_HI = hx("#202030")  # botones secundarios, elementos elevados
HAIRLINE = (1, 1, 1, 0.09)  # borde finísimo de las tarjetas

# --- Texto --------------------------------------------------------------------------------
TEXT = hx("#F5F5F7")        # texto principal
TEXT_2 = hx("#C4C4D4")      # texto de lectura
MUTED = hx("#8E8EA8")       # texto secundario
FAINT = hx("#5E5E78")       # texto terciario

# --- Marca y estados ----------------------------------------------------------------------
ACCENT = hx("#7C6CFF")
ACCENT_2 = hx("#4B8DFF")
SUCCESS = hx("#34D399")
WARNING = hx("#FBBF24")
DANGER = hx("#F87171")

# Colores de las luces del fondo animado de la pantalla de inicio.
AURORA = (hx("#7C6CFF"), hx("#2FB8FF"), hx("#FF5E9A"))
