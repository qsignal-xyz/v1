from __future__ import annotations

import time
from typing import Any

import requests

USER_AGENT = "Mozilla/5.0 (compatible; research-script; +local-analysis)"
DEFAULT_ENDPOINTS = [
    "https://mantle.api.pocket.network",
    "https://rpc.mantle.xyz",
]


class MantleRpc:
    def __init__(self, endpoints: list[str] | None = None) -> None:
        self.endpoints = endpoints or DEFAULT_ENDPOINTS
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Content-Type": "application/json"})
        self.request_id = 0
        self.errors: list[str] = []

    def call(self, method: str, params: list[Any]) -> Any:
        self.request_id += 1
        payload = {"jsonrpc": "2.0", "id": self.request_id, "method": method, "params": params}
        failures: list[str] = []
        for endpoint in self.endpoints:
            for attempt in range(3):
                try:
                    response = self.session.post(endpoint, json=payload, timeout=30)
                    if response.status_code != 200:
                        raise RuntimeError(f"HTTP {response.status_code}: {response.text[:180]}")
                    data = response.json()
                    if "error" in data:
                        raise RuntimeError(str(data["error"])[:220])
                    return data["result"]
                except Exception as exc:
                    failure = f"{endpoint} {method} attempt={attempt + 1}: {exc}"
                    failures.append(failure)
                    time.sleep(min(0.5 * (2**attempt), 4.0))
        self.errors.extend(failures)
        raise RuntimeError("; ".join(failures[-4:]))

    def latest_block(self) -> int:
        return int(self.call("eth_blockNumber", []), 16)

    def block(self, number: int) -> dict[str, Any]:
        result = self.call("eth_getBlockByNumber", [hex(number), False])
        if not result:
            raise RuntimeError(f"Missing block {number}")
        return result

    def block_timestamp(self, number: int) -> int:
        return int(self.block(number)["timestamp"], 16)

    def get_logs(self, address: str, topic0: str, from_block: int, to_block: int) -> list[dict[str, Any]]:
        params = [
            {
                "address": address,
                "fromBlock": hex(from_block),
                "toBlock": hex(to_block),
                "topics": [topic0],
            }
        ]
        result = self.call("eth_getLogs", params)
        if not isinstance(result, list):
            raise RuntimeError(f"Unexpected eth_getLogs result for {address}: {type(result).__name__}")
        return result

    def decimals(self, address: str) -> int:
        result = self.call("eth_call", [{"to": address, "data": "0x313ce567"}, "latest"])
        if not result or result == "0x":
            raise RuntimeError(f"Empty decimals() result for {address}")
        return int(result, 16)

    def total_supply(self, address: str, decimals: int) -> float:
        result = self.call("eth_call", [{"to": address, "data": "0x18160ddd"}, "latest"])
        if not result or result == "0x":
            raise RuntimeError(f"Empty totalSupply() result for {address}")
        return int(result, 16) / (10**decimals)
