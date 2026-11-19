"""Flappy Bird: toca para aletear y pasa entre los tubos.

Todo se dibuja por código (sin imágenes). Es un buen ejemplo de un juego completo:

  * Fases propias dentro del juego: "ready" (esperando el primer toque), "play", "dead" y
    "over" (el pájaro ya cayó y se muestra el marcador final).
  * Física sencilla con gravedad: velocidad vertical que cambia con el tiempo (dt).
  * Escala por altura de pantalla: todas las medidas están en «unidades» (u = alto/640),
    así el juego se ve igual en un móvil pequeño que en uno grande.
  * Fondo con parallax (capas que se mueven a distinta velocidad) usando texturas en mosaico.
  * Colisiones círculo-rectángulo, partículas, sacudida de pantalla y sonidos.

Cómo se conecta con la app:
  * `run_update = True`  ->  la app llama a update(dt) unas 60 veces por segundo.
  * panel.kv tiene los textos (marcador, «TOCA PARA VOLAR») y la tarjeta de fin de partida.
  * Lo que se dibuja a mano (cielo, tubos, pájaro) va en `GameStage`, del que se ocupa hub/gamekit.py.
  * self.save / self.load recuerdan la mejor puntuación aunque cierres la app.

Para cambiar el juego, empieza por las constantes de aquí abajo (gravedad, salto, hueco...).
"""

import math
import random

from kivy.animation import Animation
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, PopMatrix, PushMatrix, Rectangle, Rotate, Scale, Translate
from kivy.metrics import dp
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.utils import get_color_from_hex as hx

from hub.gamekit import ParticleBurst, play_sound, vertical_gradient, vibrate, warm_up_sounds
from hub.panel import PanelScreen

from .art import ground_texture, pipe_body_texture, pipe_cap_texture, skyline_texture

# ---- Constantes de juego (en «unidades»: 1 unidad = alto de pantalla / 640) ----------
GRAVITY = 1500.0        # aceleración hacia abajo
FLAP_SPEED = 440.0      # velocidad hacia arriba al aletear
MAX_FALL = 640.0        # velocidad máxima de caída
GROUND_H = 84.0         # alto del suelo
BIRD_R = 14.0           # radio de colisión del pájaro (un poco menor que el dibujo: es justo)
PIPE_W = 58.0           # ancho del cuerpo del tubo
CAP_W, CAP_H = 66.0, 26.0
PIPE_SPACING = 218.0    # distancia horizontal entre tubos
START_SPEED = 138.0     # velocidad de los tubos al inicio...
MAX_SPEED = 188.0       # ...y al final
GAP_START, GAP_MIN = 170.0, 142.0   # hueco entre tubos: empieza amplio y se va cerrando
HUD_H = 64.0            # alto de la zona superior (los tubos no dejan el hueco ahí)
KEY_SPACE, KEY_UP = 32, 273

# Colores del pájaro (¡cámbialos!)
BIRD_BODY = "#FFD23F"
BIRD_WING = "#F5A80A"


def _circle_hits_rect(cx, cy, r, rx, ry, rw, rh):
    """¿Un círculo (cx, cy, r) toca el rectángulo (rx, ry, rw, rh)?"""
    nearest_x = max(rx, min(cx, rx + rw))
    nearest_y = max(ry, min(cy, ry + rh))
    return (cx - nearest_x) ** 2 + (cy - nearest_y) ** 2 < r * r


