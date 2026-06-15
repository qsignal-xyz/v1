from __future__ import annotations

import math
from typing import Any

import pandas as pd

TAKER_FEE = 0.00055
BACKTEST_START = pd.Timestamp("2024-06-01T00:00:00Z")


def max_drawdown(returns: pd.Series) -> float:
    equity = (1 + returns.fillna(0)).cumprod()
    peak = equity.cummax()
    return float((equity / peak - 1).min())


def sharpe(returns: pd.Series) -> float:
    clean = returns.dropna()
    std = float(clean.std())
    if not len(clean) or std == 0:
        return 0.0
    return float((clean.mean() / std) * math.sqrt(365))


def daily_yield_return(apy_pct: pd.Series) -> pd.Series:
    apy = apy_pct.fillna(0).clip(lower=0, upper=80) / 100
    return (1 + apy) ** (1 / 365) - 1


def mode_return(
    base: pd.DataFrame,
    target_position: pd.Series,
    yield_when_flat: bool,
) -> pd.DataFrame:
    out = base.copy()
    out["position"] = target_position.astype(float)
    out["turnover"] = out["position"].diff().abs().fillna(out["position"].abs())
    out["fee_drag"] = out["turnover"] * TAKER_FEE
    out["funding_pnl"] = -out["position"] * out["funding_daily"]
    out["yield_pnl"] = out["yield_daily"].where(out["position"].eq(0) & yield_when_flat, 0.0)
    out["strategy_return"] = (
        out["position"] * out["fwd_ret_1d"].fillna(0)
        + out["funding_pnl"].fillna(0)
        + out["yield_pnl"].fillna(0)
        - out["fee_drag"].fillna(0)
    )
    out["equity"] = (1 + out["strategy_return"]).cumprod()
    return out


def stats(label: str, frame: pd.DataFrame, key: str) -> dict[str, Any]:
    returns = frame[key]
    equity = (1 + returns.fillna(0)).cumprod()
    days = int(len(frame))
    x_return = float(equity.iloc[-1])
    return {
        "label": label,
        "return": x_return - 1,
        "x_return": x_return,
        "cagr": (x_return ** (365 / days) - 1) if days and x_return > 0 else -1.0,
        "sharpe": sharpe(returns),
        "max_dd": max_drawdown(returns),
        "days": days,
    }


def build_backtest_modes(
    replay: pd.DataFrame,
    daily: pd.DataFrame,
    yields: pd.DataFrame,
    btc_daily: pd.DataFrame,
) -> dict[str, Any]:
    clean = replay.dropna(subset=["fwd_ret_1d"]).copy()
    clean["timestamp"] = pd.to_datetime(clean["timestamp"], utc=True)
    data_start = clean["timestamp"].min()
    clean = clean[clean["timestamp"] >= BACKTEST_START].copy()
    daily = daily[[
        "timestamp",
        "bybit_perp_high",
        "bybit_perp_low",
        "bybit_perp_close",
        "bybit_funding_rate_avg",
    ]].copy()
    daily = daily.sort_values("timestamp")
    daily["next_bybit_perp_high"] = daily["bybit_perp_high"].shift(-1)
    daily["next_bybit_perp_low"] = daily["bybit_perp_low"].shift(-1)
    merged = clean.merge(daily, on="timestamp", how="left")
    if not yields.empty:
        yields = yields.rename(columns={"stable_yield_apy": "yield_apy"})
        merged = merged.merge(yields[["timestamp", "yield_apy"]], on="timestamp", how="left")
        merged["yield_apy_observed"] = merged["yield_apy"].notna()
        merged["yield_apy"] = merged["yield_apy"].ffill().bfill().fillna(0.0)
    else:
        merged["yield_apy"] = 0.0
        merged["yield_apy_observed"] = False
    if not btc_daily.empty:
        btc_daily = btc_daily.sort_values("timestamp").copy()
        btc_daily["btc_fwd_ret_1d"] = btc_daily["btc_spot_close"].shift(-1) / btc_daily["btc_spot_close"] - 1
        merged = merged.merge(
            btc_daily[["timestamp", "btc_spot_close", "btc_fwd_ret_1d"]],
            on="timestamp",
            how="left",
        )
    else:
        merged["btc_spot_close"] = pd.NA
        merged["btc_fwd_ret_1d"] = 0.0
    merged["funding_daily"] = merged["bybit_funding_rate_avg"].fillna(0) * 3
    merged["yield_daily"] = daily_yield_return(merged["yield_apy"])

    model = mode_return(merged, merged["direction"].clip(lower=0), True)
    hold_return = merged["fwd_ret_1d"].fillna(0)
    hold_equity = (1 + hold_return).cumprod()
    btc_return = merged["btc_fwd_ret_1d"].fillna(0)
    btc_equity = (1 + btc_return).cumprod()

    points = []
    for pos, (_, row) in enumerate(merged.iterrows()):
        points.append(
            {
                "date": str(row["timestamp"])[:10],
                "mnt_price": float(row["bybit_perp_close"]),
                "next_high": float(row["next_bybit_perp_high"]) if not pd.isna(row["next_bybit_perp_high"]) else 0.0,
                "next_low": float(row["next_bybit_perp_low"]) if not pd.isna(row["next_bybit_perp_low"]) else 0.0,
                "btc_price": float(row["btc_spot_close"]) if not pd.isna(row["btc_spot_close"]) else 0.0,
                "action": "long" if int(row["direction"]) > 0 else "yield",
                "direction": int(row["direction"]),
                "mnt_ret_1d": float(row["fwd_ret_1d"]) if not pd.isna(row["fwd_ret_1d"]) else 0.0,
                "btc_ret_1d": float(row["btc_fwd_ret_1d"]) if not pd.isna(row["btc_fwd_ret_1d"]) else 0.0,
                "yield_apy": float(row["yield_apy"]) if not pd.isna(row["yield_apy"]) else 0.0,
                "yield_observed": bool(row["yield_apy_observed"]),
                "yield_daily": float(row["yield_daily"]) if not pd.isna(row["yield_daily"]) else 0.0,
                "funding_daily": float(row["funding_daily"]),
                "hold": float(hold_equity.iloc[pos]),
                "btc_hold": float(btc_equity.iloc[pos]),
                "directional": float(model["equity"].iloc[pos]),
                "position": float(model["position"].iloc[pos]),
            }
        )

    summary = [
        stats("Buy & Hold MNT", pd.DataFrame({"r": hold_return}), "r"),
        stats("Buy & Hold BTC", pd.DataFrame({"r": btc_return}), "r"),
        stats("Model Long / Yield", model, "strategy_return"),
    ]
    return {
        "points": points,
        "summary": summary,
        "assumptions": {
            "fee_rate": TAKER_FEE,
            "fee_source": "Bybit futures example taker fee 0.055%; applied on notional turnover.",
            "funding": "Bybit MNTUSDT daily average funding * 3 funding windows/day.",
            "yield": "TVL-weighted Mantle stable pool APY from DeFiLlama Yields; missing early history is filled with the first observed Mantle stable APY as a stable-yield proxy.",
            "warmup": f"Replay starts on {str(BACKTEST_START)[:10]}; earlier data is warmup for rolling signal health.",
            "leverage": "Leverage slider scales long exposure only; risk-off or neutral signals allocate to stable yield. Liquidation uses next-day low approximation and ignores exchange maintenance tiers.",
            "data_start": str(data_start)[:10],
            "backtest_start": str(BACKTEST_START)[:10],
        },
    }
