# QSignal App

Static QSignal demo UI plus a tiny local API for the AI analyst button.

Run:

```bash
python3 scripts/server.py
```

Open:

```text
http://127.0.0.1:3008/
```

Live refresh:

```bash
scripts/install_intraday_cron.sh
scripts/listen_intraday_app.sh 300
```

The browser polls `intraday_events.json`, `tx_activity.json`, `live_signals.json`, `ai_reports.json`, and `history_backtest.json` every 15 seconds and revalidates on focus.
The cron installer refreshes Mantle head data, network activity, and live Bybit/Mantle context every 5 minutes.
The listener script is the foreground equivalent for demo sessions.

The app shows daily parent signals with intraday MNT/stablecoin child alerts.
`scripts/server.py` also exposes `POST /api/ai/analyze`, which runs `scripts/ai_analyze.py` locally with a 1-hour cooldown. The OpenRouter key is read server-side from `/agents/shared/config/keys.env`; the browser never receives it.

Notifications:

```bash
python3 5_send/_3_dispatch.py --kind daily --dry-run
python3 5_send/_3_dispatch.py --kind live --dry-run
python3 5_send/_3_dispatch.py --kind daily --send
```

Delivery reads `QSIGNAL_TELEGRAM_BOT_TOKEN`, `QSIGNAL_TELEGRAM_CHAT_ID`, and
`QSIGNAL_DISCORD_WEBHOOK_URL` from `/agents/shared/config/keys.env`. Daily
reports send once per report date. Live delivery sends only medium/high/critical
live alerts and on-chain events, with per-channel dedupe state in
`4_runtime/send/state.json`.

Generated app payloads live in `4_runtime/app/` and are ignored by git:

- `intraday_events.json`
- `tx_activity.json`
- `live_signals.json`
- `ai_reports.json`
- `history_backtest.json`
