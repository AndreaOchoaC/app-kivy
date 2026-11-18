"""EJEMPLO DE APP: «Mis notas».

Qué enseña:
  * TextInput: leer lo que escribe el usuario (self.ids.entrada.text).
  * ListProperty: una lista «viva». on_notas() se ejecuta cada vez que cambia.
  * Crear tus propios widgets (NotaFila) y añadirlos desde Python: una fila por cada nota.
  * save / load: las notas sobreviven al cerrar la app.
"""

from kivy.properties import ListProperty, NumericProperty, ObjectProperty, StringProperty

from hub.panel import PanelScreen
from hub.widgets import Card


class NotaFila(Card):
    """Una fila de la lista. Su aspecto está en panel.kv (regla <NotaFila>:)."""

    texto = StringProperty("")
    indice = NumericProperty(0)
    al_borrar = ObjectProperty(None, allownone=True)


class NotasPanel(PanelScreen):
    notas = ListProperty([])

    def on_build(self):
        self.notas = self.load("notas", [])

    def agregar(self):
        texto = self.ids.entrada.text.strip()
        if not texto:
            self.toast("Escribe algo primero")
            return
        self.notas = [texto, *self.notas]       # la nota nueva va arriba
        self.ids.entrada.text = ""

    def borrar(self, indice):
        self.notas = [n for i, n in enumerate(self.notas) if i != indice]

    def on_notas(self, _panel, notas):
        """Se ejecuta SOLA cada vez que `notas` cambia: redibuja la lista y guarda."""
        lista = self.ids.lista
        lista.clear_widgets()
        for indice, texto in enumerate(notas):
            lista.add_widget(NotaFila(texto=texto, indice=indice, al_borrar=self.borrar))
        self.save("notas", list(notas))
