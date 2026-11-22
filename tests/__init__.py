"""Tests. Run from the project folder:  python -m unittest

They run headless: no window, no sound, no Pi hardware.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
