from __future__ import annotations

import argparse
import importlib.util
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "0_data/cache/onchain"
APP_JSON = ROOT / "4_runtime/app/intraday_events.json"


def load_module(rel_path: str, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, ROOT / rel_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {rel_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tokens_mod = load_module("0_data/_0_types/_2_tokens.py", "mantle_tokens")
rpc_mod = load_module("0_data/_1_fetch/_7_mantle_rpc.py", "mantle_rpc")
events_mod = load_module("0_data/_2_normalize/_2_transfer_events.py", "transfer_events")
outputs_mod = load_module("0_data/_4_build/_3_intraday_outputs.py", "intraday_outputs")


def block_at_or_after(rpc: Any, target_ts: int, latest: int) -> int:
    lo, hi = 1, latest
    while lo < hi:
        mid = (lo + hi) // 2
        if rpc.block_timestamp(mid) < target_ts:
            lo = mid + 1
        else:
            hi = mid
    return lo


def cached_json(path: Path, force: bool, fetch: Any) -> Any:
    if path.exists() and not force:
        return json.loads(path.read_text())
    data = fetch()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    return data


def token_decimals(rpc: Any, token: dict[str, object], force: bool) -> tuple[int, str]:
    path = CACHE / "decimals.json"
    existing = json.loads(path.read_text()) if path.exists() and not force else {}
    symbol = str(token["symbol"])
    if symbol in existing:
        return int(existing[symbol]["decimals"]), str(existing[symbol]["source"])
    try:
        decimals = int(rpc.decimals(str(token["address"])))
        source = "rpc"
    except Exception as exc:
        decimals = int(token["decimals_fallback"])
        source = f"fallback: {exc}"
    existing[symbol] = {"decimals": decimals, "source": source}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(existing, indent=2))
    return decimals, source


def token_total_supply(rpc: Any, token: dict[str, object], decimals: int, force: bool) -> tuple[float | None, str]:
    path = CACHE / "total_supply.json"
    existing = json.loads(path.read_text()) if path.exists() else {}
    symbol = str(token["symbol"])
    try:
        total_supply = float(rpc.total_supply(str(token["address"]), decimals))
        source = "rpc"
    except Exception as exc:
        total_supply = None
        source = f"unavailable: {exc}"
    existing[symbol] = {"total_supply": total_supply, "source": source}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(existing, indent=2))
    return total_supply, source


