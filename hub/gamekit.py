"""Herramientas para hacer JUEGOS dentro de un panel: dibujo, partículas, sonidos y vibración.

Todo se dibuja con instrucciones del canvas de Kivy y se genera por código (sin imágenes ni
audios), así funciona igual en el PC, en Android y en iOS. Cualquier panel puede usarlas:

    from hub.gamekit import GameStage, ParticleBurst, play_sound, texture_from_rows, vertical_gradient

    GameStage          lienzo del juego: sus coordenadas empiezan en (0, 0) en SU esquina.
    vertical_gradient  textura de degradado vertical (cielos, fondos...).
    texture_from_rows  dibuja un sprite con letras (arte de píxeles) y lo convierte en textura.
    ParticleBurst      explosiones de partículas (plumas, chispas, polvo...).
    play_sound(nombre) efectos de sonido «chiptune» (flap, point, hit, jump, coin...).
    vibrate(ms)        hace vibrar el teléfono (solo Android).

Ejemplo completo de uso: panels/pilar/ (Flappy Bird).
"""

from __future__ import annotations

import array
import math
import os
import random
import struct
import tempfile
import threading
import wave
from pathlib import Path

from kivy.graphics import Color, Ellipse, InstructionGroup, PopMatrix, PushMatrix, Translate
from kivy.graphics.texture import Texture
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex, platform


