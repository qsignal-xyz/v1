from __future__ import annotations

import json
import statistics
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "4_runtime/app/live_signals.json"
INTRADAY = ROOT / "4_runtime/app/intraday_events.json"
BYBIT = "https://api.bybit.com"
UA = "Mozilla/5.0 (compatible; research-script; +local-analysis)"


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso_ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d:%H:%M:%S")


def bybit(path: str, params: dict[str, object]) -> dict[str, Any]:
    query = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{BYBIT}{path}?{query}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as response:
        payload = json.loads(response.read())
    if payload.get("retCode") not in (0, None):
        raise RuntimeError(f"Bybit retCode={payload.get('retCode')}: {payload.get('retMsg')}")
    time.sleep(0.1)
    return payload


def klines(symbol: str, category: str = "linear", limit: int = 48) -> list[dict[str, float]]:
    payload = bybit(
        "/v5/market/kline",
        {"category": category, "symbol": symbol, "interval": "60", "limit": limit},
    )
    rows = []
    for row in payload.get("result", {}).get("list", []):
        rows.append(
            {
                "timestamp_ms": float(row[0]),
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[5]),
                "turnover": float(row[6]),
            }
        )
    return sorted(rows, key=lambda row: row["timestamp_ms"])


def open_interest(symbol: str) -> list[dict[str, float]]:
    end_ms = int(time.time() * 1000)
    start_ms = end_ms - 48 * 60 * 60 * 1000
    payload = bybit(
        "/v5/market/open-interest",
        {
            "category": "linear",
            "symbol": symbol,
            "intervalTime": "1h",
            "startTime": start_ms,
            "endTime": end_ms,
            "limit": 48,
        },
    )
    rows = []
    for row in payload.get("result", {}).get("list", []):
        rows.append({"timestamp_ms": float(row["timestamp"]), "open_interest": float(row["openInterest"])})
    return sorted(rows, key=lambda row: row["timestamp_ms"])


def funding(symbol: str) -> list[dict[str, float]]:
    end_ms = int(time.time() * 1000)
    start_ms = end_ms - 7 * 24 * 60 * 60 * 1000
    payload = bybit(
        "/v5/market/funding/history",
        {"category": "linear", "symbol": symbol, "startTime": start_ms, "endTime": end_ms, "limit": 21},
    )
    rows = []
    for row in payload.get("result", {}).get("list", []):
        rows.append({"timestamp_ms": float(row["fundingRateTimestamp"]), "funding_rate": float(row["fundingRate"])})
    return sorted(rows, key=lambda row: row["timestamp_ms"])


def pct_change(rows: list[dict[str, float]], periods: int) -> float | None:
    if len(rows) <= periods:
        return None
    prev = rows[-1 - periods]["close"]
    if prev == 0:
        return None
    return rows[-1]["close"] / prev - 1


def safe_ratio(new: float, old: float) -> float | None:
    if old == 0:
        return None
    return new / old - 1


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value * 100:+.2f}%"


def fmt_usd(value: float) -> str:
    sign = "-" if value < 0 else "+" if value > 0 else ""
    abs_value = abs(value)
    if abs_value >= 1_000_000_000:
        return f"{sign}${abs_value / 1_000_000_000:.2f}B"
    if abs_value >= 1_000_000:
        return f"{sign}${abs_value / 1_000_000:.2f}M"
    if abs_value >= 1_000:
        return f"{sign}${abs_value / 1_000:.2f}K"
    return f"{sign}${abs_value:.0f}"


def severity_from_abs_pct(value: float | None, medium: float, high: float) -> str:
    if value is None:
        return "low"
    abs_value = abs(value)
    if abs_value >= high:
        return "high"
    if abs_value >= medium:
        return "medium"
    return "low"


def add_signal(
    out: list[dict[str, object]],
    *,
    ts: str,
    kind: str,
    severity: str,
    label: str,
    value: str,
    detail: str,
    evidence: list[str],
    proposed_action: str,
) -> None:
    out.append(
        {
            "id": f"{kind}:{label.lower().replace(' ', '_')}:{ts}",
            "timestamp": ts,
            "type": kind,
            "severity": severity,
            "label": label,
            "value": value,
            "detail": detail,
            "evidence": evidence,
            "proposed_action": proposed_action,
            "source": "bybit/onchain-local",
        }
    )


