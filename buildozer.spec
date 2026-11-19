[app]

# ============================================================================================
#  Configuración para empaquetar la app en ANDROID con buildozer (lo hace GitHub Actions solo;
#  ver .github/workflows/android.yml). Normalmente NO tienes que tocar este archivo.
#
#  Lo ÚNICO que quizá cambies: si tu panel usa una librería nueva de Python, agrégala en
#  `requirements` (separada por comas) Y en requirements.txt. Hay una prueba que avisa si no
#  coinciden. Las líneas de iOS se leen de aquí también (ver .github/workflows/ios.yml).
# ============================================================================================

title = App
package.name = timeclubstudio
package.domain = org.timeclub
version = 0.1.0

# Carpeta del código y extensiones de archivo que se empaquetan en la app.
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,txt,ttf,otf,wav,ogg,mp3
source.exclude_dirs = tests, docs, bin, scripts, .github, .git, .venv, venv, .vscode, .buildozer, ios-toolchain, examples
source.exclude_patterns = panels/_template/*, dev.py

# Python y librerías que viajan dentro de la app. Debe coincidir con requirements.txt
# (sin las versiones: python-for-android elige la suya).
requirements = python3,kivy

# Versión de python-for-android: fija Python 3.11 y el NDK 25b. No la cambies a la ligera.
p4a.branch = v2024.01.21

icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/presplash.png
android.presplash_color = #08080F

orientation = portrait
fullscreen = 0

# Android: solo 64 bits (todos los celulares actuales). Añade x86_64 si quieres probar en el
# emulador de Android Studio: android.archs = arm64-v8a, x86_64
android.archs = arm64-v8a
android.api = 33
android.ndk = 25b
android.accept_sdk_license = True
android.permissions = INTERNET, VIBRATE
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
