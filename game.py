"""Ties the world, the horse, the buttons and the hardware together.

controls.py turns input into calls on this class; main.py runs the loop.
"""

import random
from pathlib import Path

import pygame

import config
import daynight
import save
from audio import Audio
from horse import Horse
from hud import FeedButton
from lights import Lights
from sensors import MotionSensor
from sprites import HorseSprites
from world import TREAT_KINDS, World

MAX_TREATS = 3  # treats allowed on the ground at once
SAVE_EVERY = 60  # seconds between saves (plus one on exit)


class Game:
    def __init__(self, rng: random.Random | None = None, hardware: bool = True,
                 clock: daynight.GameClock | None = None, save_path: Path | None = None):
        """`save_path` None means nothing is loaded or saved (used by tests)."""
        self.rng = rng or random.Random()
        self.clock = clock or daynight.GameClock()
        self.sky = daynight.SkyWash((config.INTERNAL_W, config.INTERNAL_H))
        self.fireflies = daynight.Fireflies()
        self.save_path = save_path
        self._since_save = 0.0
        self.load_note = ""
        self.world = World()
        self.sprites = HorseSprites()
        self.horse = Horse(self.rng)
        self.horse.anim_length = self.sprites.length  # jump and rear last as long as their art
        self.horse.treats = self.world.treats
        self.feed_button = FeedButton()
        self.debug = config.MOCK  # the overlay starts visible on a laptop
        self.sensor = MotionSensor(mock=config.MOCK)
        self.lights = Lights(mock=config.MOCK)
        self.audio = Audio() if hardware else None
        if save_path is not None:
            self.load_note = save.load(save_path, self.horse)
            print(f"[save] {self.load_note}")
        if daynight.is_bedtime(self.clock.hour):
            self.horse.sleep()  # started at night: already asleep
        self._last_state = self.horse.state

    # ---------------------------------------------------------- actions

    def can_feed(self) -> bool:
        return self.world.treats_waiting() < MAX_TREATS

    def feed(self) -> bool:
        """Drop a treat near the horse. False if there's no room for one."""
        self.feed_button.press()
        if not self.can_feed():
            return False
        spot = self.horse.find_treat_spot()
        if spot is None:
            return False
        treat = self.world.drop_treat(self.rng.choice(TREAT_KINDS), *spot)
        self.horse.notice_treat(treat)
        return True

    def tap(self, x: float, y: float) -> None:
        """A tap or click, in internal (266x160) pixels."""
        if self.feed_button.hit(x, y):
            self.feed()

    def fake_motion(self) -> None:
        """Mock mode: pretend the PIR saw someone (the spacebar)."""
        self.sensor.trigger()

    def skip_time(self) -> None:
        """Test key: jump to just before the next bedtime or wake-up."""
        if daynight.is_bedtime(self.clock.hour):
            self.clock.skip_to(daynight.WAKE_UP - 0.75)   # pre-dawn
        else:
            self.clock.skip_to(daynight.BEDTIME - 1.75)   # late afternoon, into dusk

    def save_now(self) -> None:
        if self.save_path is not None:
            try:
                save.save(self.save_path, self.horse)
            except OSError as err:  # full or read-only SD card: keep running
                print(f"[save] could not save: {err}")

    # ---------------------------------------------------------- frame

    def update(self, dt: float) -> None:
        self.clock.tick(dt)
        if self.sensor.update(dt):
            self.horse.motion()
            self.lights.motion()

        self._bedtime()
        self.horse.update(dt)
        for kind, x, y in self.horse.effects:
            self.world.spawn(kind, x, y)
        self.horse.effects.clear()
        self._react_to_state()

        dark = daynight.darkness(self.clock.hour)
        self.lights.set_night(dark)
        self.lights.update(dt)
        if self.audio:
            self.audio.set_night(dark > 0.5)
            self.audio.update()

        self.world.update(dt)
        self.feed_button.update(dt)

        self._since_save += dt
        if self._since_save >= SAVE_EVERY:
            self._since_save = 0.0
            self.save_now()

    def _bedtime(self) -> None:
        """Sleep at bedtime (once it's done what it's doing), wake at dawn."""
        horse = self.horse
        if daynight.is_bedtime(self.clock.hour):
            if horse.state == "idle":
                horse.sleep()
        elif horse.state == "sleep":
            horse.wake()

    def _react_to_state(self) -> None:
        """Sounds and lights for what the horse just started (or stopped) doing."""
        old, new = self._last_state, self.horse.state
        if old == new:
            return
        self._last_state = new
        a = self.audio
        if new == "startled" and a:
            a.whinny(loud=True)
        elif new == "trot" and old != "startled" and a:
            a.whinny()
        elif new == "sniff" and a:
            a.sniff()
        eating = new == "eat"
        self.lights.set_eating(eating)
        if a:
            a.set_munching(eating)

    def draw(self, canvas: pygame.Surface) -> None:
        horse, sprites = self.horse, self.sprites
        hour = self.clock.hour
        self.world.draw(canvas, actors=[(horse.y, lambda s: horse.draw(s, sprites))])
        self.sky.draw(canvas, hour)
        self.fireflies.draw(canvas, self.world.t, daynight.darkness(hour))
        self.feed_button.draw(canvas, enabled=self.can_feed(),
                              invite=horse.wants_food and horse.state != "sleep")

    def draw_screen_overlay(self, screen: pygame.Surface) -> None:
        """Things drawn at full screen resolution, after scaling (mock LEDs)."""
        self.lights.draw_mock(screen)

    def close(self) -> None:
        """Save, then turn things off on exit."""
        self.save_now()
        self.lights.close()
        self.sensor.close()
        if self.audio:
            self.audio.close()
