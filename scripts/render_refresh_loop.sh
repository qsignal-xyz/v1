#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INTERVAL_SECONDS="${QSIGNAL_RENDER_REFRESH_SECONDS:-300}"

cd "$ROOT"
while true; do
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) render light refresh start"
  if python3 scripts/fetch_tx_activity.py && python3 scripts/generate_live_signals.py; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) render light refresh ok"
  else
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) render light refresh failed"
  fi
  sleep "$INTERVAL_SECONDS"
done
