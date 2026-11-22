"""The meadow: layout, background, props, and effects.

Layout constants live at module level so horse.py (and tests) can use them
without building any images. All positions are internal (266x160) pixels.

Drawing order each frame:
  1. background (grass, dirt, flowers, puddle, fence, tree shadows), drawn once
  2. props and the horse, sorted by the y of their base so nearer things
     (lower on screen) are drawn on top
  3. tree tops, so the horse can walk under them
  4. effects (hearts, sparkles, dust)
"""

import math
import random

import pygame

import config
import sprites_world as art
from palette import BIG_PETALS, SMALL_FLOWERS

FENCE_INSET = 6      # distance from the screen edge to the fence line
POST_SPACING = 20    # pixels between fence posts
GATE = (64, 92)      # y range of the gate in the left fence

# Inside the fence, with a small margin.
PLAY_AREA = pygame.Rect(
    FENCE_INSET + 6,
    FENCE_INSET + 6,
    config.INTERNAL_W - 2 * (FENCE_INSET + 6),
    config.INTERNAL_H - 2 * (FENCE_INSET + 6),
)

# Where the horse's feet may stand, so the whole sprite stays inside the
# fence. The horse is about 57x45 from the side.
BOUNDS = pygame.Rect(PLAY_AREA.left + 30, PLAY_AREA.top + 38,
                     PLAY_AREA.width - 60, PLAY_AREA.height - 40)

# Props.
TROUGH = pygame.Rect(100, 33, 34, 9)            # the top; front face is 5 below
HAY_BALE = (234, 98)                            # base points
BUCKET = (238, 122)
JUMP_X, JUMP_TOP, JUMP_BOTTOM = 150, 100, 130   # the rail runs up and down
JUMP_LANE = 120                                 # the horse crosses at this y
JUMP_RUNUP = 44                                 # take-off distance from the rail
TREES = [(22, 40, 15, 11), (246, 42, 16, 12)]   # trunk base x, y, canopy radius, seed
BUSHES = [(20, 150, 8, 21)]                     # base x, y, radius, seed
PUDDLE = (62, 130, 26, 9)                       # center x, y, w, h

# Where the horse stands to drink: (x, y, facing). Its head dips into the
# trough from either end.
DRINK_SPOTS = [
    (TROUGH.right + 30, TROUGH.bottom + 8, "left"),
    (TROUGH.left - 30, TROUGH.bottom + 8, "right"),
]

# Ground footprints of solid things, and the zones the horse's feet must stay
# out of (footprint grown by half a horse sideways, a little front and back).
FOOTPRINTS = [
    pygame.Rect(TROUGH.left, TROUGH.top, TROUGH.width, TROUGH.height + 5),
    pygame.Rect(HAY_BALE[0] - 11, HAY_BALE[1] - 15, 22, 15),
    pygame.Rect(BUCKET[0] - 6, BUCKET[1] - 10, 12, 10),
    pygame.Rect(JUMP_X - 3, JUMP_TOP - 6, 7, JUMP_BOTTOM - JUMP_TOP + 6),
] + [pygame.Rect(x - 4, y - 6, 8, 6) for x, y, _, _ in TREES] \
  + [pygame.Rect(x - r, y - r, 2 * r, r) for x, y, r, _ in BUSHES]

BLOCKED =[pygame.Rect(r.left - 26, r.top - 2, r.width + 52, r.height + 12) for r in FOOTPRINTS]


def ground_clear(x: float, y: float, margin: int = 8) -> bool:
    """True if (x, y) is open meadow: inside the fence and off every prop."""
    return (PLAY_AREA.inflate(-2 * margin, -2 * margin).collidepoint(x, y)
            and not any(f.inflate(2 * margin, 2 * margin).collidepoint(x, y) for f in FOOTPRINTS))


def spot_free(x: float, y: float) -> bool:
    return BOUNDS.collidepoint(x, y) and not any(z.collidepoint(x, y) for z in BLOCKED)


PATH_MARGIN = 2  # pixels; covers rounding between clipline and collidepoint


def path_clear(a: tuple[float, float], b: tuple[float, float]) -> bool:
    """True if the horse can walk straight from a to b without hitting a prop."""
    for zone in BLOCKED:
        wide = zone.inflate(2 * PATH_MARGIN, 2 * PATH_MARGIN)
        # Standing (or stopping) inside the margin: use the real edge, so the
        # horse can still walk away from a spot right next to a prop.
        if wide.collidepoint(a) or wide.collidepoint(b):
            wide = zone
        if wide.clipline(a, b):
            return False
    return True


TREAT_KINDS = ("carrot", "apple", "hay")
TREAT_FALL = 0.35   # seconds for a dropped treat to land
_TREAT_ART = {"carrot": art.draw_carrot, "apple": art.draw_apple, "hay": art.draw_hay_pile}


