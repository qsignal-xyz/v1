from __future__ import annotations

import pandas as pd

HORIZONS = (1, 2, 3, 7)


def event_returns(events: pd.DataFrame, paths: pd.DataFrame) -> pd.DataFrame:
    base_cols = ["timestamp", "bybit_perp_close"]
    path_cols = base_cols + [
        col for col in paths.columns if col.startswith(("fwd_ret_", "fwd_low_", "fwd_high_"))
    ]
    merged = events.merge(paths[path_cols], on="timestamp", how="left")
    rows: list[dict[str, object]] = []
    for _, event in merged.iterrows():
        for horizon in HORIZONS:
            raw_ret = event[f"fwd_ret_{horizon}d"]
            if pd.isna(raw_ret):
                continue
            direction = int(event["direction"])
            if direction > 0:
                adverse = min(0.0, float(event[f"fwd_low_{horizon}d"]))
            else:
                adverse = min(0.0, -float(event[f"fwd_high_{horizon}d"]))
            rows.append(
                {
                    "timestamp": event["timestamp"],
                    "signal_name": event["signal_name"],
                    "horizon": f"{horizon}d",
                    "direction": direction,
                    "direction_label": event["direction_label"],
                    "strength": float(event["strength"]),
                    "raw_forward_return": float(raw_ret),
                    "directional_return": float(raw_ret) * direction,
                    "max_adverse_excursion": adverse,
                    "entry_price": float(event["entry_price"]),
                    "reason": event["reason"],
                }
            )
    return pd.DataFrame(rows)


def ensemble_events(events: pd.DataFrame, min_abs_score: float = 1.25) -> pd.DataFrame:
    if events.empty:
        return events.copy()
    votes = events.assign(vote=events["direction"] * events["strength"])
    grouped = votes.groupby("timestamp", as_index=False).agg(
        net_score=("vote", "sum"),
        rule_count=("signal_name", "count"),
        reasons=("signal_name", lambda values: ", ".join(sorted(values)[:6])),
        entry_price=("entry_price", "last"),
    )
    grouped = grouped[grouped["net_score"].abs() >= min_abs_score].copy()
    if grouped.empty:
        return events.iloc[0:0].copy()
    grouped["signal_name"] = "ensemble_vote"
    grouped["direction"] = grouped["net_score"].map(lambda value: 1 if value > 0 else -1)
    grouped["direction_label"] = grouped["direction"].map(lambda value: "long" if value > 0 else "short")
    grouped["strength"] = (grouped["net_score"].abs() / 3.0).clip(0.25, 1.0)
    grouped["reason"] = "combined agreement: " + grouped["reasons"]
    return grouped[
        ["timestamp", "signal_name", "direction", "direction_label", "strength", "reason", "entry_price"]
    ].reset_index(drop=True)

