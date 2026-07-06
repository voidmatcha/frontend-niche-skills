#!/usr/bin/env bash
# figma-export.sh — export Figma node(s) as PNG reference images via the REST Images API.
#
# Usage: figma-export.sh <file-key> <node-ids> <out-dir> [scale]
#   node-ids: comma-separated ids in URL form (3-809) or API form (3:809)
#   token:    FIGMA_TOKEN or FIGMA_API_KEY (never inline a token on argv)
# Output: <out-dir>/<node-id-with-underscore>.png and "saved <path>" lines.
# Exit: 0 success; 2 blocked/setup/API/download error.
#
# Network knobs:
#   FIGMA_EXPORT_CONNECT_TIMEOUT   curl connect timeout seconds (default: 10)
#   FIGMA_EXPORT_MAX_TIME          curl total request timeout seconds (default: 60)
#   FIGMA_EXPORT_RETRIES           curl retry count (default: 0; avoids long 429 Retry-After sleeps)
#   FIGMA_EXPORT_RETRY_MAX_TIME    cap retry duration seconds when retries are enabled (default: 20)
#   FIGMA_EXPORT_DOWNLOAD_TIMEOUT  image download timeout seconds (default: 60)

set -uo pipefail

if [ "$#" -lt 3 ]; then
  echo "Usage: figma-export.sh <file-key> <node-ids> <out-dir> [scale]" >&2
  exit 2
fi

KEY="$1"
NODES_RAW="$2"
OUT="$3"
SCALE="${4:-2}"
TOKEN="${FIGMA_TOKEN:-${FIGMA_API_KEY:-}}"
CONNECT_TIMEOUT="${FIGMA_EXPORT_CONNECT_TIMEOUT:-10}"
MAX_TIME="${FIGMA_EXPORT_MAX_TIME:-60}"
RETRIES="${FIGMA_EXPORT_RETRIES:-0}"
RETRY_MAX_TIME="${FIGMA_EXPORT_RETRY_MAX_TIME:-20}"
DOWNLOAD_TIMEOUT="${FIGMA_EXPORT_DOWNLOAD_TIMEOUT:-60}"

[ -n "$TOKEN" ] || { echo "ERROR: set FIGMA_TOKEN or FIGMA_API_KEY" >&2; exit 2; }
command -v curl >/dev/null 2>&1 || { echo "ERROR: curl required" >&2; exit 2; }
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 required" >&2; exit 2; }

case "$SCALE" in ''|*[!0-9.]*) echo "ERROR: scale must be numeric" >&2; exit 2 ;; esac
case "$CONNECT_TIMEOUT" in ''|*[!0-9]*) echo "ERROR: FIGMA_EXPORT_CONNECT_TIMEOUT must be an integer" >&2; exit 2 ;; esac
case "$MAX_TIME" in ''|*[!0-9]*) echo "ERROR: FIGMA_EXPORT_MAX_TIME must be an integer" >&2; exit 2 ;; esac
case "$RETRIES" in ''|*[!0-9]*) echo "ERROR: FIGMA_EXPORT_RETRIES must be an integer" >&2; exit 2 ;; esac
case "$RETRY_MAX_TIME" in ''|*[!0-9]*) echo "ERROR: FIGMA_EXPORT_RETRY_MAX_TIME must be an integer" >&2; exit 2 ;; esac
case "$DOWNLOAD_TIMEOUT" in ''|*[!0-9]*) echo "ERROR: FIGMA_EXPORT_DOWNLOAD_TIMEOUT must be an integer" >&2; exit 2 ;; esac

mkdir -p "$OUT"
IDS=$(printf '%s' "$NODES_RAW" | sed 's/-/:/g')
RESP_FILE=$(mktemp "${TMPDIR:-/tmp}/figma-images-response-XXXXXX.json")
HDR_FILE=$(mktemp "${TMPDIR:-/tmp}/figma-images-headers-XXXXXX.txt")
cleanup() { rm -f "$RESP_FILE" "$HDR_FILE"; }
trap cleanup EXIT

