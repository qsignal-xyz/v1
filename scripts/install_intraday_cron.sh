#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MARKER="qsignal-intraday-refresh"
CURRENT="$(mktemp)"
NEXT="$(mktemp)"

cleanup() {
  rm -f "$CURRENT" "$NEXT"
}
trap cleanup EXIT

mkdir -p "$ROOT/logs"
if crontab -l > "$CURRENT" 2>/dev/null; then
  :
else
  : > "$CURRENT"
fi

awk -v marker="$MARKER" 'index($0, marker) == 0 { print }' "$CURRENT" > "$NEXT"
echo "*/5 * * * * cd $ROOT && $ROOT/scripts/update_intraday_app.sh >> $ROOT/logs/intraday_cron.log 2>&1 # $MARKER" >> "$NEXT"
crontab "$NEXT"
crontab -l | grep "$MARKER"