class EmilianoPanel(PanelScreen):
    run_update = True               # ¡el interruptor del juego!

    score = NumericProperty(0)
    best = NumericProperty(0)
    phase = StringProperty("ready")     # "ready", "play", "dead" u "over"
    new_record = BooleanProperty(False)

    # ------------------------------------------------------------------ construcción
    def on_build(self):
        self.best = self.load("best", 0)
        self.stage = self.ids.stage
        # La tarjeta de «fin de partida» viene en el .kv, pero solo se muestra al perder.
        # (`ids` guarda referencias débiles: `.__self__` nos da el widget de verdad, para que
        #  no desaparezca mientras está fuera de la pantalla.)
        self._overlay = self.ids.overlay.__self__
        self.ids.arena.remove_widget(self._overlay)

        self.u = 1.0                # escala; se calcula en _layout() con el alto real
        self.time = 0.0
        self.scroll_ground = 0.0
        self.scroll_city = 0.0
        self.flap_glow = 0.0
        self.shake = 0.0
        self.flash = 0.0
        self.dead_timer = 0.0
        self.pipes = []
        self._keys_bound = False

        self._build_scene()
        self.stage.bind(size=lambda *_: self._on_resize())
        self.new_game()

    def _build_scene(self):
        """Crea una sola vez todo lo que se dibuja (después solo se mueve, nunca se vuelve a crear)."""
        stage = self.stage
        tex_sky = vertical_gradient(["#2F9BF2", "#6CC4FF", "#C6EEFF"])
        self.tex_city = skyline_texture()
        self.tex_ground = ground_texture()
        tex_body, tex_cap = pipe_body_texture(), pipe_cap_texture()

        with stage.canvas:
            Color(1, 1, 1, 1)
            self.sky = Rectangle(texture=tex_sky, size=(10, 10))
            self.city = Rectangle(texture=self.tex_city, size=(10, 10))

            # Nubes: 4 elipses por nube. Se reutilizan siempre (no se crean más).
            self.clouds = []
            for _ in range(5):
                Color(1, 1, 1, 0.9)
                parts = [Ellipse(size=(1, 1)) for _ in range(4)]
                self.clouds.append({"parts": parts, "x": 0, "y": 0, "s": 1, "v": 0})

            # Tubos: 4 pares (se reciclan al salir por la izquierda).
            Color(1, 1, 1, 1)
            for _ in range(4):
                self.pipes.append(
                    {
                        "x": -999.0, "gap_y": 0.0, "gap": GAP_START, "passed": False,
                        "top_body": Rectangle(texture=tex_body, size=(1, 1)),
                        "top_cap": Rectangle(texture=tex_cap, size=(1, 1)),
                        "bot_body": Rectangle(texture=tex_body, size=(1, 1)),
                        "bot_cap": Rectangle(texture=tex_cap, size=(1, 1)),
                    }
                )

            Color(1, 1, 1, 1)
            self.ground = Rectangle(texture=self.tex_ground, size=(10, 10))
            self._build_bird()

        # Encima de todo: partículas y el destello blanco al chocar.
        self.particles = ParticleBurst(stage.fx, capacity=90)
        self.flash_color = Color(1, 1, 1, 0)
        self.flash_rect = Rectangle(size=(10, 10))
        stage.fx.add(self.flash_color)
        stage.fx.add(self.flash_rect)

    def _build_bird(self):
        """Dibuja el pájaro con elipses. Sus medidas están en unidades y se escalan con Scale."""
        PushMatrix()
        self.bird_move = Translate(0, 0)
        self.bird_turn = Rotate(angle=0, axis=(0, 0, 1), origin=(0, 0))
        self.bird_scale = Scale(1, 1, 1)
        Color(*hx("#F4A300"))
        Ellipse(pos=(-27, -5), size=(15, 11))                        # cola
        Color(*hx("#3B2A12"))
        Ellipse(pos=(-20, -17), size=(40, 34))                       # contorno del cuerpo
        Color(*hx(BIRD_BODY))
        Ellipse(pos=(-18, -15), size=(36, 30))                       # cuerpo
        Color(*hx("#FFF1B0"))
        Ellipse(pos=(-8, -14), size=(24, 14))                        # panza
        Color(*hx("#B36B00"))
        self.wing_edge = Ellipse(pos=(-15, -8), size=(20, 14))       # ala (contorno)
        Color(*hx(BIRD_WING))
        self.wing = Ellipse(pos=(-14, -7), size=(18, 12))            # ala
        Color(*hx("#3B2A12"))
        Ellipse(pos=(3, 1), size=(16, 16))                           # ojo (contorno)
        Color(1, 1, 1, 1)
        Ellipse(pos=(4, 2), size=(14, 14))                           # ojo
        Color(0.05, 0.05, 0.08, 1)
        self.pupil = Ellipse(pos=(10, 5), size=(6, 6))               # pupila
        Color(*hx("#FF7A2F"))
        Ellipse(pos=(12, -3), size=(17, 9))                          # pico (arriba)
        Color(*hx("#E4571A"))
        Ellipse(pos=(12, -9), size=(14, 8))                          # pico (abajo)
        PopMatrix()

    # ------------------------------------------------------------------ geometría
    def _on_resize(self):
        self._layout()
        if self.phase == "ready":
            self.new_game()      # reacomoda al pájaro y los tubos al nuevo tamaño

    def _layout(self):
        """Coloca y dimensiona lo que no se mueve cada cuadro. Se llama al conocer el tamaño."""
        w, h = self.stage.size
        u = self.u = h / 640.0
        self.sky.size = (w, h)
        self.flash_rect.size = (w, h)

        ground_h = GROUND_H * u
        self.ground.pos = (0, 0)
        self.ground.size = (w, ground_h)
        self.ground_tile = 64 * (ground_h / 32.0)       # ancho en pantalla de una repetición

        city_h = 112 * u
        self.city.pos = (0, ground_h - 4 * u)
        self.city.size = (w, city_h)
        self.city_tile = 256 * (city_h / 64.0)

        self.ground_top = ground_h
        self.bird_x = w * 0.30
        self.top_limit = h - 6 * u
        self.bird_scale.xyz = (u, u, u)

    def _place_clouds(self):
        w, h = self.stage.size
        u = self.u
        for i, cloud in enumerate(self.clouds):
            cloud["s"] = random.uniform(0.8, 1.5) * u
            cloud["x"] = (i + random.random() * 0.8) * (w / len(self.clouds)) * 1.15
            cloud["y"] = h * random.uniform(0.52, 0.86)
            cloud["v"] = random.uniform(6, 16) * u

    def _move_clouds(self, dt):
        w, h = self.stage.size
        shapes = ((0, 0, 70, 26), (14, 9, 44, 32), (36, 5, 40, 28), (-12, 3, 34, 20))
        for cloud in self.clouds:
            cloud["x"] -= cloud["v"] * dt
            s = cloud["s"]
            if cloud["x"] < -110 * s:
                cloud["x"] = w + random.uniform(10, 120) * s
                cloud["y"] = h * random.uniform(0.52, 0.86)
            for part, (ox, oy, pw, ph) in zip(cloud["parts"], shapes):
                part.pos = (cloud["x"] + ox * s, cloud["y"] + oy * s)
                part.size = (pw * s, ph * s)

    # ------------------------------------------------------------------ partida
    def new_game(self):
        """Deja todo como al principio: el pájaro flota esperando el primer toque."""
        self._layout()
        self._hide_overlay()
        u = self.u
        h = self.stage.height
        self.score = 0
        self.new_record = False
        self.phase = "ready"
        self.time = 0.0
        self.dead_timer = 0.0
        self.shake = 0.0
        self.flash = 0.0
        self.flap_glow = 0.0
        self.bird_y = h * 0.56
        self.base_y = self.bird_y
        self.bird_vy = 0.0
        self.angle = 0.0
        self.speed = START_SPEED
        self.gap = GAP_START
        self.last_gap_y = h * 0.55
        for i, pipe in enumerate(self.pipes):
            self._spawn_pipe(pipe, self.stage.width + 70 * u + i * PIPE_SPACING * u)
        self.particles.clear()
        self._place_clouds()
        self._draw_pipes()
        self._draw_bird()

    def play_again(self):
        """Botón «Jugar otra vez» de la tarjeta final."""
        self.new_game()

    def _spawn_pipe(self, pipe, x):
        """Coloca un tubo en `x` con el hueco a una altura al azar (sin saltos imposibles)."""
        u = self.u
        gap = self.gap * u
        low = self.ground_top + gap / 2 + 46 * u
        high = self.stage.height - HUD_H * u - gap / 2 - 18 * u
        centre = self.last_gap_y + random.uniform(-190, 190) * u
        centre = max(low, min(high, centre))
        self.last_gap_y = centre
        pipe.update(x=x, gap_y=centre, gap=gap, passed=False)

    def _draw_pipes(self):
        u = self.u
        height = self.stage.height
        for pipe in self.pipes:
            x, gy, gap = pipe["x"], pipe["gap_y"], pipe["gap"]
            body_w, cap_w, cap_h = PIPE_W * u, CAP_W * u, CAP_H * u
            top_edge = gy + gap / 2          # donde empieza el tubo de arriba
            bottom_edge = gy - gap / 2       # donde termina el tubo de abajo
            pipe["top_cap"].pos = (x - cap_w / 2, top_edge)
            pipe["top_cap"].size = (cap_w, cap_h)
            pipe["top_body"].pos = (x - body_w / 2, top_edge + cap_h)
            pipe["top_body"].size = (body_w, max(height - top_edge - cap_h + 8, 1))
            pipe["bot_cap"].pos = (x - cap_w / 2, bottom_edge - cap_h)
            pipe["bot_cap"].size = (cap_w, cap_h)
            pipe["bot_body"].pos = (x - body_w / 2, self.ground_top - 6 * u)
            pipe["bot_body"].size = (body_w, max(bottom_edge - cap_h - self.ground_top + 6 * u, 1))

    def _draw_bird(self):
        self.bird_move.xy = (self.bird_x, self.bird_y)
        self.bird_turn.angle = self.angle
        # El ala sube y baja; mientras aleteas se mueve más rápido.
        speed = 26 if self.flap_glow > 0 else 9
        offset = math.sin(self.time * speed) * 4
        self.wing.pos = (-14, -7 + offset)
        self.wing_edge.pos = (-15, -8 + offset)
        self.pupil.pos = (10 + (2 if self.phase in ("dead", "over") else 0), 5)

    # ------------------------------------------------------------------ entrada
    def on_show(self):
        self.new_game()
        warm_up_sounds()
        if not self._keys_bound:
            Window.bind(on_key_down=self._on_key_down)
            self._keys_bound = True

    def on_hide(self):
        if self._keys_bound:
            Window.unbind(on_key_down=self._on_key_down)
            self._keys_bound = False
        self._hide_overlay()

    def _on_key_down(self, _window, key, *_args):
        if key in (KEY_SPACE, KEY_UP) and self.phase in ("ready", "play"):
            self._flap()
            return True
        return False

    def on_touch_down(self, touch):
        if super().on_touch_down(touch):   # primero los botones (volver, jugar otra vez...)
            return True
        if self.phase in ("ready", "play"):
            self._flap()
            return True
        return False

    def _flap(self):
        if self.phase not in ("ready", "play"):
            return
        self.phase = "play"
        u = self.u
        self.bird_vy = FLAP_SPEED * u
        self.flap_glow = 0.25
        play_sound("flap")
        self.particles.emit(
            self.bird_x - 16 * u, self.bird_y - 4 * u, (1, 1, 1, 0.9),
            count=5, speed=70 * u, size=7 * u, life=0.4, gravity=-60 * u,
        )

    # ------------------------------------------------------------------ bucle
    def update(self, dt):
        dt = min(dt, 0.05)              # si un cuadro tarda mucho, no damos un salto enorme
        self.time += dt
        u = self.u
        self.flap_glow = max(0.0, self.flap_glow - dt)
        self._move_clouds(dt)
        self.particles.update(dt)

        # Sacudida y destello al chocar
        self.shake = max(0.0, self.shake - dt * 3.2)
        amplitude = self.shake * 12 * u
        self.stage.shake.xy = (
            random.uniform(-amplitude, amplitude), random.uniform(-amplitude, amplitude)
        ) if amplitude > 0.05 else (0, 0)
        self.flash = max(0.0, self.flash - dt * 2.6)
        self.flash_color.a = self.flash

        if self.phase == "ready":
            self._update_ready(dt)
        elif self.phase == "play":
            self._update_play(dt)
        elif self.phase == "dead":
            self._update_dead(dt)
        self._scroll(dt)
        self._draw_pipes()
        self._draw_bird()

    def _scroll(self, dt):
        """Suelo y ciudad se desplazan cambiando las coordenadas de la textura (parallax)."""
        u = self.u
        if self.phase in ("ready", "play"):
            self.scroll_ground += self.speed * u * dt
        self.scroll_city += self.speed * 0.18 * u * dt
        w = self.stage.width
        for rect, scroll, tile in (
            (self.ground, self.scroll_ground, self.ground_tile),
            (self.city, self.scroll_city, self.city_tile),
        ):
            start = (scroll % tile) / tile
            span = w / tile
            rect.tex_coords = (start, 0, start + span, 0, start + span, 1, start, 1)

    def _update_ready(self, dt):
        """Antes del primer toque el pájaro flota arriba y abajo."""
        self.bird_y = self.base_y + math.sin(self.time * 4.2) * 9 * self.u
        self.angle = math.sin(self.time * 4.2) * 6

    def _update_play(self, dt):
        u = self.u
        # --- Física del pájaro ---
        self.bird_vy = max(self.bird_vy - GRAVITY * u * dt, -MAX_FALL * u)
        self.bird_y += self.bird_vy * dt
        if self.bird_y > self.top_limit:                 # techo: no se puede salir
            self.bird_y = self.top_limit
            self.bird_vy = min(self.bird_vy, 0)
        # Inclinación según la velocidad: hacia arriba un poco, picado hacia abajo mucho.
        ratio = self.bird_vy / u
        self.angle = ratio * 0.06 if ratio > 0 else max(-88.0, ratio * 0.14)

        # --- Tubos ---
        self.speed = min(MAX_SPEED, START_SPEED + self.score * 2.0)
        self.gap = max(GAP_MIN, GAP_START - self.score * 1.2)
        farthest = max(p["x"] for p in self.pipes)
        for pipe in self.pipes:
            pipe["x"] -= self.speed * u * dt
            if pipe["x"] < -CAP_W * u:                   # salió por la izquierda: se recicla
                self._spawn_pipe(pipe, farthest + PIPE_SPACING * u)
                farthest = pipe["x"]
            if not pipe["passed"] and pipe["x"] + PIPE_W * u / 2 < self.bird_x - BIRD_R * u:
                pipe["passed"] = True
                self.score += 1
                play_sound("point")

        # --- Colisiones ---
        if self._collides():
            self._die()

    def _collides(self):
        u = self.u
        r = BIRD_R * u
        cx, cy = self.bird_x, self.bird_y
        if cy - r <= self.ground_top:
            return True
        body_w, cap_w, cap_h = PIPE_W * u, CAP_W * u, CAP_H * u
        for pipe in self.pipes:
            x, gy, gap = pipe["x"], pipe["gap_y"], pipe["gap"]
            if abs(cx - x) > cap_w / 2 + r:
                continue
            top_edge, bottom_edge = gy + gap / 2, gy - gap / 2
            hits = (
                _circle_hits_rect(cx, cy, r, x - cap_w / 2, top_edge, cap_w, cap_h),
                _circle_hits_rect(cx, cy, r, x - body_w / 2, top_edge + cap_h, body_w, 9999),
                _circle_hits_rect(cx, cy, r, x - cap_w / 2, bottom_edge - cap_h, cap_w, cap_h),
                _circle_hits_rect(cx, cy, r, x - body_w / 2, 0, body_w, bottom_edge - cap_h),
            )
            if any(hits):
                return True
        return False

    def _die(self):
        u = self.u
        self.phase = "dead"
        self.bird_vy = 230 * u
        self.shake = 1.0
        self.flash = 0.85
        play_sound("hit")
        vibrate(70)
        for color in ((1, 0.82, 0.25, 1), (0.96, 0.66, 0.04, 1), (1, 1, 1, 1)):
            self.particles.emit(self.bird_x, self.bird_y, color, count=7, speed=230 * u,
                                size=9 * u, life=0.8, gravity=-700 * u)

    def _update_dead(self, dt):
        """El pájaro cae girando hasta el suelo y luego aparece la tarjeta de fin de partida."""
        u = self.u
        floor = self.ground_top + BIRD_R * u
        if self.bird_y > floor:
            self.bird_vy = max(self.bird_vy - GRAVITY * u * dt, -MAX_FALL * u)
            self.bird_y = max(self.bird_y + self.bird_vy * dt, floor)
            self.angle = max(-90.0, self.angle - 360 * dt)
        else:
            self.angle = -90.0
            self.dead_timer += dt
            if self.dead_timer > 0.75:
                self._game_over()

    def _game_over(self):
        """Guarda el récord (si lo hay) y muestra la tarjeta con los puntos."""
        self.phase = "over"
        if self.score > self.best:
            self.best = int(self.score)
            self.save("best", self.best)
            self.new_record = True
        self._show_overlay()

    # ------------------------------------------------------------------ tarjeta final
    def _show_overlay(self):
        if self._overlay.parent is None:
            self.ids.arena.add_widget(self._overlay)
        card = self.ids.over_card
        Animation.cancel_all(card)
        card.opacity = 0
        card.offset_y = -dp(30)
        Animation(opacity=1, offset_y=0, d=0.35, t="out_cubic").start(card)

    def _hide_overlay(self):
        if self._overlay.parent is not None:
            self._overlay.parent.remove_widget(self._overlay)
