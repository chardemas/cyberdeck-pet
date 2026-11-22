# Horse Deck: Claude Code prompts (corrected)

Corrected version of the prompts in *Horse Cyberdeck: Full Build Guide* (Nov 21, 2026).
Give them to Claude Code one at a time, in order, and run the result after each.
Each prompt assumes the earlier ones are done. The project lives in this folder (`cyberdeck-pet`).

Fixes compared with the PDF:
- Prompt order: the sprite import now comes after the horse exists, so no prompt edits files that don't exist yet.
- One camera view: a top-down meadow, matching the four-direction Onfe horse pack.
- One motion key: spacebar fakes motion everywhere (F feeds, D toggles the debug overlay).
- LED count is a setting (`LED_COUNT`, default 42 for a 6x8" frame), not a hard-coded 30. Color order is set to GRB to match the strip I bought (WS2812B ECO, 60 LEDs/m).
- Horse size is given at the internal resolution, so it matches the 2x pixel scaling.

---

## Prompt 1: project setup and the meadow

```
Create a Python project in this folder using pygame. It is a pixel-art digital
pet: a horse in a fenced meadow seen from above (top-down), shown on an 800x480
screen.

Requirements:
- Window is 800x480. A command-line flag --fullscreen switches to full-screen, no
mouse cursor.
- config.py holds screen size, FPS (30), and a MOCK flag. MOCK is true by default on
non-Raspberry-Pi machines and can be forced with --mock.
- Render at a small internal resolution of 400x240 and scale it up 2x with
nearest-neighbor so the pixels look chunky. All positions and sizes in game code
use the 400x240 internal coordinates.
- world.py draws a simple top-down meadow: grass filling the screen and a wooden
fence around the edge. Draw it from code. All art must be original. Leave room for
day and night as a color overlay later (no sky; the view is top-down).
- main.py runs a 30 fps loop, handles quit with Escape, and shows a placeholder
rectangle for the horse so I can see the layout.
- Add a README with how to install (pip install pygame) and run it.
Keep the code small and readable. Run it to check it opens.
```

## Prompt 2: horse behavior

```
Add the horse to the project.

- sprites.py loads sprite sheets from assets/horse/ and animates them. Sheets are
per animation and per direction (up, down, left, right). If real art files are
missing, generate simple original placeholder frames in code so the game still
runs. Document the expected file names and frame counts in the README so I can
drop in my own sheets later.
- horse.py implements a state machine with these states: idle, walk, graze, trot
(greeting), eat, sleep.
- idle is the home state. From idle the horse randomly picks walk or graze after a
few seconds. Every other state returns to idle when it finishes.
- The horse walks around the meadow in 2D (any direction), staying inside the
fence. It faces up, down, left or right based on its movement and uses the
matching direction's frames.
- "Toward me" means toward the bottom of the screen (the side facing the room).
- Add hunger (0 to 100, rises slowly). When hunger is high, the horse grazes more and
comes toward the bottom of the screen.
- Add keyboard test keys in mock mode: Space = motion detected, F = feed. Both are
described on screen in a small debug overlay that I can toggle with D.
Keep states separate and easy to extend. Run it and confirm the horse moves.
```

## Prompt 3: import the horse pack and draw the props

Uses the free Horse Sprite pack by Onfe. Download it, check the license on its page, and unzip it into `assets/source/`. Use the horse-only file if one is offered.

```
I downloaded the Horse Sprite pack by Onfe into assets/source/. Inspect the files,
then build tools/import_sprites.py that converts the horse into sprite sheets in
assets/horse/, using the file names and layout sprites.py already expects. Ignore
any rider or leading-character files.

Horse pack:
- Print a table of every horse animation you find: name, direction (up, down, left,
right), frame size and frame count. The pack should have idle with blinking, walk,
trot, gallop, jump, rearing and grazing (left and right only), in several coat
colors.
- Confirm the view is top-down / three-quarter with four directions. If it turns
out to be side-on only, stop and tell me before changing anything.
- Default to the brown coat and make the coat a setting in config.py.
- Map animations to game states: idle to idle, walk to walk, grazing to graze (turn
to face left or right first), trot to trot (greeting me), rearing to a startled
reaction when motion is detected suddenly, jump to jump (hops over the jump poles),
gallop to gallop (rare, when excited or after a treat).
- If an animation is missing (eat, drink, sleep), build it from existing frames: eat
and drink reuse graze, and sleep uses a darkened idle frame with a small z icon.
- Scale frames with nearest-neighbor only, by a whole-number factor, so the horse is
roughly 50 to 70 pixels long at the 400x240 internal resolution (100 to 140 on the
800x480 screen).

Everything else is drawn in code as original pixel art. Sample the horse's colors for
the palette and keep it in palette.py, using 3 to 4 shaded tones per surface:
- Grass: several tileable tile variants, tufts, small flowers and worn dirt patches.
- The wooden fence around the field edge with straight pieces, corners and a gate.
- A water trough with a small animated ripple, and a puddle.
- Food: a hay pile, a carrot, an apple, a hay bale and a feed bucket.
- A pole jump (two posts and a rail) placed in the field.
- A few trees or bushes at the field edge, and a soft shadow under the horse.
- Effects: hearts, sparkles and dust puffs when galloping.
Put the drawing code in sprites_world.py and use it from world.py.

Also:
- Write tools/preview.py that shows every animation looping at 8 fps, plus a scene
preview with all the props, so I can check the look.
- Add drink, jump, gallop and startled states to horse.py (drink at the trough, jump
over the poles when idle or excited), and update sprites.py for the new sheets.
Keep states separate and easy to extend.
- Create assets/CREDITS.md with the pack name, author, link and license, and leave
the license text for me to fill in.
```

## Prompt 4: touch feeding

```
Add feeding by touch.

- Show a small food icon (a carrot or hay bundle from sprites_world.py) in the
bottom-right corner of the screen.
- Tapping or clicking the icon drops a treat on the ground near the horse. The horse
walks to it, enters the eat state, and hunger drops.
- Treat drop works with the mouse on my laptop and with a touchscreen on the Pi
(pygame sends both as mouse events). Convert screen coordinates to the 400x240
internal coordinates.
- Limit feeding so it only works when hunger is above a threshold. Otherwise the
horse sniffs the treat and walks away.
- Add small hearts or sparkles when the horse eats.
- The F key in mock mode does the same as tapping the icon.
Keep input handling in one place so I can change it later.
```

## Prompt 5: motion, glow and sound (with mock mode)

```
Add hardware modules. Each must work in mock mode on a laptop with no hardware.

- sensors.py: a PIR motion sensor on GPIO17 using gpiozero MotionSensor. In mock
mode, the spacebar triggers motion (the same key the debug overlay already lists).
When motion is detected, the horse enters the trot state and trots toward the
bottom of the screen, then returns to idle. Add a cooldown of about 20 seconds so
it does not retrigger constantly.
- lights.py: a WS2812B strip on SPI (GPIO10), using
adafruit-circuitpython-neopixel-spi. The number of LEDs is LED_COUNT in config.py,
default 42 (a 6x8 inch frame perimeter on a 60 LED/m strip), with a comment telling
me to set it to the number of LEDs I actually cut. My strip's color order is GRB
(not RGB): put LED_PIXEL_ORDER = "GRB" in config.py and pass it as pixel_order
when creating the strip. Brightness must stay low (about
0.2) by default and be set in config.py. Colors: warm amber by day, deep
blue-purple at night, a pulse of neon pink when motion is detected, green flicker
when eating. In mock mode, draw a glow bar around the screen edge instead.
- audio.py: uses pygame.mixer. Play a soft whinny when the horse greets me, a
munching loop while eating, and quiet ambient field sounds. If sound files are
missing, skip silently. Describe in the README where to put the files in
assets/sounds/. Do not use copyrighted audio.
- All hardware imports must be guarded so the project still runs on a laptop without
gpiozero or neopixel libraries installed.
Explain any pins I must double-check against my wiring.
```

## Prompt 6: day and night, memory and polish

```
Polish the project.

- Day and night follow the real clock. Shift a color overlay on the meadow smoothly
through dawn (soft pink), day (warm, near clear), dusk (orange) and night (deep
blue, with a few fireflies). At night the horse goes to sleep and lights dim. At
dawn it wakes up.
- save.py stores hunger, mood and last-seen time in state.json. If the program was
off, apply a gentle hunger increase for the time away (cap it) so the horse is hungry
but not in trouble.
- Add a mood value (happy, calm, lonely) that changes with how often I fed it and how
long since motion was seen. Mood affects idle animations, not anything dramatic.
- Add a --speed flag that fast-forwards the clock so I can test day and night
quickly.
- Add simple tests for the state machine and the save file.
Keep everything fast enough for a Raspberry Pi 4 at 30 fps.
```

## Prompt 7: put it on the Pi and start on boot

```
Prepare the project for a Raspberry Pi 4 running Raspberry Pi OS (64-bit with
desktop), with an 800x480 HDMI touchscreen.

- Write a requirements.txt (pygame, gpiozero, adafruit-circuitpython-neopixel-spi,
and any others you need).
- Write install_pi.sh that installs dependencies, enables SPI, and creates a Python
virtual environment.
- Create a systemd user service (horse-deck.service) that starts the game full-screen
at boot after the desktop session is ready, restarts it if it crashes, and hides the
mouse cursor. Include exact commands to enable, start, stop and view logs.
- Add a README section called Troubleshooting that covers: screen rotation or wrong
resolution, touch offset, no sound, PIR false triggers, LED flicker or wrong colors,
and under-voltage warnings.
- Provide the commands I run over SSH to copy the project from my laptop to the Pi
with rsync.
```
