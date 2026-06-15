from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd

SUPPLY_ANOMALY_PCT = 0.01


def topic_address(topic: str) -> str:
    return "0x" + topic[-40:].lower()


def bridge_type_label(value: object) -> str:
    labels = {
        "standard": "Mantle",
        "oft": "USDT0",
        "layerzero": "LayerZero",
        "symbiosis": "Symbiosis",
        "fbtc": "FBTC Bridge",
    }
    return labels.get(str(value), str(value or "bridge"))


def decode_logs(
    logs: list[dict[str, Any]],
    token: dict[str, object],
    decimals: int,
    chunk_start_block: int,
    chunk_end_block: int,
    chunk_start_ts: int,
    chunk_end_ts: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    block_span = max(chunk_end_block - chunk_start_block, 1)
    ts_span = max(chunk_end_ts - chunk_start_ts, 1)
    for log in logs:
        topics = log.get("topics", [])
        if len(topics) < 3:
            continue
        block_number = int(log["blockNumber"], 16)
        ratio = (block_number - chunk_start_block) / block_span
        timestamp = int(chunk_start_ts + ratio * ts_span)
        amount_raw = int(log.get("data", "0x0"), 16)
        amount = amount_raw / (10**decimals)
        from_address = topic_address(topics[1])
        to_address = topic_address(topics[2])
        bridge_protocols = token.get("bridge_protocols", {})
        from_bridge_protocol = str(bridge_protocols.get(from_address, "")) if isinstance(bridge_protocols, dict) else ""
        to_bridge_protocol = str(bridge_protocols.get(to_address, "")) if isinstance(bridge_protocols, dict) else ""
        rows.append(
            {
                "timestamp": datetime.fromtimestamp(timestamp, tz=timezone.utc),
                "block_number": block_number,
                "tx_hash": log["transactionHash"],
                "log_index": int(log["logIndex"], 16),
                "token_symbol": token["symbol"],
                "token_address": str(token["address"]).lower(),
                "stable": bool(token["stable"]),
                "yield_pool_token": bool(token.get("yield_pool_token", False)),
                "total_supply": token.get("total_supply"),
                "category": token.get("category", ""),
                "bridge_type": token.get("bridge_type", ""),
                "from_bridge": from_address in token.get("bridge_contracts", []),
                "to_bridge": to_address in token.get("bridge_contracts", []),
                "from_bridge_protocol": from_bridge_protocol,
                "to_bridge_protocol": to_bridge_protocol,
                "bridge_protocol": from_bridge_protocol or to_bridge_protocol,
                "bridge_mint_burn": bool(token.get("bridge_mint_burn", False)),
                "price_usd": token.get("price_usd"),
                "value_usd": None if token.get("price_usd") is None else amount * float(token["price_usd"]),
                "alert_min_usd": float(token.get("alert_min_usd", 100_000)),
                "medium_usd": float(token.get("medium_usd", 1_000_000)),
                "high_usd": float(token.get("high_usd", 5_000_000)),
                "from_address": from_address,
                "to_address": to_address,
                "amount_raw": str(amount_raw),
                "amount": amount,
            }
        )
    return rows


def classify_events(frame: pd.DataFrame, zero_address: str) -> pd.DataFrame:
    if frame.empty:
        return frame
    events = frame.copy()
    zero = zero_address.lower()
    events["from_zero"] = events["from_address"].str.lower().eq(zero)
    events["to_zero"] = events["to_address"].str.lower().eq(zero)
    if "from_bridge" not in events.columns:
        events["from_bridge"] = False
    if "to_bridge" not in events.columns:
        events["to_bridge"] = False
    if "bridge_mint_burn" not in events.columns:
        events["bridge_mint_burn"] = False
    if "bridge_protocol" not in events.columns:
        events["bridge_protocol"] = ""
    if "category" not in events.columns:
        events["category"] = ""
    events["event_type"] = "transfer"
    events.loc[events["stable"] & events["from_zero"], "event_type"] = "stableMint"
    events.loc[events["stable"] & events["to_zero"], "event_type"] = "stableBurn"
    events.loc[~events["stable"] & events["from_zero"], "event_type"] = "tokenMint"
    events.loc[~events["stable"] & events["to_zero"], "event_type"] = "tokenBurn"
    bridge_in = events["from_bridge"] | (events["bridge_mint_burn"] & events["from_zero"])
    bridge_out = events["to_bridge"] | (events["bridge_mint_burn"] & events["to_zero"])
    bridge_mint_burn = events["bridge_mint_burn"] & (events["from_zero"] | events["to_zero"])
    missing_protocol = events["bridge_protocol"].fillna("").eq("")
    events.loc[bridge_mint_burn & missing_protocol, "bridge_protocol"] = events.loc[
        bridge_mint_burn & missing_protocol,
        "bridge_type",
    ].map(bridge_type_label)
    events.loc[bridge_in, "event_type"] = "bridgeIn"
    events.loc[bridge_out, "event_type"] = "bridgeOut"
    stable_large = events["stable"] & events["event_type"].eq("transfer") & (events["value_usd"] >= events["alert_min_usd"])
    wmnt_large = events["token_symbol"].eq("WMNT") & events["event_type"].eq("transfer")
    wmnt_large &= events["value_usd"] >= events["alert_min_usd"]
    asset_large = ~events["stable"] & events["event_type"].eq("transfer") & (events["value_usd"] >= events["alert_min_usd"])
    events.loc[stable_large, "event_type"] = "stableTransfer"
    events.loc[wmnt_large, "event_type"] = "wmntTransfer"
    events.loc[asset_large & ~wmnt_large, "event_type"] = "assetTransfer"
    return events


def aggregate_events(events: pd.DataFrame, interval: str) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame()
    grouped = events.copy()
    grouped["timestamp"] = grouped["timestamp"].dt.floor(interval)
    grouped["mint_amount"] = grouped["amount"].where(grouped["from_zero"], 0.0)
    grouped["burn_amount"] = grouped["amount"].where(grouped["to_zero"], 0.0)
    grouped["large_transfer_amount"] = grouped["amount"].where(
        grouped["event_type"].isin(["stableTransfer", "wmntTransfer", "assetTransfer"]),
        0.0,
    )
    grouped["bridge_in_usd"] = grouped["value_usd"].where(grouped["event_type"].eq("bridgeIn"), 0.0)
    grouped["bridge_out_usd"] = grouped["value_usd"].where(grouped["event_type"].eq("bridgeOut"), 0.0)
    return (
        grouped.groupby(["timestamp", "token_symbol", "stable", "yield_pool_token", "category"], as_index=False)
        .agg(
            transfer_count=("tx_hash", "count"),
            transfer_amount=("amount", "sum"),
            transfer_usd=("value_usd", "sum"),
            mint_amount=("mint_amount", "sum"),
            burn_amount=("burn_amount", "sum"),
            large_transfer_amount=("large_transfer_amount", "sum"),
            bridge_in_usd=("bridge_in_usd", "sum"),
            bridge_out_usd=("bridge_out_usd", "sum"),
        )
        .sort_values(["timestamp", "token_symbol"])
        .reset_index(drop=True)
    )


def build_alerts(events: pd.DataFrame, max_rows: int | None = None) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame()
    event_types = [
        "stableMint",
        "stableBurn",
        "tokenMint",
        "tokenBurn",
        "stableTransfer",
        "wmntTransfer",
        "assetTransfer",
        "bridgeIn",
        "bridgeOut",
    ]
    alerts = events[events["event_type"].isin(event_types)]
    alerts = alerts.copy()
    alerts = alerts[alerts["value_usd"] >= alerts["alert_min_usd"]]
    if "yield_pool_token" not in alerts.columns:
        alerts["yield_pool_token"] = False
    if "total_supply" not in alerts.columns:
        alerts["total_supply"] = pd.NA
    if "value_usd" not in alerts.columns:
        alerts["value_usd"] = pd.NA
    alerts["risk_scope"] = "market"
    alerts["supply_pct"] = alerts.apply(supply_pct, axis=1)
    thresholds = mint_burn_thresholds(events)
    alerts = alerts.merge(thresholds, on=["token_symbol", "event_type"], how="left")
    alerts["supply_threshold"] = alerts["total_supply"].astype(float) * SUPPLY_ANOMALY_PCT
    alerts.loc[alerts["supply_threshold"].le(0) | alerts["supply_threshold"].isna(), "supply_threshold"] = pd.NA
    alerts["anomaly_threshold"] = alerts[["historical_threshold", "supply_threshold"]].max(axis=1).fillna(float("inf"))
    alerts["severity"] = "low"
    medium = alerts["value_usd"] >= alerts["medium_usd"]
    high = alerts["value_usd"] >= alerts["high_usd"]
    alerts.loc[medium, "severity"] = "medium"
    alerts.loc[high, "severity"] = "high"
    yield_anomaly = (
        alerts["yield_pool_token"]
        & alerts["event_type"].isin(["stableMint", "stableBurn", "bridgeIn", "bridgeOut"])
        & (alerts["amount"] >= alerts["anomaly_threshold"])
    )
    alerts.loc[yield_anomaly, "severity"] = "high"
    alerts.loc[yield_anomaly, "risk_scope"] = "yield_pool"
    bridge_flow = alerts["event_type"].isin(["bridgeIn", "bridgeOut"])
    alerts.loc[bridge_flow, "risk_scope"] = "bridge"
    alerts["proposed_action"] = alerts["event_type"].map(
        {
            "stableMint": "Watch inflows",
            "stableBurn": "Risk off context",
            "tokenMint": "Watch asset issuance",
            "tokenBurn": "Watch asset redemption",
            "stableTransfer": "Watch stable flow",
            "wmntTransfer": "Watch WMNT flow",
            "assetTransfer": "Watch asset flow",
            "bridgeIn": "Watch bridge inflow",
            "bridgeOut": "Bridge outflow risk",
        }
    )
    yield_mint = yield_anomaly & alerts["event_type"].isin(["stableMint", "bridgeIn"])
    yield_burn = yield_anomaly & alerts["event_type"].isin(["stableBurn", "bridgeOut"])
    alerts.loc[yield_mint, "proposed_action"] = "Review pool/token risk"
    alerts.loc[yield_burn, "proposed_action"] = "Exit affected yield pool"
    alerts["value_label"] = alerts.apply(value_label, axis=1)
    alerts["detail"] = alerts.apply(alert_detail, axis=1)
    alerts = alerts.sort_values(["timestamp", "block_number", "log_index"]).reset_index(drop=True)
    return alerts.tail(max_rows).reset_index(drop=True) if max_rows else alerts


def value_label(row: pd.Series) -> str:
    value_usd = row.get("value_usd")
    if pd.isna(value_usd):
        return f"{float(row['amount']):,.4g} {row['token_symbol']}"
    prefix = "+" if row["event_type"] in ["stableMint", "tokenMint", "bridgeIn"] else "-"
    if row["event_type"] in ["stableTransfer", "wmntTransfer", "assetTransfer"]:
        prefix = ""
    return f"{prefix}${float(value_usd) / 1_000_000:.2f}M"


def mint_burn_thresholds(events: pd.DataFrame) -> pd.DataFrame:
    columns = ["token_symbol", "event_type", "historical_threshold"]
    if events.empty or "yield_pool_token" not in events.columns:
        return pd.DataFrame(columns=columns)
    mints_burns = events[
        events["yield_pool_token"]
        & events["event_type"].isin(["stableMint", "stableBurn", "bridgeIn", "bridgeOut"])
        & (events["amount"] > 0)
    ]
    rows: list[dict[str, object]] = []
    for (symbol, event_type), group in mints_burns.groupby(["token_symbol", "event_type"]):
        amounts = group["amount"].astype(float)
        q = 0.99 if len(amounts) >= 20 else 0.95 if len(amounts) >= 8 else 1.0
        median = amounts.median()
        mad = (amounts - median).abs().median()
        robust = median + 8 * 1.4826 * mad
        rows.append(
            {
                "token_symbol": symbol,
                "event_type": event_type,
                "historical_threshold": max(float(amounts.quantile(q)), float(robust), 100_000.0),
            }
        )
    return pd.DataFrame(rows, columns=columns)


def supply_pct(row: pd.Series) -> float | None:
    supply = row.get("total_supply")
    if pd.isna(supply) or float(supply) <= 0:
        return None
    return float(row["amount"]) / float(supply)


def alert_detail(row: pd.Series) -> str:
    short_hash = str(row["tx_hash"])[:10]
    amount = f"{float(row['amount']):,.4g} {row['token_symbol']}"
    detail = (
        f"{row['token_symbol']} {row['event_type']} of {row['value_label']} ({amount}) at block "
        f"{int(row['block_number'])}. Tx {short_hash}."
    )
    if row["event_type"] in ["bridgeIn", "bridgeOut"] and row.get("bridge_protocol"):
        detail += f" Bridge protocol: {row['bridge_protocol']}."
    if row.get("risk_scope") == "yield_pool":
        pct = row.get("supply_pct")
        threshold = row.get("anomaly_threshold")
        pct_text = "" if pd.isna(pct) else f" {float(pct) * 100:.2f}% of supply."
        threshold_text = "" if pd.isna(threshold) else f" Critical amount threshold {float(threshold):,.4g} {row['token_symbol']}."
        detail += f" Yield-pool anomaly:{pct_text}{threshold_text} Verify protocol/token risk before allocating."
    return detail
