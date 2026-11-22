"""Sounds: whinny, munching, sniffing, and quiet field sounds.

Every sound is synthesized here from sine waves and filtered noise, so
there's no copyrighted audio. The first run saves them as WAV files in
.cache/sounds/ (a few seconds on a Pi), and later runs just load them.

To use your own sounds, put a file with the same name in assets/sounds/:
  whinny.wav  munch.wav  sniff.wav  ambient_day.wav  ambient_night.wav
(.ogg works too). Your file is used instead of the generated one. munch and
the ambient sounds loop, so trim them to loop cleanly.

If there's no sound device, or a file can't load, the game stays silent
instead of crashing.
"""

import array
import math
import random
import wave
from pathlib import Path

import pygame

import config

ROOT = Path(__file__).parent
USER_DIR = ROOT / "assets" / "sounds"
CACHE_DIR = ROOT / ".cache" / "sounds"
SYNTH_VERSION = 2     # bump to regenerate the cached sounds after editing them
SR = 22050             # sample rate for generated sounds
NAMES = ("whinny", "munch", "sniff", "ambient_day", "ambient_night")


# ---------------------------------------------------------------- synthesis
# Each function returns a list of floats from -1 to 1.

def _lowpass(samples: list, a: float) -> list:
    out, y = [], 0.0
    for x in samples:
        y += a * (x - y)
        out.append(y)
    return out


def _noise(n: int, rng: random.Random) -> list:
    return [rng.uniform(-1, 1) for _ in range(n)]


def synth_whinny(rng: random.Random) -> list:
    """A rising then wobbling, falling neigh, ending in a little snort."""
    dur = 1.3
    n = int(SR * dur)
    breath = _lowpass(_noise(n, rng), 0.25)
    out, phase = [], 0.0
    for i in range(n):
        t = i / SR
        if t < 0.12:                      # quick rise
            f = 520 + (1050 - 520) * (t / 0.12)
        else:                             # trilling fall
            k = min((t - 0.12) / 0.9, 1.0)
            f = 1050 - 480 * k
            f += 70 * k * math.sin(2 * math.pi * 9 * t)
        phase += 2 * math.pi * f / SR
        tone = (math.sin(phase) + 0.5 * math.sin(2 * phase)
                + 0.25 * math.sin(3 * phase) + 0.12 * math.sin(4 * phase)) / 1.9
        if t < 0.04:
            env = t / 0.04
        elif t < 1.02:
            env = 1.0 - 0.35 * (t - 0.04)
            depth = 0.35 * min(1.0, max(0.0, (t - 0.12) / 0.15))  # pulsing eases in
            env *= 1 - depth + depth * math.sin(2 * math.pi * 11 * t)  # "hee-hee-hee"
        else:
            env = max(0.0, 1 - (t - 1.02) / 0.05) * 0.6
        s = tone * env * 0.8 + breath[i] * env * 0.12
        if t >= 1.08:                     # snort: a short burst of breath
            s += breath[i] * 2.2 * math.exp(-(t - 1.08) / 0.05)
        out.append(s)
    return out


def synth_munch(rng: random.Random) -> list:
    """Three crunchy chews, 0.9 s, meant to loop."""
    n = int(SR * 0.9)
    out = [0.0] * n
    for start in (0.04, 0.33, 0.6):
        s0 = int(start * SR)
        grit = _lowpass(_noise(int(0.09 * SR), rng), 0.55)
        for j, g in enumerate(grit):
            t = j / SR
            env = math.exp(-t / 0.018)
            crackle = 1.0 if rng.random() < 0.3 else 0.4
            thump = math.sin(2 * math.pi * 110 * t) * math.exp(-t / 0.03) * 0.5
            if s0 + j < n:
                out[s0 + j] += (g * crackle * 1.6 + thump) * env
    return out


def synth_sniff(rng: random.Random) -> list:
    """Two quick breathy sniffs."""
    n = int(SR * 0.55)
    raw = _noise(n, rng)
    low = _lowpass(raw, 0.08)
    airy = [x - y for x, y in zip(raw, low)]  # keep the hissy part
    out = []
    for i in range(n):
        t = i / SR
        env = 0.0
        for start in (0.0, 0.22):
            u = t - start
            if 0 <= u < 0.14:
                env += math.sin(math.pi * u / 0.14) ** 2
        out.append(airy[i] * env * 0.5)
    return out


def _wind(n: int, rng: random.Random, loop: float) -> list:
    """A soft breeze that loops without a click: extra samples past the end
    are crossfaded into the start, so the end flows straight into it."""
    fade = int(0.3 * SR)
    w = _lowpass(_lowpass(_noise(n + fade, rng), 0.03), 0.06)
    for i in range(fade):
        k = i / fade
        w[i] = w[i] * k + w[n + i] * (1 - k)
    return [w[i] * (0.6 + 0.4 * math.sin(2 * math.pi * i / SR / loop)) * 2.5
            for i in range(n)]


