from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from backtest_modes import build_backtest_modes, daily_yield_return

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "4_runtime/app/history_backtest.json"
AAVE_MANTLE_ASSETS = {
    "USDC": "0x09Bc4E0D864854c6aFB6eB9A9cdF58aC190D0dF9",
    "USDT0": "0x779Ded0c9e1022225f8E0630b35a9b54bE713736",
    "USDE": "0x5d3a1Ff2b6BAb83b63cd9AD0787074081a52ef34",
    "SUSDE": "0x211CC4dD073734dA055fBf44a2b4667d5E5fE5d2",
}


def pct(value: float) -> str:
    return f"{value * 100:+.2f}%"


def title(value: str) -> str:
    return value.replace("_", " ").title()


def clean_number(value: object) -> float | None:
    if pd.isna(value):
        return None
    return float(value)


def latest_live_mnt_price() -> dict[str, Any] | None:
    candles_path = ROOT / "3_app/_3_live/mnt_candles.json"
    if not candles_path.exists():
        return None
    payload = json.loads(candles_path.read_text())
    candles = payload.get("candles") or []
    if not candles:
        return None
    latest = candles[-1]
    return {
        "timestamp": pd.to_datetime(int(latest["t"]), unit="ms", utc=True),
        "price": float(latest["c"]),
    }


def pool_url(row: pd.Series) -> str:
    project = str(row["project"])
    symbol = str(row["symbol"]).upper()
    if project == "aave-v3" and symbol in AAVE_MANTLE_ASSETS:
        asset = AAVE_MANTLE_ASSETS[symbol]
        return f"https://app.aave.com/reserve-overview/?underlyingAsset={asset}&marketName=proto_mantle_v3"
    return f"https://defillama.com/yields/pool/{row['pool']}"


def build_yield_map(replay: pd.DataFrame, yields: pd.DataFrame) -> dict[str, dict[str, float]]:
    dates = pd.DataFrame({"timestamp": pd.to_datetime(replay["timestamp"], utc=True)})
    if yields.empty:
        dates["yield_apy"] = 0.0
    else:
        clean = yields.rename(columns={"stable_yield_apy": "yield_apy"}).copy()
        dates = dates.merge(clean[["timestamp", "yield_apy"]], on="timestamp", how="left")
        dates["yield_apy"] = dates["yield_apy"].ffill().bfill().fillna(0.0)
    dates["yield_daily"] = daily_yield_return(dates["yield_apy"])
    dates["date"] = dates["timestamp"].dt.strftime("%Y-%m-%d")
    return {
        row["date"]: {"daily": float(row["yield_daily"]), "apy": float(row["yield_apy"])}
        for _, row in dates.iterrows()
    }


def yield_info_for_date(yields: pd.DataFrame, date: str) -> dict[str, object] | None:
    if yields.empty:
        return None
    clean = yields.copy()
    clean["date"] = clean["timestamp"].dt.strftime("%Y-%m-%d")
    exact = clean[clean["date"] == date]
    observed = not exact.empty
    row = (exact if observed else clean.sort_values("timestamp")).tail(1).iloc[0]
    apy = float(row["stable_yield_apy"])
    return {
        "apy": apy,
        "daily": float(daily_yield_return(pd.Series([apy])).iloc[0]),
        "observed": observed,
    }


def build_yield_options(yields: pd.DataFrame, charts: pd.DataFrame) -> dict[str, Any]:
    if yields.empty or charts.empty:
        return {"as_of": None, "basket_apy": 0.0, "basket_tvl_usd": 0.0, "pool_count": 0, "pools": []}
    latest_daily = yields.sort_values("timestamp").tail(1).iloc[0]
    latest = charts.sort_values("date").groupby("pool", as_index=False).tail(1).copy()
    latest = latest.dropna(subset=["apy", "tvlUsd"])
    latest = latest[(latest["apy"] > 0) & (latest["tvlUsd"] > 0)]
    latest = latest.sort_values(["apy", "tvlUsd"], ascending=[False, False]).reset_index(drop=True)
    pools = [
        {
            "pool": str(row["pool"]),
            "project": str(row["project"]),
            "symbol": str(row["symbol"]),
            "tvl_usd": clean_number(row["tvlUsd"]),
            "apy": clean_number(row["apy"]),
            "apy_base": clean_number(row["apyBase"]),
            "apy_reward": clean_number(row["apyReward"]),
            "date": str(row["date"])[:10],
            "url": pool_url(row),
        }
        for _, row in latest.iterrows()
    ]
    capacity = max(pools, key=lambda row: row["tvl_usd"] or 0) if pools else None
    return {
        "as_of": str(latest_daily["timestamp"])[:10],
        "basket_apy": float(latest_daily["stable_yield_apy"]),
        "basket_tvl_usd": float(latest_daily["yield_tvl_usd"]),
        "pool_count": int(latest_daily["yield_pool_count"]),
        "best": pools[0] if pools else None,
        "capacity": capacity,
        "pools": pools,
    }


def build_event_map(alerts: pd.DataFrame) -> dict[str, list[dict[str, object]]]:
    if alerts.empty:
        return {}
    clean = alerts.copy()
    clean["date"] = clean["timestamp"].dt.strftime("%Y-%m-%d")
    clean["time"] = clean["timestamp"].dt.strftime("%H:%M")
    out: dict[str, list[dict[str, object]]] = {}
    for date, group in clean.sort_values("timestamp", ascending=False).groupby("date", sort=False):
        out[date] = [
            {
                "time": row["time"],
                "severity": row["severity"],
                "signal": row["event_type"],
                "token": row["token_symbol"],
                "value": row["value_label"],
                "action": row["proposed_action"],
                "detail": row["detail"],
                "tx_hash": row["tx_hash"],
                "block": int(row["block_number"]),
            }
            for _, row in group.iterrows()
        ]
    return out


