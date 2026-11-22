"""Horse animations.

Loads sprite strips from assets/horse/ when they exist. Anything missing is
drawn in code as simple original placeholder frames, so the game always runs.

Drop-in art (see the README for the full table):
  assets/horse/<animation>_<direction>.png
  - one horizontal strip per file, frames side by side, all the same size
  - assets/horse/frames.json gives each strip's frame count and speed, as
    {"walk_right": {"frames": 9, "fps": 10}, ...}. Strips missing from it use
    the counts and speeds in ANIMATIONS below.
  - the horse's feet touch the bottom edge of each frame, centered
  - a missing *_left.png is made by mirroring *_right.png, and vice versa
  - graze, eat, drink and sleep only need left/right (the horse turns sideways)

tools/import_sprites.py writes all of this from the Onfe horse pack.
"""

import json
from pathlib import Path

import pygame

ASSET_DIR = Path(__file__).parent / "assets" / "horse"
DIRECTIONS = ("down", "up", "left", "right")

# name: (frame count, frames per second) for placeholders and unlisted strips
ANIMATIONS = {
    "idle": (4, 2),   # frame 4 is a blink
    "walk": (4, 8),
    "trot": (4, 12),
    "graze": (2, 2),
    "eat": (2, 5),
    "sleep": (2, 1),  # slow breathing
    "drink": (2, 2),
    "gallop": (4, 16),
    "jump": (4, 4),
    "rear": (4, 3),
}
SIDE_ONLY = {"graze", "eat", "drink", "sleep"}
# With no art and no placeholder drawing, borrow another animation's frames.
FALLBACK = {"drink": "graze", "gallop": "trot", "jump": "trot", "rear": "idle"}
PLACEHOLDER_DRAWN = {"idle", "walk", "trot", "graze", "eat", "sleep"}

# Placeholder frame size, in internal (266x160) pixels.
FRAME_W, FRAME_H = 40, 32

COAT = (150, 94, 52)
COAT_LIGHT = (184, 126, 76)
COAT_DARK = (112, 68, 38)
MANE = (64, 40, 28)
MUZZLE = (104, 66, 44)
HOOF = (52, 40, 34)
EYE = (24, 16, 14)


# ---------------------------------------------------------------- placeholders

def _gait_swing(anim: str, i: int) -> int:
    return (2, 0, -2, 0)[i % 4] if anim in ("walk", "trot") else 0


def _tail_sway(anim: str, i: int) -> int:
    return (0, 1, 0, -1)[i % 4] if anim in ("idle", "walk", "trot") else 0


def _bob(anim: str, i: int) -> int:
    return 1 if anim == "trot" and i % 2 else 0


def _blink(anim: str, i: int) -> bool:
    return anim == "sleep" or (anim == "idle" and i == 3)


