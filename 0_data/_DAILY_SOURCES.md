# Daily Data Sources

Main product dataset:

`0_data/cache/processed/mnt_daily_2026.parquet`

Range:

`2023-11-04` through the latest complete UTC day in the Bybit hourly cache.

Current fetched range:

`2023-11-04` through `2026-06-12`

## Fetched Metrics

| Metric | Column(s) | Source | Interval | Notes |
| --- | --- | --- | --- | --- |
| MNT perp price | `bybit_perp_open/high/low/close` | Bybit | daily from 1h | Complete UTC days only |
| MNT perp volume | `bybit_perp_volume_base`, `bybit_perp_turnover_quote` | Bybit | daily from 1h | Used instead of paid DefiLlama perps volume |
| MNT spot price | `bybit_spot_open/high/low/close` | Bybit | daily from 1h | Tradable spot proxy |
| MNT spot volume | `bybit_spot_volume_base`, `bybit_spot_turnover_quote` | Bybit | daily from 1h | CEX spot confirmation |
| Open interest | `bybit_open_interest_close`, `bybit_open_interest_avg` | Bybit | daily from 1h | Main leverage/crowding feature |
| Funding | `bybit_funding_rate_avg` | Bybit | daily from 1h ffill | Native funding is 8h |
| Basis | `bybit_basis_pct_avg` | Bybit | daily from 1h | Perp vs spot |
| TVL | `mantle_tvl_usd` | DefiLlama | daily | Mantle ecosystem context |
| DEX volume | `mantle_dex_volume_usd` | DefiLlama | daily | Mantle app liquidity/activity context |
| Stablecoin mcap | `mantle_stables_mcap_usd` | DefiLlama | daily | Capital on-chain context |
| Bridged stablecoins | `mantle_stables_bridged_usd` | DefiLlama | daily | Not full bridge volume |
| App fees | `mantle_app_fees_usd` | DefiLlama | daily | Protocol/app fees on Mantle |
| App revenue | `mantle_app_revenue_usd` | DefiLlama | daily | Protocol/app revenue on Mantle |
| Chain fees | `mantle_chain_fees_usd` | DefiLlama | daily | Chain gas-fee metric |
| Chain revenue | `mantle_chain_revenue_usd` | DefiLlama | daily | Chain revenue metric |
| MNT market cap | `mnt_market_cap_usd` | CoinGecko | daily, partial | Optional market context; public API is range-limited/throttled |
| MNT total volume | `mnt_total_volume_usd` | CoinGecko | daily, partial | Optional aggregate volume context |
| Stable yield APY | `stable_yield_apy` | DeFiLlama Yields | daily, partial | TVL-weighted selected Mantle stable pools, used for yield/flat-position simulation |
| BTC spot benchmark | `btc_spot_close` | Bybit | daily from 1h | Buy-and-hold benchmark only, starts 2024-06-01 |

## Derived Features

The daily normalizer adds:

- 1d returns for Bybit perp/spot.
- 1d open-interest change.
- 1d and 7d pct changes for Mantle context metrics.
- `mantle_dex_volume_to_tvl`.

## Not Fetched Yet

| Metric | Status | Reason |
| --- | --- | --- |
| DefiLlama perps volume | unavailable in free API | endpoint returned HTTP 402 |
| Bridge flow / bridge volume | unavailable in free API | endpoint returned HTTP 402 |
| Full historical CoinGecko market data | partial only | public endpoint rejects/throttles full 2023-2026 history |
| Stable yield before 2026-01-28 | unavailable | selected public Mantle pool charts do not have earlier daily history |
| Full bridged TVL | not fetched | no free endpoint confirmed |
| Active addresses | not fetched | no free endpoint confirmed |
| New addresses | not fetched | no free endpoint confirmed |
| Transactions | not fetched | no free endpoint confirmed |
| Gas used | not fetched | no free endpoint confirmed |

## Design Rule

Daily Mantle context is not interpolated into fake hourly data. Signals/backtests should use
`mnt_daily_2026.parquet` first. Hourly Bybit data remains an internal source cache and can support
intraday modules later.
