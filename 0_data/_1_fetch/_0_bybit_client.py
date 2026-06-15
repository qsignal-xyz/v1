from __future__ import annotations

import time
from typing import Any

import requests


class BybitClient:
    def __init__(
        self,
        base_url: str = "https://api.bybit.com",
        delay_seconds: float = 0.25,
        user_agent: str = "Mozilla/5.0 (compatible; research-script; +local-analysis)",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.delay_seconds = delay_seconds
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        last_error: Exception | None = None
        for attempt in range(4):
            if attempt:
                time.sleep(1.5 * attempt)
            try:
                response = self.session.get(url, params=params, timeout=20)
                response.raise_for_status()
                payload = response.json()
                if payload.get("retCode") not in (0, None):
                    raise RuntimeError(f"Bybit retCode={payload.get('retCode')}: {payload}")
                time.sleep(self.delay_seconds)
                return payload
            except Exception as exc:
                last_error = exc
        raise RuntimeError(f"Bybit request failed: {path} {params}") from last_error

