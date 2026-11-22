"""The horse: where it is, what it's doing, and how hungry it is.

States
  idle      home state. After a few seconds picks what to do next.
  walk      strolls to a spot (or to the trough or the jump), then continues.
  graze     head down eating grass for a while (lowers hunger a little).
  drink     drinks at the trough.
  jump      jumps over the poles.
  gallop    a rare happy dash across the meadow, often after a treat.
  trot      greeting: trots to the front (bottom of the screen) and looks at you.
  startled  rears up when motion comes after a long quiet spell, then trots over.
  eat       eats a treat it walked to (lowers hunger a lot).
  sniff     not hungry enough: sniffs the treat, then wanders off. The treat
            stays, and the horse comes back for it once it's hungry.
  sleep     dozes standing up until woken.

Mood (happy, calm or lonely) comes from how often it's been fed lately and how
long since anyone walked by. It only changes idle habits: a happy horse
fidgets more and jumps and gallops more often, and sometimes a heart floats
up; a lonely horse stands longer, looks out toward the room, and plays less.

Every state except sleep returns to idle when it ends. To add a state, add
its name, an `_update_<name>` method, and an animation in sprites.py.

The horse asks for effects (hearts, sparkles, dust) by appending
(kind, x, y) to `self.effects`; main.py hands them to the world.
"""

import math
import random

from sprites_world import draw_shadow
from world import (BOUNDS, DRINK_SPOTS, JUMP_LANE, JUMP_RUNUP, JUMP_X,
                   find_path, ground_clear, path_clear, spot_free)

IDLE, WALK, GRAZE, DRINK, JUMP, GALLOP = "idle", "walk", "graze", "drink", "jump", "gallop"
TROT, STARTLED, EAT, SNIFF, SLEEP = "trot", "startled", "eat", "sniff", "sleep"
ANIMATION = {STARTLED: "rear", SNIFF: "graze"}  # states whose animation has another name
ONE_SHOT = {JUMP, STARTLED}     # play once instead of looping

WALK_SPEED = 20           # internal pixels per second
TROT_SPEED = 42
GALLOP_SPEED = 80
HUNGER_PER_SEC = 100 / (4 * 3600)   # empty to starving in about 4 hours
HUNGRY = 70               # at or above this, the horse counts as hungry
GRAZE_FILL_PER_SEC = 0.4
EAT_FILL = 35             # one treat
FEED_MIN_HUNGER = 40      # below this, the horse only sniffs treats
STARTLE_AFTER = 300       # seconds without motion before a sudden one startles
GALLOP_AFTER_TREAT = 0.4  # chance of a happy gallop after eating
HEAD_OFFSET = 24          # how far the head is from the feet, side view
TREAT_REACH = 30          # feet stand this far from a treat to eat it
SLEEP_HUNGER_RATE = 0.5   # hunger rises at half speed while asleep
FED_HALF_LIFE = 6 * 3600  # the "fed lately" score halves every 6 hours
LONELY_AFTER = 3 * 3600   # awake this long without seeing anyone: lonely
HAPPY_FED = 1.5           # fed-lately score that makes the horse happy

# Mood: (idle seconds min, max), play multiplier for jump and gallop chances.
MOOD_IDLE = {"happy": ((2, 4), 1.6), "calm": ((3, 6), 1.0), "lonely": ((5, 9), 0.3)}
BUSY = {SLEEP, JUMP, STARTLED, EAT}  # states a new treat can't interrupt


