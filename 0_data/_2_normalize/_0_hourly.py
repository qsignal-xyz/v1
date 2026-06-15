from __future__ import annotations

import pandas as pd


def _prefixed_kline(frame: pd.DataFrame, prefix: str) -> pd.DataFrame:
    keep = frame[
        ["timestamp", "open", "high", "low", "close", "volume_base", "turnover_quote"]
    ].copy()
    return keep.rename(
        columns={
            "open": f"{prefix}_open",
            "high": f"{prefix}_high",
            "low": f"{prefix}_low",
            "close": f"{prefix}_close",
            "volume_base": f"{prefix}_volume_base",
            "turnover_quote": f"{prefix}_turnover_quote",
        }
    )


def build_hourly_dataset(
    start_ms: int,
    end_ms: int,
    perp: pd.DataFrame,
    spot: pd.DataFrame,
    oi: pd.DataFrame,
    funding: pd.DataFrame,
) -> pd.DataFrame:
    timestamps = pd.date_range(
        pd.to_datetime(start_ms, unit="ms", utc=True),
        pd.to_datetime(end_ms, unit="ms", utc=True),
        freq="1h",
    )
    out = pd.DataFrame({"timestamp": timestamps})
    out = out.merge(_prefixed_kline(perp, "bybit_perp"), on="timestamp", how="left")
    out = out.merge(_prefixed_kline(spot, "bybit_spot"), on="timestamp", how="left")
    out = out.merge(
        oi[["timestamp", "open_interest", "single_open_interest"]].rename(
            columns={
                "open_interest": "bybit_open_interest",
                "single_open_interest": "bybit_single_open_interest",
            }
        ),
        on="timestamp",
        how="left",
    )
    funding_hourly = funding[["timestamp", "funding_rate"]].rename(
        columns={"funding_rate": "bybit_funding_rate"}
    )
    out = out.merge(funding_hourly, on="timestamp", how="left")
    out["bybit_funding_rate"] = out["bybit_funding_rate"].ffill()
    out["bybit_perp_ret_1h"] = out["bybit_perp_close"].pct_change()
    out["bybit_spot_ret_1h"] = out["bybit_spot_close"].pct_change()
    out["bybit_basis_pct"] = out["bybit_perp_close"] / out["bybit_spot_close"] - 1.0
    out["bybit_oi_change_1h"] = out["bybit_open_interest"].pct_change()
    return out

