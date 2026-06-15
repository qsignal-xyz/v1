from __future__ import annotations

from typing import Any

import pandas as pd

MS_PER_HOUR = 60 * 60 * 1000


def fetch_funding(
    client: Any,
    symbol: str,
    start_ms: int,
    end_ms: int,
) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    cursor = start_ms
    while cursor <= end_ms:
        window_end = min(cursor + (199 * 8 * MS_PER_HOUR), end_ms)
        payload = client.get(
            "/v5/market/funding/history",
            {
                "category": "linear",
                "symbol": symbol,
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
    frame["timestamp_ms"] = pd.to_numeric(frame["fundingRateTimestamp"], errors="raise")
    frame["timestamp"] = pd.to_datetime(frame["timestamp_ms"], unit="ms", utc=True)
    frame["funding_rate"] = pd.to_numeric(frame["fundingRate"], errors="raise")
    frame["symbol"] = symbol
    frame = frame.drop_duplicates("timestamp").sort_values("timestamp").reset_index(drop=True)
    return frame[["timestamp", "timestamp_ms", "symbol", "funding_rate"]]

