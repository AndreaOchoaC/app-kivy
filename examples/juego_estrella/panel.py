"""EJEMPLO DE JUEGO: «Atrapa la estrella».

Qué enseña:
  * run_update = True  ->  Kivy llama a update(dt) unas 60 veces por segundo.
  * dt (segundos desde el cuadro anterior): mover con  posición += velocidad * dt  hace que
    el juego vaya igual de rápido en cualquier celular.
  * on_touch_down: reaccionar a los toques.
  * Properties (score, time_left...) que el .kv muestra y actualiza SOLO.
  * save / load para recordar la mejor puntuación.
"""

import math
import random

from kivy.metrics import dp
from kivy.properties import BooleanProperty, NumericProperty

from hub.panel import PanelScreen


class JuegoEstrellaPanel(PanelScreen):
    run_update = True               # ¡el interruptor del juego!

    TIME_LIMIT = 20.0               # segundos por partida
    score = NumericProperty(0)
    best = NumericProperty(0)
    time_left = NumericProperty(0)
    playing = BooleanProperty(False)

    def on_build(self):
        self.best = self.load("best", 0)
        self.vx = self.vy = 0.0

    # ------------------------------------------------------------------ partida
    def start(self):
        """Empieza (o reinicia) una partida."""
        self.score = 0
        self.time_left = self.TIME_LIMIT
        self.playing = True
        self.ids.star.center = self.ids.arena.center
        self._set_speed(dp(170))

    def _set_speed(self, speed):
        angle = random.uniform(0, 2 * math.pi)
        self.vx, self.vy = math.cos(angle) * speed, math.sin(angle) * speed

    def finish(self):
        self.playing = False
        if self.score > self.best:
            self.best = self.score
            self.save("best", self.best)
            self.toast(f"¡Nuevo récord: {self.score}!")

    # ------------------------------------------------------------------ cada cuadro
    def update(self, dt):
        if not self.playing:
            return
        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = 0
            self.finish()
            return

        star, arena = self.ids.star, self.ids.arena
        star.x += self.vx * dt              # distancia = velocidad × tiempo
        star.y += self.vy * dt
        # Rebote en las paredes de la arena
        if star.x < arena.x or star.right > arena.right:
            self.vx = -self.vx
            star.x = min(max(star.x, arena.x), arena.right - star.width)
        if star.y < arena.y or star.top > arena.top - dp(70):   # dejamos sitio al marcador
            self.vy = -self.vy
            star.y = min(max(star.y, arena.y), arena.top - dp(70) - star.height)

    # ------------------------------------------------------------------ toques
    def on_touch_down(self, touch):
        if super().on_touch_down(touch):          # primero los botones (empezar, volver...)
            return True
        if self.playing and self.ids.star.collide_point(*touch.pos):
            self.score += 1
            self._set_speed(math.hypot(self.vx, self.vy) * 1.06)   # cada acierto, más rápido
            return True
        return False
