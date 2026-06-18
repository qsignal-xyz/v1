#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/fetch_tx_activity.py || echo "initial tx activity refresh failed"
python3 scripts/render_intraday_refresh.py || echo "initial intraday events refresh failed"
python3 3_app/_3_live/fetch_mnt_candles.py || echo "initial MNT candle refresh failed"
python3 scripts/generate_live_signals.py || echo "initial live signal refresh failed"

scripts/render_refresh_loop.sh &
exec python3 scripts/server.py
