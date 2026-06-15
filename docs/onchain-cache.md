# On-Chain Cache

`0_data/cache/onchain/` is generated runtime data. It is ignored by git and can
be rebuilt from Mantle RPC.

Runtime outputs used by the app:

- `alerts_14d.parquet`
- `alerts_14d.csv`
- `transfer_events_14d.parquet`
- `hourly_token_flows_14d.parquet`
- `daily_token_flows_14d.parquet`
- `summary_14d.json`
- `_coverage.md`

Fetch cache:

- `raw_logs/*.json`

`raw_logs` exists to avoid re-fetching every token/chunk from RPC on every
refresh. It is not needed by the browser app and should not be deployed as a
static asset. The refresh pipeline prunes raw log chunks outside the current
14-day window with:

```bash
python3 0_data/_4_build/_5_prune_onchain_raw_logs.py
```

Use dry-run to inspect cleanup:

```bash
python3 0_data/_4_build/_5_prune_onchain_raw_logs.py --dry-run
```

For production, keep parquet/JSON app outputs and raw log cache on the server
disk only. SQLite is useful for send/dedupe state or cursors, but the current
analytics path is better served by parquet files unless we need ad-hoc queries
over months of raw logs.
