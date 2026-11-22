"""Settings for the horse deck. Everything tunable lives here."""

from pathlib import Path

# Real screen size (the 5" HDMI touchscreen).
SCREEN_W, SCREEN_H = 800, 480

# The game draws at this small size, then scales up 3x with nearest-neighbor
# so the pixels look chunky. All game positions use these coordinates.
# 800 isn't divisible by 3, so 266x3 = 798 leaves a 1-pixel border each side.
INTERNAL_W, INTERNAL_H = 266, 160
SCALE = 3

FPS = 30

# Horse art from the Onfe pack (run tools/import_sprites.py after changing).
# Coats: fullcolor_brown, fullcolor_black, fullcolor_white, paint_brown,
# paint_black, paint_beige, socks_brown, socks_black, socks_beige.
HORSE_COAT = "fullcolor_brown"
HORSE_SCALE = 1  # whole numbers only; 1 makes the horse 57 px long (171 on screen)


def _is_raspberry_pi() -> bool:
    model = Path("/proc/device-tree/model")
    try:
        return "Raspberry Pi" in model.read_text(errors="ignore")
    except OSError:
        return False


# ---- Hardware (see the README's wiring table before changing pins) ----

# PIR motion sensor: OUT pin on GPIO17 = physical pin 11.
PIR_PIN = 17
MOTION_COOLDOWN = 20        # seconds before motion can trigger the horse again

# WS2812B LED strip on SPI: DIN on GPIO10 (MOSI) = physical pin 19.
LED_COUNT = 42              # SET THIS to the number of LEDs you actually cut.
                            # 42 fits a 6x8" frame on a 60 LED/m strip.
LED_BRIGHTNESS = 0.2        # 0 to 1. Keep it low: the Pi's 5V pin powers the strip.
LED_PIXEL_ORDER = "GRB"     # your strip's color order (the SEZO strip is GRB)

# Where the horse's hunger and mood are saved between runs.
STATE_FILE = Path(__file__).parent / "state.json"

# Sound.
SOUND_VOLUME = 0.6          # 0 to 1, master volume
AMBIENT_VOLUME = 0.25       # field sounds, relative to the master volume

# Mock mode fakes the hardware (motion sensor, LEDs) so the game runs on a
# laptop. On by default anywhere that isn't a Pi; force it with --mock.
MOCK = not _is_raspberry_pi()
