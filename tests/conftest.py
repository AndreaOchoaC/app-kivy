"""Configuración de las pruebas.

Kivy lee sys.argv al importarse (y pytest usa argumentos propios), así que lo desactivamos.
Estas pruebas necesitan una ventana: en tu PC se abre brevemente; en GitHub Actions se usa
xvfb (una pantalla virtual).
"""

import os
import pkgutil
import sys
from pathlib import Path

os.environ["KIVY_NO_ARGS"] = "1"
os.environ.setdefault("KIVY_NO_CONSOLELOG", "1")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402


def panel_folders():
    """Nombres de las carpetas de panels/ (sin importarlas), para parametrizar las pruebas."""
    return sorted(
        m.name for m in pkgutil.iter_modules([str(ROOT / "panels")])
        if m.ispkg and not m.name.startswith("_")
    )


@pytest.fixture
def app(tmp_path):
    """La app completa, construida pero sin ejecutar el bucle principal."""
    from hub.app import HubApp

    application = HubApp(storage_path=tmp_path / "data.json")
    application.build()
    yield application
    application.on_stop()
