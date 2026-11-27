# Horse Deck

A pixel-art horse in a fenced meadow, seen from above, for a Raspberry Pi 4 with a
5" 800x480 touchscreen. It also runs on a laptop in mock mode, with no Pi hardware.

The build steps and Claude Code prompts are in [PROMPTS.md](PROMPTS.md).

## Install

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install pygame
```

That's all a laptop needs. For the Pi, see [On the Pi](#on-the-pi).

## Horse art

The horse comes from the Horse Sprite Asset Pack by Onfe (see
[assets/CREDITS.md](assets/CREDITS.md)). The converted sprites are in
`assets/horse/`. To rebuild them, or to change the coat:

1. Unzip the pack into `assets/source/` so that
   `assets/source/Full_Pack/Horse_Sprite_Asset/` exists. If macOS `unzip`
   stops with "write error (disk full?)", a few file names in the zip have
   broken characters; extract with a tool that renames them instead.
2. Set `HORSE_COAT` in `config.py` (the coats are listed there).
3. Run `python tools/import_sprites.py`. It prints a table of every animation
   it found.

Without any art, the game draws a simple placeholder horse instead.

## Run

```sh
python main.py               # 800x480 window
python main.py --fullscreen  # full-screen, no mouse cursor (for the Pi)
python main.py --mock        # fake the hardware even on a Pi
python main.py --speed 600   # a whole day in about 2.5 minutes
python main.py --time 20:45  # start at a given time of day
python main.py --no-save     # don't load or save state.json
python tools/preview.py      # every animation, plus a scene with all props
python -m unittest           # run the tests
```

Press Escape to quit.

Mock mode is on automatically on any machine that isn't a Raspberry Pi.

### Feeding

Tap the carrot button in the bottom-right corner (or click it on a laptop).
A treat (carrot, apple or hay) drops near the horse and it walks over:

- **Hunger 40 or more:** it eats, with hearts and sparkles, and hunger drops by 35.
  Sometimes it gallops off happily afterwards.
- **Below 40:** it sniffs the treat and wanders off. The treat stays on the
  ground, and the horse comes back for it once it's hungry.
- At most 3 treats can wait on the ground; the button greys out until one is
  eaten. It bobs gently when the horse would like a treat.

### Test keys (mock mode)

| Key | Does |
|---|---|
| Space | Motion detected: the horse trots to the front to greet you (then a 20 s cooldown, like the real sensor) |
| F | Feed, same as tapping the carrot button |
| N | Jump the clock to just before the next dusk or dawn |
| J | Jump the poles |
| G | Gallop |
| W | Drink at the trough |
| H | +20 hunger, to test hungry behavior quickly |
| D | Show or hide the debug overlay (on by default in mock mode) |

## Hardware

Each hardware module works in mock mode on a laptop and turns itself off with a
warning (instead of crashing) if its library or wiring is missing on the Pi.

| Part | Module | Pi pin (physical) | Mock mode |
|---|---|---|---|
| PIR motion sensor OUT | `sensors.py` (gpiozero) | GPIO17 (pin 11) | Space key |
| PIR VCC / GND | | 5V (pin 2) / GND (pin 6) | |
| LED strip DIN, via 330 ohm | `lights.py` (neopixel_spi) | GPIO10 / SPI MOSI (pin 19) | glowing ring drawn around the window |
| LED strip 5V / GND | | 5V (pin 4) / GND (pin 14) | |
| Speaker | `audio.py` (pygame) | USB sound card | your laptop's speakers |

Settings are in `config.py`:

- `LED_COUNT`: set it to the number of LEDs you actually cut (default 42).
- `LED_BRIGHTNESS`: 0.2 by default. The strip runs off the Pi's 5V pin, so
  keep it low.
- `LED_PIXEL_ORDER`: "GRB", the color order of the SEZO strip.
- `MOTION_COOLDOWN`: after motion, the horse ignores the sensor for 20 seconds.
- `SOUND_VOLUME`, `AMBIENT_VOLUME`.

To test each part on its own (over SSH, no screen needed):
`python tools/hwcheck.py pir`, `leds` or `sound`.

The LED strip uses SPI, so SPI must be on (`sudo raspi-config` → Interface
Options → SPI). LED 0 is the strip's input end; the effects assume it starts
at the top center, behind the PIR, and runs clockwise as seen from the front.

### Lights

Warm amber by day (breathing slowly), deep blue-purple at night, a neon pink
pulse spreading out from the top when motion is seen, and green sparkles while
the horse eats. The strip is switched off when the program exits.

### Sounds

A whinny when the horse greets you (louder when startled), munching while it
eats, a sniff, and quiet field sounds: a breeze and birds by day, crickets at
night. All are generated in code the first time the game runs and cached in
`.cache/sounds/`. To use your own, put files with these names in
`assets/sounds/` (`.wav` or `.ogg`); they replace the generated ones:

`whinny`, `munch`, `sniff`, `ambient_day`, `ambient_night`

`munch` and the two ambient sounds loop, so trim them to loop cleanly. Don't
use copyrighted audio.

The ambient sound switches from day to night with the clock.

## On the Pi

For a Raspberry Pi 4 running Raspberry Pi OS (64-bit, with desktop). In
Raspberry Pi Imager's settings, set Wi-Fi, a hostname (say `horsedeck`), a
username, and turn on SSH.

**1. Copy the project over** from your laptop (rsync skips `.venv`, `.git` and
the Pi's `state.json`):

```sh
./deploy.sh <user>@horsedeck.local
```

or by hand:

```sh
rsync -av --exclude .git/ --exclude .venv/ --exclude __pycache__/ \
  --exclude .cache/ --exclude assets/source/ --exclude state.json \
  ./ <user>@horsedeck.local:~/cyberdeck-pet/
