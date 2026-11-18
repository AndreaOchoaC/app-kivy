"""La App principal: crea la portada, navega entre paneles y los protege de errores."""

from __future__ import annotations

import traceback
from pathlib import Path

from kivy.animation import Animation, AnimationTransition
from kivy.app import App
from kivy.base import ExceptionHandler, ExceptionManager
from kivy.core.window import Window
from kivy.logger import Logger
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, SlideTransition

from hub import theme
from hub.config import APP_NAME
from hub.device import is_mobile
from hub.home import HomeScreen
from hub.panel import PanelScreen
from hub.registry import discover, reload_panel
from hub.storage import Storage
from hub.widgets import ErrorSheet, Toast

ESC_KEY = 27   # la tecla Esc en el PC y el botón «atrás» de Android generan este código
F5_KEY = 286   # recargar el panel actual (solo PC)


class HubTransition(SlideTransition):
    """Deslizamiento al estilo iOS: la pantalla nueva entra rápido y la vieja se mueve menos."""

    def on_progress(self, progression):
        a, b = self.screen_in, self.screen_out
        x, y = self.manager.pos
        width = self.manager.width
        p = AnimationTransition.out_cubic(progression)
        a.y = b.y = y
        if self.direction == "right":
            b.x = x + width * p
            a.x = x - width * 0.28 * (1 - p)
        else:
            a.x = x + width * (1 - p)
            b.x = x - width * 0.28 * p


class PanelErrorHandler(ExceptionHandler):
    """Si el código de un panel falla, muestra una hoja explicativa en vez de cerrar la app."""

    def __init__(self, app):
        super().__init__()
        self.app = app

    def handle_exception(self, inst):
        if self.app.current_panel() is None and not self.app.sheet_open:
            return ExceptionManager.RAISE   # error en el núcleo de la app: que se vea en consola
        self.app.show_panel_error(inst)
        return ExceptionManager.PASS


