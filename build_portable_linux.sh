#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install --upgrade pyinstaller
rm -rf build dist

pyinstaller --noconfirm --clean --onefile --name "BorodachambaMusic_v1_0" borodachamba_player.py

echo "Portable build ready: dist/BorodachambaMusic_v1_0"
