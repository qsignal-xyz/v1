# Walk-Forward Signal Health

Uses one fixed 120-day lookback. Each day only sees signal outcomes before that day.

- evaluated fired-signal rows: `1689`
- recommendation days: `969`
- active recommendation days: `263`

## Recommendation Replay

| Horizon | Active Days | Coverage | Hit Rate | Median Return | Avg Return | Worst |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1d | 263 | 27.14% | 56.27% | 0.49% | 0.71% | -10.23% |
| 2d | 263 | 27.14% | 52.47% | 0.33% | 0.82% | -12.49% |
| 3d | 263 | 27.14% | 53.05% | 0.55% | 1.00% | -25.13% |
| 7d | 263 | 27.14% | 51.94% | 0.39% | 1.78% | -29.65% |

## Realized Outcomes After Active Fires

| Signal | Horizon | Active Fires | Hit Rate | Median Return | Avg Return | Worst |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| basis_premium_fade | 3d | 11 | 81.82% | 2.45% | 2.66% | -15.21% |
| stablecoin_inflow_momentum | 7d | 33 | 75.76% | 8.43% | 9.54% | -14.14% |
| fee_activity_drop | 3d | 12 | 75.00% | 1.64% | 0.79% | -7.62% |
| ecosystem_growth_confirmed | 7d | 10 | 70.00% | 7.19% | 2.91% | -18.94% |
| fee_activity_drop | 2d | 18 | 61.11% | 1.41% | 0.26% | -6.81% |
| ecosystem_growth_confirmed | 2d | 30 | 60.00% | 1.39% | 1.30% | -9.89% |
| ecosystem_outflow_risk | 3d | 12 | 58.33% | 0.89% | 2.79% | -7.49% |
| basis_premium_fade | 1d | 26 | 57.69% | 0.52% | 0.32% | -7.20% |
| oi_unwind_downtrend | 7d | 16 | 56.25% | 1.57% | 0.11% | -16.41% |
| ecosystem_outflow_risk | 1d | 9 | 55.56% | 0.46% | -0.49% | -6.52% |
| stablecoin_inflow_momentum | 3d | 13 | 53.85% | 0.19% | 0.80% | -8.66% |
| stablecoin_inflow_momentum | 2d | 19 | 52.63% | 0.97% | 1.87% | -8.61% |
| fee_activity_drop | 7d | 10 | 50.00% | -0.01% | -1.84% | -29.65% |
| basis_discount_reversion | 7d | 11 | 45.45% | -0.54% | 6.15% | -11.21% |
| leveraged_momentum | 3d | 9 | 44.44% | -0.26% | 1.86% | -9.25% |
| volume_breakout | 3d | 16 | 37.50% | -0.85% | 1.59% | -13.45% |
| short_squeeze_setup | 1d | 8 | 37.50% | -1.53% | -1.05% | -6.95% |
| short_squeeze_setup | 3d | 11 | 36.36% | -1.37% | -1.69% | -9.66% |
| volume_breakout | 7d | 2 | 100.00% | 24.56% | 24.56% | 17.70% |
| fee_activity_lag | 1d | 1 | 100.00% | 9.83% | 9.83% | 9.83% |
| leveraged_sell_pressure | 1d | 3 | 100.00% | 3.32% | 2.73% | 1.41% |
| volume_breakout | 2d | 4 | 100.00% | 2.44% | 3.61% | 1.07% |
| leveraged_momentum | 2d | 1 | 100.00% | 0.97% | 0.97% | 0.97% |
| fee_activity_lag | 7d | 4 | 75.00% | 11.32% | 7.42% | -8.86% |
| volume_breakout | 1d | 6 | 66.67% | 4.11% | 3.55% | -3.43% |
| oi_unwind_downtrend | 1d | 6 | 66.67% | 0.59% | -0.34% | -5.62% |
| basis_premium_fade | 7d | 5 | 60.00% | 1.28% | -1.00% | -13.92% |
| short_squeeze_setup | 2d | 2 | 50.00% | -0.31% | -0.31% | -1.81% |
| basis_discount_reversion | 1d | 2 | 50.00% | -0.81% | -0.81% | -1.82% |
| ecosystem_outflow_risk | 2d | 2 | 50.00% | -3.08% | -3.08% | -6.54% |

## Prior 120d Health Used For Decisions

