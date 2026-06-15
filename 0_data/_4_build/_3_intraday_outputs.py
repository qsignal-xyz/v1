from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def write_app_payload(
    alerts: pd.DataFrame,
    latest_block: int,
    start_block: int,
    start_ts: int,
    end_ts: int,
    counts: dict[str, int],
    output: Path,
) -> None:
    payload_alerts = []
    for _, row in alerts.tail(250).iterrows():
        payload_alerts.append(
            {
                "timestamp": row["timestamp"].strftime("%Y-%m-%d:%H:%M:%S"),
                "severity": row["severity"],
                "signal": row["event_type"],
                "proposed_action": row["proposed_action"],
                "value": row["value_label"],
                "strength": "-",
                "token": row["token_symbol"],
                "tx_hash": row["tx_hash"],
                "detail": row["detail"],
                "risk_scope": row.get("risk_scope", "market"),
                "category": row.get("category", ""),
                "bridge_type": row.get("bridge_type", ""),
                "bridge_protocol": row.get("bridge_protocol", ""),
                "value_usd": None if pd.isna(row.get("value_usd")) else float(row["value_usd"]),
            }
        )
    output.write_text(
        json.dumps(
            {
                "generated_at": utc_now().isoformat(),
                "window_start": datetime.fromtimestamp(start_ts, tz=timezone.utc).isoformat(),
                "window_end": datetime.fromtimestamp(end_ts, tz=timezone.utc).isoformat(),
                "start_block": start_block,
                "latest_block": latest_block,
                "timestamp_method": "linear interpolation between exact chunk boundary block timestamps",
                "counts": counts,
                "alerts": payload_alerts,
            },
            indent=2,
        )
    )


def write_coverage(
    summary: dict[str, Any],
    failed: list[dict[str, object]],
    decimal_sources: dict[str, str],
    supply_sources: dict[str, str],
    price_sources: dict[str, str],
    root: Path,
    cache: Path,
) -> None:
    lines = [
        "# Intraday Event Coverage",
        "",
        f"- generated_at: {summary['generated_at']}",
        f"- window: {summary['window_start']} to {summary['window_end']}",
        f"- blocks: {summary['start_block']} to {summary['latest_block']}",
        f"- raw_logs: {summary['raw_logs']}",
        f"- normalized_events: {summary['normalized_events']}",
        f"- alerts: {summary['alerts']}",
        f"- timestamp_method: {summary['timestamp_method']}",
        "",
        "## Alert Semantics",
        "",
        "- Tracked assets: stables, WMNT, WETH, mETH, cmETH, FBTC, WBTC, COOK, and confirmed Mantle xStocks from CoinGecko platform metadata.",
        "- Bridge flows are labeled from canonical bridge mints/burns and transfers involving known bridge, pool, depository, or route contracts.",
        "- Known bridge protocols: Mantle, USDT0, Stargate, Relay, deBridge, Hyperlane; LayerZero/Symbiosis/FBTC are detected through token mint/burn semantics where explicit route contracts are not tracked.",
        "- Low/medium/high severity uses token-specific USD thresholds; the UI labels the base severity as low, not info.",
        "- Yield-pool tokens: USDC, USDT0, USDe, sUSDe, USDY.",
        "- Yield-pool mint/burn alerts are critical only when they exceed the stricter of the token/event historical outlier threshold and 1% of current total supply.",
        "- Other flow alerts use token-specific USD thresholds.",
        "",
        "## Token Decimals",
        "",
    ]
    lines.extend(f"- {symbol}: {source}" for symbol, source in decimal_sources.items())
    lines.extend(["", "## Token Supply", ""])
    lines.extend(f"- {symbol}: {source}" for symbol, source in supply_sources.items())
    lines.extend(["", "## Token Prices", ""])
    lines.extend(f"- {symbol}: {source}" for symbol, source in price_sources.items())
    lines.extend(["", "## Failed Chunks", ""])
    lines.extend([json.dumps(item, sort_keys=True) for item in failed] or ["- none"])
    text = "\n".join(lines) + "\n"
    docs = root / "0_data/_5_docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "_3_intraday_events.md").write_text(text)
    (cache / "_coverage.md").write_text(text)
