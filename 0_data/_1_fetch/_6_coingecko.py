from __future__ import annotations

import time
from datetime import timedelta, timezone

import pandas as pd
import requests


def fetch_mnt_market_daily(start_ms: int, end_ms: int) -> pd.DataFrame:
    start = pd.to_datetime(start_ms, unit="ms", utc=True)
    end = pd.to_datetime(end_ms, unit="ms", utc=True)
    start = max(start, end - timedelta(days=364))
    payloads: list[dict[str, list[list[float]]]] = []
    cursor = start
    headers = {"User-Agent": "Mozilla/5.0 (compatible; research-script; +local-analysis)"}
    while cursor <= end:
        chunk_end = min(cursor + timedelta(days=80), end)
        url = (
            "https://api.coingecko.com/api/v3/coins/mantle/market_chart/range"
            f"?vs_currency=usd&from={int(cursor.timestamp())}&to={int(chunk_end.timestamp())}"
        )
        last_status = "not-requested"
        for attempt in range(4):
            response = requests.get(url, timeout=30, headers=headers)
            last_status = f"{response.status_code}: {response.text[:120]}"
            if response.status_code == 429:
                time.sleep(3 * (attempt + 1))
                continue
            if response.status_code == 401:
                return _empty_market_frame()
            response.raise_for_status()
            payloads.append(response.json())
            break
        else:
            raise RuntimeError(f"CoinGecko chunk failed after retries: {last_status}")
        cursor = chunk_end + timedelta(days=1)

    frames = []
    for source_key, column in [
        ("prices", "mnt_coingecko_price_usd"),
        ("market_caps", "mnt_market_cap_usd"),
        ("total_volumes", "mnt_total_volume_usd"),
    ]:
        rows = [row for payload in payloads for row in payload[source_key]]
        frame = pd.DataFrame(rows, columns=["timestamp_ms", column])
        frame["timestamp"] = pd.to_datetime(frame["timestamp_ms"], unit="ms", utc=True)
        frame["timestamp"] = frame["timestamp"].dt.tz_convert(timezone.utc).dt.floor("D")
        frame[column] = pd.to_numeric(frame[column], errors="raise")
        frames.append(frame[["timestamp", column]])

    out = frames[0]
    for frame in frames[1:]:
        out = out.merge(frame, on="timestamp", how="outer")
    return out.drop_duplicates("timestamp").sort_values("timestamp").reset_index(drop=True)


def _empty_market_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=["timestamp", "mnt_coingecko_price_usd", "mnt_market_cap_usd", "mnt_total_volume_usd"]
    )
