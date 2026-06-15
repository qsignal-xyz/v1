# QSignal

Mantle portfolio signals with live on-chain radar, walk-forward backtests, AI summaries, and public signal commitments.

QSignal watches MNT market structure, Mantle ecosystem data, bridge/token flows, and stable-yield routes. The hackathon version recommends either **long MNT** or **move to stable yield**.

## Links

- App: `https://qsignal.xyz`
- Telegram: `https://t.me/qsignal_xyz`
- Discord: `https://discord.gg/hgAfJXnKtw`
- GitHub org: `https://github.com/qsignal-xyz`
- Verified contract: [`0x0000000c5c652995bdcAe8e78902414A00AF8983`](https://mantlescan.xyz/address/0x0000000c5c652995bdcAe8e78902414A00AF8983#code)

## Structure

```text
qsignal/
├── 0_data/       # Bybit, DeFiLlama, CoinGecko, Mantle RPC ingestion
├── 1_signal/     # daily features and explainable signal rules
├── 2_backtest/   # walk-forward signal health and long/yield replay
├── 3_app/        # static web app
├── 4_runtime/    # committed seed JSON for deployment
├── 5_send/       # Telegram and Discord dispatch
├── contracts/    # Mantle SignalLedger
├── docs/         # build, app, contract, cache docs
└── scripts/      # app data, AI analyst, live refresh, server
```

## Run

```bash
pip install -r requirements.txt
python3 scripts/server.py
```

Open `http://127.0.0.1:3008/live`.

Refresh data:

```bash
python3 scripts/build_app_data.py
bash scripts/update_intraday_app.sh
```

Send previews:

```bash
python3 5_send/_3_dispatch.py --kind daily --dry-run
python3 5_send/_3_dispatch.py --kind live --dry-run
```

## Docs

- [Build and hackathon requirements](docs/BUILD.md)
- [DoraHacks BUIDL submission copy](docs/DORAHACKS_BUIDL.md)
- [App/runtime](docs/app.md)
- [Contracts](docs/contracts.md)
- [On-chain cache](docs/onchain-cache.md)

## Caveat

This is a hackathon MVP. The backtest is evidence for the demo, not financial advice or a production trading guarantee.
