#!/usr/bin/env bash
# visual-diff.sh — compare one design/reference image against one rendered implementation image.
#
# Usage:  bash visual-diff.sh <reference.png> <render.png> [diff.png]
# Stdout: AE=<pixels> AE_RATIO=<0..1> STATUS=PASS|FAIL STRUCT=ALIGNED|DRIFT|UNKNOWN MAX_BLOCK=<px>@<WxH+X+Y> STRUCT_RATIO=<0..1> REGION=<top|middle|bottom> MAX_AE=<px>
# Exit:   0 = pass, 1 = diff/structural fail, 2 = setup/usage/tool error
# Env:
#   AE_THRESHOLD         Raw AE pass threshold (default 500). Mostly useful for identical-source baselines.
#   AE_RATIO_THRESHOLD   Raw AE area-ratio pass threshold (default 0.002). Prevents small-image false passes.
#   AE_FUZZ              ImageMagick fuzz tolerance, e.g. 10% for cross-renderer comparisons (default 0).
#   STRUCT_GATE=1        Always compute STRUCT and exit on STRUCT. UNKNOWN exits 2.
#   STRUCT_THRESHOLD     Largest eroded connected diff block treated as drift (default 4000 px).
#   STRUCT_RATIO_THRESHOLD Largest eroded block area-ratio treated as drift (default 0.01).
#   STRUCT_ERODE         Erosion radius for noise/text thinning before connected components (default 3).

set -uo pipefail

if command -v magick >/dev/null 2>&1; then
  MAGICK=(magick)
  IDENTIFY=(magick identify)
  COMPARE=(magick compare)
else
  if ! command -v convert >/dev/null 2>&1 || ! command -v identify >/dev/null 2>&1 || ! command -v compare >/dev/null 2>&1; then
    echo "ERROR: ImageMagick missing. Need 'magick' or legacy 'convert'/'identify'/'compare'." >&2
    exit 2
  fi
  MAGICK=(convert)
  IDENTIFY=(identify)
  COMPARE=(compare)
fi

REF="${1:-}"
IMPL="${2:-}"
DIFF="${3:-/dev/null}"
THRESHOLD="${AE_THRESHOLD:-500}"
AE_RATIO_THRESHOLD="${AE_RATIO_THRESHOLD:-0.002}"
FUZZ="${AE_FUZZ:-0}"
STRUCT_THRESHOLD="${STRUCT_THRESHOLD:-4000}"
STRUCT_RATIO_THRESHOLD="${STRUCT_RATIO_THRESHOLD:-0.01}"
ERODE="${STRUCT_ERODE:-3}"
STRUCT_GATE="${STRUCT_GATE:-0}"

if [ -z "$REF" ] || [ -z "$IMPL" ]; then
  echo "Usage: visual-diff.sh <reference.png> <render.png> [diff.png]" >&2
  exit 2
fi
[ -f "$REF" ] || { echo "ERROR: reference not found: $REF" >&2; exit 2; }
[ -f "$IMPL" ] || { echo "ERROR: render not found: $IMPL" >&2; exit 2; }

TMP_FILES=()
# shellcheck disable=SC2329 # Invoked indirectly by the EXIT trap.
cleanup() { [ "${#TMP_FILES[@]}" -eq 0 ] || rm -f "${TMP_FILES[@]}"; }
trap cleanup EXIT
mktemp_png() {
  local p
  p=$(mktemp "${TMPDIR:-/tmp}/visual-diff-XXXXXX") || exit 2
  p="${p}.png"
  TMP_FILES+=("$p")
  printf '%s' "$p"
}

read -r REF_W REF_H <<EOF_SIZE
$("${IDENTIFY[@]}" -format "%w %h" "$REF" 2>/dev/null)
EOF_SIZE
read -r IMPL_W IMPL_H <<EOF_SIZE
$("${IDENTIFY[@]}" -format "%w %h" "$IMPL" 2>/dev/null)
EOF_SIZE
if [ -z "${REF_W:-}" ] || [ -z "${IMPL_W:-}" ]; then
  echo "ERROR: could not read image dimensions" >&2
  exit 2
fi

REF_SIZE="${REF_W}x${REF_H}"
IMPL_SIZE="${IMPL_W}x${IMPL_H}"
DID_NORMALIZE=0

