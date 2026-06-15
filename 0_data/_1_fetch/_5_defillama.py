from __future__ import annotations

import time
from typing import Any

import pandas as pd
import requests


class DefiLlamaClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (compatible; research-script; +local-analysis)"}
        )

    def get_json(self, url: str) -> Any:
        last_error: Exception | None = None
        for attempt in range(4):
            if attempt:
                time.sleep(1.5 * attempt)
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response.json()
            except Exception as exc:
                last_error = exc
        raise RuntimeError(f"DefiLlama request failed: {url}") from last_error


def chart_from_pairs(rows: list[list[Any]], column: str) -> pd.DataFrame:
    frame = pd.DataFrame(rows, columns=["timestamp_s", column])
    frame["timestamp_s"] = pd.to_numeric(frame["timestamp_s"], errors="raise")
    frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["timestamp"] = pd.to_datetime(frame["timestamp_s"], unit="s", utc=True)
    return frame[["timestamp", column]].dropna().sort_values("timestamp").reset_index(drop=True)


def tvl_daily(client: DefiLlamaClient) -> pd.DataFrame:
    rows = client.get_json("https://api.llama.fi/v2/historicalChainTvl/Mantle")
    frame = pd.DataFrame(rows).rename(columns={"date": "timestamp_s", "tvl": "mantle_tvl_usd"})
    frame["timestamp"] = pd.to_datetime(frame["timestamp_s"], unit="s", utc=True)
    frame["mantle_tvl_usd"] = pd.to_numeric(frame["mantle_tvl_usd"], errors="raise")
    return frame[["timestamp", "mantle_tvl_usd"]].sort_values("timestamp").reset_index(drop=True)


def dex_volume_daily(client: DefiLlamaClient) -> pd.DataFrame:
    data = client.get_json(
        "https://api.llama.fi/overview/dexs/mantle"
        "?excludeTotalDataChart=false&excludeTotalDataChartBreakdown=false&dataType=dailyVolume"
    )
    return chart_from_pairs(data["totalDataChart"], "mantle_dex_volume_usd")


def stables_daily(client: DefiLlamaClient) -> pd.DataFrame:
    rows = client.get_json("https://stablecoins.llama.fi/stablecoincharts/Mantle")
    out: list[dict[str, float | int]] = []
    for row in rows:
        out.append(
            {
                "timestamp_s": int(row["date"]),
                "mantle_stables_mcap_usd": float(
                    row.get("totalCirculatingUSD", {}).get("peggedUSD", 0.0)
                ),
                "mantle_stables_bridged_usd": float(
                    row.get("totalBridgedToUSD", {}).get("peggedUSD", 0.0)
                ),
            }
        )
    frame = pd.DataFrame(out)
    frame["timestamp"] = pd.to_datetime(frame["timestamp_s"], unit="s", utc=True)
    return frame[
        ["timestamp", "mantle_stables_mcap_usd", "mantle_stables_bridged_usd"]
    ].sort_values("timestamp").reset_index(drop=True)


def app_fees_daily(client: DefiLlamaClient) -> pd.DataFrame:
    data = client.get_json(
        "https://api.llama.fi/overview/fees/mantle"
        "?excludeTotalDataChart=false&excludeTotalDataChartBreakdown=false&dataType=dailyFees"
    )
    return chart_from_pairs(data["totalDataChart"], "mantle_app_fees_usd")


def app_revenue_daily(client: DefiLlamaClient) -> pd.DataFrame:
    data = client.get_json(
        "https://api.llama.fi/overview/fees/mantle"
        "?excludeTotalDataChart=false&excludeTotalDataChartBreakdown=false&dataType=dailyRevenue"
    )
    return chart_from_pairs(data["totalDataChart"], "mantle_app_revenue_usd")


def chain_fees_daily(client: DefiLlamaClient) -> pd.DataFrame:
    data = client.get_json("https://api.llama.fi/summary/fees/mantle")
    return chart_from_pairs(data["totalDataChart"], "mantle_chain_fees_usd")


def chain_revenue_daily(client: DefiLlamaClient) -> pd.DataFrame:
    data = client.get_json("https://api.llama.fi/summary/fees/mantle?dataType=dailyRevenue")
    return chart_from_pairs(data["totalDataChart"], "mantle_chain_revenue_usd")

