from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

import pandas as pd

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
defillama_mod = load_module("0_data/_1_fetch/_5_defillama.py", "defillama")
coingecko_mod = load_module("0_data/_1_fetch/_6_coingecko.py", "coingecko")
daily_mod = load_module("0_data/_2_normalize/_1_daily.py", "daily")
coverage_mod = load_module("0_data/_3_validate/_0_coverage.py", "coverage")


def cache_or_fetch(path: Path, force: bool, fetch: Any) -> pd.DataFrame:
    if path.exists() and not force:
        return pd.read_parquet(path)
    frame = fetch()
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False)
    return frame


def filter_days(frame: pd.DataFrame, start_ms: int, end_ms: int) -> pd.DataFrame:
    start = pd.to_datetime(start_ms, unit="ms", utc=True).floor("D")
    end = pd.to_datetime(end_ms, unit="ms", utc=True).floor("D")
    clean = frame.copy()
    clean["timestamp"] = clean["timestamp"].dt.floor("D")
    return clean[(clean["timestamp"] >= start) & (clean["timestamp"] <= end)].reset_index(drop=True)


def complete_day_range(hourly: pd.DataFrame) -> tuple[int, int]:
    daily_counts = hourly.assign(day=hourly["timestamp"].dt.floor("D")).groupby("day").size()
    complete_days = daily_counts[daily_counts == 24].index
    if complete_days.empty:
        raise RuntimeError("No complete UTC days in hourly dataset")
    start_ms = int(complete_days.min().timestamp() * 1000)
    end_ms = int(complete_days.max().timestamp() * 1000)
    return start_ms, end_ms


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    raw = ROOT / "0_data/cache/raw"
    processed = ROOT / "0_data/cache/processed"
    hourly_path = processed / "mnt_bybit_hourly_2026.parquet"
    if not hourly_path.exists():
        raise RuntimeError("Run 0_data/_4_build/_0_backfill_2026.py first")

    hourly = pd.read_parquet(hourly_path)
    start_ms, end_ms = complete_day_range(hourly)
    client = defillama_mod.DefiLlamaClient()

    source_specs: list[tuple[str, str, str, Any]] = [
        ("defillama_tvl_daily", "defillama_tvl_daily.parquet", "DefiLlama", client and defillama_mod.tvl_daily),
        (
            "defillama_dex_volume_daily",
            "defillama_dex_volume_daily.parquet",
            "DefiLlama",
            client and defillama_mod.dex_volume_daily,
        ),
        (
            "defillama_stables_daily",
            "defillama_stables_daily.parquet",
            "DefiLlama",
            client and defillama_mod.stables_daily,
        ),
        (
            "defillama_app_fees_daily",
            "defillama_app_fees_daily.parquet",
            "DefiLlama",
            client and defillama_mod.app_fees_daily,
        ),
        (
            "defillama_app_revenue_daily",
            "defillama_app_revenue_daily.parquet",
            "DefiLlama",
            client and defillama_mod.app_revenue_daily,
        ),
        (
            "defillama_chain_fees_daily",
            "defillama_chain_fees_daily.parquet",
            "DefiLlama",
            client and defillama_mod.chain_fees_daily,
        ),
        (
            "defillama_chain_revenue_daily",
            "defillama_chain_revenue_daily.parquet",
            "DefiLlama",
            client and defillama_mod.chain_revenue_daily,
        ),
    ]

    frames: dict[str, pd.DataFrame] = {}
    sources: dict[str, str] = {}
    for name, filename, source, fetcher in source_specs:
        frames[name] = cache_or_fetch(
            raw / filename,
            args.force,
            lambda fetcher=fetcher: filter_days(fetcher(client), start_ms, end_ms),
        )
        sources[name] = source

    optional_notes: list[str] = []
    coingecko_path = raw / "coingecko_mnt_market_daily.parquet"
    try:
        frames["coingecko_mnt_market_daily"] = cache_or_fetch(
            coingecko_path,
            args.force,
            lambda: filter_days(coingecko_mod.fetch_mnt_market_daily(start_ms, end_ms), start_ms, end_ms),
        )
    except Exception as exc:
        if not coingecko_path.exists():
            raise
        print(f"WARNING optional CoinGecko refresh failed; using cached data: {exc}")
        optional_notes.append(f"Optional CoinGecko refresh failed; cached data used: {exc}")
        frames["coingecko_mnt_market_daily"] = pd.read_parquet(coingecko_path)
    sources["coingecko_mnt_market_daily"] = "CoinGecko"

    bybit_daily = daily_mod.aggregate_bybit_daily(hourly)
    bybit_daily = filter_days(bybit_daily, start_ms, end_ms)
    bybit_daily.to_parquet(raw / "bybit_daily_agg.parquet", index=False)

    joined = daily_mod.join_daily_context(bybit_daily, list(frames.values()))
    joined = daily_mod.add_daily_features(joined)
    daily_path = processed / "mnt_daily_2026.parquet"
    joined.to_parquet(daily_path, index=False)

    rows = [
        coverage_mod.coverage_row(
            "bybit_daily_agg",
            bybit_daily,
            start_ms,
            end_ms,
            "1d",
            ["timestamp", "bybit_perp_close", "bybit_spot_close", "bybit_open_interest_close"],
            "Bybit derived",
        )
    ]
    for name, frame in frames.items():
        spec = schema.DAILY_DATASETS[name]
        rows.append(
            coverage_mod.coverage_row(
                name,
                frame,
                start_ms,
                end_ms,
                "1d",
                spec["required"],
                sources[name],
            )
        )
    rows.append(
        coverage_mod.coverage_row(
            "mnt_daily_2026",
            joined,
            start_ms,
            end_ms,
            "1d",
            ["timestamp", "bybit_perp_close", "mantle_tvl_usd", "mantle_dex_volume_usd"],
            "Derived",
        )
    )

    unavailable = [
        "DefiLlama bridge volume / bridge day stats returned HTTP 402 on free API.",
        "DefiLlama derivatives/perps volume returned HTTP 402 on free API; Bybit perp turnover is used instead.",
        "DefiLlama active addresses, new addresses, transactions, and gas-used endpoints were not found on free API.",
    ]
    notes = [
        "Daily dataset uses complete UTC days only; today's partial Bybit candles are excluded.",
        "MNT price/volume in the signal dataset comes from Bybit; market cap comes from CoinGecko.",
        "Mantle native metrics are daily context, not interpolated intraday features.",
        *optional_notes,
        *unavailable,
    ]
    coverage_mod.write_markdown(rows, ROOT / "0_data/_5_docs/_0_data_coverage.md", notes)
    coverage_mod.write_markdown(rows, ROOT / "0_data/cache/_coverage.md", notes)
    (raw / "unavailable_daily_sources.json").write_text(json.dumps(unavailable, indent=2))
    print(json.dumps({"processed": str(daily_path), "coverage": rows}, indent=2))


if __name__ == "__main__":
    main()