if [ "$REF_SIZE" != "$IMPL_SIZE" ]; then
  DW=$((IMPL_W - REF_W))
  DH=$((IMPL_H - REF_H))
  CROP_W=$((REF_W < IMPL_W ? REF_W : IMPL_W))
  CROP_H=$((REF_H < IMPL_H ? REF_H : IMPL_H))
  echo "SIZE_DELTA=${DW}x${DH}px (render-ref; ref=$REF_SIZE render=$IMPL_SIZE)"
  echo "WARN: dimension mismatch — AE/STRUCT are non-strict until framing is fixed"
  echo "NORMALIZE=CROP_COMMON_TOP_LEFT ${CROP_W}x${CROP_H}+0+0"
  REF_CROP=$(mktemp_png)
  IMPL_CROP=$(mktemp_png)
  if ! "${MAGICK[@]}" "$REF" -crop "${CROP_W}x${CROP_H}+0+0" +repage "$REF_CROP"; then
    echo "ERROR: failed to crop reference image" >&2
    exit 2
  fi
  if ! "${MAGICK[@]}" "$IMPL" -crop "${CROP_W}x${CROP_H}+0+0" +repage "$IMPL_CROP"; then
    echo "ERROR: failed to crop render image" >&2
    exit 2
  fi
  REF="$REF_CROP"
  IMPL="$IMPL_CROP"
  REF_W=$CROP_W
  REF_H=$CROP_H
  DID_NORMALIZE=1
fi

PIXELS=$((REF_W * REF_H))
if [ "$PIXELS" -le 0 ]; then
  echo "ERROR: invalid image area: ${REF_W}x${REF_H}" >&2
  exit 2
fi

AE_RAW=$("${COMPARE[@]}" -metric AE -fuzz "$FUZZ" "$REF" "$IMPL" "$DIFF" 2>&1)
CMP_RC=$?
if [ "$CMP_RC" -ge 2 ]; then
  echo "ERROR: ImageMagick compare failed (rc=$CMP_RC): $AE_RAW" >&2
  exit 2
fi
AE=$(printf '%s' "$AE_RAW" | awk '{printf "%d", $1}')
case "${AE:-}" in ''|*[!0-9]*) echo "ERROR: could not parse AE from compare: $AE_RAW" >&2; exit 2 ;; esac

AE_RATIO=$(awk -v ae="$AE" -v px="$PIXELS" 'BEGIN { printf "%.6f", ae / px }')

RAW_STATUS=PASS
[ "$AE" -gt "$THRESHOLD" ] && RAW_STATUS=FAIL
if awk -v ratio="$AE_RATIO" -v threshold="$AE_RATIO_THRESHOLD" 'BEGIN { exit (ratio > threshold ? 0 : 1) }'; then
  RAW_STATUS=FAIL
fi
[ "$DID_NORMALIZE" = "1" ] && RAW_STATUS=FAIL

# Without STRUCT_GATE, identical-source baselines can use raw AE directly.
if [ "$STRUCT_GATE" != "1" ] && [ "$RAW_STATUS" = PASS ] && [ "$DID_NORMALIZE" != "1" ]; then
  echo "AE=$AE AE_RATIO=$AE_RATIO STATUS=PASS"
  exit 0
fi
if [ "$STRUCT_GATE" != "1" ] && [ "$RAW_STATUS" = FAIL ] && [ "$DID_NORMALIZE" != "1" ] && [ "$FUZZ" = "0" ]; then
  echo "AE=$AE AE_RATIO=$AE_RATIO STATUS=FAIL"
  exit 1
fi

STRUCT=UNKNOWN
MAX_BLOCK=0
MAX_AT=none
MASK=$(mktemp_png)
ERODED=$(mktemp_png)

if ! "${MAGICK[@]}" "$REF" "$IMPL" -compose difference -composite \
  -fuzz "$FUZZ" -threshold 0 -alpha off -type bilevel "$MASK"; then
  echo "ERROR: failed to generate structural diff mask" >&2
  echo "AE=$AE AE_RATIO=$AE_RATIO STATUS=$RAW_STATUS STRUCT=UNKNOWN MAX_BLOCK=0@none REGION=unknown MAX_AE=0"
  exit 2
fi

if ! "${MAGICK[@]}" "$MASK" -morphology Erode "Disk:$ERODE" "$ERODED"; then
  echo "ERROR: failed to erode structural diff mask" >&2
  echo "AE=$AE AE_RATIO=$AE_RATIO STATUS=$RAW_STATUS STRUCT=UNKNOWN MAX_BLOCK=0@none REGION=unknown MAX_AE=0"
  exit 2
fi

