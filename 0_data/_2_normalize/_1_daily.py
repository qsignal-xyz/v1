from __future__ import annotations

import pandas as pd


def aggregate_bybit_daily(hourly: pd.DataFrame) -> pd.DataFrame:
    frame = hourly.copy()
    frame["date"] = frame["timestamp"].dt.floor("D")
    grouped = frame.groupby("date", sort=True)
    daily = grouped.agg(
        hours=("timestamp", "count"),
        bybit_perp_open=("bybit_perp_open", "first"),
        bybit_perp_high=("bybit_perp_high", "max"),
        bybit_perp_low=("bybit_perp_low", "min"),
        bybit_perp_close=("bybit_perp_close", "last"),
        bybit_perp_volume_base=("bybit_perp_volume_base", "sum"),
        bybit_perp_turnover_quote=("bybit_perp_turnover_quote", "sum"),
        bybit_spot_open=("bybit_spot_open", "first"),
        bybit_spot_high=("bybit_spot_high", "max"),
        bybit_spot_low=("bybit_spot_low", "min"),
        bybit_spot_close=("bybit_spot_close", "last"),
        bybit_spot_volume_base=("bybit_spot_volume_base", "sum"),
        bybit_spot_turnover_quote=("bybit_spot_turnover_quote", "sum"),
        bybit_open_interest_close=("bybit_open_interest", "last"),
        bybit_open_interest_avg=("bybit_open_interest", "mean"),
        bybit_funding_rate_avg=("bybit_funding_rate", "mean"),
        bybit_basis_pct_avg=("bybit_basis_pct", "mean"),
    ).reset_index()
    daily = daily[daily["hours"] == 24].drop(columns=["hours"])
    daily = daily.rename(columns={"date": "timestamp"})
    daily["bybit_perp_ret_1d"] = daily["bybit_perp_close"].pct_change()
    daily["bybit_spot_ret_1d"] = daily["bybit_spot_close"].pct_change()
    daily["bybit_oi_change_1d"] = daily["bybit_open_interest_close"].pct_change()
    return daily.reset_index(drop=True)


def join_daily_context(base: pd.DataFrame, context_frames: list[pd.DataFrame]) -> pd.DataFrame:
    out = base.copy()
    for frame in context_frames:
        clean = frame.copy()
        clean["timestamp"] = clean["timestamp"].dt.floor("D")
        out = out.merge(clean.drop_duplicates("timestamp"), on="timestamp", how="left")
    return out.sort_values("timestamp").reset_index(drop=True)


def add_daily_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for column in [
        "mantle_tvl_usd",
        "mantle_dex_volume_usd",
        "mantle_stables_mcap_usd",
        "mantle_app_fees_usd",
        "mantle_app_revenue_usd",
        "mantle_chain_fees_usd",
        "mantle_chain_revenue_usd",
        "mnt_market_cap_usd",
        "mnt_total_volume_usd",
    ]:
        if column in out.columns:
            out[f"{column}_change_1d"] = out[column].pct_change(fill_method=None)
            out[f"{column}_change_7d"] = out[column].pct_change(7, fill_method=None)
    if {"mantle_dex_volume_usd", "mantle_tvl_usd"}.issubset(out.columns):
        out["mantle_dex_volume_to_tvl"] = out["mantle_dex_volume_usd"] / out["mantle_tvl_usd"]
    return out
