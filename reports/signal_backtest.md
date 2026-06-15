# Signal Backtest

This is a research ranking, not a deployable trading claim. Rules are simple and explainable; later work should add out-of-sample validation before using weights live.

- date range: `2023-11-12 00:00:00+00:00` -> `2026-06-13 00:00:00+00:00`
- signal events: `1957`
- evaluated event-horizon rows: `7815`
- unique signals: `21`

## Top Ranked Signal-Horizons

| Rank | Signal | Horizon | N | Hit Rate | Median Return | Avg Return | Worst | PF | Score |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | leveraged_sell_pressure | 7d | 46 | 63.04% | 3.34% | 1.12% | -33.38% | 1.28 | 73.41 |
| 2 | market_volume_confirmation | 2d | 10 | 70.00% | 1.51% | 1.73% | -9.42% | 1.79 | 66.22 |
| 3 | failed_volume_breakout | 3d | 13 | 61.54% | 2.44% | 2.25% | -21.31% | 1.67 | 65.60 |
| 4 | deleveraged_rebound | 3d | 37 | 59.46% | 2.06% | 2.53% | -15.53% | 2.07 | 64.79 |
| 5 | failed_volume_breakout | 7d | 13 | 53.85% | 4.89% | -1.31% | -51.95% | 0.84 | 46.48 |
| 6 | deleveraged_rebound | 2d | 37 | 54.05% | 1.16% | 2.21% | -14.45% | 2.09 | 44.75 |
| 7 | failed_volume_breakout | 1d | 13 | 61.54% | 1.41% | -0.04% | -17.01% | 0.98 | 44.07 |
| 8 | price_ecosystem_divergence | 2d | 30 | 60.00% | 1.09% | -1.28% | -23.18% | 0.66 | 43.43 |
| 9 | volume_breakout | 1d | 87 | 59.77% | 0.52% | 0.87% | -12.96% | 1.51 | 41.69 |
| 10 | price_ecosystem_divergence | 1d | 30 | 56.67% | 1.34% | -0.39% | -15.40% | 0.85 | 40.11 |
| 11 | price_ecosystem_divergence | 3d | 30 | 53.33% | 1.90% | -1.12% | -27.37% | 0.75 | 39.84 |
| 12 | deleveraged_rebound | 1d | 37 | 54.05% | 1.06% | 1.38% | -9.16% | 1.80 | 39.58 |
| 13 | volume_breakout | 2d | 87 | 54.02% | 0.97% | 1.12% | -36.02% | 1.50 | 37.39 |
| 14 | fee_activity_drop | 7d | 237 | 56.96% | 0.98% | -1.24% | -45.96% | 0.77 | 37.02 |
| 15 | market_volume_confirmation | 1d | 10 | 60.00% | 0.70% | 0.97% | -4.25% | 1.78 | 36.81 |
| 16 | leveraged_sell_pressure | 3d | 46 | 54.35% | 0.82% | 1.08% | -15.79% | 1.52 | 36.17 |
| 17 | basis_premium_fade | 7d | 143 | 55.24% | 1.14% | -1.01% | -30.89% | 0.80 | 35.54 |
| 18 | short_squeeze_setup | 3d | 57 | 50.88% | 0.90% | 1.88% | -13.02% | 1.74 | 34.93 |
| 19 | failed_volume_breakout | 2d | 13 | 53.85% | 1.04% | 0.89% | -4.84% | 1.64 | 31.38 |
| 20 | oi_unwind_downtrend | 7d | 167 | 55.09% | 0.72% | -2.70% | -55.97% | 0.56 | 31.10 |

## Per-Signal Best Horizon

| Signal | Best Horizon | N | Hit Rate | Median Return | Score |
| --- | --- | ---: | ---: | ---: | ---: |
| leveraged_sell_pressure | 7d | 46 | 63.04% | 3.34% | 73.41 |
| market_volume_confirmation | 2d | 10 | 70.00% | 1.51% | 66.22 |
| failed_volume_breakout | 3d | 13 | 61.54% | 2.44% | 65.60 |
| deleveraged_rebound | 3d | 37 | 59.46% | 2.06% | 64.79 |
| price_ecosystem_divergence | 2d | 30 | 60.00% | 1.09% | 43.43 |
| volume_breakout | 1d | 87 | 59.77% | 0.52% | 41.69 |
| fee_activity_drop | 7d | 237 | 56.96% | 0.98% | 37.02 |
| basis_premium_fade | 7d | 143 | 55.24% | 1.14% | 35.54 |
| short_squeeze_setup | 3d | 57 | 50.88% | 0.90% | 34.93 |
| oi_unwind_downtrend | 7d | 167 | 55.09% | 0.72% | 31.10 |
| ecosystem_outflow_risk | 1d | 115 | 54.78% | 0.52% | 29.46 |
| stablecoin_inflow_momentum | 3d | 186 | 51.61% | 0.46% | 27.53 |
| leveraged_momentum | 1d | 80 | 55.00% | 0.15% | 26.53 |
| ensemble_vote | 1d | 286 | 53.85% | 0.30% | 26.15 |
| ecosystem_growth_confirmed | 7d | 170 | 50.00% | 0.07% | 25.38 |
| basis_discount_reversion | 2d | 162 | 50.62% | 0.10% | 20.33 |
| fee_activity_lag | 1d | 64 | 50.00% | 0.07% | 17.19 |
| crowded_long_risk | 2d | 30 | 36.67% | -0.60% | 15.97 |
| spot_led_accumulation | 1d | 24 | 33.33% | -1.21% | 15.00 |

## Caveats

- Ranking is in-sample. Do not treat top scores as production alpha yet.
- Next step is train/test or rolling validation across this full-history dataset.
- Mantle-native metrics are daily context; no fake hourly interpolation is used.
- CoinGecko market-cap context is partial and should not drive core signals.
