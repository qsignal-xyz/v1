from __future__ import annotations

from typing import Any

import pandas as pd

MS_PER_HOUR = 60 * 60 * 1000


def fetch_klines_1h(
    client: Any,
    category: str,
    symbol: str,
    start_ms: int,
    end_ms: int,
) -> pd.DataFrame:
    rows: list[list[str]] = []
    cursor = start_ms
    while cursor <= end_ms:
        window_end = min(cursor + (999 * MS_PER_HOUR), end_ms)
        payload = client.get(
            "/v5/market/kline",
            {
                "category": category,
                "symbol": symbol,
                "interval": "60",
                "start": cursor,
                "end": window_end,
                "limit": 1000,
            },
        )
        rows.extend(payload.get("result", {}).get("list", []))
        cursor = window_end + MS_PER_HOUR

    columns = ["timestamp_ms", "open", "high", "low", "close", "volume_base", "turnover_quote"]
    frame = pd.DataFrame(rows, columns=columns)
    if frame.empty:
        return frame
    for column in columns:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    frame["timestamp"] = pd.to_datetime(frame["timestamp_ms"], unit="ms", utc=True)
    frame["symbol"] = symbol
    frame["category"] = category
    frame = frame.drop_duplicates("timestamp").sort_values("timestamp").reset_index(drop=True)
    return frame[
        [
            "timestamp",
            "timestamp_ms",
            "symbol",
            "category",
            "open",
            "high",
            "low",
            "close",
            "volume_base",
            "turnover_quote",
        ]
    ]

