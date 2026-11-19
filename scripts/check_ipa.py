"""Revisa un .ipa SIN instalarlo: comprueba que tiene todo lo que Sideloadly y el iPhone necesitan.

    python scripts/check_ipa.py app-kivy-ios-main.ipa

Funciona en Windows, Mac y Linux (solo usa la biblioteca estándar). GitHub lo ejecuta solo en cada
build de iOS; tú puedes ejecutarlo en tu PC con el .ipa que descargaste de Releases.

OJO: esto confirma que el paquete está bien armado, NO que la app se vea bien. Para eso hay que abrirla
en un iPhone (o en el Simulador de un Mac). Mira docs/BUILDS.md.
"""

import plistlib
import struct
import sys
import zipfile

MH_MAGIC_64 = 0xFEEDFACF
CPU_TYPE_ARM64 = 0x0100000C
LC_BUILD_VERSION = 0x32
LC_VERSION_MIN_IPHONEOS = 0x25     # forma antigua de decir «esto es para iPhone»
PLATFORM_IOS = 2
PLATFORM_IOS_SIMULATOR = 7


def _platform_of(binary: bytes):
    """(cpu, plataforma) de un ejecutable Mach-O de 64 bits, o (None, None) si no lo es."""
    if len(binary) < 32:
        return None, None
    magic, cpu = struct.unpack_from("<II", binary, 0)
    if magic != MH_MAGIC_64:
        return None, None
    ncmds = struct.unpack_from("<I", binary, 16)[0]
    offset, platform = 32, None
    for _ in range(ncmds):
        cmd, size = struct.unpack_from("<II", binary, offset)
        if cmd == LC_BUILD_VERSION:
            platform = struct.unpack_from("<I", binary, offset + 8)[0]
            break
        if cmd == LC_VERSION_MIN_IPHONEOS:
            platform = PLATFORM_IOS
            break
        offset += size
    return cpu, platform


def check(path: str):
    """Devuelve (errores, avisos, datos): listas de textos y un diccionario con lo encontrado."""
    errors, warnings, info = [], [], {}
    try:
        z = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as exc:
        return [f"No se puede abrir el .ipa: {exc}"], [], info
    names = z.namelist()

    apps = sorted({n.split("/")[1] for n in names if n.startswith("Payload/") and n.count("/") >= 2
                   and n.split("/")[1].endswith(".app")})
    if len(apps) != 1:
        return [f"Dentro de Payload/ debe haber exactamente una carpeta .app (hay {len(apps)})."], [], info
    root = f"Payload/{apps[0]}/"
    info["app"] = apps[0]

    if f"{root}Info.plist" not in names:
        return ["Falta Info.plist dentro de la app."], [], info
    plist = plistlib.loads(z.read(f"{root}Info.plist"))
    for key in ("CFBundleIdentifier", "CFBundleExecutable", "CFBundleDisplayName", "CFBundleShortVersionString"):
        if not plist.get(key):
            errors.append(f"Info.plist no tiene {key}.")
    info["id"] = plist.get("CFBundleIdentifier")
    info["nombre"] = plist.get("CFBundleDisplayName")
    info["version"] = plist.get("CFBundleShortVersionString")
    info["iOS mínimo"] = plist.get("MinimumOSVersion")
    if plist.get("DTPlatformName") not in (None, "iphoneos"):
        errors.append(f"Está compilada para «{plist.get('DTPlatformName')}», no para iphoneos (¿es la del simulador?).")

    # Ejecutable: arm64 y para iPhone (no para el simulador)
    exe = f"{root}{plist.get('CFBundleExecutable')}"
    if exe not in names:
        errors.append(f"Falta el ejecutable «{plist.get('CFBundleExecutable')}».")
    else:
        cpu, platform = _platform_of(z.read(exe))
        if cpu is None:
            errors.append("El ejecutable no es un Mach-O de 64 bits.")
        else:
            if cpu != CPU_TYPE_ARM64:
                errors.append("El ejecutable no es arm64 (los iPhone actuales lo exigen).")
            if platform == PLATFORM_IOS_SIMULATOR:
                errors.append("El ejecutable es del SIMULADOR: no se puede instalar en un iPhone.")
            elif platform != PLATFORM_IOS:
                warnings.append(f"No pude confirmar la plataforma del ejecutable (código {platform}).")

    # Ícono de la pantalla de inicio
    if f"{root}Assets.car" not in names:
        errors.append("No hay Assets.car: la app saldría SIN ícono en el iPhone.")
    if not plist.get("CFBundleIcons"):
        errors.append("Info.plist no declara ningún ícono (CFBundleIcons vacío).")

    # El código de la app
    if f"{root}YourApp/main.pyc" not in names and f"{root}YourApp/main.py" not in names:
        errors.append("Falta main.py dentro de YourApp/: la app no arrancaría.")
    if not any(n.startswith(f"{root}YourApp/hub/kv/") and n.endswith(".kv") for n in names):
        errors.append("Faltan los archivos .kv de hub/kv/: la app saldría en blanco.")
    panels = sorted({n.split("/")[4] for n in names
                     if n.startswith(f"{root}YourApp/panels/") and n.count("/") >= 5})
    info["paneles"] = ", ".join(panels) or "(ninguno)"
    if not [p for p in panels if not p.startswith("_")]:
        errors.append("No hay ningún panel de alumno dentro de la app.")
    for sobra in ("panels/_template/", "examples/", "tests/", "docs/", ".git/"):
        if any(n.startswith(f"{root}YourApp/{sobra}") for n in names):
            warnings.append(f"Se empaquetó {sobra} (no debería ir dentro de la app).")

    # Cosas que NO deben estar si el IPA va a firmarse con Sideloadly
    if any(n.startswith(f"{root}_CodeSignature/") for n in names):
        warnings.append("Trae _CodeSignature (el IPA ya viene firmado): Sideloadly lo vuelve a firmar igual.")
    orient = plist.get("UISupportedInterfaceOrientations") or []
    if orient != ["UIInterfaceOrientationPortrait"]:
        warnings.append("La app permite girar la pantalla; el diseño está pensado solo en vertical.")
    return errors, warnings, info


def main(argv):
    if len(argv) != 2:
        print("Uso: python scripts/check_ipa.py <archivo.ipa>")
        return 2
    errors, warnings, info = check(argv[1])
    for key, value in info.items():
        print(f"  {key:<10}: {value}")
    for text in warnings:
        print(f"AVISO : {text}")
    for text in errors:
        print(f"ERROR : {text}")
    if errors:
        print(f"\nEl IPA NO está listo ({len(errors)} error(es)).")
        return 1
    print("\nOK: el paquete está bien armado. Falta probarlo en un iPhone o en el Simulador.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
