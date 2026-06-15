from __future__ import annotations

import numpy as np
import pandas as pd


def _profit_factor(returns: pd.Series) -> float:
    wins = returns[returns > 0].sum()
    losses = -returns[returns < 0].sum()
    if losses == 0:
        return float("inf") if wins > 0 else 0.0
    return float(wins / losses)


def summarize(event_returns: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    grouped = event_returns.groupby(["signal_name", "horizon"], sort=True)
    for (signal_name, horizon), group in grouped:
        returns = group["directional_return"].dropna()
        if returns.empty:
            continue
        signal_values = group["direction"] * group["strength"]
        raw_values = group["raw_forward_return"]
        ic = signal_values.corr(raw_values) if len(group) >= 3 else np.nan
        rows.append(
            {
                "signal_name": signal_name,
                "horizon": horizon,
                "sample_count": int(len(returns)),
                "hit_rate": float((returns > 0).mean()),
                "avg_directional_return": float(returns.mean()),
                "median_directional_return": float(returns.median()),
                "profit_factor": _profit_factor(returns),
                "worst_directional_return": float(returns.min()),
                "avg_adverse_excursion": float(group["max_adverse_excursion"].mean()),
                "ic": float(ic) if not pd.isna(ic) else np.nan,
            }
        )
    return pd.DataFrame(rows).sort_values(["signal_name", "horizon"]).reset_index(drop=True)


def rank_signals(summary: pd.DataFrame, min_samples: int = 10) -> pd.DataFrame:
    ranked = summary[summary["sample_count"] >= min_samples].copy()
    if ranked.empty:
        return ranked
    ranked["score"] = (
        ((ranked["hit_rate"] - 0.5) / 0.2).clip(0, 1) * 35
        + (ranked["median_directional_return"] / 0.03).clip(0, 1) * 30
        + (ranked["avg_directional_return"] / 0.04).clip(0, 1) * 20
        + (ranked["sample_count"] / 20).clip(0, 1) * 15
    ).round(2)
    ranked = ranked.sort_values(
        ["score", "sample_count", "median_directional_return"],
        ascending=[False, False, False],
    )
    return ranked.reset_index(drop=True)
