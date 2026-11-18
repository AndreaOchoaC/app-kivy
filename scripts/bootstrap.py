#!/usr/bin/env python3
"""Prepara el entorno de trabajo después de clonar el repositorio. Es seguro ejecutarlo varias veces.

    Windows:     setup.bat
    Mac/Linux:   ./setup.sh

Qué hace:
  1. Busca un Python compatible con Kivy (3.10 a 3.13) en tu computadora.
  2. Crea el entorno virtual `.venv` (una carpeta con las librerías SOLO de este proyecto).
  3. Instala las librerías de requirements-dev.txt (Kivy, pytest, ruff).
  4. Comprueba que todo funciona y te dice cuál es el siguiente paso.

Solo usa la biblioteca estándar de Python: puede ejecutarse antes de instalar nada.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV = ROOT / ".venv"
VENV_PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
STAMP = VENV / ".requirements-hash"
MIN_VERSION, MAX_VERSION = (3, 10), (3, 13)     # Kivy 2.3.1 funciona hasta Python 3.13
QUIET = "--quiet" in sys.argv


def say(message=""):
    if not QUIET:
        print(message)


def version_of(command: list[str]):
    """(mayor, menor) del intérprete `command`, o None si no existe o no responde."""
    try:
        out = subprocess.run(
            [*command, "-c", "import sys; print(sys.version_info[0], sys.version_info[1])"],
            capture_output=True, text=True, timeout=20,
        )
        major, minor = out.stdout.split()
        return int(major), int(minor)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def supported(version) -> bool:
    return version is not None and MIN_VERSION <= version <= MAX_VERSION


def find_python() -> list[str] | None:
    """Devuelve el comando de un Python compatible, probando de más nuevo a más viejo."""
    candidates: list[list[str]] = [[sys.executable]]
    if os.name == "nt":
        candidates += [["py", f"-3.{minor}"] for minor in range(MAX_VERSION[1], MIN_VERSION[1] - 1, -1)]
    candidates += [[f"python3.{minor}"] for minor in range(MAX_VERSION[1], MIN_VERSION[1] - 1, -1)]
    candidates += [["python3"], ["python"]]
    for command in candidates:
        if shutil.which(command[0]) and supported(version_of(command)):
            return command
    return None


def requirements_hash() -> str:
    digest = hashlib.sha256()
    for name in ("requirements.txt", "requirements-dev.txt"):
        digest.update((ROOT / name).read_bytes())
    return digest.hexdigest()


def fail(message: str):
    print(f"\n✗ {message}\n")
    sys.exit(1)


def main() -> int:
    say("=== Preparando el entorno del proyecto ===\n")

    # 1) ¿El entorno virtual existente sirve?
    if VENV_PY.exists() and not supported(version_of([str(VENV_PY)])):
        say("El entorno virtual existente usa un Python no compatible: lo vuelvo a crear.")
        shutil.rmtree(VENV, ignore_errors=True)

    # 2) Crear el entorno virtual si falta
    if not VENV_PY.exists():
        python = find_python()
        if python is None:
            fail(
                "No encontré Python 3.10 a 3.13 (Kivy todavía no funciona con 3.14).\n"
                "  Instálalo desde https://www.python.org/downloads/  (versión 3.13)\n"
                "  En Windows marca la casilla «Add python.exe to PATH» al instalar.\n"
                "  Después cierra y abre la terminal y vuelve a ejecutar este script."
            )
        say(f"Usando: {' '.join(python)}  (Python {'.'.join(map(str, version_of(python)))})")
        say("Creando el entorno virtual en .venv ...")
        if subprocess.call([*python, "-m", "venv", str(VENV)]) != 0:
            fail("No se pudo crear el entorno virtual. En Linux prueba: sudo apt install python3-venv")
        STAMP.unlink(missing_ok=True)

    # 3) Instalar librerías (solo si cambiaron los requirements)
    wanted = requirements_hash()
    installed = STAMP.read_text().strip() if STAMP.exists() else ""
    if installed != wanted:
        say("Instalando librerías (la primera vez tarda un par de minutos) ...")
        pip = [str(VENV_PY), "-m", "pip", "install", "--disable-pip-version-check", "-q"]
        subprocess.call([*pip, "--upgrade", "pip"])
        if subprocess.call([*pip, "-r", str(ROOT / "requirements-dev.txt")]) != 0:
            fail("Falló la instalación de las librerías. Revisa tu conexión a Internet y reintenta.")
        STAMP.write_text(wanted)
    else:
        say("Las librerías ya están al día.")

    # 4) Comprobación final
    env = dict(os.environ, KIVY_NO_ARGS="1", KIVY_NO_CONSOLELOG="1")
    check = subprocess.run(
        [str(VENV_PY), "-c", "import kivy, pytest, ruff; print(kivy.__version__)"],
        capture_output=True, text=True, env=env,
    )
    if check.returncode != 0:
        STAMP.unlink(missing_ok=True)
        fail(f"Kivy no se pudo importar:\n{check.stderr.strip()[-600:]}")
    say(f"\n✓ Kivy {check.stdout.strip()} instalado.")

    if shutil.which("git") is None:
        say("\n! No encontré git. Instálalo desde https://git-scm.com/downloads")
    else:
        name = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True).stdout.strip()
        if not name:
            say(
                "\n! git no sabe quién eres todavía. Ejecuta (con tus datos):\n"
                '    git config --global user.name "Tu Nombre"\n'
                '    git config --global user.email "tu@correo.com"'
            )

    say("\nListo. Siguientes pasos:")
    say("    python dev.py run            abre la app completa")
    say("    python dev.py panel <nombre> abre solo tu panel")
    say("    python dev.py doctor         revisa que todo esté bien")
    return 0


if __name__ == "__main__":
    sys.exit(main())
