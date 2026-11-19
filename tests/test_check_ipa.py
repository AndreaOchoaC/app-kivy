"""Pruebas de scripts/check_ipa.py con un .ipa de mentira (sin necesidad de Mac ni iPhone)."""

import importlib.util
import plistlib
import struct
import zipfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check_ipa.py"
spec = importlib.util.spec_from_file_location("check_ipa", SCRIPT)
check_ipa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_ipa)


def _macho(platform=check_ipa.PLATFORM_IOS):
    """Cabecera mínima de un ejecutable arm64 con un comando LC_BUILD_VERSION."""
    header = struct.pack("<IIIIIIII", check_ipa.MH_MAGIC_64, check_ipa.CPU_TYPE_ARM64, 0, 2, 1, 24, 0, 0)
    return header + struct.pack("<IIIIII", check_ipa.LC_BUILD_VERSION, 24, platform, 0, 0, 0)


def _ipa(tmp_path, *, icon=True, platform=check_ipa.PLATFORM_IOS, extra=()):
    plist = {
        "CFBundleIdentifier": "org.timeclub.timeclubstudio",
        "CFBundleExecutable": "app",
        "CFBundleDisplayName": "App",
        "CFBundleShortVersionString": "0.1.0",
        "MinimumOSVersion": "13.0",
        "DTPlatformName": "iphoneos",
        "CFBundleIcons": {"CFBundlePrimaryIcon": {"CFBundleIconName": "AppIcon"}} if icon else {},
        "UISupportedInterfaceOrientations": ["UIInterfaceOrientationPortrait"],
    }
    path = tmp_path / "app.ipa"
    root = "Payload/app.app/"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(root + "Info.plist", plistlib.dumps(plist))
        z.writestr(root + "app", _macho(platform))
        z.writestr(root + "YourApp/main.pyc", b"x")
        z.writestr(root + "YourApp/hub/kv/home.kv", "x")
        z.writestr(root + "YourApp/panels/pilar/panel.pyc", b"x")
        if icon:
            z.writestr(root + "Assets.car", b"x")
        for name in extra:
            z.writestr(root + name, b"x")
    return str(path)


def test_a_good_ipa_has_no_errors(tmp_path):
    errors, warnings, info = check_ipa.check(_ipa(tmp_path))
    assert errors == [] and warnings == []
    assert info["id"] == "org.timeclub.timeclubstudio" and info["paneles"] == "pilar"


def test_missing_icon_is_an_error(tmp_path):
    errors, _, _ = check_ipa.check(_ipa(tmp_path, icon=False))
    assert any("ícono" in e for e in errors)


def test_a_simulator_build_is_rejected(tmp_path):
    errors, _, _ = check_ipa.check(_ipa(tmp_path, platform=check_ipa.PLATFORM_IOS_SIMULATOR))
    assert any("SIMULADOR" in e for e in errors)


def test_extra_folders_only_warn(tmp_path):
    errors, warnings, _ = check_ipa.check(_ipa(tmp_path, extra=["YourApp/examples/x.pyc"]))
    assert errors == [] and any("examples/" in w for w in warnings)


def test_not_a_zip_is_reported(tmp_path):
    bad = tmp_path / "bad.ipa"
    bad.write_bytes(b"no soy un zip")
    errors, _, _ = check_ipa.check(str(bad))
    assert errors and "No se puede abrir" in errors[0]


@pytest.mark.parametrize("args,code", [(["x"], 2)])
def test_main_needs_a_file(args, code):
    assert check_ipa.main(args) == code