class Treat:
    """A snack on the ground. It stays until the horse eats it."""

    def __init__(self, kind: str, x: float, y: float):
        self.kind, self.x, self.y = kind, x, y
        self.age = 0.0
        self.eaten = False

    @property
    def landed(self) -> bool:
        return self.age >= TREAT_FALL

    def draw(self, surf: pygame.Surface) -> None:
        x, y = round(self.x), round(self.y)
        if self.age < TREAT_FALL:  # falling in from above
            k = self.age / TREAT_FALL
            lift = round(40 * (1 - k * k))
            art.draw_shadow(surf, x, y, 4 + round(8 * k))
        else:  # one small bounce after landing
            b = self.age - TREAT_FALL
            lift = round(3 * math.sin(math.pi * b / 0.2)) if b < 0.2 else 0
            art.draw_shadow(surf, x, y, 12)
        _TREAT_ART[self.kind](surf, x, y - lift)


def _corner_nodes() -> list[tuple[int, int]]:
    """Points just outside each prop's corners: the turns a detour can take."""
    nodes = []
    for zone in BLOCKED:
        z = zone.inflate(8, 8)
        for p in (z.topleft, (z.right, z.top), (z.left, z.bottom), z.bottomright):
            if spot_free(*p) and p not in nodes:
                nodes.append(p)
    return nodes


_NODES = _corner_nodes()
# Which corner points can see each other. Props never move, so this is
# worked out once instead of on every search.
_LINKS = {i: [j for j in range(len(_NODES)) if j != i and path_clear(_NODES[i], _NODES[j])]
          for i in range(len(_NODES))}


def find_path(a: tuple[float, float], b: tuple[float, float]) -> list | None:
    """Shortest walk from a to b around the props.

    Returns the turning points between them ([] means walk straight), or None
    if b can't be reached.
    """
    if path_clear(a, b):
        return []
    n = len(_NODES)
    start, goal = n, n + 1
    pts = _NODES + [a, b]
    links = {i: list(_LINKS[i]) for i in range(n)}
    links[start] = [i for i in range(n) if path_clear(a, _NODES[i])]
    links[goal] = []
    for i in range(n):
        if path_clear(_NODES[i], b):
            links[i].append(goal)
    # Dijkstra on a few dozen points.
    dist = {start: 0.0}
    prev: dict[int, int] = {}
    todo = {start}
    done = set()
    while todo:
        cur = min(todo, key=dist.__getitem__)
        todo.discard(cur)
        if cur == goal:
            break
        done.add(cur)
        for nxt in links[cur]:
            if nxt in done:
                continue
            d = dist[cur] + math.dist(pts[cur], pts[nxt])
            if d < dist.get(nxt, math.inf):
                dist[nxt], prev[nxt] = d, cur
                todo.add(nxt)
    if goal not in dist:
        return None
    path, cur = [], prev[goal]
    while cur != start:
        path.append(pts[cur])
        cur = prev[cur]
    return path[::-1]


