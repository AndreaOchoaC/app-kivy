"""Pruebas del núcleo: portada, navegación, errores y recarga."""

from hub.home import greeting
from hub.panel import PanelScreen
from hub.registry import discover


def test_home_has_one_card_per_panel(app):
    cards = app.home.ids.grid.children
    assert len(cards) == len(app.entries) >= 3


def test_template_is_not_listed(app):
    assert "_template" not in [e.folder for e in app.entries]


def test_open_panel_and_go_home(app):
    app.open_panel("pilar", animate=False)
    assert app.current_panel() is not None and app.manager.current == "pilar"
    app.go_home()
    assert app.manager.transition.direction == "right"


def test_unknown_panel_shows_message_instead_of_crashing(app):
    app.open_panel("no_existe")  # no debe lanzar excepción
    assert app.current_panel() is None


def test_back_key_returns_home(app):
    app.open_panel("pilar", animate=False)
    handled = app._on_keyboard(None, 27)
    assert handled is True


def test_error_in_a_panel_shows_sheet_and_does_not_crash(app):
    app.open_panel("pilar", animate=False)
    try:
        raise ValueError("error de prueba")
    except ValueError as exc:
        app.show_panel_error(exc)
    assert app.sheet_open is True
    app._error_home()
    assert app.sheet_open is False


def test_reload_current_panel_recreates_it(app):
    app.open_panel("pilar", animate=False)
    before = app.current_panel()
    app.reload_current_panel()
    after = app.current_panel()
    assert after is not None and after is not before


def test_only_mode_lists_a_single_panel(tmp_path):
    entries = discover(only="pilar")
    assert [e.folder for e in entries] == ["pilar"] and entries[0].ok


def test_panel_screen_routes_kv_children_into_content(app):
    app.open_panel("pilar", animate=False)
    panel = app.current_panel()
    assert isinstance(panel, PanelScreen)
    assert panel.content is not panel
    assert len(panel.content.children) >= 1


def test_greeting_changes_with_the_hour():
    from datetime import datetime

    assert greeting(datetime(2026, 1, 1, 9)) == "Buenos días"
    assert greeting(datetime(2026, 1, 1, 15)) == "Buenas tardes"
    assert greeting(datetime(2026, 1, 1, 22)) == "Buenas noches"