def _side(anim: str, i: int) -> pygame.Surface:
    """Side view, facing right."""
    s = pygame.Surface((FRAME_W, FRAME_H), pygame.SRCALPHA)
    lying = anim == "sleep"
    head_low = anim in ("graze", "eat")
    body_y = 19 if lying else 12 - _bob(anim, i)
    breath = 1 if lying and i % 2 else 0

    # Tail, behind everything.
    sway = _tail_sway(anim, i)
    tail_len = 6 if lying else 11
    pygame.draw.line(s, MANE, (9, body_y + 2), (4 + sway, body_y + tail_len), 3)

    # Legs: far pair darker and drawn first. Diagonal pairs swing together.
    if lying:
        for x in (11, 24):
            pygame.draw.rect(s, COAT_DARK, (x, body_y + 9, 7, 2))
            pygame.draw.rect(s, HOOF, (x + 6, body_y + 9, 2, 2))
    else:
        swing = _gait_swing(anim, i)
        legs = [(11, -swing, True), (26, swing, True),
                (14, swing, False), (29, -swing, False)]
        for x, dx, far in legs:
            top = body_y + 7
            bottom = 29 - (1 if dx > 0 else 0)  # the leg reaching forward lifts
            pygame.draw.rect(s, COAT_DARK if far else COAT, (x + dx, top, 3, bottom - top))
            pygame.draw.rect(s, HOOF, (x + dx, bottom, 3, 2))

    # Body with a belly shadow and a back highlight.
    pygame.draw.ellipse(s, COAT_DARK, (7, body_y + 1 - breath, 26, 12 + breath))
    pygame.draw.ellipse(s, COAT, (7, body_y - breath, 26, 11 + breath))
    pygame.draw.ellipse(s, COAT_LIGHT, (11, body_y + 1 - breath, 16, 3))

    # Head position for this pose.
    if head_low:
        hx, hy = 30, 23 + i % 2
    elif lying:
        hx, hy = 30, body_y - 4
    else:
        hx, hy = 30, body_y - 8

    # Neck, then the mane along its top edge.
    if head_low:  # neck reaches forward and down; the mane rides on top
        pygame.draw.polygon(s, COAT, [(26, body_y + 2), (31, body_y),
                                      (hx + 6, hy + 1), (hx + 1, hy + 4)])
        pygame.draw.line(s, MANE, (29, body_y), (hx + 5, hy), 2)
    else:
        pygame.draw.polygon(s, COAT, [(25, body_y + 1), (hx + 1, hy + 1),
                                      (hx + 5, hy + 5), (31, body_y + 5)])
        pygame.draw.line(s, MANE, (25, body_y), (hx + 1, hy), 2)

    # Head.
    pygame.draw.rect(s, COAT, (hx, hy, 7, 6), border_radius=2)
    pygame.draw.rect(s, MUZZLE, (hx + 5, hy + 2, 4, 4), border_radius=1)
    s.set_at((hx + 7, hy + 3), HOOF)                       # nostril
    pygame.draw.rect(s, COAT_DARK, (hx + 1, hy - 2, 2, 3))  # ear
    s.set_at((hx + 3, hy - 1), MANE)                        # forelock
    if _blink(anim, i):
        pygame.draw.line(s, EYE, (hx + 3, hy + 2), (hx + 4, hy + 2))
    else:
        pygame.draw.line(s, EYE, (hx + 4, hy + 1), (hx + 4, hy + 2))
    return s


def _front(anim: str, i: int) -> pygame.Surface:
    """Facing down, toward the room."""
    s = pygame.Surface((FRAME_W, FRAME_H), pygame.SRCALPHA)
    bob = _bob(anim, i)

    # Tail flicks out to the side now and then.
    if anim == "idle" and i in (1, 2):
        pygame.draw.line(s, MANE, (27, 13), (29, 19), 2)

    for x in (14, 23):  # hind legs, behind the body
        pygame.draw.rect(s, COAT_DARK, (x, 20 - bob, 3, 8))
        pygame.draw.rect(s, HOOF, (x, 28 - bob, 3, 1))

    pygame.draw.ellipse(s, COAT_DARK, (12, 10 - bob, 16, 13))
    pygame.draw.ellipse(s, COAT, (12, 9 - bob, 16, 12))

    lifted = (0, None, 1, None)[i % 4] if anim in ("walk", "trot") else None
    for k, x in enumerate((15, 22)):  # front legs
        lift = 2 if lifted == k else 0
        pygame.draw.rect(s, COAT, (x, 18 - bob, 3, 11 - lift + bob))
        pygame.draw.rect(s, HOOF, (x, 29 - lift, 3, 2))

    hy = 1 - bob
    pygame.draw.rect(s, COAT_DARK, (16, hy - 1, 2, 3))  # ears
    pygame.draw.rect(s, COAT_DARK, (22, hy - 1, 2, 3))
    pygame.draw.rect(s, COAT, (16, hy + 1, 8, 11), border_radius=3)
    pygame.draw.rect(s, MUZZLE, (17, hy + 8, 6, 4), border_radius=2)
    s.set_at((18, hy + 10), HOOF)  # nostrils
    s.set_at((21, hy + 10), HOOF)
    pygame.draw.rect(s, MANE, (19, hy, 2, 3))  # forelock
    for x in (17, 22):
        if _blink(anim, i):
            s.set_at((x, hy + 5), EYE)
        else:
            pygame.draw.line(s, EYE, (x, hy + 4), (x, hy + 5))
    return s


