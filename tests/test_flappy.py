"""Pruebas del juego Flappy Bird que viene en los paneles de Pilar, Emiliano y Jorge.

Si un alumno convierte su panel en otra cosa (ya no hay pájaro), la prueba se salta sola.
"""

import pytest
from conftest import panel_folders


def _flappy(app, folder):
    app.open_panel(folder, animate=False)
    panel = app.current_panel()
    assert panel is not None, f"panels/{folder} no se pudo abrir"
    if not hasattr(panel, "_flap"):
        pytest.skip(f"panels/{folder} ya no es el Flappy Bird original")
    panel.dispatch("on_enter")
    return panel


@pytest.mark.parametrize("folder", panel_folders())
def test_flappy_starts_waiting_for_the_first_tap(app, folder):
    panel = _flappy(app, folder)
    assert panel.phase == "ready" and panel.score == 0
    panel._flap()
    assert panel.phase == "play"
    panel.dispatch("on_leave")


@pytest.mark.parametrize("folder", panel_folders())
def test_flappy_dies_saves_best_and_restarts(app, folder):
    panel = _flappy(app, folder)
    panel._flap()
    panel.score = 5                       # como si ya hubiera pasado 5 tubos
    for _ in range(600):                  # 10 s sin aletear: cae al suelo
        panel.update(1 / 60)
    assert panel.phase == "over"
    assert panel.new_record is True and panel.load("best") == 5
    assert panel._overlay.parent is not None       # se ve la tarjeta de fin

    panel.play_again()
    assert panel.phase == "ready" and panel.score == 0
    assert panel._overlay.parent is None
    panel.dispatch("on_leave")


@pytest.mark.parametrize("folder", panel_folders())
def test_flappy_keeps_the_best_score_between_games(app, folder):
    panel = _flappy(app, folder)
    panel.save("best", 9)
    panel.best = 9
    panel._flap()
    panel.score = 3
    for _ in range(600):
        panel.update(1 / 60)
    assert panel.phase == "over" and panel.new_record is False
    assert panel.load("best") == 9
    panel.dispatch("on_leave")
