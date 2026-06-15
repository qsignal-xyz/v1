from __future__ import annotations

import numpy as np
import pandas as pd


def _prior_zscore(series: pd.Series, window: int = 30, min_periods: int = 20) -> pd.Series:
    mean = series.rolling(window, min_periods=min_periods).mean().shift(1)
    std = series.rolling(window, min_periods=min_periods).std(ddof=0).shift(1)
    return (series - mean) / std.replace(0, np.nan)


def _prior_rank(series: pd.Series, window: int = 30, min_periods: int = 20) -> pd.Series:
    def rank_last(values: np.ndarray) -> float:
        current = values[-1]
        history = values[:-1]
        if len(history) == 0 or np.isnan(current):
            return np.nan
        return float((history <= current).mean())

    return series.rolling(window + 1, min_periods=min_periods + 1).apply(rank_last, raw=True)


def add_daily_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy().sort_values("timestamp").reset_index(drop=True)
    out["ret_3d"] = out["bybit_perp_close"].pct_change(3)
    out["ret_7d"] = out["bybit_perp_close"].pct_change(7)
    out["oi_change_3d"] = out["bybit_open_interest_close"].pct_change(3)
    out["perp_turnover_z"] = _prior_zscore(np.log1p(out["bybit_perp_turnover_quote"]))
    out["spot_turnover_z"] = _prior_zscore(np.log1p(out["bybit_spot_turnover_quote"]))
    out["oi_change_z"] = _prior_zscore(out["bybit_oi_change_1d"])
    out["funding_z"] = _prior_zscore(out["bybit_funding_rate_avg"])
    out["basis_z"] = _prior_zscore(out["bybit_basis_pct_avg"])
    out["cg_volume_z"] = _prior_zscore(np.log1p(out["mnt_total_volume_usd"]))
    out["dex_volume_z"] = _prior_zscore(np.log1p(out["mantle_dex_volume_usd"]))
    out["tvl_change_z"] = _prior_zscore(out["mantle_tvl_usd_change_7d"])
    out["stables_change_z"] = _prior_zscore(out["mantle_stables_mcap_usd_change_7d"])
    out["app_fees_z"] = _prior_zscore(np.log1p(out["mantle_app_fees_usd"]))
    out["chain_fees_z"] = _prior_zscore(np.log1p(out["mantle_chain_fees_usd"]))
    out["dex_volume_rank"] = _prior_rank(out["mantle_dex_volume_usd"])
    out["perp_volume_rank"] = _prior_rank(out["bybit_perp_turnover_quote"])
    out["spot_volume_rank"] = _prior_rank(out["bybit_spot_turnover_quote"])
    out["price_above_7d"] = out["bybit_perp_close"] > out["bybit_perp_close"].rolling(7).mean()
    out["price_below_7d"] = out["bybit_perp_close"] < out["bybit_perp_close"].rolling(7).mean()
    return out

