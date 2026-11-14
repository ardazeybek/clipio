#!/bin/sh
# One-line Linux install:  curl -fsSL https://github.com/ardazeybek/clipio/releases/latest/download/install.sh | sh
# Downloads the latest Clipio setup file and opens its setup window (or installs silently without a display).
set -e
URL="https://github.com/ardazeybek/clipio/releases/latest/download/Clipio-Setup-Linux"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "Downloading Clipio…"
if command -v curl >/dev/null 2>&1; then curl -fL --progress-bar -o "$TMP/clipio-setup" "$URL"
else wget -q --show-progress -O "$TMP/clipio-setup" "$URL"; fi
chmod +x "$TMP/clipio-setup"

if [ -n "$WAYLAND_DISPLAY" ] || [ -n "$DISPLAY" ]; then
    "$TMP/clipio-setup" setup
else
    "$TMP/clipio-setup" setup --silent && echo "Clipio was installed."
fi
