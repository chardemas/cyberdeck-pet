"""On-screen buttons, drawn on top of the meadow."""

import math

import pygame

import config
import sprites_world as art


class FeedButton:
    """The carrot button in the bottom-right corner."""

    CENTER = (config.INTERNAL_W - 15, config.INTERNAL_H - 15)  # internal pixels
    RADIUS = 13
    TOUCH_SLOP = 6       # extra pixels around it that still count as a tap

    def __init__(self):
        self.t = 0.0
        self.pressed_for = 0.0

    def hit(self, x: float, y: float) -> bool:
        cx, cy = self.CENTER
        return math.hypot(x - cx, y - cy) <= self.RADIUS + self.TOUCH_SLOP

    def press(self) -> None:
        self.pressed_for = 0.15

    def update(self, dt: float) -> None:
        self.t += dt
        self.pressed_for = max(0.0, self.pressed_for - dt)

    def draw(self, surf: pygame.Surface, enabled: bool, invite: bool) -> None:
        """`invite` makes it bob gently, when the horse would like a treat."""
        cx, cy = self.CENTER
        if invite and enabled and not self.pressed_for:
            cy -= round(max(0.0, math.sin(self.t * 4)) * 2)
        art.draw_feed_button(surf, cx, cy, self.pressed_for > 0, enabled)
