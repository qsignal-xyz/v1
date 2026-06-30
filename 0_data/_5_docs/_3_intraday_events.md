# Intraday Event Coverage

- generated_at: 2026-06-30T22:06:01+00:00
- window: 2026-06-16T22:05:00+00:00 to 2026-06-30T22:05:00+00:00
- blocks: 96758594 to 97363394
- raw_logs: 257568
- normalized_events: 253261
- alerts: 787
- timestamp_method: linear interpolation between exact chunk boundary block timestamps

## Alert Semantics

- Tracked assets: stables, WMNT, WETH, mETH, cmETH, FBTC, WBTC, COOK, and confirmed Mantle xStocks from CoinGecko platform metadata.
- Bridge flows are labeled from canonical bridge mints/burns and transfers involving known bridge, pool, depository, or route contracts.
- Known bridge protocols: Mantle, USDT0, Stargate, Relay, deBridge, Hyperlane; LayerZero/Symbiosis/FBTC are detected through token mint/burn semantics where explicit route contracts are not tracked.
- Low/medium/high severity uses token-specific USD thresholds; the UI labels the base severity as low, not info.
- Yield-pool tokens: USDC, USDT0, USDe, sUSDe, USDY.
- Yield-pool mint/burn alerts are critical only when they exceed the stricter of the token/event historical outlier threshold and 1% of current total supply.
- Other flow alerts use token-specific USD thresholds.

## Token Decimals

- WMNT: rpc
- WETH: rpc
- mETH: rpc
- cmETH: rpc
- FBTC: rpc
- WBTC: rpc
- COOK: rpc
- USDC: rpc
- USDT: rpc
- USDe: rpc
- sUSDe: rpc
- USDY: rpc
- USDT0: rpc
- ABBVx: rpc
- GOOGLx: rpc
- AMZNx: rpc
- AAPLx: rpc
- BRK.Bx: rpc
- AVGOx: rpc
- CVXx: rpc
- KOx: rpc
- LLYx: rpc
- XOMx: rpc
- HDx: rpc
- JNJx: rpc
- JPMx: rpc
- MAx: rpc
- MRKx: rpc
- METAx: rpc
- MSFTx: rpc
- NVDAx: rpc
- PEPx: rpc
- PFEx: rpc
- PGx: rpc
- SPCXx: rpc
- TSLAx: rpc
- UNHx: rpc
- Vx: rpc

## Token Supply

- WMNT: rpc; total_supply=16037343.371839037
- WETH: rpc; total_supply=158512.72806198892
- mETH: rpc; total_supply=28634.701684382846
- cmETH: rpc; total_supply=10236.148653
- FBTC: rpc; total_supply=263.68890494
- WBTC: rpc; total_supply=48.82770076
- COOK: rpc; total_supply=4066360450.606808
- USDC: rpc; total_supply=25641818.45912
- USDT: rpc; total_supply=13284299.321273
- USDe: rpc; total_supply=78801807.135021
- sUSDe: rpc; total_supply=143850423.8204
- USDY: rpc; total_supply=25218092.86847119
- USDT0: rpc; total_supply=375252488.261325
- ABBVx: rpc; total_supply=10109.666088957134
- GOOGLx: rpc; total_supply=10013.658871173786
- AMZNx: rpc; total_supply=10000.0
- AAPLx: rpc; total_supply=10012.689523588211
- BRK.Bx: rpc; total_supply=10000.0
- AVGOx: rpc; total_supply=10037.900742010122
- CVXx: rpc; total_supply=10184.84352284944
- KOx: rpc; total_supply=10129.255589886372
- LLYx: rpc; total_supply=10034.895712496029
- XOMx: rpc; total_supply=10119.084722117206
- HDx: rpc; total_supply=10145.197827133095
- JNJx: rpc; total_supply=10114.033382734224
- JPMx: rpc; total_supply=10067.160350031967
- MAx: rpc; total_supply=10022.287611910813
- MRKx: rpc; total_supply=10151.236074562146
- METAx: rpc; total_supply=10018.152481705582
- MSFTx: rpc; total_supply=10036.007142843298
- NVDAx: rpc; total_supply=10008.871820382203
- PEPx: rpc; total_supply=10207.630905655727
- PFEx: rpc; total_supply=240263.3179535724
- PGx: rpc; total_supply=10100.251029399033
- SPCXx: rpc; total_supply=30000.0
- TSLAx: rpc; total_supply=10000.0
- UNHx: rpc; total_supply=10140.692880232007
- Vx: rpc; total_supply=10044.89302836559

## Token Prices

- WMNT: coingecko
- WETH: coingecko
- mETH: coingecko
- cmETH: coingecko
- FBTC: coingecko
- WBTC: coingecko
- COOK: coingecko
- USDC: stable_1_usd
- USDT: stable_1_usd
- USDe: stable_1_usd
- sUSDe: stable_1_usd
- USDY: stable_1_usd
- USDT0: stable_1_usd
- ABBVx: coingecko
- GOOGLx: coingecko
- AMZNx: coingecko
- AAPLx: coingecko
- BRK.Bx: coingecko
- AVGOx: coingecko
- CVXx: coingecko
- KOx: coingecko
- LLYx: coingecko
- XOMx: coingecko
- HDx: coingecko
- JNJx: coingecko
- JPMx: coingecko
- MAx: coingecko
- MRKx: coingecko
- METAx: coingecko
- MSFTx: coingecko
- NVDAx: coingecko
- PEPx: coingecko
- PFEx: coingecko
- PGx: coingecko
- SPCXx: coingecko
- TSLAx: coingecko
- UNHx: coingecko
- Vx: coingecko

## Failed Chunks

- none