class Horse:
    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()
        self.x, self.y = float(BOUNDS.centerx - 40), float(BOUNDS.centery)
        self.facing = "down"
        self.hunger = 50.0
        self.quiet = 0.0           # seconds since motion was last seen
        self.treats: list = []     # the world's treats; main.py shares the list
        self.treat = None          # the treat being eaten
        self.fed_score = 0.0       # +1 per treat eaten, fading with FED_HALF_LIFE
        self.lonely_time = 0.0     # awake seconds since motion was last seen
        self.target = (self.x, self.y)
        self.then = None           # what to do when the current state ends
        self.effects: list[tuple[str, float, float]] = []
        self._effect_clock = 0.0
        # Seconds for one-shot animations; main.py swaps in the real lengths.
        self.anim_length = lambda anim, facing: {"jump": 1.0, "rear": 1.2}[anim]
        self._enter(IDLE)

    @property
    def hungry(self) -> bool:
        return self.hunger >= HUNGRY

    @property
    def mood(self) -> str:
        if self.lonely_time >= LONELY_AFTER:
            return "lonely"
        if self.fed_score >= HAPPY_FED:
            return "happy"
        return "calm"

    @property
    def animation(self) -> str:
        return ANIMATION.get(self.state, self.state)

    # ------------------------------------------------------------ events

    def motion(self) -> None:
        """Someone walked by: come to the front to say hello."""
        startled = self.quiet >= STARTLE_AFTER
        self.quiet = 0.0
        self.lonely_time = 0.0
        if self.state in (SLEEP, EAT, JUMP, STARTLED):
            return
        if startled:
            self._enter(STARTLED, duration=self.anim_length("rear", self.facing),
                        then=self._trot_to_front)
        else:
            self._trot_to_front()

    @property
    def wants_food(self) -> bool:
        return self.hunger >= FEED_MIN_HUNGER

    def find_treat_spot(self) -> tuple[float, float] | None:
        """Somewhere near the horse to drop a treat that it can walk to."""
        ahead = {"right": 1, "left": -1}.get(self.facing) or self.rng.choice((1, -1))
        # Nearby first, in front of the horse first; then wider rings.
        candidates = []
        for dist in (50, 35, 70, 95, 120):
            for ang in (0, 30, -30, 60, -60, 180, 150, -150, 120, -120, 90, -90):
                a = math.radians(ang)
                candidates.append((ahead * dist * math.cos(a), dist * math.sin(a) * 0.6))
        for dx, dy in candidates:
            tx = self.x + dx + self.rng.uniform(-4, 4)
            ty = self.y + dy + self.rng.uniform(-3, 3)
            apart = all(math.dist((tx, ty), (t.x, t.y)) >= 14 for t in self._waiting_treats())
            if apart and ground_clear(tx, ty) and self._treat_stance(tx, ty):
                return tx, ty
        return None

    def notice_treat(self, treat) -> None:
        """A treat just landed: go to it now, unless busy (then it waits)."""
        if self.state not in BUSY:
            self._go_to_treat(treat)

    def sleep(self) -> None:
        self.treat = None  # a half-eaten treat stays on the ground for later
        self._face_sideways()
        self._enter(SLEEP, duration=math.inf)

    def wake(self) -> None:
        if self.state == SLEEP:
            self._enter(IDLE)

    # Test helpers (mock-mode keys); each returns False if the way is blocked.
    def try_jump(self) -> bool:
        return self.state not in (SLEEP, JUMP) and self._start_jump()

    def try_gallop(self) -> bool:
        return self.state not in (SLEEP, JUMP) and self._start_gallop()

    def try_drink(self) -> bool:
        return self.state not in (SLEEP, JUMP) and self._start_drink()

    # ------------------------------------------------------------ update

    def update(self, dt: float) -> None:
        asleep = self.state == SLEEP
        rate = HUNGER_PER_SEC * (SLEEP_HUNGER_RATE if asleep else 1.0)
        self.hunger = min(100.0, self.hunger + rate * dt)
        self.fed_score *= math.pow(0.5, dt / FED_HALF_LIFE)
        if not asleep:  # nobody visits at night, and that's fine
            self.lonely_time += dt
        self.quiet += dt
        self.timer += dt
        self._effect_clock += dt
        getattr(self, f"_update_{self.state}")(dt)

    def _update_idle(self, dt: float) -> None:
        if self.timer < self.duration:
            return
        if self.wants_food:  # a treat left lying around comes first
            for treat in sorted(self._waiting_treats(),
                                key=lambda t: math.dist((t.x, t.y), (self.x, self.y))):
                if self._go_to_treat(treat):
                    return
        r = self.rng.random()
        graze = 0.25 + 0.5 * self.hunger / 100  # hungrier, grazes more
        play = 0.0 if self.hungry else MOOD_IDLE[self.mood][1]
        if r < graze:
            self._face_sideways()
            self._enter(GRAZE, duration=self.rng.uniform(4, 8))
            return
        r -= graze
        started = False
        if r < 0.10:
            started = self._start_drink()
        elif r < 0.10 + 0.08 * play:
            started = self._start_jump()
        elif r < 0.10 + 0.11 * play:
            started = self._start_gallop()
        if not started and not self._start_walk():
            self._rest()  # nowhere to go right now; think again shortly

    def _rest(self) -> None:
        """Stand idle for a while; how long, and how, depends on mood."""
        (lo, hi), _ = MOOD_IDLE[self.mood]
        if self.mood == "lonely":
            self.facing = "down"  # looking out toward the room
        elif self.mood == "happy" and self.rng.random() < 0.15:
            self.effects.append(("heart", self.x, self.y - 46))
        self._enter(IDLE, duration=self.rng.uniform(lo, hi))

    def _update_walk(self, dt: float) -> None:
        if self._move(WALK_SPEED, dt):
            self._arrived()

    def _update_trot(self, dt: float) -> None:
        if self._move(TROT_SPEED, dt):
            self.facing = "down"  # look at the person
            self._enter(IDLE)

    def _update_gallop(self, dt: float) -> None:
        if self._effect_clock >= 0.08:  # dust kicked up behind
            self._effect_clock = 0.0
            back = {"right": -18, "left": 18}.get(self.facing, 0)
            self.effects.append(("dust", self.x + back, self.y - 1))
        if self._move(GALLOP_SPEED, dt):
            self._arrived()

    def _update_graze(self, dt: float) -> None:
        self.hunger = max(0.0, self.hunger - GRAZE_FILL_PER_SEC * dt)
        if self.timer >= self.duration:
            self._arrived()

    def _update_drink(self, dt: float) -> None:
        if self.timer >= self.duration:
            self._enter(IDLE)

    def _update_jump(self, dt: float) -> None:
        (x0, y0), (x1, y1) = self.jump_from, self.target
        p = min(self.timer / self.duration, 1.0)
        self.x, self.y = x0 + (x1 - x0) * p, y0 + (y1 - y0) * p
        if p >= 1.0:
            for k in range(3):
                self.effects.append(("dust", self.x - 6 + 6 * k, self.y - 1))
            self._enter(IDLE)

    def _update_startled(self, dt: float) -> None:
        if self.timer >= self.duration:
            self._arrived()

    def _update_eat(self, dt: float) -> None:
        self.hunger = max(0.0, self.hunger - EAT_FILL / self.duration * dt)
        if self._effect_clock >= 0.7:
            self._effect_clock = 0.0
            self.effects.append(("heart", *self.head()))
        if self.timer >= self.duration:
            if self.treat is not None:
                self.treat.eaten = True
                self.treat = None
                self.fed_score += 1.0
            for _ in range(4):
                self.effects.append(("sparkle", *self.head()))
            if self.rng.random() < GALLOP_AFTER_TREAT and self._start_gallop():
                return
            self._enter(IDLE)

    def _update_sniff(self, dt: float) -> None:
        if self.timer >= self.duration:
            self._arrived()

    def _update_sleep(self, dt: float) -> None:
        pass

    # ------------------------------------------------------------ plans

    def _start_walk(self) -> bool:
        spot = self._pick_spot()
        if spot is None:
            return False
        self._go(WALK, spot)
        return True

    def _start_gallop(self) -> bool:
        spot = self._pick_spot(min_distance=120)
        if spot is None:
            return False
        self._go(GALLOP, spot)
        return True

    def _start_drink(self) -> bool:
        spots = sorted(DRINK_SPOTS, key=lambda s: math.dist((s[0], s[1]), (self.x, self.y)))
        for x, y, face in spots:
            def drink(face=face):
                self.facing = face
                self._enter(DRINK, duration=self.rng.uniform(4, 7))
            if self._walk_to((x, y), then=drink):
                return True
        return False

    def _start_jump(self) -> bool:
        side = -1 if self.x < JUMP_X else 1  # take off from the near side
        takeoff = (JUMP_X + side * JUMP_RUNUP, JUMP_LANE)
        landing = (JUMP_X - side * JUMP_RUNUP, JUMP_LANE)

        def jump():
            self.facing = "right" if side < 0 else "left"
            self.jump_from = (self.x, self.y)
            self.target = landing
            self._enter(JUMP, duration=self.anim_length("jump", self.facing))
        return self._walk_to(takeoff, then=jump)

    def _walk_to(self, spot: tuple[float, float], then) -> bool:
        """Walk to `spot`, straight if possible, else around whatever is in the way."""
        route = self._route(spot)
        if route is None:
            return False
        self._follow(route + [spot], then)
        return True

    def _follow(self, points: list, then) -> None:
        """Walk through each point in turn, then do `then`."""
        first, rest = points[0], points[1:]
        self._go(WALK, first, then=(lambda: self._follow(rest, then)) if rest else then)

    def _waiting_treats(self) -> list:
        return [t for t in self.treats if not t.eaten]

    def _treat_stance(self, tx: float, ty: float):
        """Where to stand to eat a treat at (tx, ty): (x, y, facing), or None.

        The horse stands beside the treat, facing it, so its head dips onto it.
        Tries the side nearer the horse first.
        """
        sides = sorted((-1, 1), key=lambda s: abs(tx + s * TREAT_REACH - self.x))
        for s in sides:
            stance = (tx + s * TREAT_REACH, ty)
            if spot_free(*stance) and self._reachable(stance):
                return stance[0], stance[1], "left" if s > 0 else "right"
        return None

    def _reachable(self, spot: tuple[float, float]) -> bool:
        return self._route(spot) is not None

    def _route(self, spot: tuple[float, float]) -> list | None:
        """Turning points to reach `spot` ([] = straight), or None."""
        return find_path((self.x, self.y), spot)

    def _go_to_treat(self, treat) -> bool:
        stance = self._treat_stance(treat.x, treat.y)
        if stance is None:
            return False
        x, y, face = stance

        def at_treat():
            self.facing = face
            if treat.eaten:
                self._enter(IDLE)
            elif self.wants_food:
                self.treat = treat
                self._enter(EAT, duration=4.0)
            else:
                self._enter(SNIFF, duration=1.6, then=self._wander_off)
        return self._walk_to((x, y), then=at_treat)

    def _wander_off(self) -> None:
        spot = self._pick_spot(min_distance=60)
        if spot is None:
            self._enter(IDLE)
        else:
            self._go(WALK, spot)

    def _trot_to_front(self) -> None:
        # Straight down to the front if possible, else the nearest clear column.
        for dx in (0, 30, -30, 60, -60, 90, -90, 120, -120):
            x = min(max(self.x + dx, BOUNDS.left), BOUNDS.right - 1)
            spot = (x, BOUNDS.bottom - 1)  # a Rect's bottom edge is just outside it
            if spot_free(*spot) and path_clear((self.x, self.y), spot):
                self._go(TROT, spot)
                return
        self.facing = "down"
        self._enter(IDLE)

    # ------------------------------------------------------------ helpers

    def _enter(self, state: str, duration: float | None = None, then=None) -> None:
        """Switch state. Any plan from before is dropped unless `then` is given."""
        self.state = state
        self.then = then
        self.timer = 0.0
        self._effect_clock = 0.0
        if duration is None:
            lo, hi = MOOD_IDLE[self.mood][0] if state == IDLE else (3, 6)
            duration = self.rng.uniform(lo, hi)
        self.duration = duration

    def _go(self, state: str, target: tuple[float, float], then=None) -> None:
        self.target = target
        dx, dy = target[0] - self.x, target[1] - self.y
        if abs(dx) >= abs(dy):
            self.facing = "right" if dx > 0 else "left"
        else:
            self.facing = "down" if dy > 0 else "up"
        self._enter(state, duration=math.inf, then=then)

    def _move(self, speed: float, dt: float) -> bool:
        """Step toward the target. True once arrived."""
        tx, ty = self.target
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)
        step = speed * dt
        if dist <= step:
            self.x, self.y = tx, ty
            return True
        self.x += dx / dist * step
        self.y += dy / dist * step
        return False

    def _arrived(self) -> None:
        then, self.then = self.then, None
        if then:
            then()
            return
        if self.hungry:
            self.facing = "down"  # hungry: looks out at you
        self._rest()

    def _face_sideways(self) -> None:
        if self.facing in ("up", "down"):
            self.facing = self.rng.choice(("left", "right"))

    def _pick_spot(self, min_distance: float = 0) -> tuple[float, float] | None:
        """A free spot the horse can walk straight to, or None."""
        for _ in range(30):
            x = self.rng.uniform(BOUNDS.left, BOUNDS.right)
            if self.hungry:  # stay near the front, where the food comes from
                y = self.rng.uniform(BOUNDS.bottom - BOUNDS.height / 3, BOUNDS.bottom)
            else:
                y = self.rng.uniform(BOUNDS.top, BOUNDS.bottom)
            if (math.dist((x, y), (self.x, self.y)) >= min_distance
                    and spot_free(x, y) and path_clear((self.x, self.y), (x, y))):
                return x, y
        return None

    def head(self) -> tuple[float, float]:
        """Roughly where the horse's mouth is."""
        dx = {"right": HEAD_OFFSET, "left": -HEAD_OFFSET}.get(self.facing, 0)
        return self.x + dx, self.y - 14

    # ------------------------------------------------------------ drawing

    def draw(self, surf, sprites) -> None:
        anim = self.animation
        if self.state in ONE_SHOT:
            frame = sprites.get_once(anim, self.facing, self.timer / self.duration)
        else:
            frame = sprites.get(anim, self.facing, self.timer)
        fw, fh = frame.get_size()
        x, y = round(self.x), round(self.y)

        draw_shadow(surf, x, y - 1, 46 if self.facing in ("left", "right") else 20)
        surf.blit(frame, (x - fw // 2, y - fh))

        if self.state == SLEEP:
            self._draw_zs(surf, x + (10 if self.facing == "right" else -14), y - 52)

    def _draw_zs(self, surf, x: int, y: int) -> None:
        # Two z's drifting up, 4x4 pixels each, with a soft shadow.
        z = ((0, 0), (1, 0), (2, 0), (3, 0), (2, 1), (1, 2),
             (0, 3), (1, 3), (2, 3), (3, 3))
        for k in range(2):
            t = (self.timer * 0.5 + k * 0.5) % 1.0
            zx, zy = x + k * 6 + round(t * 3), y - k * 7 - round(t * 8)
            for px, py in z:
                surf.set_at((zx + px + 1, zy + py + 1), (60, 70, 110))
            for px, py in z:
                surf.set_at((zx + px, zy + py), (240, 240, 255))
