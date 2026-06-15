# QSignal Build

QSignal is built for the Mantle Turing Test Hackathon 2026, AI Alpha & Data track.

The product is a live portfolio signal desk for MNT. It turns market, Mantle-native, and on-chain flow data into a daily long/yield recommendation, shows live intraday context, asks an AI analyst for concise interpretation, and can publish reports to Telegram and Discord.

## User Flow

1. Open the app at `/live`.
2. Review live market and Mantle on-chain context.
3. Open `/reports` for the daily recommendation and past report table.
4. Open `/backtest` to compare QSignal long/yield replay against MNT and BTC.
5. Click Ask AI for a fresh multi-model analyst summary.
6. Subscribe through Telegram or Discord for daily and live alerts.

## Data Sources

| Layer | Source | What It Provides |
|---|---|---|
| Market | Bybit | MNTUSDT spot/perp candles, open interest, funding |
| Benchmark | Bybit | BTC comparison series |
| Mantle ecosystem | DeFiLlama | TVL, stablecoin supply, DEX volume, fees, revenue, yield pools |
| Market cap/volume | CoinGecko | MNT market context |
| Live on-chain | Mantle RPC | ERC-20 transfers, mints/burns, bridge-like flows, yield-pool risk events |
| AI | OpenRouter | Daily/live report summarization through server-side model calls |

No browser secret keys are used. Runtime secrets live in environment variables.

## Signal Logic

Daily signals are built from explainable rules, then filtered through walk-forward health checks. The hackathon app exposes only two allocation states:

- **Long**: positive validated edge for MNT.
- **Yield**: no validated long edge or risk-off context; idle capital moves to Mantle stable yield.

The live radar does not overwrite the daily model. It adds intraday evidence: stable mint/burn anomalies, bridge in/out events, large token transfers, MNT price momentum, open interest, funding, and MNT-vs-BTC beta gap.

## AI Layer

The AI analyst is not a generic chatbot. It receives:

- latest daily report
- active live market signals
- 24h on-chain flow summary
- latest yield route
- recent AI reports for continuity

It returns a short stance, confidence, why, action, risks, and evidence. The app enforces a cooldown and stores reports in `4_runtime/app/ai_reports.json`.

## Backtest

The demo replay starts on `2024-06-01`; earlier history is warmup for signal-health selection. The model:

- goes long MNT on positive daily signals
- allocates to stable yield on neutral/risk-off days
- includes yield carry
- includes Bybit futures fee/funding assumptions for leverage simulation
- compares against MNT buy-and-hold and BTC buy-and-hold

Limitations are shown in the app: no slippage model, no maintenance-margin tier model, no guarantee that historical edge persists.

## Mantle Integration

QSignal uses Mantle in three places:

1. Mantle-native ecosystem data in the daily signal layer.
2. Mantle RPC live token/bridge/yield-pool monitoring.
3. A Mantle mainnet `SignalLedger` contract for public report-hash commitments.

Canonical verified ledger:

```text
0x0000000c5c652995bdcAe8e78902414A00AF8983
```

Source: `SignalLedger`, verified on Mantlescan:
`https://mantlescan.xyz/address/0x0000000c5c652995bdcAe8e78902414A00AF8983#code`

## Hackathon Requirements Mapping

| Requirement Area | How QSignal Addresses It |
|---|---|
| Robust and unique data sources | Combines Bybit market/perp data, BTC benchmark, DeFiLlama Mantle metrics, CoinGecko MNT data, Mantle RPC live events, and current Mantle yield pools. |
| Mantle-native priority | Uses Mantle TVL, stables, DEX volume, fees/revenue, stable-yield pools, and live Mantle token/bridge events. |
| Fresh data pipeline | Render refresh loop updates live context every few minutes; browser polls runtime JSON and revalidates on focus. |
| Alpha generation | Daily rules are selected by walk-forward signal health rather than static hardcoded opinions. |
| Backtest evidence | `/backtest` shows replay, benchmarks, Sharpe, CAGR, max drawdown, equity curves, and assumptions. |
| AI usefulness | AI summarizes actual signal state and live data into an actionable report; it is not the source of raw signals. |
| User experience | Live radar, daily report table, backtest, docs tab, Telegram/Discord delivery, and social links are shipped. |
| On-chain component | Signal report hashes can be committed to the verified Mantle `SignalLedger`. |
| Openness | Source includes data builders, signal rules, backtest code, app, notification sender, contract, and docs. |

## What Is Intentionally Not Claimed

- QSignal does not promise guaranteed alpha.
- It does not expose private API keys or private execution logic.
- It does not short MNT in the hackathon UI.
- It does not pretend daily Mantle ecosystem data is hourly data.

## Demo Checklist

- `/live`: live radar, filters, AI analyst, on-chain events table
- `/reports`: daily signal and past reports
- `/backtest`: MNT/BTC/model comparison
- `/docs`: product explanation
- Telegram/Discord: daily report and live alert delivery
- Mantlescan: verified SignalLedger address above
