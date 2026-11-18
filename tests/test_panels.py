"""Pruebas AUTOMÁTICAS para cada panel: se aplican a todas las carpetas de panels/.

Si tu panel está roto (error de sintaxis, falta PANEL, un .kv mal escrito...), estas pruebas
lo detectan en GitHub antes de que se mezcle con main. No tienes que escribir nada.
"""

import pytest
from conftest import panel_folders

from hub.registry import load_panel


@pytest.mark.parametrize("folder", panel_folders())
def test_panel_loads(folder):
    entry = load_panel(folder)
    assert entry.ok, f"panels/{folder} no cargó: {entry.error}"
    assert entry.info.id == folder


@pytest.mark.parametrize("folder", panel_folders())
def test_panel_opens_and_runs(app, folder):
    app.open_panel(folder, animate=False)
    panel = app.current_panel()
    assert panel is not None, f"panels/{folder} no se pudo abrir"
    panel.dispatch("on_enter")
    for _ in range(30):          # simula medio segundo de juego a 60 cuadros por segundo
        panel.update(1 / 60)
    panel.save("prueba", 123)
    assert panel.load("prueba") == 123
    panel.dispatch("on_leave")
