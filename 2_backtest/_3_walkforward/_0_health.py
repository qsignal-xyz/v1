from __future__ import annotations

import pandas as pd

LOOKBACK_DAYS = 120
MIN_EVENTS = 8
HIT_RATE_MIN = 0.55
MEDIAN_RETURN_MIN = 0.0
PROFIT_FACTOR_MIN = 1.2
WORST_RETURN_MIN = -0.12


def profit_factor(returns: pd.Series) -> float:
    wins = returns[returns > 0].sum()
    losses = -returns[returns < 0].sum()
    if losses == 0:
        return float("inf") if wins > 0 else 0.0
    return float(wins / losses)


def score_rows(rows: pd.DataFrame) -> dict[str, float | int | bool]:
    returns = rows["directional_return"].dropna()
    if returns.empty:
        return empty_health()
    hit_rate = float((returns > 0).mean())
    median_return = float(returns.median())
    avg_return = float(returns.mean())
    worst_return = float(returns.min())
    pf = profit_factor(returns)
    active = (
        len(returns) >= MIN_EVENTS
        and hit_rate >= HIT_RATE_MIN
        and median_return > MEDIAN_RETURN_MIN
        and pf >= PROFIT_FACTOR_MIN
        and worst_return > WORST_RETURN_MIN
    )
    return {
        "sample_count": int(len(returns)),
        "hit_rate": hit_rate,
        "median_return": median_return,
        "avg_return": avg_return,
        "worst_return": worst_return,
        "profit_factor": pf,
        "active": active,
    }


def empty_health() -> dict[str, float | int | bool]:
    return {
        "sample_count": 0,
        "hit_rate": 0.0,
        "median_return": 0.0,
        "avg_return": 0.0,
        "worst_return": 0.0,
        "profit_factor": 0.0,
        "active": False,
    }


def best_prior_health(
    event_returns: pd.DataFrame,
    signal_name: str,
    asof: pd.Timestamp,
    horizons: tuple[str, ...] = ("1d", "2d", "3d", "7d"),
) -> dict[str, object]:
    start = asof - pd.Timedelta(days=LOOKBACK_DAYS)
    prior = event_returns[
        (event_returns["signal_name"] == signal_name)
        & (event_returns["timestamp"] >= start)
        & (event_returns["timestamp"] < asof)
    ]
    rows: list[dict[str, object]] = []
    for horizon in horizons:
        metrics = score_rows(prior[prior["horizon"] == horizon])
        metrics["horizon"] = horizon
        metrics["health_score"] = health_score(metrics)
        rows.append(metrics)
    best = sorted(rows, key=lambda row: row["health_score"], reverse=True)[0]
    best["lookback_days"] = LOOKBACK_DAYS
    return best


def health_score(metrics: dict[str, object]) -> float:
    if int(metrics["sample_count"]) < MIN_EVENTS:
        return 0.0
    score = (
        min(1.0, max(0.0, (float(metrics["hit_rate"]) - 0.5) / 0.2)) * 35
        + min(1.0, max(0.0, float(metrics["median_return"]) / 0.03)) * 30
        + min(1.0, max(0.0, float(metrics["avg_return"]) / 0.04)) * 20
        + min(1.0, int(metrics["sample_count"]) / 20) * 15
    )
    return round(min(100.0, score), 2)