| Signal | Horizon | Active Fires | Prior Hit Rate | Prior Median | Prior Avg | Prior Worst | Avg Health |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| basis_premium_fade | 7d | 5 | 76.52% | 4.25% | 3.73% | -5.38% | 98.30 |
| fee_activity_drop | 7d | 10 | 77.01% | 2.89% | 4.66% | -4.98% | 97.56 |
| ecosystem_growth_confirmed | 7d | 10 | 73.02% | 7.56% | 10.83% | -9.51% | 93.61 |
| leveraged_sell_pressure | 7d | 1 | 75.00% | 4.20% | 6.24% | -9.08% | 91.00 |
| stablecoin_inflow_momentum | 7d | 33 | 69.77% | 6.68% | 7.58% | -9.47% | 89.67 |
| deleveraged_rebound | 3d | 2 | 70.83% | 9.68% | 9.93% | -8.95% | 88.46 |
| deleveraged_rebound | 2d | 3 | 68.43% | 3.32% | 4.28% | -8.22% | 87.84 |
| volume_breakout | 3d | 16 | 66.65% | 3.85% | 5.53% | -6.67% | 87.63 |
| basis_premium_fade | 3d | 11 | 71.65% | 3.32% | 3.52% | -6.25% | 87.55 |
| basis_discount_reversion | 7d | 11 | 71.96% | 11.15% | 14.83% | -7.87% | 84.02 |
| volume_breakout | 7d | 2 | 63.60% | 3.07% | 5.56% | -8.38% | 82.77 |
| fee_activity_lag | 7d | 4 | 63.20% | 4.77% | 5.38% | -8.28% | 80.79 |
| short_squeeze_setup | 3d | 11 | 66.50% | 4.30% | 4.69% | -8.49% | 80.10 |
| stablecoin_inflow_momentum | 3d | 13 | 67.00% | 3.89% | 4.44% | -9.66% | 80.08 |
| ecosystem_growth_confirmed | 3d | 3 | 65.02% | 3.78% | 3.27% | -9.70% | 78.89 |
| fee_activity_drop | 3d | 12 | 72.99% | 2.55% | 2.22% | -8.78% | 76.03 |
| leveraged_momentum | 3d | 9 | 69.29% | 4.58% | 2.95% | -8.11% | 75.78 |
| short_squeeze_setup | 2d | 2 | 64.58% | 2.60% | 3.33% | -2.83% | 74.51 |
| leveraged_sell_pressure | 1d | 3 | 75.00% | 2.53% | 2.36% | -4.18% | 73.70 |
| ecosystem_outflow_risk | 3d | 12 | 65.72% | 2.82% | 2.56% | -6.89% | 72.75 |
| leveraged_momentum | 7d | 6 | 61.12% | 3.16% | 4.97% | -6.80% | 71.80 |
| basis_discount_reversion | 2d | 6 | 67.57% | 4.85% | 4.75% | -6.72% | 70.48 |
| oi_unwind_downtrend | 7d | 16 | 69.60% | 1.44% | 1.95% | -8.85% | 69.69 |
| stablecoin_inflow_momentum | 2d | 19 | 66.33% | 1.45% | 2.82% | -8.28% | 68.95 |
| fee_activity_drop | 2d | 18 | 66.43% | 1.95% | 1.17% | -8.81% | 68.95 |
| volume_breakout | 2d | 4 | 75.27% | 1.51% | 1.79% | -2.63% | 67.47 |
| oi_unwind_downtrend | 3d | 7 | 65.40% | 1.74% | 1.09% | -7.76% | 63.79 |
| basis_discount_reversion | 3d | 1 | 59.09% | 1.83% | 2.60% | -5.07% | 62.27 |
| ecosystem_growth_confirmed | 2d | 30 | 67.28% | 1.40% | 1.90% | -7.34% | 60.70 |
| volume_breakout | 1d | 6 | 70.33% | 0.98% | 1.83% | -4.97% | 56.81 |
| basis_premium_fade | 1d | 26 | 65.83% | 1.29% | 0.60% | -6.21% | 56.17 |
| oi_unwind_downtrend | 1d | 6 | 72.58% | 0.67% | 0.34% | -5.32% | 56.13 |
| short_squeeze_setup | 1d | 8 | 73.20% | 0.58% | 1.21% | -5.54% | 54.20 |
| basis_premium_fade | 2d | 7 | 59.60% | 1.90% | 0.98% | -9.66% | 52.41 |
| fee_activity_lag | 3d | 2 | 61.11% | 1.58% | 1.91% | -7.12% | 51.55 |
| oi_unwind_downtrend | 2d | 2 | 60.15% | 1.66% | 0.85% | -5.92% | 50.96 |
| ecosystem_outflow_risk | 2d | 2 | 64.10% | 1.20% | 0.91% | -5.94% | 49.48 |
| fee_activity_lag | 1d | 1 | 62.50% | 0.80% | 2.67% | -4.11% | 49.27 |
| stablecoin_inflow_momentum | 1d | 5 | 59.18% | 1.58% | 0.61% | -6.09% | 45.46 |
| ecosystem_outflow_risk | 1d | 9 | 61.59% | 0.66% | 1.15% | -5.98% | 41.10 |
| leveraged_momentum | 1d | 2 | 56.25% | 0.70% | 2.10% | -6.28% | 40.39 |
| spot_led_accumulation | 2d | 2 | 59.03% | 0.42% | 2.33% | -10.55% | 38.05 |
| leveraged_momentum | 2d | 1 | 56.25% | 0.53% | 1.57% | -8.09% | 36.07 |
| basis_discount_reversion | 1d | 2 | 57.17% | 0.32% | 0.66% | -5.71% | 31.02 |

## Latest Recommendation

- date: `2026-06-29 00:00:00+00:00`
- action: `neutral_yield`
- long score: `0.0`
- short score: `0.0`
- active signals: `none`
