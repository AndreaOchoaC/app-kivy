"""Pruebas de coherencia del proyecto: que lo que se instala en el PC y en el móvil coincida."""

import re
from pathlib import Path

from hub.config import APP_VERSION

ROOT = Path(__file__).resolve().parent.parent


def _spec_value(key):
    text = (ROOT / "buildozer.spec").read_text(encoding="utf-8")
    match = re.search(rf"^{re.escape(key)}\s*=\s*(.*)$", text, re.MULTILINE)
    assert match, f"falta '{key}' en buildozer.spec"
    return match.group(1).strip()


def _requirement_names(path):
    names = set()
    for line in (ROOT / path).read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if line and not line.startswith("-"):
            names.add(re.split(r"[=<>!~\[ ]", line)[0].lower())
    return names


def test_buildozer_requirements_match_requirements_txt():
    """Una librería nueva hay que anotarla en requirements.txt Y en buildozer.spec."""
    mobile = {r.strip().lower() for r in _spec_value("requirements").split(",")}
    mobile.discard("python3")
    pc = _requirement_names("requirements.txt")
    assert mobile == pc, (
        f"requirements.txt {sorted(pc)} y buildozer.spec {sorted(mobile)} no coinciden. "
        "Agrega la librería en los dos sitios (ver docs/GUIA_ALUMNO.md)."
    )


def test_version_matches_buildozer_spec():
    assert _spec_value("version") == APP_VERSION


def test_main_py_is_in_the_root():
    assert (ROOT / "main.py").exists()