```

**2. Install, once,** over SSH:

```sh
ssh <user>@horsedeck.local
cd ~/cyberdeck-pet && bash install_pi.sh
sudo reboot
```

`install_pi.sh` installs pygame, gpiozero, lgpio and spidev from apt, makes a
`.venv` that can see them (`--system-site-packages`) and pip-installs the
Adafruit LED library into it. It turns on SPI, desktop auto-login and "never
blank the screen", then installs and enables the `horse-deck` user service.

**3. Test each part** before relying on autostart:

```sh
cd ~/cyberdeck-pet
.venv/bin/python tools/hwcheck.py all
```

After the reboot the horse starts full-screen by itself once the desktop is
up. Escape quits to the desktop; a crash restarts it after 3 seconds.

**Updating:** run `./deploy.sh <user>@horsedeck.local` again. It copies the
changes and restarts the service.

### Service commands (over SSH)

```sh
systemctl --user start horse-deck     # start now
systemctl --user stop horse-deck      # stop (saves state, LEDs off)
systemctl --user restart horse-deck   # after copying a new version
systemctl --user status horse-deck    # is it running?
journalctl --user -u horse-deck -f    # live logs (Ctrl+C to leave)
systemctl --user disable horse-deck   # stop starting it at boot
```

The service lives in `~/.config/systemd/user/horse-deck.service`, made from
`horse-deck.service` in this folder. It waits for the desktop's display, runs
`.venv/bin/python main.py --fullscreen` (no cursor), and needs desktop
auto-login, since a user service only runs while you're logged in.

## Troubleshooting

Check power, wiring and the screen's settings first. Logs:
`journalctl --user -u horse-deck -b`. The game also prints a line at startup
when a hardware part turns itself off (`[sensors] ...`, `[lights] ...`).

**Lightning-bolt icon, random reboots, flicker (under-voltage).**
`vcgencmd get_throttled` should print `throttled=0x0`; anything else means the
power dipped at some point. Use a 5V/3A supply and a short, thick USB-C cable.
The screen and LED strip both draw from the Pi, so keep `LED_BRIGHTNESS` low.

**Wrong resolution or a black screen.** Use the micro-HDMI port nearest the
USB-C power port. If the picture is the wrong size, add this to the end of the
single line in `/boot/firmware/cmdline.txt` (space-separated) and reboot:
`video=HDMI-A-1:800x480M@60D`

**Screen rotated.** Fix it in Preferences → Screen Configuration (right-click
the screen → Orientation). The game always draws 800x480 landscape.

**Touch is offset or goes the wrong way** (usually after rotating). Make sure
the screen's USB cable is plugged in, then map touch to the HDMI screen: in
`~/.config/labwc/rc.xml`, inside `<openbox_config>`, add
`<touch deviceName="..." mapToOutput="HDMI-A-1" />`, with the touch device's
name from `libinput list-devices`. Log out and back in.

**The service doesn't start.** `systemctl --user status horse-deck`. "Failed
at step EXEC" means `.venv` is missing: run `install_pi.sh`. If
ExecStartPre timed out, desktop auto-login is off: `sudo raspi-config` →
System Options → Boot / Auto Login → Desktop Autologin.

**No sound.** Right-click the speaker icon on the desktop's top bar and pick
the USB sound card, or over SSH: `wpctl status`, then
`wpctl set-default <id of the USB sink>`. Test with
`.venv/bin/python tools/hwcheck.py sound`. The speaker goes in the card's
headphone jack, not the mic jack.

**PIR triggers constantly or never.** Give it about a minute after power-up to
settle. Turn the time dial fully counterclockwise (shortest hold) and lower the
sensitivity dial. HC-SR501s also misfire next to heat and radio noise, so keep
the dome away from the Pi's Wi-Fi antenna and the LED strip's wires. Watch it
with `.venv/bin/python tools/hwcheck.py pir`.

**LEDs flicker, stay dark or show wrong colors.**
- Dark: SPI must be on (`ls /dev/spidev*` should list a device; reboot after
  `install_pi.sh`), and the data wire must go to the strip's input end.
- Wrong colors everywhere (red and green swapped): change `LED_PIXEL_ORDER`.
- Flicker or a few random colors: check the shared ground, the 330 ohm
  resistor and keep the data wire short. If it continues, add
  `core_freq_min=500` to `/boot/firmware/config.txt` (the SPI clock follows
  the CPU core clock on a Pi 4), and then the optional 74AHCT125 level
  shifter.
- Effects starting from the wrong place: LED 0 belongs at top center behind
  the PIR, running clockwise seen from the front.

## Day and night

The meadow follows the real time of day (`daynight.py`): a soft pink dawn
around 5:30 to 7:30, clear day, a warm sunset from about 18:30, and a blue
night with fireflies from about 20:45. The LED strip and the sounds follow
along. The horse goes to sleep at 21:00 (once it finishes what it's doing) and
wakes at 6:30; asleep, it gets hungry at half speed. It still responds at
night: walking by or dropping a treat wakes it gently (no rearing), it comes
over or eats, stands about sleepily for 20 seconds (`STAY_UP` in `horse.py`),
then dozes off again. Change `BEDTIME` and `WAKE_UP` in `daynight.py`.

The Pi has no clock battery, so it gets the time from the internet after it
boots. At normal speed the game reads the clock fresh every frame, so it
corrects itself as soon as the Pi does.

## Mood and memory

The horse's mood is **happy**, **calm** or **lonely**:

- **happy:** it has eaten about 2 treats in the last few hours. It fidgets
  more, jumps and gallops more often, and now and then a heart floats up.
- **lonely:** nobody has walked past for 3 waking hours. It stands longer,
  looks out toward the room, and plays less. Any motion cheers it up.
- **calm:** everything else.

`save.py` keeps hunger and mood in `state.json`: every minute, and when the
program exits. If the deck was off for a while, the horse comes back hungrier,
but by at most 40 and never past 80 from the time away alone, so it's hungry
but never in trouble. Saves are written to a temporary file first and then
swapped in, so pulling the plug can't damage the file. Delete `state.json` to
start fresh.

## The horse

`horse.py` is a state machine. Idle is the home state; every other state
returns to idle when it ends (sleep waits to be woken).

| State | What happens |
|---|---|
| idle | Stands and swishes its tail for 3 to 6 seconds, then picks what to do |
| walk | Strolls to a spot inside the fence, around the props |
| graze | Head down eating grass for 4 to 8 seconds; hunger drops a little |
| drink | Walks to the trough and drinks for 4 to 7 seconds |
| jump | Walks to the near side of the poles and jumps over them |
| gallop | A rare happy dash with dust puffs, often right after a treat |
| trot | Trots to the front (bottom of the screen) and looks at you |
| startled | Rears up when motion comes after 5 quiet minutes, then trots over |
| eat | Eats a treat for 4 seconds with hearts; hunger drops by 35 |
| sniff | Not hungry enough: sniffs the treat, then wanders off |
| sleep | Dozes with drifting z's from bedtime until dawn; motion or a treat wakes it briefly |

Hunger goes from 0 to 100 over about 4 hours. At 70 or more the horse is
hungry: it grazes about three times as often, wanders near the front, faces
you when it stops, and doesn't jump or gallop.

### Using your own art

`sprites.py` loads PNG strips from `assets/horse/`:

```
assets/horse/<animation>_<direction>.png
```

- Frames sit side by side in one horizontal strip, all the same size.
- `assets/horse/frames.json` gives each strip's frame count and speed:
  `{"walk_right": {"frames": 9, "fps": 10}}`. Strips not listed there use the
  counts in `ANIMATIONS` in `sprites.py`.
- Draw at game size (the 266x160 world), not screen size.
- The horse's feet touch the bottom edge of each frame, centered.
- A missing `_left` strip is made by mirroring `_right`. graze, eat, drink and
  sleep only need left and right.
- Anything missing falls back to a drawn placeholder or a similar animation.

## How it draws

The game draws at 266x160 and scales up 3x with nearest-neighbor, so pixels stay
chunky and the horse is 171 pixels long on screen. 266x3 is 798, so there's a
1-pixel border on each side of the 800-pixel screen. All positions in the code
use the 266x160 coordinates. The horse walks around props using a small
path-finder (`find_path` in `world.py`). Props and the
horse are drawn in order of how far down the screen they stand, so the horse
can walk in front of or behind things, and under the tree tops.

| File | Job |
|---|---|
| `main.py` | 30 fps game loop, command-line flags, debug overlay |
| `game.py` | Ties the world, horse and buttons together; feeding |
| `controls.py` | All input: taps, clicks and test keys |
| `hud.py` | The carrot button |
| `sensors.py` | PIR motion sensor, with cooldown |
| `lights.py` | LED strip colors and effects |
| `audio.py` | Generated sounds and playback |
| `daynight.py` | Clock, sky colors, fireflies, bedtime |
| `save.py` | Saving and loading `state.json` |
| `tests/` | Tests for the horse, saving, feeding and day/night |
| `config.py` | Screen size, FPS, mock-mode switch, horse coat |
| `world.py` | Meadow layout, background, props, effects |
| `sprites_world.py` | Pixel art for everything except the horse |
| `palette.py` | All world colors |
| `horse.py` | The horse's states, movement and hunger |
| `sprites.py` | Loads horse art, or draws placeholder frames |
| `tools/import_sprites.py` | Converts the Onfe pack into `assets/horse/` |
| `tools/preview.py` | Shows every animation and prop |
