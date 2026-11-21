#!/usr/bin/env bash
# render.sh — renders every docs/assets/src/<name>.html to docs/assets/<name>.png at 2x (needs Chromium + network for Google Fonts)
# usage: docs/assets/src/render.sh [name ...]
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"; OUT="$(dirname "$SRC")"

# Find a Chromium: Playwright cache first, then system
chrome() {
  for d in $(ls -d "$HOME"/.cache/ms-playwright/chromium-* 2>/dev/null | sort -r); do
    [ -x "$d/chrome-linux64/chrome" ] && { echo "$d/chrome-linux64/chrome"; return; }
  done
  command -v chromium || command -v google-chrome-stable || { echo "no chromium: npx playwright install chromium" >&2; exit 1; }
}
CH="$(chrome)"

# Every page by default
names=("$@"); [ ${#names[@]} -eq 0 ] && names=($(cd "$SRC" && ls *.html | sed 's/\.html$//'))

# Measure the height, then screenshot at that exact size (social card at 1x, 1280x640)
for n in "${names[@]}"; do
  f="file://$SRC/$n.html"
  w=$(grep -o 'data-w="*[0-9]*' "$SRC/$n.html" | grep -o '[0-9]*' || true); w=${w:-1280}
  h=$("$CH" --headless=new --disable-gpu --hide-scrollbars --virtual-time-budget=5000 --window-size="$w",3000 \
      --dump-dom "$f" 2>/dev/null | grep -o 'data-h="[0-9]*"' | head -1 | grep -o '[0-9]*' || true); h=${h:-800}
  s=2; [ "$n" = social ] && s=1
  "$CH" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=$s --force-color-profile=srgb \
    --default-background-color=00000000 --virtual-time-budget=5000 --window-size="$w","$h" \
    --screenshot="$OUT/$n.png" "$f" 2>/dev/null
  echo "$n.png  ${w}x$h @${s}x  $(du -k "$OUT/$n.png" | cut -f1) KB"
done
