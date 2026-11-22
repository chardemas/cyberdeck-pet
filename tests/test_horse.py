"""The horse's state machine, movement, hunger and mood."""

import random
import unittest

import horse as H
from horse import Horse
from tests.helpers import DT
from world import BLOCKED, BOUNDS, JUMP_X


def new_horse(seed: int = 1) -> Horse:
    h = Horse(random.Random(seed))
    h.anim_length = lambda anim, facing: 1.0
    return h


def step(h: Horse, seconds: float) -> None:
    for _ in range(int(seconds * 30)):
        h.update(DT)
        h.effects.clear()


# Every state change the horse is allowed to make. Idle is the hub; the rest
# are plans that chain one action into the next.
ALLOWED = {
    ("idle", "walk"), ("idle", "graze"), ("idle", "gallop"), ("idle", "sleep"),
    ("walk", "idle"), ("graze", "idle"), ("drink", "idle"), ("jump", "idle"),
    ("gallop", "idle"), ("trot", "idle"), ("eat", "idle"), ("sniff", "walk"),
    ("sniff", "idle"), ("sleep", "idle"),
    ("walk", "walk"), ("walk", "drink"), ("walk", "jump"), ("walk", "eat"),
    ("walk", "sniff"), ("eat", "gallop"), ("startled", "trot"), ("startled", "idle"),
}


class StateMachine(unittest.TestCase):
    def test_starts_idle(self):
        self.assertEqual(new_horse().state, "idle")

    def test_long_run_only_allowed_transitions(self):
        h = new_horse(3)
        prev, seen = h.state, set()
        for _ in range(30 * 60 * 30):  # 30 minutes
            h.update(DT)
            h.effects.clear()
            if h.state != prev:
                seen.add((prev, h.state))
                prev = h.state
        self.assertTrue(seen <= ALLOWED, seen - ALLOWED)
        for state in ("walk", "graze", "drink"):
            self.assertIn(state, {b for _, b in seen}, f"never saw {state}")

    def test_stays_inside_fence_and_out_of_props(self):
        h = new_horse(4)
        for _ in range(30 * 60 * 20):
            h.update(DT)
            h.effects.clear()
            self.assertTrue(BOUNDS.inflate(1, 1).collidepoint(h.x, h.y), (h.state, h.x, h.y))
            if h.state != "jump":  # jumping crosses the rail on purpose
                self.assertFalse(any(z.collidepoint(h.x, h.y) for z in BLOCKED), (h.state, h.x, h.y))


class Events(unittest.TestCase):
    def test_motion_makes_it_trot_then_face_you(self):
        h = new_horse()
        h.motion()
        self.assertEqual(h.state, "trot")
        step(h, 15)
        self.assertNotEqual(h.state, "trot")

    def test_motion_after_long_quiet_startles_first(self):
        h = new_horse()
        h.quiet = H.STARTLE_AFTER + 1
        h.motion()
        self.assertEqual(h.state, "startled")
        step(h, 1.1)
        self.assertEqual(h.state, "trot")

    def test_sleeping_horse_ignores_motion(self):
        h = new_horse()
        h.sleep()
        h.motion()
        self.assertEqual(h.state, "sleep")
        h.wake()
        self.assertEqual(h.state, "idle")

    def test_jump_lands_on_the_other_side(self):
        h = new_horse(13)
        self.assertTrue(h.try_jump())
        for _ in range(30 * 30):  # walk to the take-off point
            if h.state == "jump":
                break
            h.update(DT)
        self.assertEqual(h.state, "jump")
        start = h.x
        while h.state == "jump":
            h.update(DT)
        self.assertLess((start - JUMP_X) * (h.x - JUMP_X), 0)


class Hunger(unittest.TestCase):
    def test_rises_over_time(self):
        h = new_horse()
        h.hunger = 50
        h._enter("idle", duration=1e9)
        step(h, 60)
        self.assertAlmostEqual(h.hunger, 50 + 60 * H.HUNGER_PER_SEC, places=2)

    def test_rises_slower_asleep(self):
        h = new_horse()
        h.hunger = 50
        h.sleep()
        step(h, 60)
        self.assertAlmostEqual(h.hunger, 50 + 60 * H.HUNGER_PER_SEC * H.SLEEP_HUNGER_RATE, places=2)

    def test_never_above_100(self):
        h = new_horse()
        h.hunger = 99.99
        step(h, 60)
        self.assertLessEqual(h.hunger, 100)


class Mood(unittest.TestCase):
    def test_calm_by_default(self):
        self.assertEqual(new_horse().mood, "calm")

    def test_happy_after_treats(self):
        h = new_horse()
        h.fed_score = H.HAPPY_FED
        self.assertEqual(h.mood, "happy")

    def test_fed_score_fades(self):
        h = new_horse()
        h.fed_score = 2.0
        h._enter("idle", duration=1e9)
        h.update(H.FED_HALF_LIFE)
        self.assertAlmostEqual(h.fed_score, 1.0, places=3)

    def test_lonely_when_nobody_visits_and_motion_cheers_it(self):
        h = new_horse()
        h.lonely_time = H.LONELY_AFTER
        self.assertEqual(h.mood, "lonely")
        h.motion()
        self.assertEqual(h.mood, "calm")

    def test_loneliness_doesnt_grow_while_asleep(self):
        h = new_horse()
        h.sleep()
        step(h, 30)
        self.assertEqual(h.lonely_time, 0)

    def test_lonely_horse_idles_longer_and_looks_out(self):
        calm, lonely = new_horse(5), new_horse(5)
        lonely.lonely_time = H.LONELY_AFTER
        calm_times, lonely_times = [], []
        for _ in range(40):
            calm._rest()
            lonely._rest()
            calm_times.append(calm.duration)
            lonely_times.append(lonely.duration)
            self.assertEqual(lonely.facing, "down")
        self.assertGreater(min(lonely_times), max(calm_times) - 1.01)
        self.assertGreater(sum(lonely_times), sum(calm_times))


if __name__ == "__main__":
    unittest.main()
