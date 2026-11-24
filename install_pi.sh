#!/usr/bin/env bash
# Set up the horse deck on a Raspberry Pi 4 (Raspberry Pi OS 64-bit, with desktop).
# Run it from the project folder, as your normal user (not with sudo):
#   cd ~/cyberdeck-pet && bash install_pi.sh
# It's safe to run again after copying a new version over.
set -euo pipefail

cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"

if [ "$(id -u)" -eq 0 ]; then
  echo "Run this as your normal user, not with sudo (it asks for sudo itself)." >&2
  exit 1
fi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
  echo "This doesn't look like a Raspberry Pi. On a laptop, just: pip install pygame" >&2
  exit 1
fi

echo "== 1/5  System packages"
sudo apt-get update
sudo apt-get install -y python3-venv python3-dev python3-pygame \
  python3-gpiozero python3-lgpio python3-spidev

echo "== 2/5  Pi settings: SPI on, desktop auto-login, screen blanking off"
sudo raspi-config nonint do_spi 0             # 0 = enable (the LED strip uses SPI)
sudo raspi-config nonint do_boot_behaviour B4 # B4 = boot to desktop, logged in
sudo raspi-config nonint do_blanking 1        # 1 = never blank the screen
# Access to GPIO and SPI without sudo (the default user already has these).
sudo usermod -aG gpio,spi,video,audio "$USER"

echo "== 3/5  Python virtual environment (.venv)"
# --system-site-packages lets the venv use the apt packages above, which are
# prebuilt for the Pi, instead of compiling them with pip.
if [ ! -x .venv/bin/python ]; then
  python3 -m venv --system-site-packages .venv
fi
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

echo "== 4/5  Autostart service"
mkdir -p "$HOME/.config/systemd/user"
sed "s|@PROJECT_DIR@|$PROJECT_DIR|g" horse-deck.service \
  > "$HOME/.config/systemd/user/horse-deck.service"
systemctl --user daemon-reload
systemctl --user enable horse-deck.service

echo "== 5/5  Quick check"
.venv/bin/python - <<'PY'
import importlib
for name in ("pygame", "gpiozero", "board", "neopixel_spi"):
    try:
        importlib.import_module(name)
        print(f"  ok       {name}")
    except Exception as err:
        print(f"  MISSING  {name}: {err}")
PY

cat <<EOF

Done. Reboot to turn SPI on and start the horse:
  sudo reboot

Before trusting autostart, test each part over SSH (no screen needed):
  cd $PROJECT_DIR && .venv/bin/python tools/hwcheck.py all

Service commands:
  systemctl --user start horse-deck     # start now
  systemctl --user stop horse-deck      # stop (saves state, LEDs off)
  systemctl --user restart horse-deck   # after copying a new version
  systemctl --user status horse-deck    # is it running?
  journalctl --user -u horse-deck -f    # live logs (Ctrl+C to leave)
  systemctl --user disable horse-deck   # stop starting it at boot
EOF
