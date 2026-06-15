from __future__ import annotations

from typing import Any

import pandas as pd

MS_PER_HOUR = 60 * 60 * 1000


def fetch_open_interest_1h(
    client: Any,
    symbol: str,
    start_ms: int,
    end_ms: int,
) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    cursor = start_ms
    while cursor <= end_ms:
        window_end = min(cursor + (199 * MS_PER_HOUR), end_ms)
        payload = client.get(
            "/v5/market/open-interest",
            {
                "category": "linear",
                "symbol": symbol,
                "intervalTime": "1h",
                "startTime": cursor,
                "endTime": window_end,
                "limit": 200,
            },
        )
        rows.extend(payload.get("result", {}).get("list", []))
        cursor = window_end + MS_PER_HOUR

    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["timestamp_ms"] = pd.to_numeric(frame["timestamp"], errors="raise")
    frame["timestamp"] = pd.to_datetime(frame["timestamp_ms"], unit="ms", utc=True)
    frame["open_interest"] = pd.to_numeric(frame["openInterest"], errors="raise")
    frame["single_open_interest"] = pd.to_numeric(frame["singleOpenInterest"], errors="raise")
    frame["symbol"] = symbol
    frame = frame.drop_duplicates("timestamp").sort_values("timestamp").reset_index(drop=True)
    return frame[["timestamp", "timestamp_ms", "symbol", "open_interest", "single_open_interest"]]

