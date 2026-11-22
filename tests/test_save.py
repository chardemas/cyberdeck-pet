"""Saving and loading state.json, including time away and damaged files."""

import json
import random
import tempfile
import unittest
from pathlib import Path

import save
from horse import Horse

HOUR = 3600


class SaveFile(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name) / "state.json"

    def tearDown(self):
        self.dir.cleanup()

    def saved_horse(self, hunger=30.0, fed=1.0, lonely=60.0, at=1_000_000.0):
        h = Horse(random.Random(1))
        h.hunger, h.fed_score, h.lonely_time = hunger, fed, lonely
        save.save(self.path, h, now=at)
        return h

    def loaded(self, at):
        h = Horse(random.Random(2))
        note = save.load(self.path, h, now=at)
        return h, note

    def test_round_trip(self):
        self.saved_horse(hunger=42.5, fed=1.25, lonely=600)
        h, note = self.loaded(at=1_000_000.0)
        self.assertAlmostEqual(h.hunger, 42.5)
        self.assertAlmostEqual(h.fed_score, 1.25)
        self.assertAlmostEqual(h.lonely_time, 600)
        self.assertIn("welcome back", note)

    def test_file_contents(self):
        self.saved_horse(hunger=30, fed=2.0)
        data = json.loads(self.path.read_text())
        self.assertEqual(set(data), {"version", "hunger", "mood", "fed_score", "lonely_time", "last_seen"})
        self.assertEqual(data["mood"], "happy")

    def test_no_temp_file_left_behind(self):
        self.saved_horse()
        self.assertEqual([p.name for p in Path(self.dir.name).iterdir()], ["state.json"])

    def test_time_away_makes_it_hungrier(self):
        self.saved_horse(hunger=30, at=0)
        h, _ = self.loaded(at=2 * HOUR)
        self.assertAlmostEqual(h.hunger, 30 + 2 * HOUR * save.AWAY_HUNGER_PER_SEC, places=3)

    def test_long_time_away_is_capped(self):
        self.saved_horse(hunger=30, at=0)
        h, _ = self.loaded(at=5 * 24 * HOUR)
        self.assertAlmostEqual(h.hunger, 30 + save.AWAY_HUNGER_MAX_GAIN)

    def test_time_away_never_pushes_past_ceiling(self):
        self.saved_horse(hunger=60, at=0)
        h, _ = self.loaded(at=5 * 24 * HOUR)
        self.assertAlmostEqual(h.hunger, save.AWAY_HUNGER_CEILING)

    def test_already_very_hungry_isnt_lowered(self):
        self.saved_horse(hunger=95, at=0)
        h, _ = self.loaded(at=5 * 24 * HOUR)
        self.assertAlmostEqual(h.hunger, 95)

    def test_clock_set_backwards_counts_as_no_time(self):
        self.saved_horse(hunger=30, at=10 * HOUR)
        h, _ = self.loaded(at=0)
        self.assertAlmostEqual(h.hunger, 30)

    def test_time_away_fades_fed_score_and_adds_some_loneliness(self):
        self.saved_horse(fed=2.0, lonely=0, at=0)
        h, _ = self.loaded(at=6 * HOUR)
        self.assertAlmostEqual(h.fed_score, 1.0, places=3)
        self.assertGreater(h.lonely_time, 0)
        h, _ = self.loaded(at=30 * 24 * HOUR)
        self.assertAlmostEqual(h.lonely_time, save.AWAY_LONELY_MAX)

    def test_missing_file_starts_fresh(self):
        h, note = self.loaded(at=0)
        self.assertEqual(h.hunger, Horse(random.Random(3)).hunger)
        self.assertIn("fresh", note)

    def test_damaged_file_starts_fresh(self):
        for junk in ("", "{not json", '{"hunger": "lots"}', "[]", '{"last_seen": 5}'):
            self.path.write_text(junk)
            h, note = self.loaded(at=0)
            self.assertIn("fresh", note, junk)
            self.assertEqual(h.hunger, Horse(random.Random(3)).hunger)

    def test_leftover_temp_file_is_ignored(self):
        self.saved_horse(hunger=33, at=0)
        self.path.with_suffix(".tmp").write_text("{half writ")  # power cut mid-save
        h, _ = self.loaded(at=0)
        self.assertAlmostEqual(h.hunger, 33)


if __name__ == "__main__":
    unittest.main()
