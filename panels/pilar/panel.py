"""Juego de salto: mueve un cuadrado y evita los obstáculos."""

import random

from kivy.graphics import Color, Ellipse, Rectangle
from kivy.metrics import dp
from kivy.properties import NumericProperty, StringProperty
from kivy.utils import get_color_from_hex

from hub.panel import PanelScreen


class PilarPanel(PanelScreen):
    run_update = True

    score = NumericProperty(0)
    best = NumericProperty(0)
    phase = StringProperty("ready")

    def on_build(self):
        self.best = self.load("best", 0)
        self.stage = self.ids.stage
        self._build_scene()
        self.stage.bind(size=lambda *_args: self._layout())
        self._layout()
        self.new_game()

    def _build_scene(self):
        with self.stage.canvas:
            Color(*get_color_from_hex("#87CEEB"))
            self.sky = Rectangle(pos=(0, 0), size=(10, 10))
            Color(*get_color_from_hex("#FFD84D"))
            self.sun = Ellipse(pos=(0, 0), size=(10, 10))
            Color(*get_color_from_hex("#62C968"))
            self.ground = Rectangle(pos=(0, 0), size=(10, 10))
            Color(*get_color_from_hex("#FF5E8A"))
            self.player = Rectangle(pos=(0, 0), size=(10, 10))
            self.obstacles = []
            for _ in range(3):
                Color(*get_color_from_hex("#36454F"))
                obstacle = Rectangle(pos=(-100, -100), size=(10, 10))
                self.obstacles.append(obstacle)
        self._obstacle_passed = [False] * len(self.obstacles)

    def _layout(self):
        width, height = self.stage.size
        ground_height = dp(70)
        self.ground.pos = (0, 0)
        self.ground.size = (width, ground_height)
        self.sky.pos = (0, ground_height)
        self.sky.size = (width, height - ground_height)
        sun_size = dp(54)
        self.sun.pos = (width - sun_size - dp(24), height - sun_size - dp(24))
        self.sun.size = (sun_size, sun_size)
        self.ground_y = ground_height
        self.player_size = dp(42)
        if self.phase == "ready":
            self.player.pos = (dp(48), self.ground_y)

    def new_game(self):
        self.score = 0
        self.phase = "ready"
        self.player_speed = 0
        width = self.stage.width
        self.player.pos = (dp(48), self.ground_y)
        self.player.size = (self.player_size, self.player_size)
        for index, obstacle in enumerate(self.obstacles):
            obstacle.size = (dp(34), dp(48))
            obstacle.pos = (width + dp(220) * (index + 1), self.ground_y)
            self._obstacle_passed[index] = False

    def hits_player(self, obstacle):
        player_x = self.player.pos[0] + dp(4)
        player_y = self.player.pos[1] + dp(3)
        player_width = self.player.size[0] - dp(8)
        player_height = self.player.size[1] - dp(6)
        obstacle_x, obstacle_y = obstacle.pos
        obstacle_width, obstacle_height = obstacle.size
        return (
            player_x < obstacle_x + obstacle_width
            and player_x + player_width > obstacle_x
            and player_y < obstacle_y + obstacle_height
            and player_y + player_height > obstacle_y
        )

    def start_game(self):
        self.score = 0
        self.phase = "play"
        self.jump()

    def jump(self):
        if self.phase == "ready":
            self.start_game()
            return
        if self.phase == "play" and self.player.pos[1] <= self.ground_y + 1:
            self.player_speed = dp(620)

    def update(self, dt):
        if self.phase != "play":
            return

        gravity = dp(1450)
        speed = dp(190) + min(self.score * dp(8), dp(120))

        self.player_speed -= gravity * dt
        player_x, player_y = self.player.pos
        player_y += self.player_speed * dt
        if player_y < self.ground_y:
            player_y = self.ground_y
            self.player_speed = 0
        self.player.pos = (player_x, player_y)

        for index, obstacle in enumerate(self.obstacles):
            obstacle_x, obstacle_y = obstacle.pos
            obstacle_x -= speed * dt
            if obstacle_x + obstacle.size[0] < 0:
                obstacle_x = self.stage.width + random.uniform(dp(100), dp(240))
                obstacle.size = (dp(34), random.uniform(dp(40), dp(68)))
                obstacle_y = self.ground_y
                self._obstacle_passed[index] = False
            obstacle.pos = (obstacle_x, obstacle_y)

            if self.hits_player(obstacle):
                self.game_over()
                return

            if obstacle.pos[0] + obstacle.size[0] < self.player.pos[0] and not self._obstacle_passed[index]:
                self._obstacle_passed[index] = True
                self.score += 1

    def game_over(self):
        if self.phase != "play":
            return
        self.phase = "over"
        if self.score > self.best:
            self.best = self.score
            self.save("best", self.best)
            self.toast("¡Nuevo récord!")

    def play_again(self):
        self.new_game()
        self.phase = "ready"

    def on_touch_down(self, touch):
        if super().on_touch_down(touch):
            return True
        if self.phase == "ready" or self.phase == "play":
            self.jump()
            return True
        return False
