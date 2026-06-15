from __future__ import annotations

import pandas as pd

HORIZONS = (1, 2, 3, 7)


def add_forward_paths(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy().sort_values("timestamp").reset_index(drop=True)
    close = out["bybit_perp_close"]
    high = out["bybit_perp_high"]
    low = out["bybit_perp_low"]
    for horizon in HORIZONS:
        out[f"fwd_ret_{horizon}d"] = close.shift(-horizon) / close - 1.0
        lows = [low.shift(-step) for step in range(1, horizon + 1)]
        highs = [high.shift(-step) for step in range(1, horizon + 1)]
        out[f"fwd_low_{horizon}d"] = pd.concat(lows, axis=1).min(axis=1) / close - 1.0
        out[f"fwd_high_{horizon}d"] = pd.concat(highs, axis=1).max(axis=1) / close - 1.0
    return out