def synth_ambient_day(rng: random.Random) -> list:
    """8 s loop: a soft breeze and a few far-off bird chirps."""
    loop = 8.0
    n = int(SR * loop)
    out = _wind(n, rng, loop)
    for start in (0.9, 3.4, 5.8):
        notes = rng.randint(2, 4)
        base = rng.uniform(3000, 3600)
        for k in range(notes):
            s0 = int((start + k * 0.11) * SR)
            length = int(0.06 * SR)
            phase = 0.0
            for j in range(length):
                u = j / length
                f = base + 900 * u                    # quick upward sweep
                phase += 2 * math.pi * f / SR
                if s0 + j < n:
                    out[s0 + j] += math.sin(phase) * math.sin(math.pi * u) * 0.35
    return out


def synth_ambient_night(rng: random.Random) -> list:
    """8 s loop: two crickets and a faint breeze."""
    loop = 8.0
    n = int(SR * loop)
    out = [x * 0.5 for x in _wind(n, rng, loop)]
    for pitch, every, offset in ((4400, 0.55, 0.0), (4900, 0.8, 0.31)):
        t = offset
        while t < loop - 0.1:
            for pulse in range(3):                    # chirp = 3 fast pulses
                s0 = int((t + pulse * 0.025) * SR)
                length = int(0.016 * SR)
                for j in range(length):
                    u = j / length
                    if s0 + j < n:
                        out[s0 + j] += (math.sin(2 * math.pi * pitch * j / SR)
                                        * math.sin(math.pi * u) * 0.16)
            t += every
    return out


SYNTHS = {"whinny": synth_whinny, "munch": synth_munch, "sniff": synth_sniff,
          "ambient_day": synth_ambient_day, "ambient_night": synth_ambient_night}


def _write_wav(path: Path, samples: list) -> None:
    peak = max(1e-6, max(abs(s) for s in samples))
    scale = 0.9 * 32767 / max(peak, 1.0)  # never clip; don't boost quiet sounds
    data = array.array("h", (int(s * scale) for s in samples))
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


def sound_file(name: str) -> Path:
    """Your file in assets/sounds/ if there is one, else the generated one."""
    for ext in (".wav", ".ogg"):
        mine = USER_DIR / f"{name}{ext}"
        if mine.exists():
            return mine
    cached = CACHE_DIR / f"{name}_v{SYNTH_VERSION}.wav"
    if not cached.exists():
        _write_wav(cached, SYNTHS[name](random.Random(name)))
    return cached


# ---------------------------------------------------------------- playback

class Audio:
    def __init__(self):
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.enabled = False
        self.status = "off"
        self.night = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.set_reserved(2)
            self.ambient = pygame.mixer.Channel(0)
            self.munch = pygame.mixer.Channel(1)
            for name in NAMES:
                self.sounds[name] = pygame.mixer.Sound(str(sound_file(name)))
            self.enabled = True
            mine = [n for n in NAMES if sound_file(n).parent == USER_DIR]
            self.status = "on" + (f" (your files: {', '.join(mine)})" if mine else " (generated)")
        except (pygame.error, OSError) as err:
            print(f"[audio] sound disabled: {err}")
            self.status = "unavailable"

    def _play(self, name: str, volume: float = 1.0) -> None:
        if self.enabled:
            sound = self.sounds[name]
            sound.set_volume(config.SOUND_VOLUME * volume)
            sound.play()

    def whinny(self, loud: bool = False) -> None:
        self._play("whinny", 1.0 if loud else 0.7)

    def sniff(self) -> None:
        self._play("sniff", 0.8)

    def set_munching(self, on: bool) -> None:
        if not self.enabled:
            return
        if on and not self.munch.get_busy():
            self.sounds["munch"].set_volume(config.SOUND_VOLUME * 0.8)
            self.munch.play(self.sounds["munch"], loops=-1)
        elif not on and self.munch.get_busy():
            self.munch.fadeout(150)

    def set_night(self, night: bool) -> None:
        if night != self.night:
            self.night = night
            if self.enabled:
                self.ambient.fadeout(1500)  # update() fades the other loop in

    def update(self) -> None:
        if self.enabled and not self.ambient.get_busy():
            sound = self.sounds["ambient_night" if self.night else "ambient_day"]
            sound.set_volume(config.SOUND_VOLUME * config.AMBIENT_VOLUME)
            self.ambient.play(sound, loops=-1, fade_ms=1500)

    def close(self) -> None:
        if self.enabled:
            pygame.mixer.stop()