HTTP_CODE=$(curl -sS \
  --connect-timeout "$CONNECT_TIMEOUT" \
  --max-time "$MAX_TIME" \
  --retry "$RETRIES" \
  --retry-max-time "$RETRY_MAX_TIME" \
  -D "$HDR_FILE" \
  -o "$RESP_FILE" \
  -H "X-Figma-Token: ${TOKEN}" \
  --get \
  --data-urlencode "ids=${IDS}" \
  --data-urlencode "format=png" \
  --data-urlencode "scale=${SCALE}" \
  -w '%{http_code}' \
  "https://api.figma.com/v1/images/${KEY}")
CURL_RC=$?

print_api_error_context() {
  if [ -s "$HDR_FILE" ]; then
    grep -iE '^(HTTP/|retry-after:|x-figma-rate-limit-type:|x-figma-plan-tier:|x-figma-upgrade-link:)' "$HDR_FILE" >&2 || true
  fi
  if [ -s "$RESP_FILE" ]; then
    head -c 1000 "$RESP_FILE" >&2 || true
    echo >&2
  fi
}

if [ "$CURL_RC" -ne 0 ]; then
  echo "ERROR: Figma Images API request failed (curl rc=$CURL_RC; max-time=${MAX_TIME}s)" >&2
  print_api_error_context
  exit 2
fi

case "$HTTP_CODE" in ''|*[!0-9]*)
  echo "ERROR: Figma Images API returned non-numeric HTTP status: ${HTTP_CODE:-<empty>}" >&2
  print_api_error_context
  exit 2
  ;;
esac

if [ "$HTTP_CODE" -lt 200 ] || [ "$HTTP_CODE" -ge 300 ]; then
  echo "ERROR: Figma Images API HTTP $HTTP_CODE (blocked/not validated)" >&2
  print_api_error_context
  exit 2
fi

python3 - "$RESP_FILE" "$OUT" "$IDS" "$DOWNLOAD_TIMEOUT" <<'PYCODE'
import json
import pathlib
import sys
import urllib.request

resp_file = pathlib.Path(sys.argv[1])
out = pathlib.Path(sys.argv[2])
requested = [node.strip() for node in sys.argv[3].split(',') if node.strip()]
download_timeout = int(sys.argv[4])

try:
    data = json.loads(resp_file.read_text())
except Exception as exc:
    print(f"ERROR: could not parse Figma response JSON: {exc}", file=sys.stderr)
    raise SystemExit(2)

if data.get('err'):
    print(f"ERROR: Figma API error: {data.get('err')}", file=sys.stderr)
    raise SystemExit(2)

images = data.get('images') or {}
if not images:
    print('ERROR: no images returned (blocked/not validated: check file-key / node-ids / token access)', file=sys.stderr)
    raise SystemExit(2)

missing = [node for node in requested if node not in images]
if missing:
    print(f"ERROR: requested nodes missing from response: {', '.join(missing)}", file=sys.stderr)
    raise SystemExit(2)

nulls = [node for node in requested if images.get(node) is None]
if nulls:
    print(f"ERROR: requested nodes returned null/unrenderable images: {', '.join(nulls)}", file=sys.stderr)
    raise SystemExit(2)

out.mkdir(parents=True, exist_ok=True)
for node in requested:
    url = images[node]
    path = out / f"{node.replace(':', '_')}.png"
    try:
        with urllib.request.urlopen(url, timeout=download_timeout) as response:
            body = response.read()
        if not body:
            print(f'ERROR: empty image download for node {node}', file=sys.stderr)
            raise SystemExit(2)
        path.write_bytes(body)
    except SystemExit:
        raise
    except Exception as exc:
        print(f'ERROR: failed to download node {node}: {exc}', file=sys.stderr)
        raise SystemExit(2)
    print(f'saved {path}')
PYCODE
