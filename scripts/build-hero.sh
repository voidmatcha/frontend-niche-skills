#!/usr/bin/env bash
# Render scripts/hero-source.html to docs/assets/hero.png.
#
# The README banner is generated rather than hand-drawn so it stays in step
# with the landing page: scripts/hero-source.html copies its palette and type scale
# from docs/intro.html. Re-run this after changing either one.
#
# Requires Google Chrome. The condensed display face comes from macOS system
# fonts, so rendering on another platform will substitute and shift the type.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_html="$root/scripts/hero-source.html"
output="$root/docs/assets/hero.png"
width=1400
height=600
scale=2

chrome="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
if [[ ! -x "$chrome" ]]; then
  echo "Chrome not found at: $chrome" >&2
  echo "Set CHROME to a Chrome or Chromium binary." >&2
  exit 1
fi
if [[ ! -f "$source_html" ]]; then
  echo "missing $source_html" >&2
  exit 1
fi

workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT

"$chrome" \
  --headless \
  --disable-gpu \
  --hide-scrollbars \
  --no-sandbox \
  --user-data-dir="$workdir" \
  --force-device-scale-factor="$scale" \
  --window-size="$width,$height" \
  --screenshot="$output" \
  "file://$source_html" 2>/dev/null

if [[ ! -s "$output" ]]; then
  echo "render produced no output" >&2
  exit 1
fi

python3 - "$output" <<'PY'
import struct
import sys

path = sys.argv[1]
with open(path, "rb") as handle:
    header = handle.read(24)
width, height = struct.unpack(">II", header[16:24])
size_kb = round(len(open(path, "rb").read()) / 1024)
print(f"wrote {path} ({width}x{height}, {size_kb} KB)")
PY
