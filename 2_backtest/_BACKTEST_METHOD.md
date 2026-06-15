# Backtest Method

Input:

`1_signal/cache/daily_signal_events_2026.parquet`

Target:

Bybit MNTUSDT perp close-to-close forward returns.

Horizons:

- `1d`
- `2d`
- `3d`
- `7d`

For each event and horizon, the backtest records:

- raw forward return
- direction-adjusted return
- max adverse excursion from daily high/low path
- entry price
- signal reason

Per signal/horizon metrics:

- sample count
- hit rate
- average and median directional return
- profit factor
- worst directional return
- average adverse excursion
- simple IC

Ranking requires at least 10 events for a signal-horizon pair.

The ranking score is deliberately simple:

- 35% hit-rate above 50%
- 30% median directional return
- 20% average directional return
- 15% sample-count support

This is an in-sample research score, not a production allocation weight.

Outputs:

- `2_backtest/cache/daily_signal_events_with_ensemble_2026.csv`
- `2_backtest/cache/daily_event_returns_2026.csv`
- `2_backtest/cache/signal_summary_2026.csv`
- `2_backtest/cache/signal_rankings_2026.csv`
- `reports/signal_backtest_2026.md`

