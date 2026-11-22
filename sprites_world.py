"""Original pixel art for everything except the horse, drawn in code.

Positions are in internal (266x160) pixels. Props take their base point: the
spot where they touch the ground, bottom-center. Light comes from the top-left,
and outlines use the horse's dark brown so props match the Onfe horse.
"""

import math
import random

import pygame

from palette import *  # noqa: F403  (colors only)

# ------------------------------------------------------------------ ground


def make_grass_tiles(rng: random.Random, size: int = 16) -> list:
    """Four tileable 16x16 grass variants: plain, speckled, deep, sunny."""
    tiles = []
    for kind in range(4):
        t = pygame.Surface((size, size))
        t.fill(GRASS)
        dots = (10, 26, 18, 18)[kind]
        for _ in range(dots):
            t.set_at((rng.randrange(size), rng.randrange(size)),
                     rng.choice((GRASS_DARK, GRASS_LIGHT)))
        if kind == 2:  # a few deeper clumps
            for _ in range(4):
                x, y = rng.randrange(size - 1), rng.randrange(size - 1)
                pygame.draw.rect(t, GRASS_DARK, (x, y, 2, 2))
                t.set_at((x, y + 1), GRASS_DEEP)
        if kind == 3:  # sunlit streaks
            for _ in range(3):
                x, y = rng.randrange(size - 2), rng.randrange(size)
                pygame.draw.line(t, GRASS_LIGHT, (x, y), (x + 2, y))
        tiles.append(t)
    return tiles


def draw_tuft(surf: pygame.Surface, x: int, y: int) -> None:
    surf.set_at((x - 1, y), GRASS_DARK)
    surf.set_at((x + 1, y), GRASS_DARK)
    surf.set_at((x, y - 1), GRASS_DARK)
    surf.set_at((x, y - 2), GRASS_LIGHT)


def draw_small_flower(surf: pygame.Surface, x: int, y: int, color: tuple) -> None:
    for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
        surf.set_at((x + dx, y + dy), color)
    surf.set_at((x, y), (250, 220, 90))


def draw_big_flower(surf: pygame.Surface, x: int, y: int,
                    petal: tuple, shade: tuple, rng: random.Random) -> None:
    """A round five-petal flower about 13 pixels across, seen from above."""
    for dx, dy in rng.sample([(-6, 4), (6, 4), (-6, -3), (6, -3), (0, 7)], 2):
        pygame.draw.circle(surf, LEAF, (x + dx, y + dy), 2)
    pygame.draw.circle(surf, GRASS_DARK, (x + 1, y + 2), 6)
    offsets = [(0, -4), (4, -1), (3, 4), (-3, 4), (-4, -1)]
    for dx, dy in offsets:
        pygame.draw.circle(surf, shade, (x + dx + 1, y + dy + 1), 2)
    for dx, dy in offsets:
        pygame.draw.circle(surf, petal, (x + dx, y + dy), 2)
    surf.set_at((x - 1, y - 5), (255, 255, 255))
    pygame.draw.circle(surf, FLOWER_MIDDLE_DARK, (x + 1, y + 1), 2)
    pygame.draw.circle(surf, FLOWER_MIDDLE, (x, y), 2)
    surf.set_at((x - 1, y - 1), (255, 244, 180))


