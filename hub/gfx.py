"""Texturas generadas por código: degradados, luces y sombras suaves.

Kivy no trae degradados ni sombras difuminadas, así que los dibujamos una vez en una
textura pequeña (en memoria, sin archivos de imagen) y el GPU la estira. Resultado: se ve
suave y no cuesta casi nada.

Se usan desde los .kv:   texture: gfx.gradient(self.color_a, self.color_b, "d")
Las texturas se guardan en caché, así que pedir la misma dos veces es gratis.
"""

from __future__ import annotations

import math
from functools import lru_cache

from kivy.graphics.texture import Texture


def _make(width: int, height: int, pixels: bytearray) -> Texture:
    texture = Texture.create(size=(width, height), colorfmt="rgba")
    texture.blit_buffer(bytes(pixels), colorfmt="rgba", bufferfmt="ubyte")
    texture.min_filter = "linear"
    texture.mag_filter = "linear"
    return texture


def _key(color) -> tuple:
    return tuple(round(float(c), 3) for c in color)


@lru_cache(maxsize=256)
def _gradient(c1: tuple, c2: tuple, direction: str) -> Texture:
    size = 32
    pixels = bytearray()
    # Kivy dibuja la fila 0 de la textura ABAJO. Por eso recorremos desde abajo hacia arriba.
    for row in range(size):
        v = row / (size - 1)          # 0 = abajo, 1 = arriba
        for col in range(size):
            u = col / (size - 1)      # 0 = izquierda, 1 = derecha
            if direction == "h":
                t = u
            elif direction == "d":    # de arriba-izquierda a abajo-derecha
                t = (u + (1 - v)) / 2
            else:                     # "v": de arriba a abajo
                t = 1 - v
            for i in range(4):
                pixels.append(int(max(0.0, min(1.0, c1[i] + (c2[i] - c1[i]) * t)) * 255))
    return _make(size, size, pixels)


def gradient(color_a, color_b, direction: str = "v") -> Texture:
    """Degradado de `color_a` a `color_b`.

    direction: "v" (de arriba a abajo), "h" (de izquierda a derecha) o "d" (en diagonal).
    Se usa como `texture:` de un Rectangle o RoundedRectangle (con `Color: rgba: 1, 1, 1, 1`).
    """
    return _gradient(_key(color_a), _key(color_b), direction)


@lru_cache(maxsize=1)
def glow() -> Texture:
    """Mancha de luz circular, blanca y difuminada. Se tiñe con `Color` antes de dibujarla."""
    size = 96
    pixels = bytearray()
    centre = (size - 1) / 2
    for y in range(size):
        for x in range(size):
            r = math.hypot(x - centre, y - centre) / centre
            alpha = max(0.0, 1.0 - r) ** 2.2
            pixels += bytes((255, 255, 255, int(alpha * 255)))
    return _make(size, size, pixels)


@lru_cache(maxsize=1)
def shadow() -> Texture:
    """Sombra suave para una tarjeta. Se dibuja con BorderImage para que se estire sin deformarse.

    La «caja» opaca ocupa del píxel 24 al 72; hay que usar border=(36, 36, 36, 36) (esquinas
    de 12 px incluidas) y recordar que la sombra sobresale 24 px a cada lado de la tarjeta.
    """
    size, margin, blur, radius = 96, 24, 11.0, 12.0
    half = size / 2 - margin                      # mitad del lado de la «caja» central
    pixels = bytearray()
    for y in range(size):
        for x in range(size):
            px, py = abs(x - (size - 1) / 2), abs(y - (size - 1) / 2)
            qx, qy = px - (half - radius), py - (half - radius)
            # Distancia con signo a un rectángulo redondeado (negativa = dentro).
            dist = math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - radius
            t = max(0.0, min(1.0, (dist + blur) / (2 * blur)))
            alpha = 1 - t * t * (3 - 2 * t)       # smoothstep invertido: 1 dentro, 0 fuera
            pixels += bytes((0, 0, 0, int(alpha * 255)))
    return _make(size, size, pixels)