COMPONENTS=$("${MAGICK[@]}" "$ERODED" -define connected-components:verbose=true -connected-components 8 null: 2>/dev/null)
CC_RC=$?
if [ "$CC_RC" -ne 0 ] || [ -z "$COMPONENTS" ]; then
  echo "ERROR: failed to compute connected components for structural diff" >&2
  echo "AE=$AE AE_RATIO=$AE_RATIO STATUS=$RAW_STATUS STRUCT=UNKNOWN MAX_BLOCK=0@none REGION=unknown MAX_AE=0"
  exit 2
fi

read -r MAX_BLOCK MAX_AT <<EOF_MAX
$(printf '%s\n' "$COMPONENTS" | awk '
  /^[[:space:]]*[0-9]+:/ {
    geom=$2;
    area=0;
    for (i = 3; i <= NF; i++) {
      if ($i ~ /^[0-9]+$/) { area=$i+0; break; }
    }
    if ($0 ~ /gray\(0\)|black|#000000/) next;
    if (area > max) { max=area; at=geom; }
  }
  END { if (max == "") print "0 none"; else print max, at; }
')
EOF_MAX
case "${MAX_BLOCK:-}" in ''|*[!0-9]*) echo "ERROR: invalid structural component area: $MAX_BLOCK" >&2; exit 2 ;; esac

STRUCT_RATIO=$(awk -v block="$MAX_BLOCK" -v px="$PIXELS" 'BEGIN { printf "%.6f", block / px }')

STRUCT=ALIGNED
if [ "$DID_NORMALIZE" = "1" ] || [ "$MAX_BLOCK" -gt "$STRUCT_THRESHOLD" ]; then
  STRUCT=DRIFT
fi
if awk -v ratio="$STRUCT_RATIO" -v threshold="$STRUCT_RATIO_THRESHOLD" 'BEGIN { exit (ratio > threshold ? 0 : 1) }'; then
  STRUCT=DRIFT
fi

THIRD=$((REF_H / 3))
REGION=full
MAX_AE=0
if [ "$THIRD" -gt 0 ]; then
  for part in top middle bottom; do
    case "$part" in
      top) off=0; ph=$THIRD ;;
      middle) off=$THIRD; ph=$THIRD ;;
      bottom) off=$((THIRD * 2)); ph=$((REF_H - THIRD * 2)) ;;
    esac
    [ "$ph" -gt 0 ] || continue
    PART_RAW=$("${COMPARE[@]}" -metric AE -fuzz "$FUZZ" \
      -extract "${REF_W}x${ph}+0+${off}" "$REF" \
      -extract "${REF_W}x${ph}+0+${off}" "$IMPL" \
      /dev/null 2>&1)
    PART_RC=$?
    if [ "$PART_RC" -ge 2 ]; then
      echo "ERROR: region compare failed for $part: $PART_RAW" >&2
      echo "AE=$AE AE_RATIO=$AE_RATIO STATUS=$RAW_STATUS STRUCT=UNKNOWN MAX_BLOCK=${MAX_BLOCK}@${MAX_AT} REGION=unknown MAX_AE=0"
      exit 2
    fi
    part_ae=$(printf '%s' "$PART_RAW" | awk '{printf "%d", $1}')
    if [ "$part_ae" -gt "$MAX_AE" ]; then
      MAX_AE=$part_ae
      REGION=$part
    fi
  done
fi

echo "AE=$AE AE_RATIO=$AE_RATIO STATUS=$RAW_STATUS STRUCT=$STRUCT MAX_BLOCK=${MAX_BLOCK}@${MAX_AT} STRUCT_RATIO=$STRUCT_RATIO REGION=$REGION MAX_AE=$MAX_AE"

if [ "$STRUCT_GATE" = "1" ]; then
  case "$STRUCT" in
    ALIGNED)
      echo "STRUCT_GATE: PASS (screening signal only; inspect artifacts and documented blind spots before claiming T1)"
      exit 0
      ;;
    DRIFT)
      if [ "$DID_NORMALIZE" = "1" ] && [ "$MAX_BLOCK" -eq 0 ]; then
        echo "STRUCT_GATE: FAIL (image dimensions differ; fix viewport/framing before trusting AE/STRUCT)"
      else
        echo "STRUCT_GATE: FAIL (largest contiguous diff block ${MAX_BLOCK}px (${STRUCT_RATIO}) at ${MAX_AT}; investigate capture/setup before calling it a defect)"
      fi
      exit 1
      ;;
    *)
      echo "STRUCT_GATE: UNKNOWN (structural analysis failed)"
      exit 2
      ;;
  esac
fi

exit 1
