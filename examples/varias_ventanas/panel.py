"""EJEMPLO DE VARIAS VENTANAS dentro de un panel.

Qué enseña:
  * Un ScreenManager propio dentro de tu panel (se define en el .kv).
  * Cambiar de ventana:  self.ir("ventana_a")   o desde el .kv:  on_release: root.ir("ventana_a")
  * handle_back(): el botón «<» de la barra y el botón «atrás» de Android primero vuelven al
    menú de TU panel; solo cuando ya estás en el menú, salen al inicio de la app.
"""

from hub.panel import PanelScreen


class VariasVentanasPanel(PanelScreen):
    def ir(self, nombre):
        """Muestra la ventana interna `nombre` con una animación hacia la derecha o la izquierda."""
        pantallas = self.ids.interior
        pantallas.transition.direction = "right" if nombre == "menu" else "left"
        pantallas.current = nombre

    def handle_back(self):
        if self.ids.interior.current != "menu":
            self.ir("menu")
            return True               # lo manejamos nosotros: no salimos del panel
        return super().handle_back()  # ya estamos en el menú: salir al inicio de la app