def draw_dirt_patch(surf: pygame.Surface, cx: int, cy: int, w: int, h: int,
                    rng: random.Random) -> None:
    """Worn ground with a soft edge and a few pebbles."""
    pygame.draw.ellipse(surf, DIRT_DARK, (cx - w // 2, cy - h // 2 + 1, w, h))
    pygame.draw.ellipse(surf, DIRT, (cx - w // 2, cy - h // 2, w, h - 1))
    for _ in range(w * h // 40 + 2):
        px = cx + rng.randint(-w // 3, w // 3)
        py = cy + rng.randint(-h // 4, h // 4)
        surf.set_at((px, py), rng.choice((DIRT_LIGHT, DIRT_DARK)))
    for _ in range(w // 3):  # grass nibbling at the edge
        a = rng.random() * 6.283
        ex = cx + round(math.cos(a) * w / 2)
        ey = cy + round(math.sin(a) * h / 2)
        surf.set_at((ex, ey), GRASS_DARK)


def draw_puddle(surf: pygame.Surface, cx: int, cy: int, w: int, h: int) -> None:
    pygame.draw.ellipse(surf, DIRT_DARK, (cx - w // 2 - 2, cy - h // 2 - 1, w + 4, h + 3))
    pygame.draw.ellipse(surf, WATER_DEEP, (cx - w // 2, cy - h // 2, w, h))
    pygame.draw.ellipse(surf, WATER_DARK, (cx - w // 2 + 1, cy - h // 2 + 1, w - 2, h - 2))
    pygame.draw.ellipse(surf, WATER, (cx - w // 2 + 3, cy - h // 2 + 1, w - 8, h - 4))
    pygame.draw.line(surf, WATER_LIGHT, (cx - w // 4, cy - h // 4), (cx - w // 8, cy - h // 4))
    surf.set_at((cx + w // 6, cy), WATER_LIGHT)


# ------------------------------------------------------------------ fence


def _fence_post(surf: pygame.Surface, x: int, y: int, big: bool = False) -> None:
    s = 4 if big else 3
    pygame.draw.rect(surf, OUTLINE, (x - s - 1, y - s - 1, 2 * s + 2, 2 * s + 2))
    pygame.draw.rect(surf, WOOD_DARK, (x - s, y - s, 2 * s, 2 * s))
    pygame.draw.rect(surf, WOOD, (x - s, y - s, 2 * s - 1, 2 * s - 1))
    pygame.draw.rect(surf, WOOD_LIGHT, (x - s + 1, y - s + 1, 2, 2))


def draw_fence(surf: pygame.Surface, inset: int, spacing: int,
               gate: tuple[int, int]) -> None:
    """Rails and posts around the edge, with a gate on the left side.

    `gate` is the (top, bottom) y range of the gate opening on the left fence.
    """
    w, h = surf.get_size()
    left, top = inset, inset
    right, bottom = w - inset - 1, h - inset - 1
    g0, g1 = gate

    def hrail(y):
        pygame.draw.line(surf, WOOD_LIGHT, (left, y - 1), (right, y - 1))
        pygame.draw.line(surf, WOOD, (left, y), (right, y))
        pygame.draw.line(surf, WOOD_DARK, (left, y + 1), (right, y + 1))

    def vrail(x, y0, y1):
        pygame.draw.line(surf, WOOD_LIGHT, (x - 1, y0), (x - 1, y1))
        pygame.draw.line(surf, WOOD, (x, y0), (x, y1))
        pygame.draw.line(surf, WOOD_DARK, (x + 1, y0), (x + 1, y1))

    hrail(top)
    hrail(bottom)
    vrail(right, top, bottom)
    vrail(left, top, g0)
    vrail(left, g1, bottom)

    # Gate: lighter slats across the opening, a diagonal brace and a latch.
    for y in range(g0 + 3, g1 - 2, 4):
        pygame.draw.line(surf, WOOD_DARK, (left - 2, y + 1), (left + 2, y + 1))
        pygame.draw.line(surf, WOOD_LIGHT, (left - 2, y), (left + 2, y))
    pygame.draw.line(surf, WOOD, (left - 1, g0 + 2), (left - 1, g1 - 2))
    pygame.draw.line(surf, WOOD_LIGHT, (left + 1, g0 + 2), (left + 1, g1 - 2))
    pygame.draw.line(surf, WOOD_DARK, (left - 2, g0 + 4), (left + 2, g1 - 4))
    surf.set_at((left + 2, g1 - 6), METAL_LIGHT)
    surf.set_at((left + 2, g1 - 5), METAL_DARK)

    xs = list(range(left, right, spacing)) + [right]
    ys = [y for y in list(range(top, bottom, spacing)) + [bottom]]
    for x in xs:
        _fence_post(surf, x, top)
        _fence_post(surf, x, bottom)
    for y in ys:
        _fence_post(surf, right, y)
        if not g0 - 3 < y < g1 + 3:
            _fence_post(surf, left, y)
    _fence_post(surf, left, g0, big=True)  # gate posts
    _fence_post(surf, left, g1, big=True)


# ------------------------------------------------------------------ props


def draw_trough(surf: pygame.Surface, rect: pygame.Rect, t: float) -> None:
    """A wooden water trough. `rect` is the top; the front face hangs below it."""
    x, y, w, h = rect
    front = 5
    pygame.draw.rect(surf, OUTLINE, (x - 1, y - 1, w + 2, h + front + 2))
    pygame.draw.rect(surf, WOOD, (x, y + h, w, front))
    pygame.draw.line(surf, WOOD_DARK, (x, y + h + 2), (x + w - 1, y + h + 2))
    pygame.draw.line(surf, WOOD_DEEP, (x, y + h + front - 1), (x + w - 1, y + h + front - 1))
    pygame.draw.rect(surf, WOOD_DARK, (x, y + h, 2, front))
    pygame.draw.rect(surf, WOOD_DARK, (x + w - 2, y + h, 2, front))
    pygame.draw.rect(surf, WOOD_LIGHT, (x, y, w, h))

    water = pygame.Rect(x + 2, y + 2, w - 4, h - 3)
    pygame.draw.rect(surf, WATER, water)
    pygame.draw.line(surf, WATER_DARK, water.topleft, (water.right - 1, water.top))

    old_clip = surf.get_clip()
    surf.set_clip(water)
    for k in range(2):  # little light dashes drifting along
        px = water.left + int((t * 5 + k * water.w / 2) % water.w)
        py = water.top + 2 + k * 2
        pygame.draw.line(surf, WATER_LIGHT, (px, py), (px + 2, py))
    phase = (t % 3.0) / 3.0  # a ring spreading out every 3 seconds
    if phase < 0.8:
        r = 1 + int(phase * 6)
        cx, cy = water.centerx + 6, water.centery
        pygame.draw.ellipse(surf, WATER_LIGHT, (cx - r, cy - r // 2, 2 * r, max(r, 2)), 1)
    surf.set_clip(old_clip)


def draw_bucket(surf: pygame.Surface, x: int, y: int) -> None:
    """A metal feed bucket full of grain."""
    pygame.draw.polygon(surf, OUTLINE, [(x - 6, y - 10), (x + 5, y - 10), (x + 4, y), (x - 5, y)])
    pygame.draw.polygon(surf, METAL, [(x - 5, y - 9), (x + 4, y - 9), (x + 3, y - 1), (x - 4, y - 1)])
    pygame.draw.line(surf, METAL_LIGHT, (x - 4, y - 8), (x - 3, y - 2))
    pygame.draw.line(surf, METAL_DARK, (x + 2, y - 8), (x + 2, y - 2))
    pygame.draw.line(surf, METAL_DARK, (x - 4, y - 5), (x + 3, y - 5))  # band
    pygame.draw.ellipse(surf, OUTLINE, (x - 6, y - 12, 12, 5))
    pygame.draw.ellipse(surf, METAL_LIGHT, (x - 5, y - 12, 10, 4))
    pygame.draw.ellipse(surf, HAY_DARK, (x - 4, y - 11, 8, 2))
    surf.set_at((x - 2, y - 11), HAY_LIGHT)
    surf.set_at((x + 1, y - 11), HAY)
    pygame.draw.arc(surf, METAL_DARK, (x - 6, y - 17, 12, 10), 0.2, 2.9)  # handle


def draw_hay_bale(surf: pygame.Surface, x: int, y: int, rng_seed: int = 3) -> None:
    """A rectangular bale tied with twine. Base point is bottom-center."""
    rng = random.Random(rng_seed)
    w, top, front = 22, 9, 6
    left, ty = x - w // 2, y - front - top
    pygame.draw.rect(surf, OUTLINE, (left - 1, ty - 1, w + 2, top + front + 2))
    pygame.draw.rect(surf, HAY, (left, ty + top, w, front))
    pygame.draw.rect(surf, HAY_LIGHT, (left, ty, w, top))
    pygame.draw.line(surf, HAY_DARK, (left, ty + top), (left + w - 1, ty + top))
    for _ in range(26):  # straw texture
        px, py = left + rng.randrange(w), ty + rng.randrange(top + front)
        surf.set_at((px, py), rng.choice((HAY_DARK, HAY, HAY_LIGHT)))
    for tx in (left + 6, left + w - 7):  # twine
        pygame.draw.line(surf, HAY_TWINE, (tx, ty), (tx, ty + top + front - 1))


def draw_hay_pile(surf: pygame.Surface, x: int, y: int) -> None:
    """A loose mound of hay, the treat dropped for the horse."""
    pygame.draw.ellipse(surf, OUTLINE, (x - 8, y - 7, 16, 8))
    pygame.draw.ellipse(surf, HAY_DARK, (x - 7, y - 6, 14, 6))
    pygame.draw.ellipse(surf, HAY, (x - 6, y - 7, 11, 5))
    pygame.draw.ellipse(surf, HAY_LIGHT, (x - 4, y - 7, 6, 3))
    for dx, dy in ((-6, -2), (5, -3), (-2, -6), (3, -5), (7, -1)):  # stray straws
        surf.set_at((x + dx, y + dy), HAY_LIGHT)


def draw_carrot(surf: pygame.Surface, x: int, y: int) -> None:
    """A carrot lying on its side, leaves to the right."""
    body = [(x - 6, y - 1), (x + 2, y - 5), (x + 3, y - 2), (x - 5, y)]
    pygame.draw.polygon(surf, OUTLINE, [(x - 7, y - 1), (x + 2, y - 6), (x + 4, y - 2), (x - 5, y + 1)])
    pygame.draw.polygon(surf, CARROT, body)
    pygame.draw.line(surf, CARROT_LIGHT, (x - 4, y - 2), (x + 1, y - 5))
    surf.set_at((x - 1, y - 2), CARROT_DARK)
    surf.set_at((x + 1, y - 3), CARROT_DARK)
    for dx, dy, c in ((4, -5, LEAF), (5, -6, LEAF_LIGHT), (4, -7, LEAF), (6, -4, LEAF_DARK), (5, -5, LEAF_DARK)):
        surf.set_at((x + dx, y + dy), c)


def draw_apple(surf: pygame.Surface, x: int, y: int) -> None:
    pygame.draw.circle(surf, OUTLINE, (x, y - 3), 4)
    pygame.draw.circle(surf, APPLE_DARK, (x, y - 3), 3)
    pygame.draw.circle(surf, APPLE, (x - 1, y - 4), 2)
    surf.set_at((x - 2, y - 5), APPLE_LIGHT)
    surf.set_at((x, y - 7), WOOD_DARK)  # stem
    surf.set_at((x + 1, y - 8), LEAF)
    surf.set_at((x + 2, y - 8), LEAF_LIGHT)


def draw_jump_post(surf: pygame.Surface, x: int, y: int) -> None:
    """A red and white striped stand on a wooden foot, 13 pixels tall."""
    pygame.draw.ellipse(surf, GRASS_DARK, (x - 6, y - 2, 13, 4))
    pygame.draw.rect(surf, OUTLINE, (x - 6, y - 3, 13, 4))  # foot
    pygame.draw.rect(surf, WOOD, (x - 5, y - 2, 11, 2))
    pygame.draw.line(surf, WOOD_LIGHT, (x - 5, y - 2), (x + 5, y - 2))
    pygame.draw.rect(surf, OUTLINE, (x - 3, y - 14, 7, 12))  # upright
    for k in range(5):
        color = RAIL_RED if k % 2 else RAIL_WHITE
        pygame.draw.rect(surf, color, (x - 2, y - 13 + k * 2, 5, 2))
    pygame.draw.line(surf, RAIL_RED_DARK, (x + 2, y - 13), (x + 2, y - 4))
    surf.set_at((x - 2, y - 13), (255, 255, 255))


def draw_jump_rail(surf: pygame.Surface, x: int, y_top: int, y_bottom: int) -> None:
    """The striped pole between the two stands, resting 9 pixels up."""
    lift = 9
    pygame.draw.line(surf, GRASS_DARK, (x + 4, y_top), (x + 4, y_bottom))  # shadow
    pygame.draw.line(surf, GRASS_DARK, (x + 5, y_top + 1), (x + 5, y_bottom - 1))
    pygame.draw.rect(surf, OUTLINE, (x - 2, y_top - lift - 1, 5, y_bottom - y_top + 2))
    for yy in range(y_top - lift, y_bottom - lift):
        color = RAIL_RED if ((yy - y_top) // 5) % 2 else RAIL_WHITE
        pygame.draw.line(surf, color, (x - 1, yy), (x + 1, yy))
    pygame.draw.line(surf, (255, 255, 255), (x - 1, y_top - lift), (x - 1, y_bottom - lift - 1), 1)


def draw_tree_trunk(surf: pygame.Surface, x: int, y: int) -> None:
    pygame.draw.rect(surf, OUTLINE, (x - 4, y - 12, 8, 12))
    pygame.draw.rect(surf, BARK, (x - 3, y - 12, 6, 11))
    pygame.draw.line(surf, BARK_DARK, (x + 1, y - 12), (x + 1, y - 2))
    pygame.draw.line(surf, HORSE_BASE, (x - 2, y - 11), (x - 2, y - 4))
    surf.set_at((x - 5, y - 1), OUTLINE)  # roots
    surf.set_at((x + 4, y - 1), OUTLINE)


def draw_canopy(surf: pygame.Surface, cx: int, cy: int, r: int, seed: int) -> None:
    """A round, lumpy tree top. Drawn over the horse so it can walk under."""
    rng = random.Random(seed)
    lumps = [(round(r * 0.55 * dx), round(r * 0.5 * dy))
             for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-0.7, -0.7), (0.7, -0.7), (0.7, 0.7), (-0.7, 0.7))]
    lr = r // 2 + 1
    for dx, dy in lumps:  # outline and shade
        pygame.draw.circle(surf, OUTLINE, (cx + dx, cy + dy), lr + 1)
    for dx, dy in lumps:
        pygame.draw.circle(surf, CANOPY_DEEP, (cx + dx + 1, cy + dy + 2), lr)
    for dx, dy in lumps:
        pygame.draw.circle(surf, CANOPY_DARK, (cx + dx, cy + dy), lr - 1)
    pygame.draw.circle(surf, CANOPY, (cx - r // 5, cy - r // 5), r * 2 // 3)
    pygame.draw.circle(surf, CANOPY_LIGHT, (cx - r // 3, cy - r // 3), r // 3)
    for _ in range(r * 2):  # leaf texture
        a, d = rng.random() * 6.283, rng.random() * r * 0.8
        px, py = cx + round(math.cos(a) * d), cy + round(math.sin(a) * d)
        surf.set_at((px, py), rng.choice((CANOPY_DARK, CANOPY_LIGHT, CANOPY)))


def draw_bush(surf: pygame.Surface, x: int, y: int, r: int, seed: int) -> None:
    pygame.draw.ellipse(surf, GRASS_DEEP, (x - r - 1, y - 3, 2 * r + 4, 6))
    draw_canopy(surf, x, y - r + 1, r, seed)


def draw_tree_shadow(surf: pygame.Surface, cx: int, cy: int, r: int) -> None:
    pygame.draw.ellipse(surf, GRASS_DARK, (cx - r + 4, cy - r // 2 + 4, 2 * r, r + 4))


# ------------------------------------------------------------------ shadows

_shadow_cache: dict[int, pygame.Surface] = {}


def draw_shadow(surf: pygame.Surface, x: int, y: int, w: int) -> None:
    """A soft dark oval on the ground, centered on (x, y)."""
    if w not in _shadow_cache:
        s = pygame.Surface((w, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (20, 50, 20, 70), (0, 0, w, 6))
        pygame.draw.ellipse(s, (20, 50, 20, 50), (2, 1, w - 4, 4))
        _shadow_cache[w] = s
    surf.blit(_shadow_cache[w], (x - w // 2, y - 3))


# ------------------------------------------------------------------ buttons

BUTTON_FACE = (250, 240, 214)
BUTTON_FACE_DARK = (226, 210, 176)


def draw_feed_button(surf: pygame.Surface, cx: int, cy: int,
                     pressed: bool, enabled: bool) -> None:
    """A round wooden button with a big carrot, about 26 pixels across."""
    if pressed:
        cy += 1
    else:  # the button's edge, visible below it when not pressed
        pygame.draw.circle(surf, OUTLINE, (cx, cy + 2), 13)
        pygame.draw.circle(surf, WOOD_DEEP, (cx, cy + 2), 12)
    pygame.draw.circle(surf, OUTLINE, (cx, cy), 13)
    pygame.draw.circle(surf, WOOD_DARK, (cx, cy), 12)
    pygame.draw.circle(surf, WOOD, (cx - 1, cy - 1), 11)
    pygame.draw.arc(surf, WOOD_LIGHT, (cx - 11, cy - 11, 20, 20), 1.7, 3.2, 2)
    pygame.draw.circle(surf, BUTTON_FACE_DARK, (cx, cy), 9)
    pygame.draw.circle(surf, BUTTON_FACE, (cx - 1, cy - 1), 8)

    # Big carrot, pointing down-left, leaves up-right.
    tip, top_a, top_b = (cx - 6, cy + 6), (cx + 1, cy - 3), (cx + 4, cy)
    pygame.draw.polygon(surf, OUTLINE, [(tip[0] - 1, tip[1] + 1), (top_a[0], top_a[1] - 1),
                                        (top_b[0] + 1, top_b[1])])
    pygame.draw.polygon(surf, CARROT, [tip, top_a, top_b])
    pygame.draw.line(surf, CARROT_LIGHT, (cx - 4, cy + 3), (cx, cy - 2))
    pygame.draw.line(surf, CARROT_DARK, (cx - 2, cy + 3), (cx - 1, cy + 3))
    pygame.draw.line(surf, CARROT_DARK, (cx + 1, cy), (cx + 2, cy))
    for dx, dy, c in ((3, -4, LEAF), (4, -6, LEAF_LIGHT), (5, -5, LEAF), (6, -3, LEAF_DARK),
                      (2, -6, LEAF_DARK), (4, -4, LEAF_DARK), (5, -7, LEAF_LIGHT)):
        surf.set_at((cx + dx, cy + dy), c)

    if not enabled:  # greyed out: too many treats already waiting
        veil = pygame.Surface((27, 27), pygame.SRCALPHA)
        pygame.draw.circle(veil, (120, 120, 120, 150), (13, 13), 13)
        surf.blit(veil, (cx - 13, cy - 13))


# ------------------------------------------------------------------ effects

_HEART = (".X.X.",
          "XHXXX",
          ".XXX.",
          "..X..")


def draw_heart(surf: pygame.Surface, x: int, y: int) -> None:
    for row, line in enumerate(_HEART):
        for col, ch in enumerate(line):
            if ch != ".":
                surf.set_at((x + col - 2, y + row - 2), HEART_LIGHT if ch == "H" else HEART)


def draw_sparkle(surf: pygame.Surface, x: int, y: int, size: int) -> None:
    """A four-point twinkle. size 0 to 2."""
    surf.set_at((x, y), SPARKLE_CORE)
    for k in range(1, size + 1):
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            surf.set_at((x + dx, y + dy), SPARKLE if k == size else SPARKLE_CORE)


def draw_dust(surf: pygame.Surface, x: int, y: int, r: int) -> None:
    if r <= 0:
        return
    pygame.draw.circle(surf, DUST, (x, y), r)
    if r > 1:
        pygame.draw.circle(surf, DUST_LIGHT, (x - 1, y - 1), r - 1)