# ============================================================================= lienzo
class GameStage(Widget):
    """Lienzo para dibujar un juego a mano con el canvas.

    En el .kv se usa como cualquier widget (`GameStage: id: stage`). Lo que dibujes en
    `stage.canvas` usa coordenadas LOCALES: (0, 0) es la esquina inferior izquierda del
    lienzo, aunque la pantalla se esté deslizando o tenga márgenes (el notch del iPhone).

    Tiene dos extras listos para usar:
      * `stage.shake`  un Translate: cámbiale `.xy` para sacudir TODO el dibujo.
      * `stage.fx`     un grupo de instrucciones que se dibuja ENCIMA de todo (partículas,
                       destellos). Añade cosas con `stage.fx.add(...)`.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.origin = Translate(self.x, self.y)
        self.shake = Translate(0, 0)
        self.fx = InstructionGroup()
        self.canvas.before.add(PushMatrix())
        self.canvas.before.add(self.origin)
        self.canvas.before.add(self.shake)
        self.canvas.after.add(self.fx)
        self.canvas.after.add(PopMatrix())
        self.bind(pos=self._follow)

    def _follow(self, *_args):
        self.origin.xy = self.pos


# ============================================================================= gráficos
def vertical_gradient(colors, steps=64):
    """Textura de degradado vertical. `colors` va de ARRIBA a ABAJO, p. ej. ["#3AA7FF", "#D6F3FF"].

    Se usa estirándola sobre un Rectangle del tamaño que quieras:
        Rectangle(texture=vertical_gradient(["#3AA7FF", "#D6F3FF"]), pos=(0, 0), size=pantalla)
    """
    stops = [get_color_from_hex(c) for c in colors]
    data = bytearray()
    for row in range(steps - 1, -1, -1):  # OpenGL empieza por abajo
        t = row / (steps - 1)               # 0 = arriba, 1 = abajo
        position = t * (len(stops) - 1)
        index = min(int(position), len(stops) - 2)
        local = position - index
        for channel in range(4):
            value = stops[index][channel] * (1 - local) + stops[index + 1][channel] * local
            data.append(round(value * 255))
    texture = Texture.create(size=(1, steps), colorfmt="rgba")
    texture.blit_buffer(bytes(data), colorfmt="rgba", bufferfmt="ubyte")
    texture.mag_filter = "linear"
    return texture


def _to_bytes(color: str):
    """'#RRGGBB' o '#RRGGBBAA' -> (r, g, b, a) como enteros de 0 a 255."""
    r, g, b, a = get_color_from_hex(color)
    return bytes((round(r * 255), round(g * 255), round(b * 255), round(a * 255)))


def texture_from_rows(rows, palette, mirror=False, repeat=False, smooth=False):
    """Convierte una lista de cadenas (una por fila) en una textura: arte de píxeles SIN imágenes.

        PALETA = {"r": "#E52521", "b": "#2E5BFF"}      # cada letra es un color
        FILAS = ["..rr..", ".rrrr.", "rrbbrr"]          # la primera fila es la de ARRIBA
        textura = texture_from_rows(FILAS, PALETA)
        Rectangle(texture=textura, pos=(x, y), size=(6 * 8, 3 * 8))   # 8 px de pantalla por píxel

    Las letras que no estén en la paleta (por ejemplo "." o " ") son transparentes.
      mirror  True para invertir el dibujo de izquierda a derecha.
      repeat  True si la textura se va a repetir en mosaico (tamaño potencia de 2 recomendado).
      smooth  True para suavizar al agrandar (degradados); False para píxeles nítidos (retro).
    """
    height = len(rows)
    width = len(rows[0])
    for index, row in enumerate(rows):
        if len(row) != width:
            raise ValueError(f"La fila {index} mide {len(row)} y debería medir {width}: {row!r}")

    colors = {letter: _to_bytes(value) for letter, value in palette.items()}
    clear = bytes((0, 0, 0, 0))
    data = bytearray()
    for row in reversed(rows):         # OpenGL empieza por la fila de ABAJO
        if mirror:
            row = row[::-1]
        for letter in row:
            data += colors.get(letter, clear)

    texture = Texture.create(size=(width, height), colorfmt="rgba")
    texture.blit_buffer(bytes(data), colorfmt="rgba", bufferfmt="ubyte")
    mode = "linear" if smooth else "nearest"
    texture.mag_filter = mode
    texture.min_filter = mode
    if repeat:
        texture.wrap = "repeat"
    return texture


class ParticleBurst:
    """Pequeñas explosiones de partículas (plumas, chispas, polvo...).

    Reserva de una vez un grupo de círculos que se reutilizan, así que no crea ni destruye
    objetos mientras se juega (importante para que el móvil no se trabe).

        self.particles = ParticleBurst(stage.fx)                    # al construir el juego
        self.particles.emit(x, y, (1, 0.8, 0, 1), count=14)         # cuando pase algo
        self.particles.update(dt)                                    # en update(dt)
    """

    def __init__(self, canvas, capacity=96):
        self._free = list(range(capacity))
        self._alive = {}
        self._items = []
        for _ in range(capacity):
            color = Color(1, 1, 1, 0)
            dot = Ellipse(pos=(0, 0), size=(0, 0))
            canvas.add(color)
            canvas.add(dot)
            self._items.append((color, dot))

    def emit(self, x, y, color, count=12, speed=180, size=7, life=0.6, gravity=-420, up=0):
        """Lanza `count` partículas desde (x, y) en todas direcciones.

        speed    velocidad inicial (píxeles/s).   size  diámetro inicial.
        life     segundos que viven.              gravity  aceleración vertical (negativa = cae).
        up       impulso extra hacia arriba (para que salten en lugar de abrirse en círculo).
        """
        for _ in range(count):
            if not self._free:
                return
            index = self._free.pop()
            angle = random.uniform(0, math.tau)
            power = random.uniform(0.35, 1.0) * speed
            self._alive[index] = {
                "x": x,
                "y": y,
                "vx": math.cos(angle) * power,
                "vy": math.sin(angle) * power + up,
                "t": 0.0,
                "life": life * random.uniform(0.7, 1.15),
                "size": size * random.uniform(0.6, 1.2),
                "gravity": gravity,
                "color": color,
            }

    def update(self, dt):
        """Mueve y desvanece las partículas vivas."""
        for index in list(self._alive):
            p = self._alive[index]
            p["t"] += dt
            color, dot = self._items[index]
            if p["t"] >= p["life"]:
                del self._alive[index]
                self._free.append(index)
                color.a = 0
                dot.size = (0, 0)
                continue
            p["vy"] += p["gravity"] * dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            fade = 1 - p["t"] / p["life"]
            size = p["size"] * (0.4 + 0.6 * fade)
            r, g, b, a = p["color"]
            color.rgba = (r, g, b, a * fade)
            dot.size = (size, size)
            dot.pos = (p["x"] - size / 2, p["y"] - size / 2)

    def clear(self):
        """Apaga todas las partículas (al reiniciar la partida)."""
        for index in list(self._alive):
            color, dot = self._items[index]
            color.a = 0
            dot.size = (0, 0)
            self._free.append(index)
        self._alive.clear()


# ============================================================================= sonido
SAMPLE_RATE = 22050

# Cada efecto es una lista de «notas»:
#   (frecuencia_inicial, frecuencia_final, duración_s, onda, volumen)
# onda: "square" (cuadrada), "tri" (triangular), "noise" (ruido)
EFFECTS = {
    "flap": [(330, 560, 0.09, "square", 0.35)],
    "point": [(880, 880, 0.07, "square", 0.3), (1320, 1320, 0.12, "square", 0.3)],
    "hit": [(220, 70, 0.28, "noise", 0.5), (160, 60, 0.2, "square", 0.4)],
    "eat": [(520, 880, 0.09, "square", 0.3)],
    "die": [(520, 520, 0.1, "tri", 0.45), (420, 420, 0.1, "tri", 0.45),
            (300, 90, 0.4, "tri", 0.45)],
    "jump": [(260, 640, 0.16, "square", 0.3)],
    "coin": [(988, 988, 0.07, "square", 0.3), (1319, 1319, 0.28, "square", 0.3)],
    "stomp": [(300, 120, 0.1, "square", 0.4), (200, 100, 0.06, "noise", 0.3)],
    "bump": [(150, 100, 0.08, "square", 0.4)],
    "win": [(523, 523, 0.12, "square", 0.3), (659, 659, 0.12, "square", 0.3),
            (784, 784, 0.12, "square", 0.3), (1047, 1047, 0.4, "square", 0.3)],
}


def _synthesize(notes):
    """Convierte la lista de notas en muestras de audio de 16 bits."""
    samples = array.array("h")
    for start_freq, end_freq, duration, kind, volume in notes:
        count = int(SAMPLE_RATE * duration)
        phase = 0.0
        for i in range(count):
            progress = i / max(count - 1, 1)
            freq = start_freq + (end_freq - start_freq) * progress
            phase += freq / SAMPLE_RATE
            if kind == "square":
                value = 1.0 if (phase % 1.0) < 0.5 else -1.0
            elif kind == "tri":
                value = 4.0 * abs((phase % 1.0) - 0.5) - 1.0
            else:
                value = random.uniform(-1.0, 1.0)
            # Envolvente: ataque cortísimo y caída suave para evitar «clics».
            attack = min(1.0, i / (SAMPLE_RATE * 0.004))
            decay = 1.0 - progress * 0.85
            samples.append(int(value * volume * attack * decay * 32000))
    return samples


def _write_wav(path, samples):
    """Escribe el .wav en un archivo temporal y lo renombra al final (así nunca queda a medias)."""
    temp = Path(f"{path}.{threading.get_ident()}.tmp")
    with wave.open(str(temp), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    os.replace(temp, path)


class SoundBank:
    """Genera (una sola vez) y reproduce los efectos. Se obtiene con SoundBank.get().

    Si algo falla (no hay audio, el dispositivo no lo soporta...), el juego sigue en silencio:
    el sonido nunca debe tumbar la app. Para apagarlo del todo (pruebas): HUB_NO_SOUND=1.
    """

    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._sounds = {}
        self._failed = set()
        self._folder = None
        self._warming = False

    @property
    def enabled(self):
        return os.environ.get("HUB_NO_SOUND") != "1"

    def _folder_path(self):
        if self._folder is None:
            base = None
            try:
                from kivy.app import App

                app = App.get_running_app()
                if app is not None:
                    base = Path(app.user_data_dir)
            except Exception:  # noqa: BLE001
                base = None
            self._folder = (base or Path(tempfile.gettempdir())) / "sfx"
            self._folder.mkdir(parents=True, exist_ok=True)
        return self._folder

    def warm_up(self):
        """Genera TODOS los efectos en segundo plano, para que no haya tirones al primer uso."""
        if not self.enabled or self._warming:
            return
        self._warming = True
        folder = self._folder_path()      # se calcula en el hilo principal (usa Kivy)

        def work():
            for name, notes in EFFECTS.items():
                path = folder / f"{name}.wav"
                if not path.exists():
                    try:
                        _write_wav(path, _synthesize(notes))
                    except Exception:  # noqa: BLE001
                        pass

        threading.Thread(target=work, daemon=True).start()

    def _load(self, name):
        if name in self._sounds or name in self._failed or name not in EFFECTS:
            return self._sounds.get(name)
        try:
            from kivy.core.audio import SoundLoader

            path = self._folder_path() / f"{name}.wav"
            if not path.exists():
                _write_wav(path, _synthesize(EFFECTS[name]))
            sound = SoundLoader.load(str(path))
        except Exception:  # noqa: BLE001 - sin audio: seguimos en silencio
            sound = None
        if sound is None:
            self._failed.add(name)
            return None
        self._sounds[name] = sound
        return sound

    def play(self, name):
        """Reproduce el efecto `name`. Nunca lanza errores."""
        if not self.enabled:
            return
        try:
            sound = self._load(name)
            if sound is not None:
                sound.stop()
                sound.play()
        except Exception:  # noqa: BLE001
            self._failed.add(name)


def play_sound(name):
    """Reproduce un efecto: "flap", "point", "hit", "eat", "die", "jump", "coin", "stomp", "bump", "win"."""
    SoundBank.get().play(name)


def warm_up_sounds():
    """Prepara todos los efectos en segundo plano (llámalo al empezar el juego)."""
    SoundBank.get().warm_up()


# ============================================================================= vibración
def vibrate(milliseconds=40):
    """Hace vibrar el teléfono un instante (solo Android; en PC e iOS no hace nada)."""
    if platform != "android":
        return
    try:
        from jnius import autoclass

        activity = autoclass("org.kivy.android.PythonActivity").mActivity
        context = autoclass("android.content.Context")
        activity.getSystemService(context.VIBRATOR_SERVICE).vibrate(int(milliseconds))
    except Exception:  # noqa: BLE001 - vibrar es un extra: si falla, no pasa nada
        pass
