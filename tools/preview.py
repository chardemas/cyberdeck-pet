"""Look at the art: every horse animation looping, and a scene with all the props.

Run from the project folder:
  python tools/preview.py                 # Tab switches page, Escape quits
  python tools/preview.py --save out/     # save both pages as PNGs and exit
"""

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PREVIEW_FPS = 8  # every animation plays at this speed here, to compare them


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--save", metavar="DIR", help="save the pages as PNGs and exit")
    args = parser.parse_args()
    if args.save:
        os.environ["SDL_VIDEODRIVER"] = "dummy"

    import pygame

    import config
    import sprites_world as art
    from horse import Horse
    from sprites import ANIMATIONS, DIRECTIONS, HorseSprites
    from world import BUCKET, World

    pygame.init()
    screen = pygame.display.set_mode((1000, 600))
    pygame.display.set_caption("Horse Deck preview (Tab: next page)")
    sprites = HorseSprites()
    font = pygame.font.Font(None, 18)
    world = World()
    canvas = pygame.Surface((config.INTERNAL_W, config.INTERNAL_H))

    anims = list(ANIMATIONS)
    cell_w, cell_h = 96, 92

    def draw_animations(t: float) -> None:
        screen.fill((92, 164, 76))
        for block in (0, 1):
            for col, d in enumerate(DIRECTIONS):
                label = font.render(d, True, (255, 255, 255))
                cx = 10 + block * 500 + 70 + col * 104 + 48
                screen.blit(label, (cx - label.get_width() // 2, 4))
        # Two columns of animations so it fits: left half and right half.
        half = (len(anims) + 1) // 2
        for i, anim in enumerate(anims):
            block, row = divmod(i, half)
            y = 22 + row * cell_h
            x0 = 10 + block * 500
            screen.blit(font.render(anim, True, (255, 255, 255)), (x0, y + cell_h // 2))
            for col, d in enumerate(DIRECTIONS):
                frames = sprites.frames[(anim, d)]
                frame = frames[int(t * PREVIEW_FPS) % len(frames)]
                cx = x0 + 70 + col * 104 + 48
                screen.blit(frame, (cx - frame.get_width() // 2, y + cell_h - 6 - frame.get_height()))
                n = font.render(str(len(frames)), True, (220, 240, 210))
                screen.blit(n, (cx + 30, y + cell_h - 18))
        hint = font.render(f"{len(anims)} animations x 4 directions at {PREVIEW_FPS} fps "
                           f"(numbers are frame counts). Tab: scene.", True, (255, 255, 255))
        screen.blit(hint, (10, 580))

    from world import DRINK_SPOTS
    horses = []
    dx, dy, dface = DRINK_SPOTS[0]
    for anim, facing, x, y in [("idle", "down", 60, 110), ("graze", "right", 196, 145),
                               ("drink", dface, dx, dy)]:
        h = Horse()
        h.state, h.facing, h.x, h.y, h.timer = anim, facing, x, y, 0.0
        horses.append(h)

    def draw_scene(t: float) -> None:
        world.t = t
        for h in horses:
            h.timer = t
        if int(t * 10) % 5 == 0:  # keep a stream of effects going
            world.spawn("heart", 60, 80)
            world.spawn("sparkle", 196, 125)
            world.spawn("dust", 110, 150)
        world.update(1 / 30)
        world.draw(canvas, actors=[(h.y, lambda s, h=h: h.draw(s, sprites)) for h in horses])
        # Food items that only appear in play, laid out in a row.
        for i, draw in enumerate((art.draw_hay_pile, art.draw_carrot, art.draw_apple)):
            draw(canvas, 100 + i * 18, 150)
        art.draw_feed_button(canvas, config.INTERNAL_W - 15, config.INTERNAL_H - 15, False, True)
        _ = BUCKET
        screen.fill((30, 30, 30))
        size = (config.INTERNAL_W * config.SCALE, config.INTERNAL_H * config.SCALE)
        screen.blit(pygame.transform.scale(canvas, size), (100, 40))
        screen.blit(font.render("Scene: trough, hay bale, bucket, jump, trees, bushes, puddle, "
                                "gate (left fence); hay pile, carrot, apple at the bottom. "
                                "Tab: animations.", True, (255, 255, 255)), (10, 540))

    pages = [draw_animations, draw_scene]
    if args.save:
        out = Path(args.save)
        out.mkdir(parents=True, exist_ok=True)
        for i, page in enumerate(pages):
            for k in range(12):
                page(k / 30)
            pygame.image.save(screen, str(out / f"preview_{i + 1}.png"))
        print(f"Saved {len(pages)} pages to {out}/")
        return

    page, t, clock = 0, 0.0, pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                page = (page + 1) % len(pages)
        pages[page](t)
        pygame.display.flip()
        t += clock.tick(30) / 1000


if __name__ == "__main__":
    main()
