from __future__ import annotations

from typing import Any


def fetch_instrument(client: Any, category: str, symbol: str) -> dict[str, Any]:
    payload = client.get(
        "/v5/market/instruments-info",
        {"category": category, "symbol": symbol},
    )
    rows = payload.get("result", {}).get("list", [])
    if not rows:
        raise RuntimeError(f"Missing Bybit instrument info for {category}:{symbol}")
    return rows[0]

