#!/usr/bin/env sh
# Prepara el entorno después de clonar el repo (ver README.md). Se puede ejecutar varias veces.
cd "$(dirname "$0")" || exit 1
PY=$(command -v python3 || command -v python) || { echo "No encontré Python. Instálalo desde https://www.python.org/downloads/"; exit 1; }
exec "$PY" scripts/bootstrap.py "$@"
