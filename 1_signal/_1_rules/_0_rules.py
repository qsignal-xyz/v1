from __future__ import annotations

import numpy as np
import pandas as pd


def _clip_strength(values: pd.Series | np.ndarray, base: float = 0.5) -> pd.Series:
    series = pd.Series(values).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return (base + series.abs() / 4.0).clip(0.25, 1.0)


def build_rules(frame: pd.DataFrame) -> list[dict[str, object]]:
    f = frame
    rules: list[dict[str, object]] = []

    def add(name: str, direction: int, mask: pd.Series, strength: pd.Series, reason: str) -> None:
        rules.append(
            {
                "name": name,
                "direction": direction,
                "mask": mask.fillna(False),
                "strength": strength.reindex(f.index).fillna(0.5).clip(0.0, 1.0),
                "reason": reason,
            }
        )

    add("leveraged_momentum", 1, (f.bybit_perp_ret_1d > 0) & (f.oi_change_z > 0.5) & (f.perp_turnover_z > 0),
        _clip_strength(f.oi_change_z + f.perp_turnover_z), "price up with rising OI and perp volume")
    add("spot_led_accumulation", 1, (f.spot_turnover_z > 1) & (f.perp_turnover_z < 0.75) & (f.bybit_spot_ret_1d > 0),
        _clip_strength(f.spot_turnover_z - f.perp_turnover_z), "spot volume leads perps while price rises")
    add("short_squeeze_setup", 1, (f.funding_z < -1) & (f.bybit_perp_ret_1d > -0.01) & (f.price_above_7d),
        _clip_strength(f.funding_z), "negative funding while price holds above 7d mean")
    add("ecosystem_growth_confirmed", 1, (f.mantle_tvl_usd_change_7d > 0) & (f.mantle_stables_mcap_usd_change_7d > 0) & (f.dex_volume_z > 0),
        _clip_strength(f.dex_volume_z + f.tvl_change_z), "Mantle TVL, stables, and DEX activity confirm growth")
    add("basis_discount_reversion", 1, (f.basis_z < -1) & (f.bybit_perp_ret_1d > -0.03),
        _clip_strength(f.basis_z), "perp trades unusually cheap to spot")
    add("fee_activity_lag", 1, (f.app_fees_z > 1) & (f.chain_fees_z > 0.5) & (f.bybit_perp_ret_1d < 0.02),
        _clip_strength(f.app_fees_z + f.chain_fees_z), "Mantle fee activity rises before price reacts")
    add("stablecoin_inflow_momentum", 1, (f.mantle_stables_mcap_usd_change_7d > 0.01) & (f.price_above_7d),
        _clip_strength(f.stables_change_z), "stablecoin supply expands while price trend is positive")
    add("deleveraged_rebound", 1, (f.ret_3d < -0.08) & (f.funding_z < 0) & (f.oi_change_3d < 0),
        _clip_strength(f.ret_3d * 10), "sharp drop with falling leverage and non-crowded funding")
    add("volume_breakout", 1, (f.perp_turnover_z > 1) & (f.spot_turnover_z > 0.5) & (f.bybit_perp_ret_1d > 0),
        _clip_strength(f.perp_turnover_z + f.spot_turnover_z), "spot and perp volume confirm an upside breakout")
    add("market_volume_confirmation", 1, (f.cg_volume_z > 1) & (f.bybit_perp_ret_1d > 0) & (f.bybit_oi_change_1d > 0),
        _clip_strength(f.cg_volume_z + f.oi_change_z), "aggregate MNT volume confirms price and OI")

    add("crowded_long_risk", -1, (f.funding_z > 1) & (f.bybit_perp_ret_1d < 0.01) & (f.oi_change_z > 0),
        _clip_strength(f.funding_z + f.oi_change_z), "positive funding and rising OI without price progress")
    add("leveraged_sell_pressure", -1, (f.bybit_perp_ret_1d < 0) & (f.oi_change_z > 0.5) & (f.perp_turnover_z > 0),
        _clip_strength(f.oi_change_z + f.perp_turnover_z), "price falls while leverage and perp volume rise")
    add("perp_pump_without_spot", -1, (f.bybit_perp_ret_1d > 0.03) & (f.perp_turnover_z > 1) & (f.spot_turnover_z < 0),
        _clip_strength(f.perp_turnover_z - f.spot_turnover_z), "perp-led pump lacks spot confirmation")
    add("ecosystem_outflow_risk", -1, (f.mantle_tvl_usd_change_7d < 0) & (f.mantle_stables_mcap_usd_change_7d < 0) & (f.dex_volume_z < 0),
        _clip_strength(f.tvl_change_z + f.stables_change_z), "Mantle TVL and stables contract together")
    add("basis_premium_fade", -1, (f.basis_z > 1) & (f.funding_z > 0.5),
        _clip_strength(f.basis_z + f.funding_z), "perp trades rich while funding is elevated")
    add("fee_activity_drop", -1, (f.mantle_app_fees_usd_change_7d < -0.2) & (f.mantle_chain_fees_usd_change_7d < 0),
        _clip_strength(f.app_fees_z + f.chain_fees_z), "app and chain fee activity deteriorate")
    add("oi_unwind_downtrend", -1, (f.ret_3d < 0) & (f.oi_change_3d < -0.03) & (f.price_below_7d),
        _clip_strength(f.ret_3d * 10 + f.oi_change_3d * 10), "price downtrend with open interest unwind")
    add("failed_volume_breakout", -1, (f.perp_turnover_z > 1) & (f.bybit_perp_ret_1d < 0) & (f.spot_turnover_z < 0.5),
        _clip_strength(f.perp_turnover_z), "large perp volume closes red without spot support")
    add("bearish_market_volume", -1, (f.cg_volume_z > 1) & (f.bybit_perp_ret_1d < 0) & (f.bybit_oi_change_1d > 0),
        _clip_strength(f.cg_volume_z + f.oi_change_z), "aggregate volume confirms downside with rising OI")
    add("price_ecosystem_divergence", -1, (f.ret_7d > 0.05) & (f.mantle_tvl_usd_change_7d < 0) & (f.mantle_stables_mcap_usd_change_7d < 0),
        _clip_strength(f.ret_7d * 10), "price rallies while Mantle TVL and stables fall")
    return rules

