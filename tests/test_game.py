"""Feeding, motion, day and night, and saving, through the whole game."""

import random
import tempfile
import unittest
from pathlib import Path

import pygame

import controls
import daynight
from game import MAX_TREATS, Game
from tests.helpers import noon_game, run


class Feeding(unittest.TestCase):
    def test_click_on_button_drops_a_treat(self):
        g = noon_game()
        bx, by = g.feed_button.CENTER
        view = controls.view_rect((800, 480))
        pos = (view.x + bx * 3 + 1, view.y + by * 3 + 1)
        click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)
        controls.handle_event(click, g, (800, 480))
        self.assertEqual(g.world.treats_waiting(), 1)

    def test_click_elsewhere_does_nothing(self):
        g = noon_game()
        click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(300, 200))
        controls.handle_event(click, g, (800, 480))
        self.assertEqual(g.world.treats_waiting(), 0)

    def test_hungry_horse_eats(self):
        g = noon_game()
        g.horse.hunger = 60
        self.assertTrue(g.feed())
        self.assertTrue(run(g, 15, until=lambda g: g.world.treats_waiting() == 0))
        self.assertLess(g.horse.hunger, 30)
        self.assertAlmostEqual(g.horse.fed_score, 1.0, places=2)

    def test_full_horse_sniffs_and_leaves_it(self):
        g = noon_game(2)
        g.horse.hunger = 10
        g.feed()
        states = set()
        run(g, 10, until=lambda g: states.add(g.horse.state))
        self.assertIn("sniff", states)
        self.assertNotIn("eat", states)
        self.assertEqual(g.world.treats_waiting(), 1)

    def test_treat_limit(self):
        g = noon_game()
        g.horse.sleep()
        results = [g.feed() for _ in range(MAX_TREATS + 1)]
        self.assertEqual(results, [True] * MAX_TREATS + [False])
        self.assertFalse(g.can_feed())


class Motion(unittest.TestCase):
    def test_cooldown(self):
        g = noon_game()
        g.fake_motion()
        run(g, 0.1)
        self.assertEqual(g.horse.state, "trot")
        g.horse._enter("idle", duration=1e9)
        g.fake_motion()
        run(g, 0.1)
        self.assertEqual(g.horse.state, "idle")  # still cooling down
        run(g, 21)
        g.fake_motion()
        run(g, 0.1)
        self.assertEqual(g.horse.state, "trot")


class DayAndNight(unittest.TestCase):
    def test_bedtime_and_dawn(self):
        g = noon_game(hour=daynight.BEDTIME - 0.01)
        g.clock.speed = 600  # ten minutes per second
        g.horse._enter("idle", duration=1e9)
        self.assertTrue(run(g, 10, until=lambda g: g.horse.state == "sleep"))
        self.assertTrue(daynight.is_bedtime(g.clock.hour))
        self.assertTrue(run(g, 120, until=lambda g: g.horse.state != "sleep"))
        self.assertFalse(daynight.is_bedtime(g.clock.hour))

    def test_starting_at_night_starts_asleep(self):
        self.assertEqual(noon_game(hour=2.0).horse.state, "sleep")

    def test_motion_at_night_wakes_it_then_it_dozes_off(self):
        g = noon_game(hour=2.0)
        g.fake_motion()
        run(g, 0.1)
        self.assertEqual(g.horse.state, "trot")
        self.assertTrue(run(g, 15, until=lambda g: g.horse.state == "idle"))
        run(g, 5)
        self.assertNotEqual(g.horse.state, "sleep")  # stays up a little
        self.assertTrue(run(g, 40, until=lambda g: g.horse.state == "sleep"))

    def test_treat_at_night_wakes_it_to_eat(self):
        g = noon_game(hour=2.0)
        g.horse.hunger = 80
        self.assertTrue(g.feed())
        run(g, 0.1)
        self.assertNotEqual(g.horse.state, "sleep")
        self.assertTrue(run(g, 30, until=lambda g: g.horse.state == "eat"))
        self.assertTrue(run(g, 60, until=lambda g: g.horse.state == "sleep"))
        self.assertEqual(g.world.treats_waiting(), 0)

    def test_horse_finishes_what_its_doing_before_bed(self):
        g = noon_game(hour=daynight.BEDTIME + 0.1)
        g.horse.wake()
        g.horse.hunger = 80
        g.feed()
        run(g, 0.5)
        self.assertNotEqual(g.horse.state, "sleep")  # off to its treat first
        self.assertTrue(run(g, 30, until=lambda g: g.horse.state == "sleep"))

    def test_darkness_and_sky(self):
        self.assertEqual(daynight.darkness(12), 0.0)
        self.assertEqual(daynight.darkness(0), 1.0)
        self.assertTrue(0 < daynight.darkness(19.5) < 1)
        self.assertEqual(daynight.sky_wash(24), daynight.sky_wash(0))
        # Smooth: no big jump from one minute to the next.
        prev = daynight.sky_wash(0)
        for minute in range(1, 24 * 60):
            cur = daynight.sky_wash(minute / 60)
            self.assertLessEqual(max(abs(a - b) for a, b in zip(cur, prev)), 8, minute)
            prev = cur

    def test_skip_to(self):
        c = daynight.GameClock(speed=0, start_hour=12)
        c.skip_to(20.5)
        self.assertAlmostEqual(c.hour, 20.5, places=3)
        c.skip_to(5.0)  # the next 5:00 is tomorrow morning
        self.assertAlmostEqual(c.hour, 5.0, places=3)


class Saving(unittest.TestCase):
    def test_game_saves_on_close_and_loads_next_time(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "state.json"
            g = Game(random.Random(1), hardware=False,
                     clock=daynight.GameClock(speed=0, start_hour=12), save_path=path)
            g.horse.hunger = 77
            g.close()
            g2 = Game(random.Random(2), hardware=False,
                      clock=daynight.GameClock(speed=0, start_hour=12), save_path=path)
            self.assertAlmostEqual(g2.horse.hunger, 77, delta=0.1)
            g2.close()


if __name__ == "__main__":
    unittest.main()
