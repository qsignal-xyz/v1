from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "0_data/cache/yields"
UA = "Mozilla/5.0 (compatible; research-script; +local-analysis)"
SYMBOLS = {"USDC", "USDT", "USDT0", "USDE", "SUSDE", "USDY"}


def get_json(session: requests.Session, url: str) -> Any:
    last_error: Exception | None = None
    for attempt in range(4):
        if attempt:
            time.sleep(1.5 * attempt)
        try:
            response = session.get(url, timeout=60)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"request failed: {url}") from last_error


def selected_pools(rows: list[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    mask = (
        frame["chain"].str.lower().eq("mantle")
        & frame["stablecoin"].eq(True)
        & frame["exposure"].eq("single")
        & frame["ilRisk"].eq("no")
        & frame["symbol"].str.upper().isin(SYMBOLS)
        & (pd.to_numeric(frame["tvlUsd"], errors="coerce") >= 500_000)
        & (pd.to_numeric(frame["apy"], errors="coerce") > 0)
    )
    cols = ["pool", "project", "symbol", "tvlUsd", "apy", "apyBase", "apyReward", "count"]
    return frame.loc[mask, cols].sort_values("tvlUsd", ascending=False).reset_index(drop=True)


def pool_chart(session: requests.Session, pool_id: str, meta: dict[str, Any]) -> pd.DataFrame:
    rows = get_json(session, f"https://yields.llama.fi/chart/{pool_id}")["data"]
    frame = pd.DataFrame(rows)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame["date"] = frame["timestamp"].dt.floor("D")
    for col in ["apy", "apyBase", "apyReward", "tvlUsd"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame = frame.sort_values("timestamp").groupby("date", as_index=False).tail(1)
    frame["pool"] = pool_id
    frame["project"] = meta["project"]
    frame["symbol"] = meta["symbol"]
    return frame[["date", "pool", "project", "symbol", "tvlUsd", "apy", "apyBase", "apyReward"]]


def weighted_daily(charts: pd.DataFrame) -> pd.DataFrame:
    if charts.empty:
        return pd.DataFrame(columns=["timestamp", "stable_yield_apy", "yield_tvl_usd", "yield_pool_count"])
    clean = charts.dropna(subset=["date", "apy", "tvlUsd"]).copy()
    clean = clean[(clean["apy"] >= 0) & (clean["apy"] <= 80) & (clean["tvlUsd"] > 0)]
    grouped = clean.groupby("date")
    daily = grouped.apply(
        lambda g: pd.Series(
            {
                "stable_yield_apy": float((g["apy"] * g["tvlUsd"]).sum() / g["tvlUsd"].sum()),
                "yield_tvl_usd": float(g["tvlUsd"].sum()),
                "yield_pool_count": int(len(g)),
            }
        ),
        include_groups=False,
    ).reset_index()
    return daily.rename(columns={"date": "timestamp"}).sort_values("timestamp").reset_index(drop=True)


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
    pools_json = get_json(session, "https://yields.llama.fi/pools")
    pools = selected_pools(pools_json["data"])
    pools.to_csv(CACHE / "mantle_stable_yield_pools.csv", index=False)
    charts = []
    for row in pools.to_dict("records"):
        chart = pool_chart(session, row["pool"], row)
        chart.to_parquet(CACHE / f"pool_{row['symbol']}_{row['pool']}.parquet", index=False)
        charts.append(chart)
        print(f"{row['symbol']} {row['project']} rows={len(chart)}")
    all_charts = pd.concat(charts, ignore_index=True) if charts else pd.DataFrame()
    all_charts.to_parquet(CACHE / "mantle_stable_yield_pool_charts.parquet", index=False)
    daily = weighted_daily(all_charts)
    daily.to_parquet(CACHE / "mantle_stable_yield_daily.parquet", index=False)
    summary = {
        "pool_count": int(len(pools)),
        "rows": int(len(daily)),
        "start": str(daily["timestamp"].min()) if not daily.empty else None,
        "end": str(daily["timestamp"].max()) if not daily.empty else None,
        "source": "https://yields.llama.fi/pools and /chart/{pool}",
    }
    (CACHE / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
