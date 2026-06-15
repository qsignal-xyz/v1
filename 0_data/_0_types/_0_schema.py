from __future__ import annotations

BYBIT_SYMBOL = "MNTUSDT"
BYBIT_INTERVAL = "60"

RAW_DATASETS = {
    "bybit_perp_klines_1h": {
        "path": "0_data/cache/raw/bybit_perp_klines_1h.parquet",
        "freq": "1h",
        "required": ["timestamp", "open", "high", "low", "close", "volume_base"],
    },
    "bybit_spot_klines_1h": {
        "path": "0_data/cache/raw/bybit_spot_klines_1h.parquet",
        "freq": "1h",
        "required": ["timestamp", "open", "high", "low", "close", "volume_base"],
    },
    "bybit_open_interest_1h": {
        "path": "0_data/cache/raw/bybit_open_interest_1h.parquet",
        "freq": "1h",
        "required": ["timestamp", "open_interest"],
    },
    "bybit_funding": {
        "path": "0_data/cache/raw/bybit_funding.parquet",
        "freq": "8h",
        "required": ["timestamp", "funding_rate"],
    },
}

PROCESSED_DATASET = {
    "name": "mnt_bybit_hourly_2026",
    "path": "0_data/cache/processed/mnt_bybit_hourly_2026.parquet",
    "freq": "1h",
}

DAILY_DATASETS = {
    "defillama_tvl_daily": {
        "path": "0_data/cache/raw/defillama_tvl_daily.parquet",
        "freq": "1d",
        "required": ["timestamp", "mantle_tvl_usd"],
    },
    "defillama_dex_volume_daily": {
        "path": "0_data/cache/raw/defillama_dex_volume_daily.parquet",
        "freq": "1d",
        "required": ["timestamp", "mantle_dex_volume_usd"],
    },
    "defillama_stables_daily": {
        "path": "0_data/cache/raw/defillama_stables_daily.parquet",
        "freq": "1d",
        "required": ["timestamp", "mantle_stables_mcap_usd"],
    },
    "defillama_app_fees_daily": {
        "path": "0_data/cache/raw/defillama_app_fees_daily.parquet",
        "freq": "1d",
        "required": ["timestamp", "mantle_app_fees_usd"],
    },
    "defillama_app_revenue_daily": {
        "path": "0_data/cache/raw/defillama_app_revenue_daily.parquet",
        "freq": "1d",
        "required": ["timestamp", "mantle_app_revenue_usd"],
    },
    "defillama_chain_fees_daily": {
        "path": "0_data/cache/raw/defillama_chain_fees_daily.parquet",
        "freq": "1d",
        "required": ["timestamp", "mantle_chain_fees_usd"],
    },
    "defillama_chain_revenue_daily": {
        "path": "0_data/cache/raw/defillama_chain_revenue_daily.parquet",
        "freq": "1d",
        "required": ["timestamp", "mantle_chain_revenue_usd"],
    },
    "coingecko_mnt_market_daily": {
        "path": "0_data/cache/raw/coingecko_mnt_market_daily.parquet",
        "freq": "1d",
        "required": ["timestamp", "mnt_market_cap_usd", "mnt_total_volume_usd"],
    },
}
