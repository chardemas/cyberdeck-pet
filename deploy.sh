#!/usr/bin/env bash
# Copy the project from your laptop to the Pi, then restart the horse if the
# autostart service is installed.
#   ./deploy.sh <user>@<hostname>.local
# Example: ./deploy.sh charlotte@horsedeck.local
set -euo pipefail

TARGET="${1:?usage: ./deploy.sh <user>@<hostname>.local}"
cd "$(dirname "$0")"

# state.json stays on the Pi (it's the horse's memory), and .venv is built
# there by install_pi.sh, so neither is copied.
rsync -av \
  --exclude .git/ --exclude .venv/ --exclude __pycache__/ --exclude .cache/ \
  --exclude assets/source/ --exclude state.json --exclude state.tmp \
  --exclude .DS_Store \
  ./ "$TARGET:~/cyberdeck-pet/"

ssh "$TARGET" 'systemctl --user is-enabled horse-deck >/dev/null 2>&1 \
  && systemctl --user restart horse-deck && echo "restarted horse-deck" \
  || echo "copied; run: cd ~/cyberdeck-pet && bash install_pi.sh"'
