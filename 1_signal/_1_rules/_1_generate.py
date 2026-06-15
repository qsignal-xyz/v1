from __future__ import annotations

import pandas as pd


def generate_events(frame: pd.DataFrame, rules: list[dict[str, object]]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for rule in rules:
        mask = rule["mask"]
        strength = rule["strength"]
        selected = frame[mask].copy()
        for idx, row in selected.iterrows():
            rows.append(
                {
                    "timestamp": row["timestamp"],
                    "signal_name": rule["name"],
                    "direction": int(rule["direction"]),
                    "direction_label": "long" if int(rule["direction"]) > 0 else "short",
                    "strength": round(float(strength.loc[idx]), 4),
                    "reason": rule["reason"],
                    "entry_price": float(row["bybit_perp_close"]),
                }
            )
    return pd.DataFrame(rows).sort_values(["timestamp", "signal_name"]).reset_index(drop=True)