def _back(anim: str, i: int) -> pygame.Surface:
    """Facing up, away from the room."""
    s = pygame.Surface((FRAME_W, FRAME_H), pygame.SRCALPHA)
    bob = _bob(anim, i)

    # Head peeking over the body, with the mane down the middle.
    pygame.draw.rect(s, COAT_DARK, (17, 0 - bob, 2, 3))
    pygame.draw.rect(s, COAT_DARK, (21, 0 - bob, 2, 3))
    pygame.draw.rect(s, COAT, (17, 2 - bob, 6, 8), border_radius=2)
    pygame.draw.rect(s, MANE, (19, 2 - bob, 2, 9))

    for x in (15, 22):  # front legs, behind the body
        pygame.draw.rect(s, COAT_DARK, (x, 19 - bob, 3, 9))

    pygame.draw.ellipse(s, COAT_DARK, (11, 10 - bob, 18, 14))
    pygame.draw.ellipse(s, COAT, (11, 9 - bob, 18, 13))
    pygame.draw.ellipse(s, COAT_LIGHT, (14, 10 - bob, 12, 3))

    lifted = (0, None, 1, None)[i % 4] if anim in ("walk", "trot") else None
    for k, x in enumerate((14, 23)):  # hind legs
        lift = 2 if lifted == k else 0
        pygame.draw.rect(s, COAT, (x, 20 - bob, 3, 9 - lift + bob))
        pygame.draw.rect(s, HOOF, (x, 29 - lift, 3, 2))

    sway = _tail_sway(anim, i)
    pygame.draw.line(s, MANE, (20, 11 - bob), (20 + sway, 24 - bob), 3)
    return s


# --------------------------------------------------------------------- loading

def _mirror(frames: list) -> list:
    return [pygame.transform.flip(f, True, False) for f in frames]


def _load_strip(anim: str, direction: str, count: int):
    path = ASSET_DIR / f"{anim}_{direction}.png"
    if not path.exists():
        return None
    image = pygame.image.load(str(path))
    if pygame.display.get_surface() is not None:
        image = image.convert_alpha()
    w = image.get_width() // count
    h = image.get_height()
    return [image.subsurface((k * w, 0, w, h)).copy() for k in range(count)]


def _load_manifest() -> dict:
    path = ASSET_DIR / "frames.json"
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


class HorseSprites:
    def __init__(self):
        self.frames: dict[tuple[str, str], list] = {}
        self.fps: dict[tuple[str, str], float] = {}
        self.files_loaded = 0
        manifest = _load_manifest()

        for anim, (count, fps) in ANIMATIONS.items():
            for d in DIRECTIONS:
                info = manifest.get(f"{anim}_{d}", {})
                strip = _load_strip(anim, d, info.get("frames", count))
                if strip:
                    self.frames[(anim, d)] = strip
                    self.fps[(anim, d)] = info.get("fps", fps)
                    self.files_loaded += 1

        # Fill gaps: drawn placeholders first, then borrowed animations.
        order = sorted(ANIMATIONS, key=lambda a: a in FALLBACK)
        for anim in order:
            count, fps = ANIMATIONS[anim]
            right, left = (anim, "right"), (anim, "left")
            if right not in self.frames and left in self.frames:
                self._set(right, _mirror(self.frames[left]), self.fps[left])
            if right not in self.frames:
                if anim in PLACEHOLDER_DRAWN:
                    self._set(right, [_side(anim, i) for i in range(count)], fps)
                else:
                    self._borrow(right, FALLBACK[anim])
            if left not in self.frames:
                self._set(left, _mirror(self.frames[right]), self.fps[right])
            for d, draw in (("down", _front), ("up", _back)):
                key = (anim, d)
                if key in self.frames:
                    continue
                if anim in SIDE_ONLY:
                    self._set(key, self.frames[right], self.fps[right])
                elif anim in PLACEHOLDER_DRAWN:
                    self._set(key, [draw(anim, i) for i in range(count)], fps)
                else:
                    self._borrow(key, FALLBACK[anim])

    def _set(self, key, frames, fps) -> None:
        self.frames[key] = frames
        self.fps[key] = fps

    def _borrow(self, key, source_anim) -> None:
        src = (source_anim, key[1])
        self._set(key, self.frames[src], self.fps[src])

    def get(self, anim: str, direction: str, t: float) -> pygame.Surface:
        """The frame to show `t` seconds into a looping animation."""
        frames = self.frames[(anim, direction)]
        return frames[int(t * self.fps[(anim, direction)]) % len(frames)]

    def get_once(self, anim: str, direction: str, progress: float) -> pygame.Surface:
        """The frame for a one-shot animation, `progress` running 0 to 1."""
        frames = self.frames[(anim, direction)]
        return frames[min(int(progress * len(frames)), len(frames) - 1)]

    def length(self, anim: str, direction: str) -> float:
        """Seconds for one play-through."""
        return len(self.frames[(anim, direction)]) / self.fps[(anim, direction)]
