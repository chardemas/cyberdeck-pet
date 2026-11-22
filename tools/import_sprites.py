"""Convert the Onfe Horse Sprite pack into sprite strips for the game.

Reads the horse-only sheets (rider and leading-character files are ignored):
  assets/source/Full_Pack/Horse_Sprite_Asset/Horses_no_equipment/Horse_<coat>.png
  assets/source/Full_Pack/Horse_Sprite_Asset/Horses_Jump/Horses_no_equipment/Horse_<coat>_jump.png
  assets/source/Full_Pack/Horse_Sprite_Asset/Horses_Rearing/Horses_no_equipment/Horse_<coat>_rearing.png

Writes:
  assets/horse/<animation>_<direction>.png   one horizontal strip per file
  assets/horse/frames.json                   frame count and speed per strip

Run from the project folder:
  python tools/import_sprites.py                 # uses HORSE_COAT from config.py
  python tools/import_sprites.py --coat paint_black
"""

import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

import config  # noqa: E402

PACK = ROOT / "assets" / "source" / "Full_Pack" / "Horse_Sprite_Asset"
OUT = ROOT / "assets" / "horse"

# Each sheet is a grid. Rows are listed as (animation, direction).
# Found by inspecting the pack: the main sheet is 9 columns of 80x64 cells,
# the jump sheet 16 columns of 80x82, the rearing sheet 12 columns of 88x66.
SHEETS = {
    "main": {
        "file": "Horses_no_equipment/Horse_{coat}.png",
        "cell": (80, 64),
        "rows": [
            ("idle", "right"), ("graze", "right"), ("walk", "right"),
            ("trot", "right"), ("gallop", "right"),
            ("idle", "left"), ("graze", "left"), ("walk", "left"),
            ("trot", "left"), ("gallop", "left"),
            ("idle", "down"), ("walk", "down"), ("trot", "down"), ("gallop", "down"),
            ("idle", "up"), ("walk", "up"), ("trot", "up"), ("gallop", "up"),
        ],
    },
    "jump": {
        "file": "Horses_Jump/Horses_no_equipment/Horse_{coat}_jump.png",
        "cell": (80, 82),
        "rows": [("jump", "right"), ("jump", "left"), ("jump", "down"), ("jump", "up")],
    },
    "rearing": {
        "file": "Horses_Rearing/Horses_no_equipment/Horse_{coat}_rearing.png",
        "cell": (88, 66),
        "rows": [("rear", "right"), ("rear", "left"), ("rear", "down"), ("rear", "up")],
    },
}

# Playback speed in frames per second. Strips not listed use 10.
FPS = {
    "idle": 6, "idle_down": 1.5, "idle_up": 1,
    "walk": 10, "trot": 12, "gallop": 12,
    "graze": 5, "eat": 7, "drink": 4,
    "jump": 16, "rear": 10, "sleep": 1,
}

MIN_FRAME_WIDTH = 6  # cells with less than this are stray pixels, not frames


def find_file(pattern: str, coat: str) -> Path:
    """Case-insensitive lookup; the pack spells black as 'back' in rearing files."""
    candidates = [coat, coat.replace("black", "back")]
    for c in candidates:
        wanted = (PACK / pattern.format(coat=c))
        if wanted.parent.exists():
            for f in wanted.parent.iterdir():
                if f.name.lower() == wanted.name.lower():
                    return f
    sys.exit(f"Missing sheet for coat '{coat}': {PACK / pattern.format(coat=coat)}")


