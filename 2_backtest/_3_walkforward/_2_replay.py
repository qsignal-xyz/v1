from __future__ import annotations

import pandas as pd

HORIZONS = (1, 2, 3, 7)


def replay_recommendations(recs: pd.DataFrame, paths: pd.DataFrame) -> pd.DataFrame:
    cols = ["timestamp"] + [f"fwd_ret_{h}d" for h in HORIZONS]
    out = recs.merge(paths[cols], on="timestamp", how="left")
    for horizon in HORIZONS:
        raw = out[f"fwd_ret_{horizon}d"]
        out[f"directional_return_{horizon}d"] = raw * out["direction"]
        out.loc[out["direction"] == 0, f"directional_return_{horizon}d"] = 0.0
    return out


def summarize_recommendations(replayed: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for horizon in HORIZONS:
        col = f"directional_return_{horizon}d"
        active = replayed[replayed["direction"] != 0]
        returns = active[col].dropna()
        rows.append(summary_row(f"{horizon}d", returns, len(active), len(replayed)))
    return pd.DataFrame(rows)


def active_signal_outcomes(health: pd.DataFrame, event_returns: pd.DataFrame) -> pd.DataFrame:
    active = health[health["active"] == True].copy()
    if active.empty:
        return active
    cols = [
        "timestamp",
        "signal_name",
        "horizon",
        "directional_return",
        "raw_forward_return",
        "max_adverse_excursion",
    ]
    return active.merge(event_returns[cols], on=["timestamp", "signal_name", "horizon"], how="left")


def summarize_active_signals(outcomes: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if outcomes.empty:
        return pd.DataFrame(rows)
    for (signal, horizon), group in outcomes.groupby(["signal_name", "horizon"], sort=True):
        returns = group["directional_return"].dropna()
        if returns.empty:
            continue
        rows.append(
            {
                "signal_name": signal,
                "horizon": horizon,
                "active_fires": len(returns),
                "hit_rate": float((returns > 0).mean()),
                "median_return": float(returns.median()),
                "avg_return": float(returns.mean()),
                "worst_return": float(returns.min()),
            }
        )
    out = pd.DataFrame(rows)
    out["enough_fires"] = out["active_fires"] >= 8
    return out.sort_values(
        ["enough_fires", "hit_rate", "median_return", "active_fires"],
        ascending=[False, False, False, False],
    ).drop(columns=["enough_fires"])


def summary_row(horizon: str, returns: pd.Series, active_days: int, total_days: int) -> dict[str, object]:
    if returns.empty:
        return {
            "horizon": horizon,
            "active_days": active_days,
            "total_days": total_days,
            "coverage_pct": 0.0,
            "hit_rate": 0.0,
            "median_return": 0.0,
            "avg_return": 0.0,
            "worst_return": 0.0,
        }
    return {
        "horizon": horizon,
        "active_days": active_days,
        "total_days": total_days,
        "coverage_pct": active_days / total_days if total_days else 0.0,
        "hit_rate": float((returns > 0).mean()),
        "median_return": float(returns.median()),
        "avg_return": float(returns.mean()),
        "worst_return": float(returns.min()),
    }
