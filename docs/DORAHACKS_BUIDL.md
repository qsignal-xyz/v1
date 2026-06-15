# QSignal DoraHacks BUIDL

**Mantle portfolio signals with live on-chain radar, AI analyst summaries, and verifiable signal commitments.**

Track: **AI Alpha & Data**

## Problem

Crypto investors drown in fragmented data: perp funding, open interest, spot/perp price action, chain TVL, stablecoin supply, bridge movement, yield pool risk, and social alerts all live in different places. Most dashboards show raw charts but do not answer the actual portfolio question:

> Should I be long MNT today, or should I stay in stable yield?

For Mantle specifically, the signal problem is harder because Mantle-native data is valuable but lower-frequency than perps/market data. A useful system needs to combine daily ecosystem context with faster live on-chain and market monitoring without pretending daily data is hourly alpha.

## Solution

QSignal is a Mantle-focused signal desk that converts market, Mantle ecosystem, and live on-chain flow data into a simple daily recommendation:

- **Long MNT** when a walk-forward-validated positive edge is active.
- **Move to stable yield** when no validated long edge exists or risk-off conditions dominate.

The product has four user surfaces:

- **Live**: 24h live signal radar with MNT market context, on-chain flow candles, event table, and AI analyst panel.
- **Reports**: current daily recommendation plus paginated historical daily reports.
- **Backtest**: model long/yield replay versus MNT and BTC benchmarks.
- **Docs**: concise explanation of data, signal logic, AI layer, notifications, and on-chain proof.

The AI layer is not a chatbot wrapper. The deterministic pipeline builds the signal first; AI explains the current state, summarizes risks, and turns structured evidence into an investor briefing.

## Use Cases

| User | Use Case | Why QSignal Helps |
|---|---|---|
| MNT holders | Know when to hold MNT vs park in yield | Turns complex market/on-chain context into one daily action. |
| Active traders | Watch live risk changes | Live radar surfaces funding, OI, momentum, bridge, stable, and whale-like transfer context. |
| Yield users | Find safer idle-capital route | Tracks current Mantle stable-yield options and flags yield-pool/token anomalies. |
| Analysts | Audit signal quality | Backtest tab shows replay assumptions, benchmark comparison, Sharpe, CAGR, and drawdown. |
| Communities | Get push alerts | Telegram/Discord delivery publishes daily reports and important live alerts. |
| Protocols | Verify public signals | Signal report hashes can be committed to the Mantle SignalLedger. |

## How It Works

```text
Bybit / DeFiLlama / CoinGecko / Mantle RPC
                  |
                  v
0_data  -> normalized daily + live datasets
                  |
                  v
1_signal -> explainable candidate rules
                  |
                  v
2_backtest -> walk-forward health + long/yield replay
                  |
                  v
3_app -> Live / Reports / Backtest / Docs
                  |
        +---------+----------+
        v                    v
5_send notifications   SignalLedger commitments
```

## Technical Architecture

```text
qsignal/
├── 0_data/       # Bybit, DeFiLlama, CoinGecko, Mantle RPC ingestion
├── 1_signal/     # daily features and explainable signal rules
├── 2_backtest/   # walk-forward signal health and long/yield replay
├── 3_app/        # static web app
├── 4_runtime/    # deployment JSON payloads
├── 5_send/       # Telegram and Discord publishing
├── contracts/    # Mantle SignalLedger
├── docs/         # build, app, contract, cache docs
└── scripts/      # app data, AI analyst, live refresh, server
```

### Data Sources

| Layer | Source | What It Provides |
|---|---|---|
| Market | Bybit | MNTUSDT spot/perp candles, open interest, funding |
| Benchmark | Bybit | BTC comparison series |
| Mantle ecosystem | DeFiLlama | TVL, stablecoin supply, DEX volume, fees, revenue, yield pools |
| Market cap/volume | CoinGecko | MNT market context |
| Live on-chain | Mantle RPC | ERC-20 transfers, mints/burns, bridge-like flows, yield-pool risk events |
| AI | OpenRouter | Server-side daily/live report summarization |

