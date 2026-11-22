"""Day and night, from the real clock.

The meadow gets a color wash that shifts smoothly through the day:
  night  deep blue, with fireflies
  dawn   soft pink        (around 5:30 to 7:30)
  day    almost clear, a touch warm
  dusk   warm sunset pink-orange (around 18:30 to 20:30)

The horse goes to sleep at BEDTIME and wakes at WAKE_UP. `--speed 600`
makes ten minutes pass every second, to watch a whole day go by quickly.
"""

import datetime as dt
import math
import random

import pygame

BEDTIME = 21.0   # hours, 24-hour clock
WAKE_UP = 6.5

# (hour, wash color with alpha). Colors in between are blended.
SKY = [
    (0.0, (20, 28, 130, 160)),
    (5.0, (20, 28, 130, 160)),
    (6.25, (255, 140, 170, 70)),   # dawn pink
    (7.5, (255, 236, 200, 12)),    # day: barely there, warm
    (17.5, (255, 236, 200, 12)),
    (19.25, (236, 92, 108, 92)),   # dusk: warm sunset pink-orange
    (20.75, (20, 28, 130, 160)),
    (24.0, (20, 28, 130, 160)),
]
# (hour, darkness 0 to 1), used for lights, sound and fireflies.
DARKNESS = [(0.0, 1.0), (5.0, 1.0), (7.0, 0.0), (18.5, 0.0), (20.75, 1.0), (24.0, 1.0)]


def _lerp_table(table: list, hour: float):
    for (h0, a), (h1, b) in zip(table, table[1:]):
        if h0 <= hour <= h1:
            k = (hour - h0) / (h1 - h0) if h1 > h0 else 0.0
            if isinstance(a, tuple):
                return tuple(round(x + (y - x) * k) for x, y in zip(a, b))
            return a + (b - a) * k
    return table[-1][1]


def sky_wash(hour: float) -> tuple:
    return _lerp_table(SKY, hour % 24)


def darkness(hour: float) -> float:
    return _lerp_table(DARKNESS, hour % 24)


def is_bedtime(hour: float) -> bool:
    hour %= 24
    return hour >= BEDTIME or hour < WAKE_UP


def _real_hour() -> float:
    now = dt.datetime.now()
    return now.hour + now.minute / 60 + now.second / 3600


class GameClock:
    """The time of day.

    Normally this is the real clock, read fresh every time, so it follows
    daylight saving and the Pi correcting its time from the internet after
    boot (a Pi has no clock battery). With `speed` other than 1, or a
    `start_hour`, it runs on game time instead: `tick(dt)` moves it on by
    dt * speed seconds.
    """

    def __init__(self, speed: float = 1.0, start_hour: float | None = None):
        self.speed = speed
        self.real = speed == 1.0 and start_hour is None
        self._base = _real_hour() if start_hour is None else start_hour % 24
        self._elapsed = 0.0  # game seconds, scaled by speed
        self._skip = 0.0     # hours added by skip_to

    def tick(self, seconds: float) -> None:
        self._elapsed += seconds * self.speed

    @property
    def hour(self) -> float:
        """Hour of the day, 0 to 24, as a float."""
        if self.real:
            return (_real_hour() + self._skip) % 24
        return (self._base + self._skip + self._elapsed / 3600) % 24

    def skip_to(self, hour: float) -> None:
        """Jump forward to the next time the clock reads `hour`."""
        self._skip += (hour - self.hour) % 24

    def text(self) -> str:
        h = self.hour
        return f"{int(h):02d}:{int(h % 1 * 60):02d}"


class Fireflies:
    """A few blinking specks drifting over the meadow at night."""

    def __init__(self, count: int = 12, seed: int = 4):
        rng = random.Random(seed)
        self.flies = [(rng.uniform(20, 246), rng.uniform(30, 140), rng.uniform(0, 6.28),
                       rng.uniform(0.3, 0.7)) for _ in range(count)]

    def draw(self, surf: pygame.Surface, t: float, level: float) -> None:
        if level < 0.3:
            return
        for x0, y0, phase, speed in self.flies:
            x = x0 + 14 * math.sin(t * speed + phase)
            y = y0 + 8 * math.sin(t * speed * 1.7 + phase * 2)
            glow = math.sin(t * 2.2 + phase * 3)
            if glow < 0.1:
                continue  # blinked off
            bright = min(1.0, (level - 0.3) / 0.4) * glow
            core = (round(220 * bright + 35), round(255 * bright), round(110 * bright + 20))
            px, py = round(x), round(y)
            surf.set_at((px, py), core)
            if glow > 0.6:
                halo = (round(core[0] * 0.5), round(core[1] * 0.6), round(core[2] * 0.4))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    surf.set_at((px + dx, py + dy), halo)


class SkyWash:
    """Draws the time-of-day color over the meadow."""

    def __init__(self, size: tuple[int, int]):
        self.surface = pygame.Surface(size, pygame.SRCALPHA)
        self._last = None

    def draw(self, surf: pygame.Surface, hour: float) -> None:
        color = sky_wash(hour)
        if color[3] == 0:
            return
        if color != self._last:
            self.surface.fill(color)
            self._last = color
        surf.blit(self.surface, (0, 0))
