"""Pruebas del guardado de datos (no necesitan ventana)."""

from hub.storage import Storage


def test_panels_do_not_share_data(tmp_path):
    storage = Storage(tmp_path / "data.json")
    storage.set("pilar", "score", 5)
    storage.set("jorge", "score", 9)
    assert storage.get("pilar", "score") == 5
    assert storage.get("jorge", "score") == 9


def test_data_survives_restart(tmp_path):
    path = tmp_path / "data.json"
    Storage(path).set("pilar", "name", "Pilar")
    assert Storage(path).get("pilar", "name") == "Pilar"


def test_corrupt_file_does_not_crash(tmp_path):
    path = tmp_path / "data.json"
    path.write_text("{esto no es json", encoding="utf-8")
    assert Storage(path).get("pilar", "x", "por_defecto") == "por_defecto"


def test_clear_panel(tmp_path):
    storage = Storage(tmp_path / "data.json")
    storage.set("pilar", "a", 1)
    storage.clear_panel("pilar")
    assert storage.get("pilar", "a") is None