### Signal Logic

Daily signals are built from explainable rules, then filtered through walk-forward health checks. The hackathon app exposes only two allocation states:

- **Long**: positive validated edge for MNT.
- **Yield**: no validated long edge or risk-off context; idle capital moves to Mantle stable yield.

Live radar adds intraday evidence: stable mint/burn anomalies, bridge in/out events, large token transfers, MNT price momentum, open interest, funding, and MNT-vs-BTC beta gap.

### AI Analyst

The AI analyst receives:

- latest daily model report
- active live market signals
- 24h Mantle on-chain event summary
- current best Mantle stable-yield route
- recent AI reports for continuity

It returns stance, confidence, why, action, risks, and evidence. Calls are server-side, cooldown-limited, and keys are never exposed to the browser.

### Backtest

The replay starts on `2024-06-01`; earlier history is warmup for walk-forward signal health. The model:

- goes long MNT on positive validated daily signals
- moves to stable yield on neutral/risk-off days
- includes yield carry
- compares against MNT buy-and-hold and BTC buy-and-hold
- displays assumptions and limitations in the app

This is hackathon evidence, not a guarantee of future returns.

## Mantle Integration

QSignal uses Mantle directly in three ways:

1. Mantle-native daily features: TVL, stablecoin supply, DEX volume, chain/app fees, revenue, and yield pools.
2. Live Mantle RPC monitoring: ERC-20 transfers, mints, burns, bridge-like flows, and yield-pool risk events.
3. A Mantle mainnet `SignalLedger` contract for public signal/report commitments.

Canonical SignalLedger:

```text
0x0000000c5c652995bdcAe8e78902414A00AF8983
```

## Hackathon Points Reference

| Judging Area | QSignal Answer |
|---|---|
| Robust and unique data sources | Combines Bybit perps/spot/OI/funding, BTC benchmark, DeFiLlama Mantle metrics, CoinGecko MNT data, Mantle RPC live events, and Mantle yield pools. |
| Mantle-native data priority | Uses Mantle TVL, stables, DEX volume, fees, revenue, yield pools, and live Mantle token/bridge events. |
| Freshness and reliability | Render refresh loop updates live context every few minutes; browser polls runtime JSON and revalidates on focus. |
| Signal predictive value | Rules are evaluated through walk-forward health and replayed against future MNT returns before becoming active. |
| AI depth | AI summarizes real model/live state into actionable reports; it does not invent raw signals or replace the data pipeline. |
| Execution/readiness | App, backtest, Telegram/Discord sender, Render deploy config, seed runtime JSON, and Mantle contract are included. |
| On-chain component | Report hashes can be committed to the Mantle SignalLedger for public timestamping. |
| User experience | Live radar, daily report history, backtest chart/table, docs tab, and social/alert channels are shipped. |
| Transparency | Source includes data builders, signal rules, backtest code, app, notification sender, contract, and docs. |

## Links

- App: `https://qsignal.xyz`
- Render preview: `https://qsignal-hvl8.onrender.com`
- GitHub org: `https://github.com/qsignal-xyz`
- Telegram: `https://t.me/qsignal_xyz`
- Discord: `https://discord.gg/hgAfJXnKtw`
- YouTube: `https://www.youtube.com/@qsignal_xyz`
- X: `https://x.com/qsignal_xyz`
- SignalLedger: `https://mantlescan.xyz/address/0x0000000c5c652995bdcAe8e78902414A00AF8983`

## Caveats

- This is not financial advice.
- The app does not claim guaranteed alpha.
- The hackathon version does not recommend shorting MNT.
- Daily Mantle ecosystem data is treated as daily context, not fake hourly data.
- Live on-chain alerts are context for the daily model, not automatic trade execution.
