"""Genera el ícono de la app y la pantalla de carga (assets/icon.png y assets/presplash.png).

Solo hace falta ejecutarlo si quieres cambiar el diseño:   python scripts/make_assets.py
Los PNG ya están en el repositorio.
"""

import os
import sys
from pathlib import Path

os.environ["KIVY_NO_ARGS"] = "1"
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kivy.config import Config  # noqa: E402

Config.set("graphics", "width", "64")
Config.set("graphics", "height", "64")

from kivy.core.window import Window  # noqa: E402,F401  (crea el contexto OpenGL)
from kivy.graphics import (  # noqa: E402
    ClearBuffers,
    ClearColor,
    Color,
    Fbo,
    Rectangle,
    RoundedRectangle,
)

from hub import gfx, theme  # noqa: E402

SIZE = 512


def draw_glyph(fbo, with_background):
    """Cuatro «paneles» (cuadrados redondeados) en cuadrícula: la idea de la app."""
    with fbo:
        ClearColor(0, 0, 0, 0)
        ClearBuffers()
        if with_background:
            Color(1, 1, 1, 1)
            Rectangle(
                size=(SIZE, SIZE),
                texture=gfx.gradient(theme.hx("#3A2BD6"), theme.hx("#FF5E9A"), "d"),
            )
            Color(*theme.with_alpha(theme.hx("#2FB8FF"), 0.55))
            Rectangle(texture=gfx.glow(), pos=(-SIZE * 0.2, SIZE * 0.35), size=(SIZE * 1.0,) * 2)
        # La cuadrícula 2 x 2
        cell, gap = SIZE * 0.22, SIZE * 0.045
        total = cell * 2 + gap
        x0 = y0 = (SIZE - total) / 2
        alphas = (1.0, 0.62, 0.62, 0.32)
        for index, alpha in enumerate(alphas):
            col, row = index % 2, 1 - index // 2
            Color(1, 1, 1, alpha)
            RoundedRectangle(
                pos=(x0 + col * (cell + gap), y0 + row * (cell + gap)),
                size=(cell, cell),
                radius=[SIZE * 0.065],
            )
    fbo.draw()


def save(name, with_background):
    fbo = Fbo(size=(SIZE, SIZE), with_stencilbuffer=False)
    draw_glyph(fbo, with_background)
    path = ROOT / "assets" / name
    path.parent.mkdir(exist_ok=True)
    fbo.texture.save(str(path), flipped=True)
    print("Creado", path.relative_to(ROOT))


if __name__ == "__main__":
    save("icon.png", with_background=True)
    save("presplash.png", with_background=False)
