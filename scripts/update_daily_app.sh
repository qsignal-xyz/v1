#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCK="/tmp/qsignal-daily.lock"

cd "$ROOT"
exec 9>"$LOCK"
flock -n 9 || exit 0

python3 0_data/_4_build/_0_backfill_2026.py
python3 0_data/_4_build/_1_backfill_daily_2026.py --force
python3 0_data/_4_build/_3_backfill_stable_yields.py
python3 0_data/_4_build/_4_backfill_btc_benchmark.py
scripts/update_intraday_app.sh
python3 1_signal/_3_build/_0_generate_daily_signals.py
python3 2_backtest/_3_build/_0_run_daily_backtest.py
python3 scripts/build_app_data.py
python3 scripts/ai_analyze.py --force

if [[ "${QSIGNAL_SKIP_SEND:-0}" == "1" ]]; then
  python3 5_send/_3_dispatch.py --kind daily --dry-run
  python3 5_send/_3_dispatch.py --kind ai --dry-run
else
  python3 5_send/_3_dispatch.py --kind daily --send --soft-fail
  python3 5_send/_3_dispatch.py --kind ai --send --soft-fail
fi
