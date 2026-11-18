#!/usr/bin/env python3
"""Herramientas del proyecto en un solo comando. Funciona con cualquier Python (no necesita Kivy).

    python dev.py run                  abre la app completa
    python dev.py panel pilar          abre SOLO tu panel (cambia «pilar» por tu carpeta)
    python dev.py new maria            crea el panel «maria» a partir de la plantilla
    python dev.py list                 lista los paneles que la app encuentra
    python dev.py test                 corre las pruebas automáticas
    python dev.py lint                 revisa el estilo del código (ruff)
    python dev.py fix                  arregla solo los problemas de estilo que se puedan
    python dev.py check                lint + test (lo mismo que hace GitHub antes de aceptar tu código)
    python dev.py doctor               revisa que tu entorno esté bien instalado

Usa el Python del entorno virtual (.venv) automáticamente. Si todavía no existe, ejecuta antes
setup.bat (Windows) o ./setup.sh (Mac/Linux).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_PY = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
COLORS = ["#FF5E8A", "#2FB8FF", "#FBBF24", "#34D399", "#A78BFA", "#FB923C", "#F472B6"]


def venv_python() -> str:
    """El Python del entorno virtual. Si no existe, explica qué hacer y termina."""
    if VENV_PY.exists():
        return str(VENV_PY)
    sys.exit(
        "Todavía no hay entorno virtual (.venv). Ejecútalo una vez:\n"
        "   Windows:   setup.bat\n"
        "   Mac/Linux: ./setup.sh"
    )


def run(args: list[str], **kwargs) -> int:
    print("»", " ".join(args), flush=True)
    return subprocess.call(args, cwd=ROOT, **kwargs)


# --------------------------------------------------------------------------- comandos
def cmd_run(_args):
    return run([venv_python(), "main.py"])


def cmd_panel(args):
    if not args:
        sys.exit("Uso: python dev.py panel <nombre_de_tu_carpeta>   (mira: python dev.py list)")
    return run([venv_python(), "main.py", args[0]])


def cmd_list(_args):
    code = (
        "import os;os.environ['KIVY_NO_ARGS']='1';os.environ['KIVY_NO_CONSOLELOG']='1';"
        "from hub.registry import discover;"
        "[print(('OK     ' if e.ok else 'ERROR  ') + e.folder + '  ->  ' + "
        "(f'{e.info.title}  ({e.info.author})' if e.ok else e.error)) for e in discover()]"
    )
    return run([venv_python(), "-c", code])


def cmd_test(args):
    return run([venv_python(), "-m", "pytest", *args])


def cmd_lint(_args):
    return run([venv_python(), "-m", "ruff", "check", "."])


def cmd_fix(_args):
    return run([venv_python(), "-m", "ruff", "check", ".", "--fix"])


def cmd_check(args):
    if cmd_lint(args) != 0:
        return 1
    return cmd_test(args)


def cmd_doctor(_args):
    print(f"Python que ejecuta dev.py : {sys.version.split()[0]}  ({sys.executable})")
    if not VENV_PY.exists():
        print("Entorno virtual           : NO existe  ->  ejecuta setup.bat / ./setup.sh")
        return 1
    print(f"Entorno virtual           : {VENV_PY}")
    code = (
        "import sys, kivy, pytest;print('Python del entorno       :', sys.version.split()[0]);"
        "print('Kivy                      :', kivy.__version__);"
        "print('pytest                    :', pytest.__version__)"
    )
    env = dict(os.environ, KIVY_NO_ARGS="1", KIVY_NO_CONSOLELOG="1")
    status = run([str(VENV_PY), "-c", code], env=env)
    git = shutil.which("git")
    print(f"git                       : {git or 'NO se encontró (instálalo desde git-scm.com)'}")
    if status == 0:
        print("\nTodo bien. Prueba:  python dev.py run")
    return status


def slugify(name: str) -> str:
    """«María José» -> «maria_jose» (un nombre de carpeta válido para Python)."""
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    if not text or text[0].isdigit():
        text = "panel_" + text
    return text


def cmd_new(args):
    options = [a for a in args if a.startswith("--color=")]
    names = [a for a in args if not a.startswith("--")]
    if not names:
        sys.exit("Uso: python dev.py new <nombre>   (opcional: --color=#FF5E8A)")
    display = " ".join(names).strip().title()
    folder = slugify(display)
    target = ROOT / "panels" / folder
    if target.exists():
        sys.exit(f"Ya existe panels/{folder}/. Elige otro nombre.")

    existing = [p for p in (ROOT / "panels").iterdir() if p.is_dir() and not p.name.startswith("_")]
    color = options[0].split("=", 1)[1] if options else COLORS[len(existing) % len(COLORS)]
    class_name = "".join(part.capitalize() for part in folder.split("_")) + "Panel"

    shutil.copytree(ROOT / "panels" / "_template", target, ignore=shutil.ignore_patterns("__pycache__"))
    replacements = {
        "TemplatePanel": class_name,
        'title="Mi panel"': f'title="Panel de {display}"',
        'author="Tu nombre"': f'author="{display}"',
        'color="#7C6CFF"': f'color="{color}"',
    }
    for file in target.rglob("*"):
        if file.suffix in (".py", ".kv"):
            text = file.read_text(encoding="utf-8")
            for old, new in replacements.items():
                text = text.replace(old, new)
            file.write_text(text, encoding="utf-8", newline="\n")
    print(f"Listo: se creó panels/{folder}/")
    print(f"  Pruébalo:   python dev.py panel {folder}")
    print(f"  Edita:      panels/{folder}/panel.kv  y  panels/{folder}/panel.py")
    return 0


COMMANDS = {
    "run": cmd_run,
    "panel": cmd_panel,
    "list": cmd_list,
    "new": cmd_new,
    "test": cmd_test,
    "lint": cmd_lint,
    "fix": cmd_fix,
    "check": cmd_check,
    "doctor": cmd_doctor,
}


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help", "help") or argv[0] not in COMMANDS:
        print(__doc__)
        return 0 if not argv or argv[0] in ("-h", "--help", "help") else 2
    return COMMANDS[argv[0]](argv[1:]) or 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
