from __future__ import annotations

import pandas as pd


def build_walkforward(
    events: pd.DataFrame,
    event_returns: pd.DataFrame,
    health_mod: object,
    all_dates: pd.Series | None = None,
    threshold: float = 0.25,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    health_rows: list[dict[str, object]] = []
    recommendation_rows: list[dict[str, object]] = []
    grouped = {date: group for date, group in events.groupby("timestamp", sort=True)}
    dates = sorted(all_dates.dropna().unique()) if all_dates is not None else sorted(grouped)
    for date in dates:
        day_events = grouped.get(date, events.iloc[0:0])
        long_score = 0.0
        short_score = 0.0
        active_names: list[str] = []
        for _, event in day_events.iterrows():
            health = health_mod.best_prior_health(event_returns, event["signal_name"], date)
            row = {**event.to_dict(), **health}
            health_rows.append(row)
            if not bool(health["active"]):
                continue
            signed_score = float(event["strength"]) * float(health["health_score"]) / 100.0
            active_names.append(f"{event['signal_name']}:{health['horizon']}")
            if int(event["direction"]) > 0:
                long_score += signed_score
            else:
                short_score += signed_score
        recommendation_rows.append(
            daily_recommendation(date, long_score, short_score, active_names, threshold)
        )
    return pd.DataFrame(health_rows), pd.DataFrame(recommendation_rows)


def daily_recommendation(
    timestamp: pd.Timestamp,
    long_score: float,
    short_score: float,
    active_names: list[str],
    threshold: float,
) -> dict[str, object]:
    net_score = long_score - short_score
    if net_score > threshold:
        action = "long"
        direction = 1
    elif net_score < -threshold:
        action = "risk_off_short"
        direction = -1
    else:
        action = "neutral_yield"
        direction = 0
    return {
        "timestamp": timestamp,
        "action": action,
        "direction": direction,
        "long_score": round(long_score, 4),
        "short_score": round(short_score, 4),
        "net_score": round(net_score, 4),
        "active_signal_count": len(active_names),
        "active_signals": ", ".join(active_names[:8]),
    }
