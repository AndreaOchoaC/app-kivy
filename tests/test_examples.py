"""Pruebas de los ejemplos de examples/ (modelos para que los alumnos copien)."""

import pkgutil

import pytest
from conftest import ROOT

from hub.registry import load_panel

EXAMPLES = sorted(
    m.name for m in pkgutil.iter_modules([str(ROOT / "examples")])
    if m.ispkg and not m.name.startswith("_")
)


def make(folder):
    entry = load_panel(folder, "examples")
    assert entry.ok, entry.error
    return entry.info.screen_class(info=entry.info, storage=None)


@pytest.mark.parametrize("folder", EXAMPLES)
def test_example_loads_and_runs(app, folder):
    panel = make(folder)
    panel.dispatch("on_enter")
    for _ in range(30):
        panel.update(1 / 60)
    panel.dispatch("on_leave")


def test_star_game_plays_and_saves_best_score(app):
    panel = make("juego_estrella")
    panel.start()
    assert panel.playing
    for _ in range(120):
        panel.update(1 / 60)
    panel.score = 7
    panel.time_left = 0.001
    panel.update(1 / 60)
    assert panel.playing is False
    assert panel.load("best") == 7


def test_notes_app_adds_and_deletes(app):
    panel = make("notas")
    panel.ids.entrada.text = "Idea 1"
    panel.agregar()
    panel.ids.entrada.text = "Idea 2"
    panel.agregar()
    assert panel.notas == ["Idea 2", "Idea 1"]
    assert len(panel.ids.lista.children) == 2
    panel.borrar(0)
    assert panel.notas == ["Idea 1"]
    assert panel.load("notas") == ["Idea 1"]


def test_multi_window_back_goes_to_inner_menu_first(app):
    panel = make("varias_ventanas")
    panel.ir("ventana_a")
    assert panel.ids.interior.current == "ventana_a"
    assert panel.handle_back() is True
    assert panel.ids.interior.current == "menu"
