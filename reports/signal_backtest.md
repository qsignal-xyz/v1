# Signal Backtest

This is a research ranking, not a deployable trading claim. Rules are simple and explainable; later work should add out-of-sample validation before using weights live.

- date range: `2023-11-12 00:00:00+00:00` -> `2026-06-27 00:00:00+00:00`
- signal events: `1977`
- evaluated event-horizon rows: `7892`
- unique signals: `21`

## Top Ranked Signal-Horizons

| Rank | Signal | Horizon | N | Hit Rate | Median Return | Avg Return | Worst | PF | Score |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | leveraged_sell_pressure | 7d | 46 | 63.04% | 3.34% | 1.12% | -33.38% | 1.28 | 73.41 |
| 2 | market_volume_confirmation | 2d | 10 | 70.00% | 1.51% | 1.73% | -9.42% | 1.79 | 66.22 |
| 3 | failed_volume_breakout | 3d | 13 | 61.54% | 2.44% | 2.25% | -21.31% | 1.67 | 65.60 |
| 4 | deleveraged_rebound | 3d | 38 | 57.89% | 1.71% | 2.37% | -15.53% | 1.99 | 57.81 |
| 5 | failed_volume_breakout | 7d | 13 | 53.85% | 4.89% | -1.31% | -51.95% | 0.84 | 46.48 |
| 6 | failed_volume_breakout | 1d | 13 | 61.54% | 1.41% | -0.04% | -17.01% | 0.98 | 44.07 |
| 7 | price_ecosystem_divergence | 2d | 30 | 60.00% | 1.09% | -1.28% | -23.18% | 0.66 | 43.43 |
| 8 | volume_breakout | 1d | 87 | 59.77% | 0.52% | 0.87% | -12.96% | 1.51 | 41.69 |
| 9 | leveraged_sell_pressure | 3d | 47 | 55.32% | 1.14% | 1.10% | -15.79% | 1.54 | 41.24 |
| 10 | price_ecosystem_divergence | 1d | 30 | 56.67% | 1.34% | -0.39% | -15.40% | 0.85 | 40.11 |
| 11 | price_ecosystem_divergence | 3d | 30 | 53.33% | 1.90% | -1.12% | -27.37% | 0.75 | 39.84 |
| 12 | volume_breakout | 2d | 87 | 54.02% | 0.97% | 1.12% | -36.02% | 1.50 | 37.39 |
| 13 | deleveraged_rebound | 2d | 38 | 52.63% | 0.70% | 2.12% | -14.45% | 2.05 | 37.18 |
| 14 | fee_activity_drop | 7d | 237 | 56.96% | 0.98% | -1.24% | -45.96% | 0.77 | 37.02 |
| 15 | basis_premium_fade | 7d | 144 | 55.56% | 1.21% | -0.98% | -30.89% | 0.80 | 36.81 |
| 16 | market_volume_confirmation | 1d | 10 | 60.00% | 0.70% | 0.97% | -4.25% | 1.78 | 36.81 |
| 17 | short_squeeze_setup | 3d | 57 | 50.88% | 0.90% | 1.88% | -13.02% | 1.74 | 34.93 |
| 18 | deleveraged_rebound | 1d | 38 | 52.63% | 0.61% | 1.32% | -9.16% | 1.78 | 32.37 |
| 19 | failed_volume_breakout | 2d | 13 | 53.85% | 1.04% | 0.89% | -4.84% | 1.64 | 31.38 |
| 20 | ecosystem_outflow_risk | 1d | 121 | 55.37% | 0.54% | 0.31% | -15.40% | 1.22 | 31.32 |

## Per-Signal Best Horizon

| Signal | Best Horizon | N | Hit Rate | Median Return | Score |
| --- | --- | ---: | ---: | ---: | ---: |
| leveraged_sell_pressure | 7d | 46 | 63.04% | 3.34% | 73.41 |
| market_volume_confirmation | 2d | 10 | 70.00% | 1.51% | 66.22 |
| failed_volume_breakout | 3d | 13 | 61.54% | 2.44% | 65.60 |
| deleveraged_rebound | 3d | 38 | 57.89% | 1.71% | 57.81 |
| price_ecosystem_divergence | 2d | 30 | 60.00% | 1.09% | 43.43 |
| volume_breakout | 1d | 87 | 59.77% | 0.52% | 41.69 |
| fee_activity_drop | 7d | 237 | 56.96% | 0.98% | 37.02 |
| basis_premium_fade | 7d | 144 | 55.56% | 1.21% | 36.81 |
| short_squeeze_setup | 3d | 57 | 50.88% | 0.90% | 34.93 |
| ecosystem_outflow_risk | 1d | 121 | 55.37% | 0.54% | 31.32 |
| oi_unwind_downtrend | 7d | 167 | 55.09% | 0.72% | 31.10 |
| stablecoin_inflow_momentum | 3d | 186 | 51.61% | 0.46% | 27.53 |
| ensemble_vote | 1d | 288 | 54.17% | 0.34% | 27.13 |
| leveraged_momentum | 1d | 80 | 55.00% | 0.15% | 26.53 |
| ecosystem_growth_confirmed | 7d | 170 | 50.00% | 0.07% | 25.38 |
| basis_discount_reversion | 3d | 165 | 49.70% | -0.10% | 18.67 |
| fee_activity_lag | 1d | 64 | 50.00% | 0.07% | 17.19 |
| crowded_long_risk | 2d | 31 | 38.71% | -0.39% | 16.34 |
| spot_led_accumulation | 1d | 24 | 33.33% | -1.21% | 15.00 |

## Caveats

- Ranking is in-sample. Do not treat top scores as production alpha yet.
- Next step is train/test or rolling validation across this full-history dataset.
- Mantle-native metrics are daily context; no fake hourly interpolation is used.
- CoinGecko market-cap context is partial and should not drive core signals.
