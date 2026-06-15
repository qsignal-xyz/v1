# QSignal

Verifiable portfolio signals backed by historical outcomes and on-chain commitments.

## Current Status

The current MVP is Mantle-focused for the hackathon. The repo uses a numbered
pipeline:

- `0_data/`: Bybit, DeFiLlama, CoinGecko, and Mantle RPC ingestion.
- `1_signal/`: explainable daily signal features and rules.
- `2_backtest/`: walk-forward health checks and replay.
- `3_app/`: static QSignal UI only.
- `4_runtime/app/`: generated JSON served by the local API server.
- `5_send/`: Telegram and Discord notification dispatch.
- `scripts/`: build, refresh, live-signal, AI analyst, and server entrypoints.
- `contracts/`: minimal signal ledger contract.

`0_data` currently covers:

- Bybit MNTUSDT linear perp 1h candles
- Bybit MNTUSDT spot 1h candles
- Bybit MNTUSDT linear open interest 1h
- Bybit MNTUSDT linear funding history
- joined UTC hourly parquet dataset
- daily Bybit aggregation
- daily DefiLlama Mantle context
- daily CoinGecko MNT market cap/volume
- generated coverage report

`1_signal` and `2_backtest` now implement the first daily research loop:

- daily feature engineering
- 20 explainable candidate rules
- event generation
- 1d/2d/3d/7d forward-return backtests
- per-rule ranking
- simple ensemble vote
- markdown report

## Run Data Backfill

```bash
python3 0_data/_4_build/_0_backfill_2026.py
python3 0_data/_4_build/_1_backfill_daily_2026.py
python3 0_data/_4_build/_3_backfill_stable_yields.py
python3 0_data/_4_build/_4_backfill_btc_benchmark.py
python3 1_signal/_3_build/_0_generate_daily_signals.py
python3 2_backtest/_3_build/_0_run_daily_backtest.py
python3 scripts/build_app_data.py
```

Force refresh:

```bash
python3 0_data/_4_build/_0_backfill_2026.py --force
```

Outputs:

- `0_data/cache/raw/*.parquet`
- `0_data/cache/processed/mnt_bybit_hourly_2026.parquet`
- `0_data/cache/processed/mnt_daily_2026.parquet`
- `1_signal/cache/daily_signal_events_2026.csv`
- `2_backtest/cache/signal_rankings_2026.csv`
- `4_runtime/app/history_backtest.json`
- `reports/signal_backtest_2026.md`
- `0_data/_DATA_COVERAGE.md`

## Run App

```bash
python3 scripts/server.py
```

Open:

```text
http://127.0.0.1:3008/signal
```

Live refresh:

```bash
scripts/update_intraday_app.sh
scripts/install_intraday_cron.sh
```

Notification dry-runs:

```bash
python3 5_send/_3_dispatch.py --kind daily --dry-run
python3 5_send/_3_dispatch.py --kind live --dry-run
```

When `QSIGNAL_TELEGRAM_BOT_TOKEN`, `QSIGNAL_TELEGRAM_CHAT_ID`, or
`QSIGNAL_DISCORD_WEBHOOK_URL` are present in `/agents/shared/config/keys.env`,
the daily and intraday refresh scripts dispatch deduped posts to those channels.

## Deploy On Render

The repo includes `render.yaml`. Render serves the Python app through
`scripts/render_start.sh`, which starts from committed seed payloads in
`4_runtime/app/` and refreshes light live context every 5 minutes.

Set these Render environment variables:

- `API_OPENROUTER` for the AI analyst button
- `QSIGNAL_APP_URL=https://qsignal.xyz`
- `QSIGNAL_LEDGER_ADDRESS=0x0000000c5c652995bdcAe8e78902414A00AF8983`

Do not put `PK_MANTLE_QSIGNAL` on Render unless this service is also meant to
publish on-chain commitments. Keep Telegram/Discord env vars on only one
runtime to avoid duplicate posts.

## Current Research Caveat

The first signal ranking is in-sample on 2026 data only. It is useful for hackathon
demo/research direction, but not yet a production trading claim.
