"""Horse deck: a pixel-art horse in a meadow.

Run:  python main.py [--fullscreen] [--mock]
Quit: Escape (or close the window)
Input and test keys are listed in controls.py.
"""

import argparse

import pygame

import config
import controls
import daynight
from game import Game
from horse import FEED_MIN_HUNGER


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Horse deck")
    parser.add_argument("--fullscreen", action="store_true",
                        help="full-screen with no mouse cursor (for the Pi)")
    parser.add_argument("--mock", action="store_true",
                        help="fake the hardware even on a Raspberry Pi")
    parser.add_argument("--speed", type=float, default=1.0,
                        help="fast-forward the day: 600 = ten minutes per second")
    parser.add_argument("--time", metavar="HH:MM",
                        help="start at this time of day instead of the real time")
    parser.add_argument("--no-save", action="store_true",
                        help="don't load or save state.json (handy while testing)")
    return parser.parse_args()


def parse_hour(text: str | None) -> float | None:
    if not text:
        return None
    h, _, m = text.partition(":")
    return int(h) % 24 + int(m or 0) / 60


def draw_debug(screen: pygame.Surface, font: pygame.font.Font, game: Game,
               fps: float) -> None:
    horse = game.horse
    if horse.hungry:
        mood = "  (hungry)"
    elif horse.wants_food:
        mood = "  (would eat a treat)"
    else:
        mood = f"  (sniffs treats until {FEED_MIN_HUNGER})"
    cooldown = game.sensor.cooldown_left
    clock = game.clock
    speed = f" (x{clock.speed:g})" if clock.speed != 1 else ""
    lines = [
        f"time: {clock.text()}{speed}   state: {horse.state}   facing: {horse.facing}",
        f"hunger: {horse.hunger:.0f}{mood}",
        f"mood: {horse.mood}   (fed lately {horse.fed_score:.1f}, "
        f"no visitors for {horse.lonely_time / 60:.0f} min)",
        f"treats waiting: {game.world.treats_waiting()}   fps: {fps:.0f}   mock: {config.MOCK}",
        f"motion: {game.sensor.status}" + (f", ready in {cooldown:.0f}s" if cooldown else ", ready"),
        f"lights: {game.lights.status}",
        f"sound: {game.audio.status if game.audio else 'off'}",
        "Space motion   F feed   N skip to dusk/dawn",
        "J jump   G gallop   W drink",
        "H +20 hunger   D hide this",
    ]
    rendered = [font.render(text, True, (255, 255, 255)) for text in lines]
    width = max(r.get_width() for r in rendered) + 12
    height = sum(r.get_height() for r in rendered) + 10
    box = pygame.Surface((width, height), pygame.SRCALPHA)
    box.fill((0, 0, 0, 140))
    screen.blit(box, (24, 24))
    y = 29
    for r in rendered:
        screen.blit(r, (30, y))
        y += r.get_height()


def main() -> None:
    args = parse_args()
    if args.mock:
        config.MOCK = True

    pygame.init()
    flags = pygame.FULLSCREEN if args.fullscreen else 0
    screen = pygame.display.set_mode((config.SCREEN_W, config.SCREEN_H), flags)
    pygame.display.set_caption("Horse Deck" + (" (mock)" if config.MOCK else ""))
    if args.fullscreen:
        pygame.mouse.set_visible(False)

    canvas = pygame.Surface((config.INTERNAL_W, config.INTERNAL_H))
    scaled = pygame.Surface(controls.view_rect(screen.get_size()).size)
    clock = daynight.GameClock(speed=args.speed, start_hour=parse_hour(args.time))
    game = Game(clock=clock, save_path=None if args.no_save else config.STATE_FILE)
    font = pygame.font.Font(None, 20)
    clock = pygame.time.Clock()

    running = True
    try:
        while running:
            dt = min(clock.tick(config.FPS) / 1000, 0.1)  # cap so a hiccup can't teleport the horse

            for event in pygame.event.get():
                if not controls.handle_event(event, game, screen.get_size()):
                    running = False

            game.update(dt)
            game.draw(canvas)

            # transform.scale is nearest-neighbor, so pixels stay sharp.
            view = controls.view_rect(screen.get_size())
            pygame.transform.scale(canvas, view.size, scaled)
            screen.fill((0, 0, 0))
            screen.blit(scaled, view.topleft)
            game.draw_screen_overlay(screen)
            if game.debug:
                draw_debug(screen, font, game, clock.get_fps())
            pygame.display.flip()
    finally:
        game.close()  # LEDs off even if something crashes
        pygame.quit()


if __name__ == "__main__":
    main()
