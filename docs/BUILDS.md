# Builds de Android e iOS (guía detallada)

Esta guía explica **qué pasa exactamente** cuando haces `git push`, cómo funcionan los workflows y qué hacer si
un build falla. Las instrucciones para **instalar** el APK y el IPA en el celular están en el
[README](../README.md#instalar-el-apk-android).

```text
git push (cualquier rama)
   │
   ├─▶ ci.yml        Pruebas   (1-2 min)   ruff + pytest de TODOS los paneles
   ├─▶ android.yml   Android   (10-40 min) buildozer  ──▶ app-kivy-android-<rama>.apk ─┐
   └─▶ ios.yml       iOS       (15-40 min) kivy-ios + Xcode ─▶ app-kivy-ios-<rama>.ipa ─┤
                                                                                        ▼
                                                        Release «build-<rama>» + Artifact de Actions
```

Los tres corren **a la vez** y de forma independiente: si las pruebas fallan, los builds siguen (así puedes
probar el celular aunque aún haya algo por arreglar), pero para unir con `main` las pruebas tienen que pasar.

---

## 1. Cuándo se ejecutan

| Evento | Pruebas | Android | iOS |
|---|:-:|:-:|:-:|
| `git push` a **cualquier rama** | ✅ | ✅ | ✅ |
| `git push` que **solo** cambia `*.md` o `docs/` | ✅ | — | — |
| Pull Request hacia `main` | ✅ | — | — |
| A mano: *Actions → (workflow) → Run workflow* y eliges la rama | — | ✅ | ✅ |
| Se borra una rama | — | — | — (`cleanup.yml` borra su release) |

**`concurrency`:** cada workflow tiene un «carril» por rama (`android-refs/heads/panel/pilar`). Si subes otro
commit mientras el anterior se compila, **el viejo se cancela** y solo se termina el último. Así no se acumulan
builds de 40 minutos de commits que ya no importan.

**`paths-ignore`:** cambiar solo documentación no gasta un build.

---

## 2. El nombre de la rama («slug») y las releases

Los nombres de rama pueden tener `/` y mayúsculas (`panel/Pilar`), que no sirven para nombres de archivo.
Cada workflow calcula un **slug**: minúsculas y todo lo raro cambiado por `-`:

| Rama | Slug | Etiqueta / release | APK | IPA |
|---|---|---|---|---|
| `main` | `main` | `build-main` | `app-kivy-android-main.apk` | `app-kivy-ios-main.ipa` |
| `panel/pilar` | `panel-pilar` | `build-panel-pilar` | `app-kivy-android-panel-pilar.apk` | `app-kivy-ios-panel-pilar.ipa` |

El script [`.github/scripts/publish_release.sh`](../.github/scripts/publish_release.sh) (lo usan Android e iOS):

1. Crea la release `build-<slug>` si no existe (marcada como *pre-release*; la de `main` se llama «Versión principal»).
   Si Android e iOS intentan crearla en el mismo segundo, el segundo simplemente continúa.
2. **Sube** el archivo (`--clobber`: reemplaza el anterior con el mismo nombre).
3. **Actualiza las notas** con el commit, el autor y la hora.
4. **Mueve la etiqueta** `build-<slug>` al commit compilado.

Resultado: una release **por rama**, siempre con el último build de esa rama. No se acumulan versiones viejas.

Además, los archivos quedan como **Artifacts** de la ejecución (14 días): *Actions → la ejecución → Artifacts*.

Al **borrar una rama**, `cleanup.yml` borra su release y su etiqueta. (GitHub ejecuta ese workflow desde la
versión que está en la rama por defecto, así que el archivo tiene que estar en `main`.)

---

## 3. Android (`android.yml`) paso a paso

| Paso | Qué hace |
|---|---|
| `Calcular nombre de la rama` | Calcula el slug. |
| `Anotar rama y commit` | Reescribe `hub/build_info.py` (solo en la copia del runner) con la rama y el commit. La portada de la app los muestra. |
| `setup-python 3.11` | Python **del runner**, el que ejecuta buildozer. El Python que se empaqueta dentro de la app es otro (3.11, lo fija `p4a.branch`). |
| `Instalar dependencias del sistema` | Java 17, compiladores y librerías (`libtool-bin`, `libltdl-dev`...). Sin ellas, compilar `libffi` falla. |
| `Instalar buildozer` | `buildozer`, `setuptools` y **Cython 0.29.34** (las recetas de python-for-android no soportan Cython 3). |
| `Caché de buildozer` | Guarda `~/.buildozer` (SDK + NDK de Android, ~2 GB) y `.buildozer/` (lo compilado). |
| `Compilar APK (debug)` | `buildozer -v android debug`, hasta **3 intentos** (a veces se corta una descarga de Internet). |
| `Renombrar` · `Subir artefacto` · `Publicar en Releases` | Deja `app-kivy-android-<slug>.apk` en Releases. |

`buildozer.spec` configura el resultado. Lo más importante:

| Línea | Para qué |
|---|---|
| `title`, `package.name`, `package.domain` | Nombre que ve el usuario e identificador único de la app (`org.timeclub.timeclubstudio`). |
| `version` | Versión (debe coincidir con `hub/config.py`; hay una prueba). |
| `requirements = python3,kivy` | Librerías que viajan en la app. **Debe coincidir con `requirements.txt`** (también hay una prueba). |
| `source.include_exts` | Extensiones de archivo que se empaquetan (`py,png,jpg,kv,json,ttf,wav,ogg,mp3...`). Un archivo con otra extensión **no llega al celular**. |
| `source.exclude_dirs` / `exclude_patterns` | Lo que no se empaqueta (`tests`, `docs`, `scripts`, `.github`, `panels/_template`, `dev.py`). |
| `p4a.branch = v2024.01.21` | Versión de python-for-android: fija Python 3.11 y el NDK 25b. Cambiarla puede romper el build. |
| `android.archs = arm64-v8a` | Solo 64 bits (todos los celulares actuales). Para el emulador de Android Studio agrega `, x86_64` (el build tarda más). |
| `android.permissions = INTERNET` | Permisos que pide la app. Si usas cámara, ubicación, vibración... agrégalos aquí (`CAMERA, VIBRATE`). |
| `orientation = portrait` | Solo vertical. Para permitir horizontal: `orientation = all`. |

El APK es de **depuración** (`debug`): está firmado con una llave de depuración, se puede instalar directamente
y **no sirve para subirlo a Google Play** (para eso hace falta un build `release` con tu propia llave).

### Tiempos y caché

- **Primera vez en el repo:** 25–40 minutos (descarga SDK/NDK y compila Python, Kivy y sus dependencias).
- **Con caché:** 10–15 minutos.
- La caché de GitHub se comparte así: **una rama nueva puede leer la caché de `main`** (por `restore-keys`),
  pero las cachés creadas en una rama no las ven otras ramas. Por eso conviene que **`main` se compile primero**.
- GitHub borra las cachés que no se usan en **7 días** y el límite es 10 GB por repositorio (Android ≈ 2–3 GB,
  iOS ≈ 1–2 GB). Si pasan varios días sin builds, el siguiente será «el primero» otra vez.
- La clave de la caché incluye `buildozer.spec` y `requirements.txt`: si cambias las librerías, se recompila.

---

## 4. iOS (`ios.yml`) paso a paso

Corre en `macos-14` (un Mac virtual con Xcode). **En repositorios públicos es gratis.**

| Paso | Qué hace |
|---|---|
| `brew install autoconf automake libtool pkg-config` | Herramientas de compilación que pide kivy-ios. |
| `pip install kivy-ios "cython==3.0.11" setuptools` | kivy-ios compila Python y Kivy para iOS. Necesita Cython. |
| `Leer las librerías de buildozer.spec` | Toma `requirements = python3,kivy,...` de **`buildozer.spec`** y lo convierte en la lista de recetas de kivy-ios. Así Android e iOS **usan siempre las mismas librerías**. |
| `Caché de la toolchain` | `ios-toolchain/build` y `dist`: Python y Kivy ya compilados para iOS (lo más lento: ~18 min). Se guarda **justo después de compilar**, para que un fallo posterior no obligue a repetirlo. |
| `toolchain build $RECIPES` | Compila Python, Kivy y tus librerías para **iPhone y simulador**. |
| `Preparar carpeta de la app` | Copia el proyecto a `ios-toolchain/app/` sin `.git`, `tests`, `docs`, `.venv`, `panels/_template`... |
| `toolchain create` | Genera el **proyecto de Xcode** con tu código dentro. |
| `xcodebuild` (simulador) | Compila `Debug` para `iphonesimulator` (arm64). |
| `xcodebuild` (iPhone) | Compila `Release` para `iphoneos` con `CODE_SIGNING_ALLOWED=NO` y **empaqueta el `.ipa` a mano** (`Payload/` + `zip`). |
| `Publicar en Releases` | Sube `app-kivy-ios-<slug>.ipa` y `app-kivy-ios-<slug>-simulador.zip`. |

**¿Por qué el IPA no está firmado?** Firmar requiere una cuenta de **Apple Developer** (99 USD/año) con
certificados que no queremos guardar en un repositorio público. El `.ipa` sin firmar se instala con
[Sideloadly](https://sideloadly.io) usando un Apple ID gratuito (que lo firma en el momento; caduca a los 7 días).

### Si algún día se quiere un IPA firmado (TestFlight / instalación directa)

1. Cuenta de Apple Developer de pago; crear un certificado *Apple Distribution* y un *provisioning profile*.
2. Guardar el `.p12` (en base64) y el `.mobileprovision` como **Secrets** del repositorio
   (*Settings → Secrets and variables → Actions*). **Nunca** en el código.
3. En `ios.yml`: importar el certificado a un *keychain* temporal y ejecutar `xcodebuild archive` +
   `xcodebuild -exportArchive` en lugar del empaquetado manual.

Es un trabajo aparte; esta versión no lo necesita.

---

## 5. Cuando un build falla

Abre *Actions → la ejecución fallida → el paso en rojo*: el registro dice qué pasó. Los más comunes:

| Síntoma | Causa probable | Solución |
|---|---|---|
| Android: `Connection reset by peer`, `Read timed out`, error al descargar el NDK/SDK | Red de GitHub | El workflow ya reintenta 3 veces. Si aun así falla: *Re-run failed jobs*. |
| Android: `possibly undefined macro: LT_SYS_SYMBOL_USCORE` | Faltan `libltdl-dev` / `libtool-bin` | Ya están en el workflow. Si lo editaste, vuelve a ponerlos. |
| Android: errores de `cython` / `cythonize` al compilar Kivy | Versión de Cython incorrecta | Debe ser `cython==0.29.34` en `android.yml`. |
| Android: `No module named ...` al **abrir** el APK en el celular | Una librería no está en `requirements` de `buildozer.spec` | Agrégala a `buildozer.spec` **y** a `requirements.txt`. |
| Android: la app abre y se cierra de inmediato | Error de Python al arrancar (mira el log con `adb logcat | grep python`) | Prueba la misma rama en PC: `python dev.py run`. Suele ser una librería o un archivo con extensión no empaquetada. |
| Android/iOS: el build falla después de agregar una librería | Esa librería no tiene receta para móviles | Quítala o pide ayuda al profesor. |
| iOS: `Missing requirement: cython is not installed` | Falta Cython 3.0.11 | Ya está en `ios.yml`. |
| iOS: `xcodebuild: error: ... requires a provisioning profile` | El comando perdió `CODE_SIGNING_ALLOWED=NO` | Restáuralo. |
| iOS: tarda > 60 min | La caché venció (7 días sin builds) | Es normal; la siguiente vez será rápida. |
| `Resource not accessible by integration` al publicar en Releases | Falta permiso de escritura | *Settings → Actions → General → Workflow permissions → Read and write*. |
| Las pruebas fallan pero «en mi PC pasan» | Otra versión de Python (3.11 vs 3.13) o rutas distintas | Revisa el registro; reproduce con `python dev.py check`. |

---

## 6. Compilar en tu propia computadora (opcional)

Normalmente **no hace falta**: GitHub lo hace por ti. Pero si quieres:

- **Android:** buildozer solo funciona en **Linux** (en Windows, usa WSL2 con Ubuntu 22.04/24.04). Instala las
  dependencias de `android.yml` y ejecuta `pip install buildozer cython==0.29.34` y `buildozer -v android debug`.
  El APK queda en `bin/`.
- **iOS:** necesita un **Mac con Xcode**. Sigue los pasos de `ios.yml` a mano (`toolchain build`, `toolchain create`...).

---

## 7. Subir la versión de la app

Cuando quieras una versión nueva (por ejemplo `0.2.0`), cámbiala en **dos** lugares: `hub/config.py`
(`APP_VERSION`) y `buildozer.spec` (`version`). Si olvidas uno, `python dev.py check` te avisa.