def onchain_summary(window_start_ms: int) -> dict[str, object]:
    if not INTRADAY.exists():
        return {"alerts_24h": 0, "net_flow_usd": 0.0, "inflow_usd": 0.0, "outflow_usd": 0.0, "types": {}}
    data = json.loads(INTRADAY.read_text())
    alerts = data.get("alerts", [])
    types: dict[str, int] = {}
    inflow = 0.0
    outflow = 0.0
    count = 0
    for alert in alerts:
        ts = datetime.strptime(alert["timestamp"], "%Y-%m-%d:%H:%M:%S").replace(tzinfo=timezone.utc)
        if ts.timestamp() * 1000 < window_start_ms:
            continue
        count += 1
        types[str(alert["signal"])] = types.get(str(alert["signal"]), 0) + 1
        value = float(alert.get("value_usd") or 0)
        if str(alert.get("signal")) in {"stableBurn", "tokenBurn", "bridgeOut"}:
            value *= -1
        if value >= 0:
            inflow += value
        else:
            outflow += abs(value)
    return {
        "alerts_24h": count,
        "net_flow_usd": inflow - outflow,
        "inflow_usd": inflow,
        "outflow_usd": outflow,
        "types": types,
    }


def build() -> dict[str, object]:
    generated = now_utc()
    ts = iso_ts(generated)
    signals: list[dict[str, object]] = []
    errors: list[str] = []
    state: dict[str, object] = {"generated_at": generated.isoformat()}

    try:
        mnt = klines("MNTUSDT", "linear", 48)
        btc = klines("BTCUSDT", "linear", 48)
        eth = klines("ETHUSDT", "linear", 48)
        oi = open_interest("MNTUSDT")
        fund = funding("MNTUSDT")
    except Exception as exc:
        errors.append(f"bybit_fetch: {exc}")
        mnt, btc, eth, oi, fund = [], [], [], [], []

    if mnt:
        price = mnt[-1]["close"]
        mnt_1h = pct_change(mnt, 1)
        mnt_6h = pct_change(mnt, 6)
        mnt_24h = pct_change(mnt, 24)
        vol_last = mnt[-1]["turnover"]
        prior = [row["turnover"] for row in mnt[-25:-1]]
        vol_med = statistics.median(prior) if prior else 0.0
        vol_ratio = vol_last / vol_med if vol_med else 0.0
        state["mnt"] = {
            "price": price,
            "change_1h": mnt_1h,
            "change_6h": mnt_6h,
            "change_24h": mnt_24h,
            "volume_last_hour_usd": vol_last,
            "volume_ratio_vs_24h_median": vol_ratio,
        }
        add_signal(
            signals,
            ts=ts,
            kind="perp_market",
            severity=severity_from_abs_pct(mnt_1h, 0.015, 0.035),
            label="MNT price momentum",
            value=fmt_pct(mnt_1h),
            detail=f"MNTUSDT perps trade at ${price:.4f}; 1h {fmt_pct(mnt_1h)}, 6h {fmt_pct(mnt_6h)}, 24h {fmt_pct(mnt_24h)}.",
            evidence=[f"price ${price:.4f}", f"1h {fmt_pct(mnt_1h)}", f"6h {fmt_pct(mnt_6h)}", f"24h {fmt_pct(mnt_24h)}"],
            proposed_action="Use as market context; daily model still controls allocation.",
        )
        if vol_ratio >= 2:
            add_signal(
                signals,
                ts=ts,
                kind="perp_market",
                severity="high" if vol_ratio >= 4 else "medium",
                label="Perp volume spike",
                value=f"{vol_ratio:.1f}x",
                detail=f"Last-hour MNT perp turnover is {vol_ratio:.1f}x its prior 24h hourly median.",
                evidence=[f"last hour {fmt_usd(vol_last)}", f"median hour {fmt_usd(vol_med)}"],
                proposed_action="Check whether price move is backed by open interest and on-chain flow.",
            )

    if oi:
        oi_6h = safe_ratio(oi[-1]["open_interest"], oi[-7]["open_interest"]) if len(oi) >= 7 else None
        oi_24h = safe_ratio(oi[-1]["open_interest"], oi[-25]["open_interest"]) if len(oi) >= 25 else None
        state["open_interest"] = {"latest": oi[-1]["open_interest"], "change_6h": oi_6h, "change_24h": oi_24h}
        add_signal(
            signals,
            ts=ts,
            kind="perp_market",
            severity=severity_from_abs_pct(oi_6h, 0.05, 0.15),
            label="Open interest shift",
            value=fmt_pct(oi_6h),
            detail=f"MNT open interest changed {fmt_pct(oi_6h)} over 6h and {fmt_pct(oi_24h)} over 24h.",
            evidence=[f"OI {oi[-1]['open_interest']:.0f}", f"6h {fmt_pct(oi_6h)}", f"24h {fmt_pct(oi_24h)}"],
            proposed_action="Rising OI confirms leverage entering; falling OI means price moves may be less durable.",
        )

    if fund:
        latest_funding = fund[-1]["funding_rate"]
        avg_funding = statistics.mean(row["funding_rate"] for row in fund[-3:]) if len(fund) >= 3 else latest_funding
        state["funding"] = {"latest": latest_funding, "avg_24h": avg_funding}
        add_signal(
            signals,
            ts=ts,
            kind="perp_market",
            severity="high" if abs(latest_funding) >= 0.0005 else "medium" if abs(latest_funding) >= 0.0002 else "low",
            label="Funding pressure",
            value=fmt_pct(latest_funding),
            detail=f"Latest 8h MNT funding is {fmt_pct(latest_funding)}; recent 24h average is {fmt_pct(avg_funding)}.",
            evidence=[f"latest {fmt_pct(latest_funding)}", f"24h avg {fmt_pct(avg_funding)}"],
            proposed_action="Crowded positive funding weakens new longs; negative funding can support contrarian longs if daily signal agrees.",
        )

    if btc and eth and mnt:
        btc_24h = pct_change(btc, 24)
        eth_24h = pct_change(eth, 24)
        mnt_24h = pct_change(mnt, 24)
        beta_gap = None if mnt_24h is None or btc_24h is None else mnt_24h - btc_24h
        state["market_context"] = {"btc_change_24h": btc_24h, "eth_change_24h": eth_24h, "mnt_vs_btc_24h": beta_gap}
        add_signal(
            signals,
            ts=ts,
            kind="market_context",
            severity=severity_from_abs_pct(beta_gap, 0.03, 0.07),
            label="MNT vs BTC beta gap",
            value=fmt_pct(beta_gap),
            detail=f"BTC 24h {fmt_pct(btc_24h)}, ETH 24h {fmt_pct(eth_24h)}, MNT minus BTC {fmt_pct(beta_gap)}.",
            evidence=[f"BTC {fmt_pct(btc_24h)}", f"ETH {fmt_pct(eth_24h)}", f"MNT-BTC {fmt_pct(beta_gap)}"],
            proposed_action="If MNT lags in a risk-on tape, wait for confirmation; if it outperforms with inflows, prefer long exposure.",
        )

    onchain = onchain_summary(int((generated.timestamp() - 86_400) * 1000))
    state["onchain"] = onchain
    add_signal(
        signals,
        ts=ts,
        kind="onchain_flow",
        severity="medium" if abs(float(onchain["net_flow_usd"])) >= 1_000_000 else "low",
        label="24h on-chain flow",
        value=fmt_usd(float(onchain["net_flow_usd"])),
        detail=(
            f"{onchain['alerts_24h']} on-chain alerts; inflows {fmt_usd(float(onchain['inflow_usd']))}, "
            f"outflows {fmt_usd(-float(onchain['outflow_usd']))}."
        ),
        evidence=[f"alerts {onchain['alerts_24h']}", f"inflows {fmt_usd(float(onchain['inflow_usd']))}", f"outflows {fmt_usd(-float(onchain['outflow_usd']))}"],
        proposed_action="Use as confirmation or warning around the daily signal.",
    )

    return {
        "generated_at": generated.isoformat(),
        "window": "24h",
        "state": state,
        "signals": signals,
        "errors": errors,
    }


def main() -> None:
    payload = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2))
    print(json.dumps({"signals": len(payload["signals"]), "errors": payload["errors"], "out": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
