# Signal Rules

The first signal layer uses 20 explainable daily rules. These are intentionally simple:
no ML, no private thresholds, and no searched parameter grid.

## Long Candidates

| Signal | Idea |
| --- | --- |
| `leveraged_momentum` | Price up with rising OI and perp volume. |
| `spot_led_accumulation` | Spot volume leads perps while price rises. |
| `short_squeeze_setup` | Negative funding while price holds above 7d mean. |
| `ecosystem_growth_confirmed` | Mantle TVL, stables, and DEX activity confirm growth. |
| `basis_discount_reversion` | Perp trades unusually cheap to spot. |
| `fee_activity_lag` | Mantle fee activity rises before price reacts. |
| `stablecoin_inflow_momentum` | Stablecoin supply expands while price trend is positive. |
| `deleveraged_rebound` | Sharp drop with falling leverage and non-crowded funding. |
| `volume_breakout` | Spot and perp volume confirm an upside breakout. |
| `market_volume_confirmation` | Aggregate MNT volume confirms price and OI. |

## Short / Risk-Off Candidates

| Signal | Idea |
| --- | --- |
| `crowded_long_risk` | Positive funding and rising OI without price progress. |
| `leveraged_sell_pressure` | Price falls while leverage and perp volume rise. |
| `perp_pump_without_spot` | Perp-led pump lacks spot confirmation. |
| `ecosystem_outflow_risk` | Mantle TVL and stables contract together. |
| `basis_premium_fade` | Perp trades rich while funding is elevated. |
| `fee_activity_drop` | App and chain fee activity deteriorate. |
| `oi_unwind_downtrend` | Price downtrend with open interest unwind. |
| `failed_volume_breakout` | Large perp volume closes red without spot support. |
| `bearish_market_volume` | Aggregate volume confirms downside with rising OI. |
| `price_ecosystem_divergence` | Price rallies while Mantle TVL and stables fall. |

## Outputs

- `1_signal/cache/daily_features_2026.parquet`
- `1_signal/cache/daily_signal_events_2026.parquet`
- `1_signal/cache/daily_signal_events_2026.csv`
- `1_signal/cache/daily_signal_summary_2026.json`

