"""Guardado local en un archivo JSON. No depende de Kivy, así que se puede probar sin ventana.

La app lo guarda dentro de `App.user_data_dir`, una carpeta privada de la app tanto en
Android como en iOS (y en el PC, en %APPDATA%). Cada panel tiene su propio espacio, así que
dos alumnos nunca se pisan los datos aunque usen la misma clave.

Desde un panel se usa con `self.save("clave", valor)` y `self.load("clave", por_defecto)`.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

log = logging.getLogger("hub.storage")


class Storage:
    """Lee y escribe `{"panels": {"pilar": {...}}, "settings": {...}}`."""

    def __init__(self, path):
        self.path = Path(path)
        self._data = {"panels": {}, "settings": {}}
        self.load()

    # -- disco ----------------------------------------------------------------------------
    def load(self):
        """Carga el archivo. Si no existe o está dañado, se parte de cero sin fallar."""
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if isinstance(raw, dict):
            for key in ("panels", "settings"):
                if isinstance(raw.get(key), dict):
                    self._data[key] = raw[key]

    def save(self):
        """Guarda de forma segura: escribe un temporal y lo renombra al final."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, self.path)
        except OSError as exc:
            log.warning("No se pudo guardar %s: %s", self.path, exc)

    # -- datos de cada panel ----------------------------------------------------------------
    def get(self, panel_id: str, key: str, default=None):
        return self._data["panels"].get(panel_id, {}).get(key, default)

    def set(self, panel_id: str, key: str, value):
        """Guarda `value` (texto, número, lista o diccionario) y escribe el archivo."""
        self._data["panels"].setdefault(panel_id, {})[key] = value
        self.save()

    def clear_panel(self, panel_id: str):
        """Borra todos los datos de un panel."""
        self._data["panels"].pop(panel_id, None)
        self.save()

    # -- ajustes generales ------------------------------------------------------------------
    def get_setting(self, key: str, default=None):
        return self._data["settings"].get(key, default)

    def set_setting(self, key: str, value):
        self._data["settings"][key] = value
        self.save()
