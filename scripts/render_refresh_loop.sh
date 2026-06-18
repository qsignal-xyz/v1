#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INTERVAL_SECONDS="${QSIGNAL_RENDER_REFRESH_SECONDS:-300}"

cd "$ROOT"
while true; do
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) render light refresh start"
  if python3 scripts/fetch_tx_activity.py && python3 3_app/_3_live/fetch_mnt_candles.py && python3 scripts/generate_live_signals.py; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) render light refresh ok"
  else
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) render light refresh failed"
  fi
  if python3 scripts/render_intraday_refresh.py; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) render intraday refresh check ok"
  else
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) render intraday refresh check failed"
  fi
  if python3 scripts/render_daily_refresh.py; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) render daily refresh check ok"
  else
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) render daily refresh check failed"
  fi
  sleep "$INTERVAL_SECONDS"
done