def build_past_signals(
    replay: pd.DataFrame,
    health: pd.DataFrame,
    yield_map: dict[str, dict[str, float]],
    daily: pd.DataFrame,
    yields: pd.DataFrame,
    live_price: dict[str, Any] | None,
) -> list[dict[str, object]]:
    universe = sorted(health["signal_name"].dropna().unique())
    closes = {
        str(row["timestamp"])[:10]: float(row["bybit_perp_close"])
        for _, row in daily.iterrows()
        if not pd.isna(row["bybit_perp_close"])
    }
    rows = []
    for _, day in replay.iloc[::-1].iterrows():
        date = str(day["timestamp"])[:10]
        direction = int(day["direction"])
        yield_info = yield_map.get(date, {"daily": 0.0, "apy": 0.0})
        raw_dir_ret = None if pd.isna(day["directional_return_1d"]) else float(day["directional_return_1d"])
        if raw_dir_ret is None and direction > 0 and live_price and live_price["timestamp"].date().isoformat() > date:
            close = closes.get(date)
            if close and close > 0:
                raw_dir_ret = live_price["price"] / close - 1.0
        display_ret = raw_dir_ret if direction > 0 else float(yield_info["daily"])
        fired = health[health["timestamp"].astype(str).str.startswith(date)].copy()
        active = fired[fired["active"]].sort_values("health_score", ascending=False)
        rejected = fired[~fired["active"]].sort_values("health_score", ascending=False)
        fired_names = set(fired["signal_name"].dropna())
        not_fired = [name for name in universe if name not in fired_names][:8]
        rows.append(
            {
                "date": date,
                "action": "long" if direction > 0 else "yield",
                "direction": direction,
                "net_score": round(float(day["net_score"]), 4),
                "active_signal_count": int(day["active_signal_count"]),
                "active_signals": [] if pd.isna(day["active_signals"]) else str(day["active_signals"]).split(", "),
                "fwd_ret_1d": None if pd.isna(day["fwd_ret_1d"]) else float(day["fwd_ret_1d"]),
                "dir_ret_1d": display_ret,
                "yield_ret_1d": float(yield_info["daily"]),
                "yield_apy": float(yield_info["apy"]),
                "active_factors": factor_rows(active),
                "rejected_factors": factor_rows(rejected.head(8)),
                "not_fired": not_fired,
            }
        )
    today = pd.Timestamp.utcnow().strftime("%Y-%m-%d")
    latest_date = str(rows[0]["date"]) if rows else ""
    current_yield = yield_info_for_date(yields, today)
    if latest_date and latest_date < today and current_yield:
        rows.insert(
            0,
            {
                "date": today,
                "action": "yield",
                "direction": 0,
                "net_score": 0.0,
                "active_signal_count": 0,
                "active_signals": [],
                "fwd_ret_1d": None,
                "dir_ret_1d": None,
                "yield_ret_1d": current_yield["daily"],
                "yield_apy": current_yield["apy"],
                "yield_observed": current_yield["observed"],
                "report_status": "current_day_pending_result",
                "active_factors": [],
                "rejected_factors": [],
                "not_fired": universe[:8],
            },
        )
    return rows


def factor_rows(frame: pd.DataFrame) -> list[dict[str, object]]:
    out = []
    for _, row in frame.iterrows():
        out.append(
            {
                "name": row["signal_name"],
                "horizon": row["horizon"],
                "side": "long" if row["direction_label"] == "long" else "yield",
                "health": round(float(row["health_score"]), 1),
                "hit_rate": pct(float(row["hit_rate"])),
                "median": pct(float(row["median_return"])),
                "reason": row["reason"],
            }
        )
    return out


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    cache = ROOT / "2_backtest/cache"
    replay = pd.read_csv(cache / "walkforward_recommendation_replay.csv")
    health = pd.read_csv(cache / "walkforward_signal_health.csv")
    daily = pd.read_parquet(ROOT / "0_data/cache/processed/mnt_daily_2026.parquet")
    yield_path = ROOT / "0_data/cache/yields/mantle_stable_yield_daily.parquet"
    yields = pd.read_parquet(yield_path) if yield_path.exists() else pd.DataFrame()
    yield_charts_path = ROOT / "0_data/cache/yields/mantle_stable_yield_pool_charts.parquet"
    yield_charts = pd.read_parquet(yield_charts_path) if yield_charts_path.exists() else pd.DataFrame()
    btc_path = ROOT / "0_data/cache/raw/bybit_btc_spot_daily.parquet"
    btc_daily = pd.read_parquet(btc_path) if btc_path.exists() else pd.DataFrame()
    alerts_path = ROOT / "0_data/cache/onchain/alerts_14d.parquet"
    alerts = pd.read_parquet(alerts_path) if alerts_path.exists() else pd.DataFrame()
    yield_options = build_yield_options(yields, yield_charts)
    backtest = build_backtest_modes(replay, daily, yields, btc_daily)
    backtest["yield_options"] = yield_options
    out = {
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "yield_options": yield_options,
        "past_signals": build_past_signals(replay, health, build_yield_map(replay, yields), daily, yields, latest_live_mnt_price()),
        "backtest": backtest,
    }
    OUT.write_text(json.dumps(out, indent=2))
    summary = {item["label"]: item["return"] for item in out["backtest"]["summary"]}
    print(
        json.dumps(
            {"past_signals": len(out["past_signals"]), "intraday_events": len(alerts), "backtest": summary},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
