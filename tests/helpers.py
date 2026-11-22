import random

import config
import daynight
from game import Game

DT = 1 / 30


def noon_game(seed: int = 1, hour: float = 12.0) -> Game:
    """A game at a fixed time of day, no sound, no saving, mock hardware."""
    config.MOCK = True
    return Game(random.Random(seed), hardware=False,
                clock=daynight.GameClock(speed=0, start_hour=hour))


def run(game: Game, seconds: float, until=None) -> bool:
    """Advance the game. Returns True as soon as `until(game)` is true."""
    for _ in range(int(seconds * 30)):
        game.update(DT)
        if until and until(game):
            return True
    return False
