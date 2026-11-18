"""Descubrimiento automático de paneles.

La app NO tiene una lista de paneles escrita a mano. Al arrancar recorre la carpeta
`panels/` y carga cada subcarpeta que no empiece por «_». Por eso:

  * Añadir un panel = crear una carpeta nueva. No hay que tocar ningún archivo compartido,
    así que los alumnos casi nunca tendrán conflictos de git al hacer merge.
  * Los archivos .kv de la carpeta se cargan solos (no hace falta Builder.load_file).
  * Si un panel tiene un error, su tarjeta dice «no se pudo cargar» y el resto de la app
    (y de los paneles) sigue funcionando.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path

from hub.config import PANELS_PACKAGE
from hub.kvloader import load_kv, unload_kv
from hub.panel import PanelInfo, PanelScreen

log = logging.getLogger("hub.registry")


@dataclass(frozen=True)
class PanelEntry:
    """Resultado de intentar cargar una carpeta de panel."""

    folder: str                      # nombre de la carpeta, p. ej. "pilar"
    info: PanelInfo | None = None    # los datos del panel, si cargó bien
    error: str | None = None         # el motivo del fallo, si no cargó

    @property
    def ok(self) -> bool:
        return self.info is not None


def _kv_files(folder: str, package: str) -> list[Path]:
    module = sys.modules.get(f"{package}.{folder}")
    paths = getattr(module, "__path__", None)
    if not paths:
        return []
    return sorted(Path(paths[0]).glob("*.kv"))


def load_panel(folder: str, package: str = PANELS_PACKAGE) -> PanelEntry:
    """Importa `panels.<folder>`, carga sus .kv y valida que cumpla el contrato (variable PANEL)."""
    module_name = f"{package}.{folder}"
    try:
        module = importlib.import_module(module_name)
        info = getattr(module, "PANEL", None)
        if info is None:
            raise ValueError("falta la variable PANEL en el __init__.py del panel")
        if not isinstance(info, PanelInfo):
            raise TypeError("PANEL debe ser un PanelInfo(...)")
        if info.id != folder:
            raise ValueError(f"el id '{info.id}' no coincide con el nombre de la carpeta '{folder}'")
        if not (isinstance(info.screen_class, type) and issubclass(info.screen_class, PanelScreen)):
            raise TypeError("screen_class debe ser una clase que herede de PanelScreen")
        for kv_file in _kv_files(folder, package):
            load_kv(kv_file)
        return PanelEntry(folder, info=info)
    except Exception as exc:  # noqa: BLE001 - queremos atrapar CUALQUIER error del panel
        log.error("No se pudo cargar el panel '%s':\n%s", folder, traceback.format_exc())
        return PanelEntry(folder, error=f"{type(exc).__name__}: {exc}")


def reload_panel(folder: str, package: str = PANELS_PACKAGE) -> PanelEntry:
    """Vuelve a leer el código y los .kv de un panel (la tecla F5 en el PC)."""
    for kv_file in _kv_files(folder, package):
        unload_kv(kv_file)
    prefix = f"{package}.{folder}"
    for name in [n for n in sys.modules if n == prefix or n.startswith(prefix + ".")]:
        del sys.modules[name]
    importlib.invalidate_caches()
    return load_panel(folder, package)


def discover(package: str = PANELS_PACKAGE, only: str | None = None) -> list[PanelEntry]:
    """Una entrada por cada subcarpeta de `package` (ignora las que empiezan con «_»).

    Con `only="pilar"` devuelve solo ese panel (modo «probar mi panel»).
    """
    pkg = importlib.import_module(package)
    folders = [
        m.name for m in pkgutil.iter_modules(pkg.__path__) if m.ispkg and not m.name.startswith("_")
    ]
    if only is not None:
        folders = [f for f in folders if f == only]
        if not folders and (Path(pkg.__path__[0]) / only).is_dir():
            folders = [only]  # p. ej. «_template», que se puede probar a propósito
    entries = [load_panel(folder, package) for folder in folders]
    # Primero los que cargaron bien (por orden y título), al final los que fallaron.
    entries.sort(key=lambda e: (0, e.info.order, e.info.title.lower()) if e.ok else (1, 0, e.folder))
    return entries
