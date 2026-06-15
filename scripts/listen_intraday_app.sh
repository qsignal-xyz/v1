#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INTERVAL_SECONDS="${1:-300}"
LOG_DIR="$ROOT/logs"
LOG_FILE="$LOG_DIR/intraday_listener.log"

mkdir -p "$LOG_DIR"
cd "$ROOT"

while true; do
  started_at="$(date +%s)"
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) qsignal intraday refresh start" | tee -a "$LOG_FILE"
  if scripts/update_intraday_app.sh 2>&1 | tee -a "$LOG_FILE"; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) qsignal intraday refresh ok" | tee -a "$LOG_FILE"
  else
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) qsignal intraday refresh failed" | tee -a "$LOG_FILE"
  fi
  elapsed=$(( $(date +%s) - started_at ))
  sleep_for=$(( INTERVAL_SECONDS - elapsed ))
  if (( sleep_for > 0 )); then
    sleep "$sleep_for"
  fi
done
