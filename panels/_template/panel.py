"""Tu panel: la lógica en Python. El diseño está en panel.kv (en esta misma carpeta).

Cómo se conectan las dos partes:

    panel.kv                                 panel.py
    ------------------------------------     ------------------------------------
    <TemplatePanel>:                         class TemplatePanel(PanelScreen):
        Label:                                   count = NumericProperty(0)
            text: str(root.count)                def add(self, amount): ...
        PillButton:
            on_release: root.add(1)

  * `<TemplatePanel>:` en el .kv tiene el MISMO nombre que la clase de Python.
  * `root` es tu panel: desde el .kv puedes leer sus Properties (root.count) y llamar a
    sus métodos (root.add(1)).
  * Todo lo que escribas dentro de `<TemplatePanel>:` aparece en tu panel, debajo de la
    barra superior. Cuando una Property cambia, el .kv se actualiza SOLO.

Ganchos que puedes escribir aquí (todos son opcionales; mira hub/panel.py para ver más):
    on_build()   una vez, al crear el panel      on_show() / on_hide()   al entrar / salir
    update(dt)   cada cuadro, si run_update = True (juegos, animaciones)
"""

from kivy.properties import ListProperty, NumericProperty

from hub import theme
from hub.panel import PanelScreen

# Colores que se pueden elegir en el panel de ejemplo.
PALETTE = ["#7C6CFF", "#FF5E8A", "#2FB8FF", "#34D399", "#FBBF24"]


class TemplatePanel(PanelScreen):
    # Una Property es una variable «viva»: si cambia, todo lo que la use en el .kv se redibuja.
    count = NumericProperty(0)
    palette = ListProperty(PALETTE)

    # run_update = True   # <- descomenta si necesitas update(dt): un juego, una animación...

    def on_build(self):
        """Se ejecuta UNA vez. Aquí recuperamos lo que se guardó la última vez."""
        self.count = self.load("count", 0)

    def add(self, amount):
        """Suma (o resta) al contador y guarda el resultado para la próxima vez."""
        self.count = max(0, self.count + amount)
        self.save("count", self.count)
        if self.count and self.count % 10 == 0:
            self.toast(f"¡Llegaste a {self.count}!")

    def set_color(self, hex_color):
        """Cambia el color de acento de TU panel (el resplandor de arriba y los botones)."""
        self.accent = theme.hx(hex_color)

    # def update(self, dt):
    #     """Se llama ~60 veces por segundo si run_update = True. `dt` = segundos del cuadro anterior."""
    #     pass
