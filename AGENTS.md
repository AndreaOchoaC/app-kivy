# Instrucciones para asistentes de IA y agentes de código

**Antes de escribir o modificar cualquier cosa, lee completo [`docs/CONTEXTO_IA.md`](docs/CONTEXTO_IA.md).**
Ahí está todo: cómo está hecho el proyecto, qué librerías y widgets existen, qué scripts hay y cómo deben escribirse
los archivos de un panel para que funcionen en PC, Android e iOS.

Resumen de las reglas más importantes:

- Este es un proyecto **educativo** (alumnos de 10 a 15 años). Responde **en español**, con explicaciones simples.
- Cada alumno trabaja **solo en su carpeta** `panels/<nombre>/` (`__init__.py`, `panel.py`, `panel.kv`, `assets/`).
  **No modifiques** `hub/`, `panels/_template/`, `main.py`, `dev.py`, `buildozer.spec`, `.github/` ni los paneles de otros alumnos.
- Solo **Kivy 2.3.1 y la biblioteca estándar** (código compatible con Python 3.11). Sin `time.sleep`, `while True`, `input`,
  emojis ni rutas de PC.
- Comandos: `python dev.py panel <carpeta>` (probar un panel), `python dev.py check` (estilo + pruebas; debe pasar antes de subir).
- Trabaja en una rama propia (`panel/<nombre>`), nunca en `main`.