def cut_row(sheet: pygame.Surface, cell: tuple[int, int], row: int) -> list:
    cw, ch = cell
    frames = []
    for col in range(sheet.get_width() // cw):
        frame = sheet.subsurface((col * cw, row * ch, cw, ch)).copy()
        if frame.get_bounding_rect().w >= MIN_FRAME_WIDTH:
            frames.append(frame)
    return frames


def center_strip(frames: list) -> list:
    """Shift a strip so the horse's body is centered in the frame.

    The game anchors frames at bottom-center, so this keeps the horse from
    jumping sideways when it switches between sheets with different cell sizes.
    """
    box = frames[0].get_bounding_rect()
    shift = round(frames[0].get_width() / 2 - box.centerx)
    if shift == 0:
        return frames
    w, h = frames[0].get_size()
    out = []
    for f in frames:
        wide = pygame.Surface((w + 2 * abs(shift), h), pygame.SRCALPHA)
        wide.blit(f, (abs(shift) + shift, 0))
        out.append(wide)
    return out


def scale(frames: list, factor: int) -> list:
    if factor == 1:
        return frames
    return [pygame.transform.scale_by(f, factor) for f in frames]  # nearest-neighbor


def darken(frame: pygame.Surface) -> pygame.Surface:
    dark = frame.copy()
    dark.fill((205, 205, 220, 255), special_flags=pygame.BLEND_RGBA_MULT)  # night darkens it more
    return dark


def save_strip(frames: list, path: Path) -> None:
    w, h = frames[0].get_size()
    strip = pygame.Surface((w * len(frames), h), pygame.SRCALPHA)
    for i, f in enumerate(frames):
        strip.blit(f, (i * w, 0))
    pygame.image.save(strip, str(path))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--coat", default=config.HORSE_COAT)
    args = parser.parse_args()
    if not PACK.exists():
        sys.exit(f"Pack not found. Unzip it so this folder exists:\n  {PACK}")
    if not isinstance(config.HORSE_SCALE, int) or config.HORSE_SCALE < 1:
        sys.exit("HORSE_SCALE in config.py must be a whole number, 1 or more.")

    pygame.init()
    pygame.display.set_mode((1, 1))
    strips: dict[tuple[str, str], list] = {}
    sources: dict[tuple[str, str], str] = {}

    for name, sheet_info in SHEETS.items():
        path = find_file(sheet_info["file"], args.coat)
        sheet = pygame.image.load(str(path)).convert_alpha()
        for row, key in enumerate(sheet_info["rows"]):
            frames = cut_row(sheet, sheet_info["cell"], row)
            if not frames:
                sys.exit(f"{path.name} row {row} ({key}) has no frames; layout changed?")
            strips[key] = scale(center_strip(frames), config.HORSE_SCALE)
            sources[key] = f"{name} sheet, row {row}"

    # Animations the pack doesn't have, built from existing frames.
    for d in ("left", "right"):
        strips[("eat", d)] = strips[("graze", d)]
        sources[("eat", d)] = "graze frames"
        strips[("drink", d)] = strips[("graze", d)]
        sources[("drink", d)] = "graze frames"
        strips[("sleep", d)] = [darken(strips[("idle", d)][0])]
        sources[("sleep", d)] = "idle frame 1, darkened (z's drawn in game)"

    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.png"):
        old.unlink()
    manifest = {}
    for (anim, d), frames in sorted(strips.items()):
        save_strip(frames, OUT / f"{anim}_{d}.png")
        key = f"{anim}_{d}"
        manifest[key] = {"frames": len(frames),
                         "fps": FPS.get(key, FPS.get(anim, 10))}
    (OUT / "frames.json").write_text(json.dumps(manifest, indent=2) + "\n")

    # Report.
    order = ["idle", "walk", "trot", "gallop", "graze", "eat", "drink",
             "jump", "rear", "sleep"]
    print(f"Coat: {args.coat}   scale: {config.HORSE_SCALE}x   output: {OUT.relative_to(ROOT)}/\n")
    print(f"{'animation':<10}{'direction':<11}{'frame size':<12}{'frames':<8}source")
    for anim in order:
        for d in ("right", "left", "down", "up"):
            if (anim, d) in strips:
                fr = strips[(anim, d)]
                size = f"{fr[0].get_width()}x{fr[0].get_height()}"
                print(f"{anim:<10}{d:<11}{size:<12}{len(fr):<8}{sources[(anim, d)]}")
    side = strips[("idle", "right")][0].get_bounding_rect()
    print(f"\nHorse size (idle, side view): {side.w}x{side.h} game pixels, "
          f"{side.w * config.SCALE}x{side.h * config.SCALE} on screen.")
    print("View: side-on for left/right, front and back for down/up, so the "
          "four-direction top-down meadow fits.")


if __name__ == "__main__":
    main()
