import os
import random

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label

from hub.panel import PanelScreen

# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# Cada imagen tiene un identificador (la clave). Dos tarjetas son pareja
# si comparten el mismo identificador.
# Si el archivo de imagen no existe, la tarjeta se muestra con un color y
# el identificador como texto, para que el juego funcione desde el inicio.
# ---------------------------------------------------------------------------
IMAGENES = {
    "gato": "gato.png",
    "perro": "perro.png",
    "pez": "pez.png",
}
COLORES_RESPALDO = {
    "gato":  (0.95, 0.60, 0.20, 1),
    "perro": (0.30, 0.65, 0.90, 1),
    "pez":   (0.40, 0.80, 0.45, 1),
}
DORSO = "dorso.png"
COLOR_DORSO = (0.25, 0.25, 0.35, 1)
TIEMPO_VOLTEO = 1.0  # segundos que se ven dos cartas distintas antes de ocultarse


class Tarjeta(Button):
    """Una tarjeta del memorama."""

    def __init__(self, id_imagen, ruta_imagen, ruta_dorso, **kwargs):
        super().__init__(**kwargs)
        self.id_imagen = id_imagen      # identificador para comparar
        self.ruta_imagen = ruta_imagen
        self.ruta_dorso = ruta_dorso
        self.volteada = False
        self.emparejada = False
        self.ocultar()

    def _poner_imagen(self, ruta, color, texto=""):
        existe = os.path.isfile(ruta)
        self.background_normal = ruta if existe else ""
        self.background_down = ruta if existe else ""
        self.background_color = (1, 1, 1, 1) if existe else color
        self.text = "" if existe else texto
        self.font_size = "28sp"

    def mostrar(self):
        self.volteada = True
        self._poner_imagen(
            self.ruta_imagen,
            COLORES_RESPALDO[self.id_imagen],
            self.id_imagen.upper(),
        )

    def ocultar(self):
        self.volteada = False
        self._poner_imagen(self.ruta_dorso, COLOR_DORSO, "?")


class AndreaPanel(PanelScreen):
    puntos = NumericProperty(0)
    intentos = NumericProperty(0)

    def on_build(self):
        self.primera = None
        self.segunda = None
        self.bloqueado = False
        self._evento = None

        raiz = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(10),
        )

        self.lbl_marcador = Label(
            size_hint_y=None,
            height=dp(48),
            font_size="20sp",
        )
        raiz.add_widget(self.lbl_marcador)

        self.tablero = GridLayout(
            cols=3,
            rows=2,
            spacing=dp(8),
        )
        raiz.add_widget(self.tablero)

        self.lbl_mensaje = Label(
            size_hint_y=None,
            height=dp(48),
            font_size="24sp",
            bold=True,
        )
        raiz.add_widget(self.lbl_mensaje)

        btn = Button(
            text="Reiniciar",
            size_hint_y=None,
            height=dp(48),
        )
        btn.bind(on_release=lambda *_: self.reiniciar())
        raiz.add_widget(btn)

        self.add_widget(raiz)
        self.reiniciar()

    # -- Marcador -----------------------------------------------------------
    def on_puntos(self, *_):
        self._actualizar_marcador()

    def on_intentos(self, *_):
        self._actualizar_marcador()

    def _actualizar_marcador(self):
        self.lbl_marcador.text = f"Puntos: {self.puntos}    Intentos: {self.intentos}"

    # -- Lógica del juego ---------------------------------------------------
    def reiniciar(self):
        if self._evento:
            self._evento.cancel()
        self.puntos = 0
        self.intentos = 0
        self.primera = self.segunda = None
        self.bloqueado = False
        self.lbl_mensaje.text = ""
        self._actualizar_marcador()

        ids = list(IMAGENES.keys()) * 2
        random.shuffle(ids)

        self.tablero.clear_widgets()
        for id_img in ids:
            t = Tarjeta(
                id_img,
                self.asset(IMAGENES[id_img]),
                self.asset(DORSO),
            )
            t.bind(on_release=self.al_presionar)
            self.tablero.add_widget(t)

    def al_presionar(self, tarjeta):
        if self.bloqueado or tarjeta.volteada or tarjeta.emparejada:
            return

        tarjeta.mostrar()

        if self.primera is None:
            self.primera = tarjeta
            return

        self.segunda = tarjeta
        self.intentos += 1

        if self.primera.id_imagen == self.segunda.id_imagen:
            self.primera.emparejada = True
            self.segunda.emparejada = True
            self.puntos += 1
            self._limpiar_ronda()
            if self.puntos == len(IMAGENES):
                self.lbl_mensaje.text = "¡Ganaste!"
        else:
            self.bloqueado = True
            self._evento = Clock.schedule_once(self._voltear_de_nuevo, TIEMPO_VOLTEO)

    def _voltear_de_nuevo(self, _dt):
        self._evento = None
        if self.primera is not None:
            self.primera.ocultar()
        if self.segunda is not None:
            self.segunda.ocultar()
        self._limpiar_ronda()

    def _limpiar_ronda(self):
        self.primera = self.segunda = None
        self.bloqueado = False

    def on_hide(self):
        if self._evento is not None:
            self._evento.cancel()
            self._evento = None
        for tarjeta in (self.primera, self.segunda):
            if tarjeta is not None and not tarjeta.emparejada:
                tarjeta.ocultar()
        self._limpiar_ronda()
