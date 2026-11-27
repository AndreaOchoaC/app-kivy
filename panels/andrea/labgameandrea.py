import os
import random

#from kivy.app import App
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.properties import NumericProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from hub.panel import PanelScreen

# ---------------------------------------------------------------------------
# NOTA ANDREA
# Si queremos que este sea el juego principal de nuestro panel:
# * la pantalla debe llamarse AndreaPanel(PanelScreen) --también importar PanelScreen--
# * debemos quitar la clase MiApp y el bloque if __name__ == "__main__"
# * en la aplicación principal, en lugar de importar AndreaPanel desde panel.py,
#       debemos importar AndreaPanel desde ESTE_ARCHIVO.py
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# Cada color tiene un identificador (la clave). Dos pelotas son del mismo
# color si comparten identificador.
# ---------------------------------------------------------------------------
COLORES = {
    "rojo":     (0.90, 0.20, 0.20, 1),
    "azul":     (0.20, 0.45, 0.90, 1),
    "verde":    (0.25, 0.75, 0.35, 1),
    "amarillo": (0.95, 0.85, 0.20, 1),
}
CAPACIDAD = 4          # pelotas que caben en cada tubo
TUBOS_VACIOS = 2       # tubos extra vacíos al iniciar
IMAGEN_TUBO = "imagenes/tubo.png"

# True  -> regla clásica: solo se puede poner una pelota sobre otra del mismo
#          color (o en un tubo vacío).
# False -> se puede mover a cualquier tubo que tenga espacio.
REGLA_ESTRICTA = True


class Tubo(ButtonBehavior, Widget):
    """Un tubo de ensayo con una pila de pelotas (la última es la de arriba)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pelotas = []            # lista de identificadores de color
        self.seleccionado = False
        self.bind(pos=self.redibujar, size=self.redibujar)

    def redibujar(self, *_):
        self.canvas.clear()
        x, y = self.pos
        w, h = self.size

        # El tubo ocupa el 75% inferior; el resto es espacio para la pelota levantada
        tubo_h = h * 0.75
        tubo_w = min(w * 0.8, tubo_h * 0.35)
        tx = x + (w - tubo_w) / 2

        with self.canvas:
            # Resalte del tubo seleccionado
            if self.seleccionado:
                Color(1, 1, 0, 0.30)
                RoundedRectangle(pos=(tx - 6, y - 6),
                                 size=(tubo_w + 12, tubo_h + 12), radius=[20])

            # Imagen del tubo (o un contorno si no existe el archivo)
            if os.path.exists(IMAGEN_TUBO):
                Color(1, 1, 1, 1)
                Rectangle(source=IMAGEN_TUBO, pos=(tx, y), size=(tubo_w, tubo_h))
            else:
                Color(0.85, 0.85, 0.9, 1)
                Line(rounded_rectangle=(tx, y, tubo_w, tubo_h, 18), width=2)

            # Pelotas
            diam = min(tubo_w * 0.8, tubo_h * 0.9 / CAPACIDAD)
            hueco = (tubo_h - CAPACIDAD * diam) / (CAPACIDAD + 1)
            bx = tx + (tubo_w - diam) / 2
            for i, id_color in enumerate(self.pelotas):
                by = y + hueco + i * (diam + hueco)
                # La pelota de arriba sube si el tubo está seleccionado
                if self.seleccionado and i == len(self.pelotas) - 1:
                    by = y + tubo_h + 8
                Color(*COLORES[id_color])
                Ellipse(pos=(bx, by), size=(diam, diam))


class AndreaPanel(PanelScreen):
    movimientos = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tubos = []
        self.origen = None
        self.terminado = False

        raiz = BoxLayout(orientation="vertical", padding=10, spacing=10)

        self.lbl_marcador = Label(size_hint_y=0.10, font_size="22sp")
        raiz.add_widget(self.lbl_marcador)

        self.zona_tubos = BoxLayout(orientation="horizontal", spacing=10)
        raiz.add_widget(self.zona_tubos)

        self.lbl_mensaje = Label(size_hint_y=0.10, font_size="28sp", bold=True)
        raiz.add_widget(self.lbl_mensaje)

        btn = Button(text="Reiniciar", size_hint_y=0.10)
        btn.bind(on_release=lambda *_: self.reiniciar())
        raiz.add_widget(btn)

        self.add_widget(raiz)
        self.reiniciar()

    # -- Marcador -----------------------------------------------------------
    def on_movimientos(self, *_):
        self._actualizar_marcador()

    def _actualizar_marcador(self):
        self.lbl_marcador.text = f"Movimientos: {self.movimientos}"

    # -- Preparación --------------------------------------------------------
    def reiniciar(self):
        self.movimientos = 0
        self.origen = None
        self.terminado = False
        self.lbl_mensaje.text = ""
        self._actualizar_marcador()

        # Mezclar pelotas y repartirlas en tubos llenos
        bolas = [c for c in COLORES for _ in range(CAPACIDAD)]
        while True:
            random.shuffle(bolas)
            contenido = [bolas[i * CAPACIDAD:(i + 1) * CAPACIDAD]
                         for i in range(len(COLORES))]
            if not self._resuelto(contenido):   # evita empezar ya resuelto
                break
        contenido += [[] for _ in range(TUBOS_VACIOS)]

        self.zona_tubos.clear_widgets()
        self.tubos = []
        for lista in contenido:
            t = Tubo()
            t.pelotas = list(lista)
            t.bind(on_release=self.al_presionar)
            self.zona_tubos.add_widget(t)
            self.tubos.append(t)
        for t in self.tubos:
            t.redibujar()

    # -- Lógica del juego ---------------------------------------------------
    @staticmethod
    def _resuelto(contenido):
        """Resuelto: cada tubo está vacío o lleno con un solo color."""
        return all(
            len(b) == 0 or (len(b) == CAPACIDAD and len(set(b)) == 1)
            for b in contenido
        )

    def _puede_mover(self, origen, destino):
        if not origen.pelotas or len(destino.pelotas) >= CAPACIDAD:
            return False
        if REGLA_ESTRICTA and destino.pelotas:
            return destino.pelotas[-1] == origen.pelotas[-1]
        return True

    def _seleccionar(self, tubo):
        self.origen = tubo
        tubo.seleccionado = True
        tubo.redibujar()

    def _deseleccionar(self):
        if self.origen:
            self.origen.seleccionado = False
            self.origen.redibujar()
        self.origen = None

    def al_presionar(self, tubo):
        if self.terminado:
            return

        # Primer toque: elegir tubo de origen
        if self.origen is None:
            if tubo.pelotas:
                self._seleccionar(tubo)
            return

        # Tocar el mismo tubo: cancelar selección
        if tubo is self.origen:
            self._deseleccionar()
            return

        # Segundo toque: intentar mover UNA pelota
        origen = self.origen
        if self._puede_mover(origen, tubo):
            tubo.pelotas.append(origen.pelotas.pop())
            self.movimientos += 1
            self._deseleccionar()
            tubo.redibujar()
            if self._resuelto([t.pelotas for t in self.tubos]):
                self.terminado = True
                self.lbl_mensaje.text = "¡Ganaste!"
        else:
            # Movimiento inválido: cambia la selección al tubo tocado
            self._deseleccionar()
            if tubo.pelotas:
                self._seleccionar(tubo)

    def on_leave(self, *args):
        self._deseleccionar()


# comentar cuando queramos integrarla en el panel principal
'''class MiApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(BallSortScreen(name="ballsort"))
        return sm


if __name__ == "__main__":
    MiApp().run()
'''
