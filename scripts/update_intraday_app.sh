#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCK="/tmp/qsignal-intraday-refresh.lock"

cd "$ROOT"
exec 9>"$LOCK"
if ! flock -n 9; then
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) qsignal intraday refresh already running"
  exit 0
fi

python3 0_data/_4_build/_2_backfill_intraday_events.py
python3 0_data/_4_build/_5_prune_onchain_raw_logs.py
python3 scripts/fetch_tx_activity.py
python3 scripts/generate_live_signals.py
python3 5_send/_3_dispatch.py --kind live --send --soft-fail
