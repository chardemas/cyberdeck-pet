"""The WS2812B LED strip glowing on the wall behind the frame.

On the Pi it drives the strip over SPI (data on GPIO10 / physical pin 19)
with adafruit-circuitpython-neopixel-spi. In mock mode it draws a ring of
glowing "LEDs" around the edge of the window instead, one per LED, so the
colors and effects can be checked on a laptop.

Colors
  day       warm amber, breathing slowly
  night     deep blue-purple, dim
  motion    a neon pink pulse that spreads out from the top (where the PIR is)
  eating    green sparkles flickering along the strip
"""

import math
import random

import pygame

import config

DAY = (255, 150, 40)
NIGHT = (60, 20, 140)
PINK = (255, 30, 160)
GREEN = (60, 255, 80)

PULSE_TIME = 1.6   # seconds for the motion pulse to spread and fade


def _mix(a: tuple, b: tuple, k: float) -> tuple:
    k = min(max(k, 0.0), 1.0)
    return tuple(round(x + (y - x) * k) for x, y in zip(a, b))


class Lights:
    def __init__(self, mock: bool, count: int = config.LED_COUNT):
        self.mock = mock
        self.count = count
        self.t = 0.0
        self.night = 0.0          # 0 = day, 1 = night; eases between them
        self.night_target = 0.0
        self.pulse_age = math.inf
        self.eating = False
        self.colors = [(0, 0, 0)] * count
        self._rng = random.Random(3)
        self._sparkle = [0.0] * count
        self._strip = None
        self._last_sent = None
        self.status = "mock (drawn on screen)" if mock else "off"
        if not mock:
            try:
                import board          # only on the Pi
                import neopixel_spi
                self._strip = neopixel_spi.NeoPixel_SPI(
                    board.SPI(), count, brightness=config.LED_BRIGHTNESS,
                    pixel_order=config.LED_PIXEL_ORDER, auto_write=False)
                self.status = f"{count} LEDs on SPI, brightness {config.LED_BRIGHTNESS}"
            except Exception as err:  # missing library, SPI not enabled...
                print(f"[lights] LED strip disabled: {err}")
                self.status = "unavailable"

    # ---------------------------------------------------------- events

    def set_night(self, darkness: float) -> None:
        """0 = full day, 1 = full night; dawn and dusk are in between."""
        self.night_target = min(max(float(darkness), 0.0), 1.0)

    def motion(self) -> None:
        self.pulse_age = 0.0

    def set_eating(self, eating: bool) -> None:
        self.eating = eating

    # ---------------------------------------------------------- frame

    def update(self, dt: float) -> None:
        self.t += dt
        self.pulse_age += dt
        self.night += (self.night_target - self.night) * min(1.0, dt / 3.0)  # ~3 s fade

        breathe = 0.85 + 0.15 * math.sin(self.t * 2 * math.pi / 6)  # 6 s breath
        base = _mix(DAY, NIGHT, self.night)
        base = tuple(round(c * breathe * (1 - 0.5 * self.night)) for c in base)

        colors = []
        for i in range(self.count):
            c = base
            if self.pulse_age < PULSE_TIME:
                # Distance around the ring from the top-center LED (0 to 1).
                d = min(i, self.count - i) / (self.count / 2)
                front = self.pulse_age / (PULSE_TIME * 0.6)   # how far the wave has spread
                fade = 1 - self.pulse_age / PULSE_TIME
                if d <= front:
                    c = _mix(c, PINK, fade * (1 - 0.5 * max(0.0, front - d)))
            if self.eating:
                if self._rng.random() < dt * 3:
                    self._sparkle[i] = 1.0
                self._sparkle[i] = max(0.0, self._sparkle[i] - dt * 4)
                c = _mix(c, GREEN, self._sparkle[i])
            colors.append(c)
        self.colors = colors

        if self._strip is not None and colors != self._last_sent:
            for i, color in enumerate(colors):
                self._strip[i] = color
            self._strip.show()
            self._last_sent = colors

    def close(self) -> None:
        """Turn the strip off (called when the program exits)."""
        if self._strip is not None:
            self._strip.fill((0, 0, 0))
            self._strip.show()

    # ---------------------------------------------------------- mock drawing

    def draw_mock(self, screen: pygame.Surface) -> None:
        """A ring of glowing dots around the window, one per LED.

        LED 0 is at the top center, going clockwise, like a strip whose input
        end starts behind the PIR.
        """
        if not self.mock:
            return
        w, h = screen.get_size()
        inset = 4
        perimeter = 2 * (w + h - 4 * inset)
        if getattr(self, "_glow", None) is None or self._glow.get_size() != (w, h):
            self._glow = pygame.Surface((w, h), pygame.SRCALPHA)
        glow = self._glow
        glow.fill((0, 0, 0, 0))
        for i, color in enumerate(self.colors):
            x, y = self._ring_point((i + 0.5) / self.count * perimeter, w, h, inset)
            pygame.draw.circle(glow, (*color, 45), (x, y), 22)   # wide soft halo
            pygame.draw.circle(glow, (*color, 110), (x, y), 12)
            pygame.draw.circle(glow, (*color, 255), (x, y), 5)   # the LED itself
            pygame.draw.circle(glow, (255, 255, 255, 140), (x - 1, y - 1), 2)
        screen.blit(glow, (0, 0))

    @staticmethod
    def _ring_point(s: float, w: int, h: int, inset: int) -> tuple[int, int]:
        """A point `s` pixels clockwise around the window edge from top center."""
        left, top, right, bottom = inset, inset, w - inset, h - inset
        top_half = w / 2 - inset
        sides = [(top_half, lambda k: (w / 2 + k, top)),
                 (bottom - top, lambda k: (right, top + k)),
                 (right - left, lambda k: (right - k, bottom)),
                 (bottom - top, lambda k: (left, bottom - k)),
                 (top_half, lambda k: (left + k, top))]
        for length, point in sides:
            if s <= length:
                x, y = point(s)
                return round(x), round(y)
            s -= length
        return round(w / 2), top
