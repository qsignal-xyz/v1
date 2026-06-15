# Source Availability

Probe date: 2026-06-13.

Goal:

Find the earliest date where the core MNT/Mantle daily dataset can be built without inventing
missing data.

## Availability Probe

| Source | Metric | First Available | Status |
| --- | --- | --- | --- |
| Bybit | MNTUSDT linear perp instrument launch | 2023-10-02 | Available |
| Bybit | MNTUSDT spot/hourly candles | 2023-11-04 tested | Available for common range |
| Bybit | MNTUSDT perp hourly candles | 2023-11-04 tested | Available for common range |
| Bybit | MNTUSDT open interest | 2023-11-04 tested | Available for common range |
| Bybit | MNTUSDT funding | 2023-11-04 tested | Available for common range |
| DefiLlama | Mantle TVL | 2023-07-17 | Available |
| DefiLlama | Mantle DEX volume | 2023-07-17 | Available |
| DefiLlama | Mantle stablecoin supply | 2023-11-04 | Shortest core source |
| DefiLlama | Mantle app fees | 2023-07-17 | Available |
| DefiLlama | Mantle app revenue | 2023-07-17 | Available |
| DefiLlama | Mantle chain fees | 2023-07-16 | Available |
| DefiLlama | Mantle chain revenue | 2023-07-16 | One missing date in common range |
| CoinGecko | MNT market cap/aggregate volume | 2025-06-13 cached partial | Optional only |

## Common Start

The common-history start is:

`2023-11-04`

Reason:

DefiLlama stablecoin history starts on `2023-11-04`, later than Mantle TVL/DEX/fees and later
than Bybit perps launch. Stablecoin supply is a core Mantle-native feature, so the daily dataset
starts there.

## Current Backfill

| Dataset | Range | Rows |
| --- | --- | ---: |
| Hourly Bybit cache | 2023-11-04 00:00 UTC -> 2026-06-13 13:00 UTC | 22,862 |
| Daily core dataset | 2023-11-04 -> 2026-06-12 | 952 |

## Optional / Partial Sources

CoinGecko public API rejected the full 2023-2026 historical range and throttled chunked requests.
It remains optional context only. Core price/volume features use Bybit data.

