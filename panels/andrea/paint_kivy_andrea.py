from random import random

from kivy.graphics import Color, Ellipse, Line
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget

from hub.panel import PanelScreen


class MyPaintWidget(Widget):
    """Lienzo que permite dibujar con el dedo o el ratón."""

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)

        x, y = self.to_widget(*touch.pos)
        color = (random(), random(), random())
        with self.canvas:
            Color(*color)
            diameter = dp(30)
            Ellipse(
                pos=(x - diameter / 2, y - diameter / 2),
                size=(diameter, diameter),
            )
            touch.ud["line"] = Line(points=(x, y), width=dp(2))
        return True

    def on_touch_move(self, touch):
        line = touch.ud.get("line")
        if line is None:
            return super().on_touch_move(touch)

        x, y = self.to_widget(*touch.pos)
        line.points += [x, y]
        return True


class AndreaPanel(PanelScreen):
    """Panel del juego de dibujo."""

    def on_build(self):
        layout = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(8),
        )
        self.painter = MyPaintWidget()
        clear_button = Button(
            text="Limpiar",
            size_hint_y=None,
            height=dp(48),
        )
        clear_button.bind(on_release=self.clear_canvas)
        layout.add_widget(self.painter)
        layout.add_widget(clear_button)
        self.add_widget(layout)

    def clear_canvas(self, *_args):
        self.painter.canvas.clear()
