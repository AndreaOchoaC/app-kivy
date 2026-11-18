"""Información sobre el dispositivo donde corre la app."""

from kivy.metrics import dp
from kivy.utils import platform


def is_mobile() -> bool:
    return platform in ("android", "ios")


def safe_insets() -> tuple:
    """(arriba, abajo) en píxeles que hay que dejar libres: la «ceja» y la barra inferior del iPhone."""
    if platform == "ios":
        return dp(47), dp(26)
    if platform == "android":
        return dp(6), dp(6)
    return 0, 0