class HubApp(App):
    """Ventana principal: portada con los paneles del equipo."""

    def __init__(self, storage_path=None, only=None, **kwargs):
        """`storage_path` cambia dónde se guardan los datos (útil en las pruebas).

        `only="pilar"` abre solo ese panel, sin portada (para probar tu panel aislado).
        """
        super().__init__(**kwargs)
        self._storage_path = storage_path
        self.only = only
        self.entries = []
        self.storage = None
        self.manager = None
        self.home = None
        self.sheet_open = False
        self._sheet = None
        self._screens = {}        # paneles ya creados (se crean la primera vez que se abren)
        self._handler = None

    # ------------------------------------------------------------------ construcción
    def build(self):
        self.title = APP_NAME
        icon = Path(__file__).resolve().parent.parent / "assets" / "icon.png"
        if icon.exists():
            self.icon = str(icon)
        Window.clearcolor = theme.BG

        path = self._storage_path or Path(self.user_data_dir) / "hub.json"
        self.storage = Storage(path)
        self.entries = discover(only=self.only)

        self.manager = ScreenManager(transition=HubTransition(duration=0.34))
        self.home = HomeScreen(name="home")
        self.home.populate(self.entries)
        self.manager.add_widget(self.home)

        self._toast = Toast()
        self.root_layout = FloatLayout()
        self.root_layout.add_widget(self.manager)
        self.root_layout.add_widget(self._toast)

        Window.bind(on_keyboard=self._on_keyboard)
        self._handler = PanelErrorHandler(self)
        ExceptionManager.add_handler(self._handler)
        return self.root_layout

    def on_start(self):
        if self.only:
            entry = next((e for e in self.entries if e.folder == self.only), None)
            if entry is None:
                raise SystemExit(f"No existe el panel '{self.only}' en la carpeta panels/")
            self.open_panel(self.only, animate=False)

    def on_stop(self):
        if self._handler is not None:
            ExceptionManager.remove_handler(self._handler)
            self._handler = None
        Window.unbind(on_keyboard=self._on_keyboard)

    # ------------------------------------------------------------------ navegación
    def current_panel(self):
        """El PanelScreen que está en pantalla ahora mismo (o None)."""
        screen = self.manager.current_screen if self.manager else None
        return screen if isinstance(screen, PanelScreen) else None

    def open_panel(self, panel_id, animate=True):
        """Abre un panel. Si falla al crearse, muestra un aviso y no pasa nada más."""
        screen = self._screens.get(panel_id)
        if screen is None:
            entry = next((e for e in self.entries if e.ok and e.info.id == panel_id), None)
            if entry is None:
                self.toast(f"El panel '{panel_id}' no está disponible")
                return
            try:
                screen = entry.info.screen_class(info=entry.info, storage=self.storage)
            except Exception as exc:  # noqa: BLE001 - el error del panel no debe tumbar la app
                Logger.exception("Hub: no se pudo crear el panel '%s'", panel_id)
                self.toast(f"{entry.info.title} no pudo abrirse: {type(exc).__name__}: {exc}")
                return
            self._screens[panel_id] = screen
            self.manager.add_widget(screen)
        self._switch(panel_id, "left", animate)

    def back(self):
        """Botón «atrás»: el panel abierto decide (handle_back); si no lo maneja, vuelve al inicio."""
        panel = self.current_panel()
        if panel is not None and panel.handle_back():
            return
        if panel is not None or self.only:
            self.go_home()

    def go_home(self):
        """Vuelve a la portada. En modo «solo un panel» cierra la app."""
        if self.only:
            self.stop()
            return
        self._switch("home", "right", True)

    def _switch(self, name, direction, animate=True):
        if self.manager.current == name:
            return
        if animate:
            self.manager.transition = HubTransition(direction=direction, duration=0.34)
        else:
            self.manager.transition = HubTransition(direction=direction, duration=0.001)
        self.manager.current = name

    # ------------------------------------------------------------------ errores y recarga
    def show_panel_error(self, exc):
        """Muestra la hoja de error para el panel actual y detiene su bucle de actualización."""
        panel = self.current_panel()
        Logger.error("Hub: error en el panel:\n%s", "".join(traceback.format_exception(exc)))
        if self.sheet_open:
            return
        if panel is not None:
            panel.stop_updates()
        frames = [f for f in traceback.extract_tb(exc.__traceback__) if "panels" in Path(f.filename).parts]
        frame = frames[-1] if frames else None
        where = f"{Path(frame.filename).name}, línea {frame.lineno}" if frame else ""
        sheet = ErrorSheet(message=f"{type(exc).__name__}: {exc}", where=where)
        sheet.set_buttons(
            [
                ("Volver al inicio", self._error_home, "primary"),
                ("Reintentar (recargar panel)", self._error_retry, "secondary"),
            ]
        )
        self._sheet = sheet
        self.sheet_open = True
        self.root_layout.add_widget(sheet)

    def dismiss_sheet(self):
        if self._sheet is not None:
            self.root_layout.remove_widget(self._sheet)
        self._sheet = None
        self.sheet_open = False

    def _error_home(self):
        self.dismiss_sheet()
        self.go_home()

    def _error_retry(self):
        self.dismiss_sheet()
        self.reload_current_panel()

    def reload_current_panel(self):
        """Vuelve a leer el código y el .kv del panel abierto y lo reconstruye (tecla F5)."""
        panel = self.current_panel()
        if panel is None:
            return
        panel_id = panel.info.id
        panel.stop_updates()
        entry = reload_panel(panel_id)
        self.entries = [entry if e.folder == panel_id else e for e in self.entries]
        self.home.populate(self.entries)
        self.manager.remove_widget(panel)
        self._screens.pop(panel_id, None)
        if not entry.ok:
            self.toast(f"No se pudo recargar: {entry.error}")
            if self.only:
                self.stop()
            else:
                self.manager.current = "home"
            return
        screen = entry.info.screen_class(info=entry.info, storage=self.storage)
        self._screens[panel_id] = screen
        self.manager.add_widget(screen)
        self.manager.transition = HubTransition(duration=0.001)
        self.manager.current = panel_id
        self.toast("Panel recargado")

    # ------------------------------------------------------------------ avisos
    def toast(self, message, seconds=2.4):
        """Muestra un aviso breve en la parte baja de la pantalla."""
        Animation.cancel_all(self._toast)
        self._toast.text = str(message)
        (
            Animation(opacity=1, d=0.15)
            + Animation(opacity=1, d=seconds)
            + Animation(opacity=0, d=0.3)
        ).start(self._toast)

    # ------------------------------------------------------------------ eventos del sistema
    def _on_keyboard(self, _window, key, *_args):
        """Esc / botón atrás = «volver». F5 = recargar el panel (solo en el PC)."""
        if self.sheet_open:
            return key == ESC_KEY
        if key == F5_KEY and not is_mobile():
            self.reload_current_panel()
            return True
        if key != ESC_KEY:
            return False
        if self.current_panel() is not None:
            self.back()
            return True
        return False   # en la portada, el botón atrás de Android cierra la app

    def on_pause(self):
        """Android/iOS: la app pasa a segundo plano. Avisamos al panel abierto."""
        panel = self.current_panel()
        if panel is not None:
            panel.stop_updates()
            panel.on_hide()
        return True  # True = permitir que la app se quede en pausa (no cerrarla)

    def on_resume(self):
        panel = self.current_panel()
        if panel is not None:
            panel.on_show()
            if panel.run_update:
                panel.start_updates()
