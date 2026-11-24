"""Test each piece of hardware on its own, before the game and the screen.

Run on the Pi (over SSH is fine; no screen needed), from the project folder:
  python tools/hwcheck.py pir      # prints MOTION / clear as the sensor changes
  python tools/hwcheck.py leds     # walks one LED along the strip, then R, G, B
  python tools/hwcheck.py sound    # plays the whinny and a few seconds of birds
  python tools/hwcheck.py all

Ctrl+C stops any test. The LEDs are switched off when a test ends.
"""

import argparse
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")  # no window needed
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402


def check_pir(seconds: float) -> None:
    try:
        from gpiozero import MotionSensor
    except ImportError:
        sys.exit("gpiozero isn't installed: sudo apt install python3-gpiozero")
    pir = MotionSensor(config.PIR_PIN)
    print(f"PIR on GPIO{config.PIR_PIN}. The sensor needs about a minute to settle "
          "after power-up, so ignore the first triggers.")
    print(f"Wave a hand in front of it. Watching for {seconds:.0f} s (Ctrl+C to stop).")
    last, since, start = None, time.monotonic(), time.monotonic()
    try:
        while time.monotonic() - start < seconds:
            high = bool(pir.motion_detected)
            if high != last:
                now = time.monotonic()
                held = f"  (previous state lasted {now - since:.1f} s)" if last is not None else ""
                print(f"{time.strftime('%H:%M:%S')}  {'MOTION' if high else 'clear '}{held}")
                last, since = high, now
            time.sleep(0.05)
    finally:
        pir.close()
    print("Tip: the 'clear' gap after motion is the sensor's own hold time "
          "(the Tx knob). Turn it fully anticlockwise for the shortest one.")


def check_leds(count: int) -> None:
    try:
        import board
        import neopixel_spi
    except ImportError:
        sys.exit("LED library missing: pip install adafruit-circuitpython-neopixel-spi\n"
                 "(and turn on SPI: sudo raspi-config -> Interface Options -> SPI)")
    strip = neopixel_spi.NeoPixel_SPI(board.SPI(), count, brightness=config.LED_BRIGHTNESS,
                                      pixel_order=config.LED_PIXEL_ORDER, auto_write=False)
    try:
        print(f"{count} LEDs, order {config.LED_PIXEL_ORDER}, brightness {config.LED_BRIGHTNESS}.")
        print("1) One white LED walks from LED 0 (the input end) to the last one.")
        print("   Every LED should light in turn. If it stops early, check the")
        print("   solder joints at that spot. If LEDs past the end stay dark, good.")
        for i in range(count):
            strip.fill((0, 0, 0))
            strip[i] = (255, 255, 255)
            strip.show()
            time.sleep(0.08)
        for name, color in (("RED", (255, 0, 0)), ("GREEN", (0, 255, 0)), ("BLUE", (0, 0, 255))):
            print(f"2) Whole strip {name} for 2 s.")
            strip.fill(color)
            strip.show()
            time.sleep(2)
        print("If red and green came out swapped, LED_PIXEL_ORDER in config.py is wrong.")
    finally:
        strip.fill((0, 0, 0))
        strip.show()


def check_sound() -> None:
    import pygame
    from audio import Audio
    pygame.init()
    audio = Audio()
    print(f"Sound: {audio.status}")
    if not audio.enabled:
        sys.exit("No sound device. See 'No sound' in the README troubleshooting.")
    print("Whinny...")
    audio.whinny(loud=True)
    time.sleep(1.8)
    print("Birds and breeze for 4 s...")
    audio.update()
    time.sleep(4)
    audio.close()
    print("Heard nothing? The sound is probably going to HDMI instead of the USB card.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Test the Horse Deck hardware.")
    parser.add_argument("part", choices=["pir", "leds", "sound", "all"])
    parser.add_argument("--count", type=int, default=config.LED_COUNT,
                        help="LEDs on the strip (default: LED_COUNT in config.py)")
    parser.add_argument("--seconds", type=float, default=60, help="how long to watch the PIR")
    args = parser.parse_args()
    try:
        if args.part in ("leds", "all"):
            check_leds(args.count)
        if args.part in ("sound", "all"):
            check_sound()
        if args.part in ("pir", "all"):
            check_pir(args.seconds)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