def token_prices(tokens: list[dict[str, object]], force: bool) -> tuple[dict[str, float | None], dict[str, str]]:
    path = CACHE / "prices.json"
    required_symbols = {str(token["symbol"]) for token in tokens}
    if path.exists() and not force:
        cached = json.loads(path.read_text())
        generated_at = cached.get("_meta", {}).get("generated_at")
        if generated_at:
            age = datetime.now(timezone.utc) - datetime.fromisoformat(generated_at)
            rows = {k: v for k, v in cached.items() if k != "_meta"}
            if age.total_seconds() < 3600:
                if required_symbols.issubset(rows):
                    return {k: v["price_usd"] for k, v in rows.items()}, {k: v["source"] for k, v in rows.items()}

    prices: dict[str, float | None] = {}
    sources: dict[str, str] = {}
    ids = sorted({str(token["coingecko_id"]) for token in tokens if token.get("coingecko_id")})
    try:
        query = urllib.parse.urlencode({"ids": ",".join(ids), "vs_currencies": "usd"})
        req = urllib.request.Request(
            f"https://api.coingecko.com/api/v3/simple/price?{query}",
            headers={"User-Agent": "Mozilla/5.0 (compatible; research-script; +local-analysis)"},
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = json.loads(response.read())
    except Exception as exc:
        payload = {}
        sources["_fetch_error"] = str(exc)

    for token in tokens:
        symbol = str(token["symbol"])
        if bool(token["stable"]):
            prices[symbol] = 1.0
            sources[symbol] = "stable_1_usd"
            continue
        coingecko_id = token.get("coingecko_id")
        price = payload.get(str(coingecko_id), {}).get("usd") if coingecko_id else None
        prices[symbol] = None if price is None else float(price)
        sources[symbol] = "coingecko" if price is not None else f"unavailable:{coingecko_id}"

    path.write_text(
        json.dumps(
            {
                "_meta": {"generated_at": datetime.now(timezone.utc).isoformat()},
                **{symbol: {"price_usd": prices[symbol], "source": sources[symbol]} for symbol in prices},
            },
            indent=2,
        )
    )
    return prices, sources


def chunk_ranges(start_block: int, end_block: int, size: int) -> list[tuple[int, int]]:
    ranges = []
    cursor = start_block - (start_block % size)
    while cursor <= end_block:
        top = min(cursor + size - 1, end_block)
        ranges.append((cursor, top))
        cursor = top + 1
    return ranges


def fetch_chunk(
    rpc: Any,
    token: dict[str, object],
    from_block: int,
    to_block: int,
    force: bool,
    cacheable: bool,
) -> list[dict[str, Any]]:
    symbol = str(token["symbol"])
    filename = f"{symbol}_{from_block}_{to_block}.json" if cacheable else f"{symbol}_head_{from_block}.json"
    path = CACHE / "raw_logs" / filename
    if not cacheable:
        logs = rpc.get_logs(str(token["address"]), tokens_mod.TRANSFER_TOPIC, from_block, to_block)
        path.write_text(json.dumps(logs))
        return logs
    return cached_json(
        path,
        force,
        lambda: rpc.get_logs(str(token["address"]), tokens_mod.TRANSFER_TOPIC, from_block, to_block),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--chunk-blocks", type=int, default=10_000)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    CACHE.mkdir(parents=True, exist_ok=True)
    APP_JSON.parent.mkdir(parents=True, exist_ok=True)
    rpc = rpc_mod.MantleRpc()
    latest = rpc.latest_block()
    end_ts = rpc.block_timestamp(latest)
    start_ts = end_ts - args.days * 86_400
    start_block = block_at_or_after(rpc, start_ts, latest)

    rows: list[dict[str, object]] = []
    failed: list[dict[str, object]] = []
    decimal_sources: dict[str, str] = {}
    supply_sources: dict[str, str] = {}
    prices, price_sources = token_prices(tokens_mod.TOKENS, args.force)
    ranges = chunk_ranges(start_block, latest, args.chunk_blocks)
    for token in tokens_mod.TOKENS:
        decimals, source = token_decimals(rpc, token, args.force)
        decimal_sources[str(token["symbol"])] = source
        total_supply, supply_source = token_total_supply(rpc, token, decimals, args.force)
        supply_sources[str(token["symbol"])] = f"{supply_source}; total_supply={total_supply}"
        token_with_supply = {**token, "total_supply": total_supply, "price_usd": prices.get(str(token["symbol"]))}
        for index, (left, right) in enumerate(ranges, start=1):
            try:
                cacheable = right == left + args.chunk_blocks - 1
                logs = fetch_chunk(rpc, token, left, right, args.force, cacheable)
                if logs:
                    left_ts = rpc.block_timestamp(left)
                    right_ts = rpc.block_timestamp(right)
                    rows.extend(events_mod.decode_logs(logs, token_with_supply, decimals, left, right, left_ts, right_ts))
                print(f"{token['symbol']} {index}/{len(ranges)} logs={len(logs)}")
            except Exception as exc:
                failed.append({"token": token["symbol"], "from_block": left, "to_block": right, "error": str(exc)})

    events = pd.DataFrame(rows)
    if not events.empty:
        events = events_mod.classify_events(events, tokens_mod.ZERO_ADDRESS)
        start_dt = datetime.fromtimestamp(start_ts, tz=timezone.utc)
        end_dt = datetime.fromtimestamp(end_ts, tz=timezone.utc)
        events = events[(events["timestamp"] >= start_dt) & (events["timestamp"] <= end_dt)]
        events = events.sort_values(["timestamp", "block_number", "log_index"]).reset_index(drop=True)
    hourly = events_mod.aggregate_events(events, "h")
    daily = events_mod.aggregate_events(events, "D")
    alerts = events_mod.build_alerts(events)

    events.to_parquet(CACHE / "transfer_events_14d.parquet", index=False)
    hourly.to_parquet(CACHE / "hourly_token_flows_14d.parquet", index=False)
    daily.to_parquet(CACHE / "daily_token_flows_14d.parquet", index=False)
    alerts.to_parquet(CACHE / "alerts_14d.parquet", index=False)
    alerts.to_csv(CACHE / "alerts_14d.csv", index=False)
    counts = {
        "tokens": len(tokens_mod.TOKENS),
        "chunks_per_token": len(ranges),
        "failed_chunks": len(failed),
        "events": len(events),
        "hourly_rows": len(hourly),
        "daily_rows": len(daily),
        "alerts": len(alerts),
    }
    outputs_mod.write_app_payload(alerts, latest, start_block, start_ts, end_ts, counts, APP_JSON)
    summary = {
        "generated_at": outputs_mod.utc_now().isoformat(),
        "window_start": datetime.fromtimestamp(start_ts, tz=timezone.utc).isoformat(),
        "window_end": datetime.fromtimestamp(end_ts, tz=timezone.utc).isoformat(),
        "start_block": start_block,
        "latest_block": latest,
        "raw_logs": len(rows),
        "normalized_events": len(events),
        "alerts": len(alerts),
        "timestamp_method": "linear interpolation between exact chunk boundary block timestamps",
    }
    (CACHE / "summary_14d.json").write_text(json.dumps({**summary, "counts": counts}, indent=2))
    outputs_mod.write_coverage(summary, failed, decimal_sources, supply_sources, price_sources, ROOT, CACHE)
    print(json.dumps({**summary, "counts": counts, "failed": failed[:5], "app_json": str(APP_JSON)}, indent=2))


if __name__ == "__main__":
    main()
