## Problem

Crypto investors drown in fragmented data — perp funding, OI, spot price, chain TVL, stablecoin supply, bridge flows, yield pools — all in different places. No dashboard answers the actual portfolio question: **should I be long MNT today, or stay in stable yield?**

Mantle-native data is valuable but lower-frequency than perps/market data. A useful system must combine daily ecosystem context with faster live on-chain monitoring without pretending daily data is hourly alpha.

## Solution

QSignal is a Mantle-focused signal desk that converts market, ecosystem, and live on-chain flow data into a simple daily recommendation:

- **Long MNT** when a walk-forward-validated positive edge is active.
- **Stable yield** when no validated long edge exists or risk-off conditions dominate.

**Walk-forward backtest (Jun 2024 – Jun 2026):** the model returned **3.33x** (Sharpe 1.50, CAGR +80.7%, max DD −23.1%) vs MNT buy-and-hold at 0.57x (−80.8% DD) and BTC at 0.97x (−51.2% DD). The edge comes from avoiding MNT drawdowns by rotating to stable yield during risk-off periods.

![Backtest equity curve](https://i.gyazo.com/89072f4c25d8e5be57ca2b46e71b6dab.png)
*Source: [qsignal.xyz/backtest](https://qsignal.xyz/backtest)*

Four surfaces:

- **Live** — 24h signal radar with MNT price line, on-chain flow candles, event table, and multi-model AI analyst panel.
- **Reports** — current daily recommendation plus paginated historical daily reports.
- **Backtest** — model long/yield replay versus MNT and BTC benchmarks with Sharpe, CAGR, max DD.
- **Docs** — data sources, signal logic, AI layer, notifications, and on-chain proof explained.

The AI layer is not a chatbot wrapper. The deterministic pipeline builds the signal first; AI explains the current state and turns structured evidence into an investor briefing.

## Use cases

One daily action for every Mantle participant:

- **MNT holders** — know when to hold MNT vs park in yield; one daily action replaces hours of research.
- **Active traders** — live radar surfaces funding, OI, momentum, bridge, stable, and whale transfer context.
- **Yield users** — tracks current Mantle stable-yield options and flags yield-pool/token anomalies.
- **Analysts** — backtest tab shows replay assumptions, benchmark comparison, and full metrics.
- **Communities** — Telegram/Discord delivery publishes daily reports and important live alerts.
- **Protocols** — signal report hashes committed to the Mantle SignalLedger for public timestamping.

## Tech

- **Data pipeline** — Bybit (spot/perp candles, OI, funding), DeFiLlama (Mantle TVL, stables, DEX volume, fees, revenue, yield pools), CoinGecko (MNT market context), Mantle RPC (ERC-20 transfers, mints/burns, bridge flows, yield-pool risk events).
- **Signal engine** — explainable candidate rules evaluated through walk-forward health checks. Two states: long or yield. No black box.
- **AI analyst** — multi-model (Gemini + DeepSeek + Qwen) server-side synthesis. Receives daily model report, live signals, 24h on-chain events, current best yield route. Returns stance, confidence, why, action, risks, evidence. Cooldown-limited; keys never exposed to browser.
- **Backtest** — walk-forward replay from 2024-06-01. Includes yield carry, compares against MNT and BTC buy-and-hold. Displays assumptions and limitations in-app. Hackathon evidence, not a guarantee.
- **Contract** — Mantle mainnet **SignalLedger** for public signal/report hash commitments. Source verified on Mantlescan: [`0x0000000c5c652995bdcAe8e78902414A00AF8983`](https://mantlescan.xyz/address/0x0000000c5c652995bdcAe8e78902414A00AF8983#code).
- **Frontend** — zero-build static web app; MNT live price from Bybit (15s poll), on-chain flow chart, aurora-bordered AI panel. Complexity lives in the pipeline, not the framework.
- **Delivery** — Telegram and Discord publishing of daily reports and live alerts.

## How it maps to the judging criteria

**Part A · Mantle general (50 pts)**

- ✅ **Technical (15)** — Walk-forward signal engine, multi-model AI analyst, live Mantle RPC monitor, on-chain flow chart, verified SignalLedger contract. Runs end-to-end on Mantle mainnet.
- ✅ **Ecosystem fit (10)** — Reads Mantle-native assets (TVL, stables, DEX volume, fees, revenue, yield pools); SignalLedger is a composable on-chain primitive any protocol can query.
- ✅ **Business potential (10)** — Signal-as-a-service for MNT holders and yield users; Telegram/Discord distribution; on-chain proof layer enables paid signal subscriptions post-hackathon.
- ✅ **Innovation (10)** — Deterministic signal pipeline + multi-model AI synthesis + on-chain commitment in one product. Not a fork, not a chatbot wrapper.
- ✅ **User experience (5)** — No wallet connect, no sign-up. Live radar, daily reports, backtest, docs, and social alerts all shipped.

**Part B · Trading Strategy (50 pts)**

- ✅ **Strategy Alpha (15)** — Explainable rules filtered through walk-forward health checks. Backtest replays long/yield against MNT and BTC benchmarks with Sharpe, CAGR, and max DD. Not a simple rule-based bot — signal candidates are validated before activation.
- ✅ **Verifiability & auditability (15)** — Backtest assumptions displayed in-app. Signal rules and data pipeline are open source. Report hashes committed to the verified Mantle SignalLedger for independent timestamping.
- ✅ **Investment potential (12)** — Clean long/yield allocation with transparent risk metrics. Yield routing to best Mantle pool (currently USDC on aave-v3). Scalable to multi-chain and additional signal factors.
- ✅ **Risk management (8)** — Two-state model (long or yield) avoids leveraged blowup. Walk-forward validation gates prevent overfitted signals from activating. Live radar flags yield-pool risk events. Backtest displays limitations honestly.
