"""Remembers the horse across restarts and power cuts, in state.json.

Saved: hunger, mood (and what it's worked out from), and when the program
last ran. If it was off for a while, the horse gets hungrier for the time away,
but gently and with a cap, so it comes back hungry but never in trouble.

Writes go to a temporary file that is then swapped in, so pulling the plug
mid-save can't leave a half-written file. A missing or damaged file just
means starting fresh.
"""

import json
import math
import os
import time
from pathlib import Path

VERSION = 1
AWAY_HUNGER_PER_SEC = 100 / (8 * 3600)  # half the awake rate, like sleeping
AWAY_HUNGER_MAX_GAIN = 40                 # at most this much hunger for time away
AWAY_HUNGER_CEILING = 80                  # time away never pushes hunger past this
AWAY_LONELY_MAX = 3 * 3600                # at most 3 hours of loneliness for time away
FED_HALF_LIFE = 6 * 3600                  # see horse.py


def save(path: Path, horse, now: float | None = None) -> None:
    data = {
        "version": VERSION,
        "hunger": round(horse.hunger, 2),
        "mood": horse.mood,
        "fed_score": round(horse.fed_score, 3),
        "lonely_time": round(horse.lonely_time, 1),
        "last_seen": now if now is not None else time.time(),
    }
    path = Path(path)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)  # atomic: the old file or the new one, never half


def load(path: Path, horse, now: float | None = None) -> str:
    """Restore the horse from `path`. Returns a short note on what happened."""
    path = Path(path)
    now = now if now is not None else time.time()
    try:
        data = json.loads(path.read_text())
        hunger = float(data["hunger"])
        fed = float(data.get("fed_score", 0.0))
        lonely = float(data.get("lonely_time", 0.0))
        last = float(data["last_seen"])
    except FileNotFoundError:
        return "no save file yet: starting fresh"
    except (OSError, ValueError, KeyError, TypeError) as err:
        return f"save file unreadable ({err.__class__.__name__}): starting fresh"

    away = max(0.0, now - last)  # a clock set backwards counts as no time
    gain = min(away * AWAY_HUNGER_PER_SEC, AWAY_HUNGER_MAX_GAIN)
    ceiling = max(hunger, AWAY_HUNGER_CEILING)  # never lowers hunger
    horse.hunger = min(max(0.0, min(hunger + gain, ceiling)), 100.0)
    horse.fed_score = fed * math.pow(0.5, away / FED_HALF_LIFE)
    horse.lonely_time = lonely + min(away * 0.5, AWAY_LONELY_MAX)
    mins = away / 60
    return (f"welcome back after {mins:.0f} min: hunger {hunger:.0f} -> {horse.hunger:.0f}, "
            f"mood {horse.mood}")
