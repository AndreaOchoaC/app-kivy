"""Carga archivos .kv una sola vez (cargarlos dos veces duplicaría los widgets)."""

from __future__ import annotations

from pathlib import Path

from kivy.lang import Builder

_loaded: set[str] = set()


def load_kv(path) -> bool:
    """Carga un archivo .kv si aún no estaba cargado. Devuelve True si lo cargó ahora."""
    key = str(Path(path).resolve())
    if key in _loaded:
        return False
    Builder.load_file(key)
    _loaded.add(key)
    return True


def unload_kv(path) -> None:
    """Descarta un .kv ya cargado (lo usa la recarga en caliente con F5)."""
    key = str(Path(path).resolve())
    if key in _loaded:
        Builder.unload_file(key)
        _loaded.discard(key)
