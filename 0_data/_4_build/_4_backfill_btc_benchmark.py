from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
SYMBOL = "BTCUSDT"
START = "2024-06-01T00:00:00Z"


def load_module(rel_path: str, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, ROOT / rel_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {rel_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


time_mod = load_module("0_data/_0_types/_1_time.py", "time_mod")
client_mod = load_module("0_data/_1_fetch/_0_bybit_client.py", "bybit_client")
klines_mod = load_module("0_data/_1_fetch/_2_klines.py", "klines")


def append_hourly(path: Path, client: Any, start_ms: int, end_ms: int) -> pd.DataFrame:
    if path.exists():
        old = pd.read_parquet(path)
        if not old.empty:
            next_ms = int(old["timestamp_ms"].max()) + time_mod.MS_PER_HOUR
            if next_ms > end_ms:
                return old
            start_ms = max(start_ms, next_ms)
    else:
        old = pd.DataFrame()
    new = klines_mod.fetch_klines_1h(client, "spot", SYMBOL, start_ms, end_ms)
    out = pd.concat([old, new], ignore_index=True)
    out = out.drop_duplicates("timestamp").sort_values("timestamp").reset_index(drop=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(path, index=False)
    return out


def daily_from_hourly(hourly: pd.DataFrame) -> pd.DataFrame:
    complete = hourly.copy()
    complete["date"] = complete["timestamp"].dt.floor("D")
    counts = complete.groupby("date")["timestamp"].transform("count")
    complete = complete[counts == 24]
    daily = complete.groupby("date", as_index=False).agg(
        timestamp=("date", "first"),
        btc_spot_open=("open", "first"),
        btc_spot_high=("high", "max"),
        btc_spot_low=("low", "min"),
        btc_spot_close=("close", "last"),
        btc_spot_volume_base=("volume_base", "sum"),
        btc_spot_turnover_quote=("turnover_quote", "sum"),
    )
    daily["btc_spot_ret_1d"] = daily["btc_spot_close"].pct_change()
    return daily


def main() -> None:
    config = yaml.safe_load((ROOT / "configs/_0_sources.yaml").read_text())["bybit"]
    client = client_mod.BybitClient(
        base_url=config["base_url"],
        delay_seconds=float(config["request_delay_seconds"]),
        user_agent=config["user_agent"],
    )
    raw = ROOT / "0_data/cache/raw/bybit_btc_spot_klines_1h.parquet"
    daily_path = ROOT / "0_data/cache/raw/bybit_btc_spot_daily.parquet"
    start_ms = time_mod.parse_utc_ms(START)
    end_ms = time_mod.last_complete_hour_ms()
    hourly = append_hourly(raw, client, start_ms, end_ms)
    daily = daily_from_hourly(hourly)
    daily.to_parquet(daily_path, index=False)
    print(json.dumps({
        "symbol": SYMBOL,
        "hourly_rows": len(hourly),
        "daily_rows": len(daily),
        "first": str(daily["timestamp"].min()) if not daily.empty else None,
        "last": str(daily["timestamp"].max()) if not daily.empty else None,
        "path": str(daily_path),
    }, indent=2))


if __name__ == "__main__":
    main()