class World:
    def __init__(self, seed: int = 7):
        self.t = 0.0
        self.treats: list[Treat] = []
        self.particles: list[dict] = []
        self.rng = random.Random(seed + 1)
        self.background = self._build_background(random.Random(seed))

    # ---------------------------------------------------------- background

    def _build_background(self, rng: random.Random) -> pygame.Surface:
        bg = pygame.Surface((config.INTERNAL_W, config.INTERNAL_H))
        w, h = bg.get_size()

        tiles = art.make_grass_tiles(rng)
        for ty in range(0, h, 16):
            for tx in range(0, w, 16):
                bg.blit(rng.choices(tiles, weights=(5, 3, 2, 2))[0], (tx, ty))

        # Worn dirt where the horse drinks and lands, plus a few random patches.
        for x, y, _ in DRINK_SPOTS:
            art.draw_dirt_patch(bg, x, y - 2, 30, 12, rng)
        art.draw_dirt_patch(bg, TROUGH.centerx, TROUGH.bottom + 4, 52, 12, rng)
        for side in (-1, 1):
            art.draw_dirt_patch(bg, JUMP_X + side * JUMP_RUNUP, JUMP_LANE, 26, 10, rng)
        for cx, cy in ((48, 96), (205, 142)):
            art.draw_dirt_patch(bg, cx, cy, rng.randrange(16, 24), rng.randrange(8, 11), rng)

        for _ in range(70):
            art.draw_tuft(bg, rng.randrange(2, w - 2), rng.randrange(3, h))
        for _ in range(20):
            art.draw_small_flower(bg, rng.randrange(2, w - 2), rng.randrange(2, h - 2),
                                  rng.choice(SMALL_FLOWERS))
        self._draw_big_flowers(bg, rng)

        art.draw_puddle(bg, *PUDDLE)
        for x, y, r, _ in TREES:
            art.draw_tree_shadow(bg, x, y - r - 6, r)
        art.draw_fence(bg, FENCE_INSET, POST_SPACING, GATE)
        return bg

    def _draw_big_flowers(self, bg: pygame.Surface, rng: random.Random) -> None:
        """Clusters of big flowers, spaced apart and clear of the props."""
        w, h = bg.get_size()
        margin = FENCE_INSET + 10
        keep_clear = [z.inflate(-30, 0) for z in BLOCKED] + [
            pygame.Rect(JUMP_X - JUMP_RUNUP - 14, JUMP_LANE - 8, 2 * JUMP_RUNUP + 28, 14),
            pygame.Rect(PUDDLE[0] - 24, PUDDLE[1] - 12, 48, 24),
        ]
        placed: list[tuple[int, int]] = []

        def free(px: int, py: int) -> bool:
            if any(r.collidepoint(px, py) for r in keep_clear):
                return False
            return all((px - qx) ** 2 + (py - qy) ** 2 >= 16 ** 2 for qx, qy in placed)

        for _ in range(12):
            cx, cy = rng.randrange(margin, w - margin), rng.randrange(margin + 20, h - margin)
            petal, shade = rng.choice(BIG_PETALS)
            for _ in range(rng.randint(1, 3)):
                px = min(max(cx + rng.randint(-12, 12), margin), w - margin)
                py = min(max(cy + rng.randint(-10, 10), margin), h - margin)
                if free(px, py):
                    placed.append((px, py))
                    art.draw_big_flower(bg, px, py, petal, shade, rng)

    # ---------------------------------------------------------- props

    def _props(self) -> list:
        """(base y, draw function) for everything that sorts with the horse."""
        t = self.t
        items = [
            (TROUGH.bottom + 5, lambda s: art.draw_trough(s, TROUGH, t)),
            (HAY_BALE[1], lambda s: art.draw_hay_bale(s, *HAY_BALE)),
            (BUCKET[1], lambda s: art.draw_bucket(s, *BUCKET)),
            # The far stand carries the rail, so the horse jumps over both.
            (JUMP_TOP, lambda s: (art.draw_jump_post(s, JUMP_X, JUMP_TOP),
                                  art.draw_jump_rail(s, JUMP_X, JUMP_TOP, JUMP_BOTTOM))),
            (JUMP_BOTTOM, lambda s: art.draw_jump_post(s, JUMP_X, JUMP_BOTTOM)),
        ]
        items += [(y, lambda s, x=x, y=y: art.draw_tree_trunk(s, x, y)) for x, y, _, _ in TREES]
        items += [(y, lambda s, x=x, y=y, r=r, k=k: art.draw_bush(s, x, y, r, k))
                  for x, y, r, k in BUSHES]
        items += [(tr.y, tr.draw) for tr in self.treats]
        return items

    # ---------------------------------------------------------- treats

    def drop_treat(self, kind: str, x: float, y: float) -> Treat:
        treat = Treat(kind, x, y)
        self.treats.append(treat)
        return treat

    def treats_waiting(self) -> int:
        return sum(1 for t in self.treats if not t.eaten)

    # ---------------------------------------------------------- effects

    def spawn(self, kind: str, x: float, y: float) -> None:
        rng = self.rng
        if kind == "heart":
            self.particles.append({"kind": kind, "x": x + rng.uniform(-3, 3), "y": y,
                                   "vx": rng.uniform(-4, 4), "vy": -14, "age": 0, "life": 1.4})
        elif kind == "sparkle":
            self.particles.append({"kind": kind, "x": x + rng.uniform(-10, 10),
                                   "y": y + rng.uniform(-8, 4), "vx": 0, "vy": -2,
                                   "age": -rng.uniform(0, 0.3), "life": 0.7})
        elif kind == "dust":
            self.particles.append({"kind": kind, "x": x, "y": y, "vx": rng.uniform(-6, 6),
                                   "vy": rng.uniform(-6, -2), "age": 0, "life": 0.5})

    def update(self, dt: float) -> None:
        self.t += dt
        for tr in self.treats:
            was_falling = not tr.landed
            tr.age += dt
            if was_falling and tr.landed:
                self.spawn("dust", tr.x - 3, tr.y)
                self.spawn("dust", tr.x + 3, tr.y)
        self.treats[:] = [tr for tr in self.treats if not tr.eaten]  # in place: shared list
        for p in self.particles:
            p["age"] += dt
            if p["age"] > 0:
                p["x"] += p["vx"] * dt
                p["y"] += p["vy"] * dt
        self.particles = [p for p in self.particles if p["age"] < p["life"]]

    def _draw_particles(self, surf: pygame.Surface) -> None:
        for p in self.particles:
            if p["age"] < 0:
                continue
            k = p["age"] / p["life"]
            x, y = round(p["x"]), round(p["y"])
            if p["kind"] == "heart":
                if k < 0.85 or int(p["age"] * 20) % 2:  # blink out at the end
                    art.draw_heart(surf, x, y)
            elif p["kind"] == "sparkle":
                art.draw_sparkle(surf, x, y, (1, 2, 1, 0)[min(int(k * 4), 3)])
            elif p["kind"] == "dust":
                art.draw_dust(surf, x, y, round(3 * (1 - k)))

    # ---------------------------------------------------------- draw

    def draw(self, surf: pygame.Surface, actors: list | None = None) -> None:
        """`actors` is a list of (base y, draw function), like the horse."""
        surf.blit(self.background, (0, 0))
        items = self._props() + list(actors or [])
        for _, draw in sorted(items, key=lambda item: item[0]):
            draw(surf)
        for x, y, r, seed in TREES:
            art.draw_canopy(surf, x, y - r - 10, r, seed)  # trunk peeks out below
        self._draw_particles(surf)
