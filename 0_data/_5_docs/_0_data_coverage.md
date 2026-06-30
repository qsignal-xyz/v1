# Data Coverage

| Dataset | Source | Interval | Rows | Expected | Coverage | First | Last | Issues |
| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| bybit_daily_agg | Bybit derived | 1d | 969 | 969 | 100.0% | 2023-11-04 00:00:00+00:00 | 2026-06-29 00:00:00+00:00 | none |
| defillama_tvl_daily | DefiLlama | 1d | 969 | 969 | 100.0% | 2023-11-04 00:00:00+00:00 | 2026-06-29 00:00:00+00:00 | none |
| defillama_dex_volume_daily | DefiLlama | 1d | 969 | 969 | 100.0% | 2023-11-04 00:00:00+00:00 | 2026-06-29 00:00:00+00:00 | none |
| defillama_stables_daily | DefiLlama | 1d | 969 | 969 | 100.0% | 2023-11-04 00:00:00+00:00 | 2026-06-29 00:00:00+00:00 | none |
| defillama_app_fees_daily | DefiLlama | 1d | 969 | 969 | 100.0% | 2023-11-04 00:00:00+00:00 | 2026-06-29 00:00:00+00:00 | none |
| defillama_app_revenue_daily | DefiLlama | 1d | 969 | 969 | 100.0% | 2023-11-04 00:00:00+00:00 | 2026-06-29 00:00:00+00:00 | none |
| defillama_chain_fees_daily | DefiLlama | 1d | 968 | 969 | 99.9% | 2023-11-04 00:00:00+00:00 | 2026-06-28 00:00:00+00:00 | missing expected timestamps: 1 |
| defillama_chain_revenue_daily | DefiLlama | 1d | 967 | 969 | 99.79% | 2023-11-04 00:00:00+00:00 | 2026-06-28 00:00:00+00:00 | missing expected timestamps: 2 |
| coingecko_mnt_market_daily | CoinGecko | 1d | 200 | 969 | 20.64% | 2025-06-13 00:00:00+00:00 | 2026-06-11 00:00:00+00:00 | missing expected timestamps: 769 |
| mnt_daily_2026 | Derived | 1d | 969 | 969 | 100.0% | 2023-11-04 00:00:00+00:00 | 2026-06-29 00:00:00+00:00 | none |

## Notes

- Daily dataset uses complete UTC days only; today's partial Bybit candles are excluded.
- MNT price/volume in the signal dataset comes from Bybit; market cap comes from CoinGecko.
- Mantle native metrics are daily context, not interpolated intraday features.
- Optional CoinGecko refresh failed; cached data used: CoinGecko chunk failed after retries: 429: {"status":{"error_code":429,"error_message":"You've exceeded the Rate Limit. Please visit https://www.coingecko.com/en/a
- DefiLlama bridge volume / bridge day stats returned HTTP 402 on free API.
- DefiLlama derivatives/perps volume returned HTTP 402 on free API; Bybit perp turnover is used instead.
- DefiLlama active addresses, new addresses, transactions, and gas-used endpoints were not found on free API.
