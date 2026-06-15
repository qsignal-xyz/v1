from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_module(rel_path: str, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, ROOT / rel_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {rel_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


schema = load_module("0_data/_0_types/_0_schema.py", "schema")
time_mod = load_module("0_data/_0_types/_1_time.py", "time_mod")
client_mod = load_module("0_data/_1_fetch/_0_bybit_client.py", "bybit_client")
meta_mod = load_module("0_data/_1_fetch/_1_market_meta.py", "market_meta")
klines_mod = load_module("0_data/_1_fetch/_2_klines.py", "klines")
oi_mod = load_module("0_data/_1_fetch/_3_open_interest.py", "open_interest")
funding_mod = load_module("0_data/_1_fetch/_4_funding.py", "funding")
hourly_mod = load_module("0_data/_2_normalize/_0_hourly.py", "hourly")
coverage_mod = load_module("0_data/_3_validate/_0_coverage.py", "coverage")


def cache_or_fetch(path: Path, force: bool, fetch: Any) -> pd.DataFrame:
    if path.exists() and not force:
        return pd.read_parquet(path)
    frame = fetch()
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False)
    return frame


def append_or_fetch(
    path: Path,
    force: bool,
    start_ms: int,
    end_ms: int,
    fetch: Any,
) -> pd.DataFrame:
    if force or not path.exists():
        frame = fetch(start_ms, end_ms)
    else:
        old = pd.read_parquet(path)
        if old.empty:
            frame = fetch(start_ms, end_ms)
        else:
            next_ms = int(old["timestamp_ms"].max()) + time_mod.MS_PER_HOUR
            if next_ms <= end_ms:
                new = fetch(next_ms, end_ms)
                frame = pd.concat([old, new], ignore_index=True)
            else:
                frame = old
    if not frame.empty:
        frame = frame[
            (frame["timestamp_ms"] >= start_ms) & (frame["timestamp_ms"] <= end_ms)
        ].drop_duplicates("timestamp").sort_values("timestamp").reset_index(drop=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False)
    return frame


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default=None)
    parser.add_argument("--end", default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    config = yaml.safe_load((ROOT / "configs/_0_sources.yaml").read_text())["bybit"]
    symbol = config["symbol"]
    start_ms = time_mod.parse_utc_ms(args.start or config["start"])
    end_ms = time_mod.parse_utc_ms(args.end) if args.end else time_mod.last_complete_hour_ms()
    client = client_mod.BybitClient(
        base_url=config["base_url"],
        delay_seconds=float(config["request_delay_seconds"]),
        user_agent=config["user_agent"],
    )

    raw = ROOT / "0_data/cache/raw"
    processed = ROOT / "0_data/cache/processed"

    meta = {
        "linear": meta_mod.fetch_instrument(client, "linear", symbol),
        "spot": meta_mod.fetch_instrument(client, "spot", symbol),
        "start": time_mod.ms_to_iso(start_ms),
        "end": time_mod.ms_to_iso(end_ms),
    }
    (raw / "bybit_instrument_meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True))

    perp = append_or_fetch(
        raw / "bybit_perp_klines_1h.parquet",
        args.force,
        start_ms,
        end_ms,
        lambda start, end: klines_mod.fetch_klines_1h(client, "linear", symbol, start, end),
    )
    spot = append_or_fetch(
        raw / "bybit_spot_klines_1h.parquet",
        args.force,
        start_ms,
        end_ms,
        lambda start, end: klines_mod.fetch_klines_1h(client, "spot", symbol, start, end),
    )
    oi = append_or_fetch(
        raw / "bybit_open_interest_1h.parquet",
        args.force,
        start_ms,
        end_ms,
        lambda start, end: oi_mod.fetch_open_interest_1h(client, symbol, start, end),
    )
    funding = append_or_fetch(
        raw / "bybit_funding.parquet",
        args.force,
        start_ms,
        end_ms,
        lambda start, end: funding_mod.fetch_funding(client, symbol, start, end),
    )

    hourly = hourly_mod.build_hourly_dataset(start_ms, end_ms, perp, spot, oi, funding)
    processed.mkdir(parents=True, exist_ok=True)
    hourly_path = processed / "mnt_bybit_hourly_2026.parquet"
    hourly.to_parquet(hourly_path, index=False)

    rows = [
        coverage_mod.coverage_row("bybit_perp_klines_1h", perp, start_ms, end_ms, "1h", schema.RAW_DATASETS["bybit_perp_klines_1h"]["required"]),
        coverage_mod.coverage_row("bybit_spot_klines_1h", spot, start_ms, end_ms, "1h", schema.RAW_DATASETS["bybit_spot_klines_1h"]["required"]),
        coverage_mod.coverage_row("bybit_open_interest_1h", oi, start_ms, end_ms, "1h", schema.RAW_DATASETS["bybit_open_interest_1h"]["required"]),
        coverage_mod.coverage_row("bybit_funding", funding, start_ms, end_ms, "8h", schema.RAW_DATASETS["bybit_funding"]["required"]),
        coverage_mod.coverage_row("mnt_bybit_hourly_2026", hourly, start_ms, end_ms, "1h", ["timestamp", "bybit_perp_close", "bybit_spot_close", "bybit_open_interest", "bybit_funding_rate"], "Derived"),
    ]
    notes = [
        "Bybit fully covers the MVP CEX/perps layer: spot candles, linear perp candles, open interest, and funding.",
        "Bybit does not provide Mantle on-chain data; DEX/TVL/bridge/whale data must come from DefiLlama, GeckoTerminal, RPC, or explorer APIs.",
        "Historical orderbook depth and liquidation history are not included in this no-key MVP.",
    ]
    coverage_mod.write_markdown(rows, ROOT / "0_data/_DATA_COVERAGE.md", notes)
    coverage_mod.write_markdown(rows, ROOT / "0_data/cache/_coverage.md", notes)
    print(json.dumps({"processed": str(hourly_path), "coverage": rows}, indent=2))


if __name__ == "__main__":
    main()
