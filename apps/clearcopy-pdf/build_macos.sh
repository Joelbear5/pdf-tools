#!/bin/sh
set -eu

if [ "$(uname -s)" != "Darwin" ]; then
    echo "Build the macOS app on a Mac." >&2
    exit 1
fi

if [ "$(uname -m)" != "arm64" ]; then
    echo "Build the Apple Silicon app on an Apple Silicon Mac." >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

python3.14 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --clean --windowed --name "ClearCopy PDF" --target-architecture arm64 --osx-bundle-identifier org.example.clearcopypdf --icon assets/clearcopy_icon.icns --add-data "assets/clearcopy_icon.png:assets" pdf_copy_app.py