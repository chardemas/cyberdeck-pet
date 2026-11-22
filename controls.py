"""All input in one place: taps and clicks, and the keyboard test keys.

pygame reports touchscreen taps as mouse clicks, so one handler covers the
mouse on a laptop and a finger on the Pi.

Test keys (mock mode only, except D):
  Space  motion detected (the horse trots over to greet you); like the real
         sensor, it then ignores motion for MOTION_COOLDOWN seconds
  F      feed, same as tapping the carrot button
  N      jump the clock to just before the next dusk or dawn
  J      jump the poles
  G      gallop
  W      drink at the trough
  H      +20 hunger (to test hungry behavior quickly)
  D      show or hide the debug overlay
"""

import pygame

import config


def view_rect(screen_size: tuple[int, int]) -> pygame.Rect:
    """Where the scaled-up game sits on the screen: the biggest whole-number
    scale that fits, centered (on the 800x480 screen, 3x with a 1 px border)."""
    sw, sh = screen_size
    scale = max(1, min(sw // config.INTERNAL_W, sh // config.INTERNAL_H))
    w, h = config.INTERNAL_W * scale, config.INTERNAL_H * scale
    return pygame.Rect((sw - w) // 2, (sh - h) // 2, w, h)


def to_internal(pos: tuple[int, int], screen_size: tuple[int, int]) -> tuple[float, float]:
    """Screen pixels to the game's internal pixels."""
    view = view_rect(screen_size)
    return ((pos[0] - view.x) * config.INTERNAL_W / view.w,
            (pos[1] - view.y) * config.INTERNAL_H / view.h)


def handle_event(event: pygame.event.Event, game, screen_size: tuple[int, int]) -> bool:
    """Apply one event to the game. Returns False when it's time to quit."""
    if event.type == pygame.QUIT:
        return False
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        game.tap(*to_internal(event.pos, screen_size))
    elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            return False
        handle_key(event.key, game)
    return True


def handle_key(key: int, game) -> None:
    horse = game.horse
    if key == pygame.K_d:
        game.debug = not game.debug
    if not config.MOCK:
        return
    if key == pygame.K_SPACE:
        game.fake_motion()  # goes through the sensor, so the cooldown applies
    elif key == pygame.K_f:
        game.feed()
    elif key == pygame.K_n:
        game.skip_time()
    elif key == pygame.K_j:
        horse.try_jump()
    elif key == pygame.K_g:
        horse.try_gallop()
    elif key == pygame.K_w:
        horse.try_drink()
    elif key == pygame.K_h:
        horse.hunger = min(100.0, horse.hunger + 20)
