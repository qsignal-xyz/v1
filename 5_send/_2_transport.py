from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from _0_common import read_key


def configured_channels() -> list[str]:
    channels = []
    if read_key("QSIGNAL_TELEGRAM_BOT_TOKEN") and read_key("QSIGNAL_TELEGRAM_CHAT_ID"):
        channels.append("telegram")
    if read_key("QSIGNAL_DISCORD_WEBHOOK_URL"):
        channels.append("discord")
    return channels


def send(channel: str, text: str) -> dict[str, Any]:
    if channel == "telegram":
        return _send_telegram(text)
    if channel == "discord":
        return _send_discord(text)
    raise ValueError(f"unknown notification channel: {channel}")


def _send_telegram(text: str) -> dict[str, Any]:
    token = read_key("QSIGNAL_TELEGRAM_BOT_TOKEN")
    chat_id = read_key("QSIGNAL_TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise ValueError("telegram credentials missing")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = urllib.parse.urlencode(
        {
            "chat_id": chat_id,
            "text": text[:3900],
            "disable_web_page_preview": "true",
        }
    ).encode()
    return _post(url, body, {"Content-Type": "application/x-www-form-urlencoded"})


def _send_discord(text: str) -> dict[str, Any]:
    url = read_key("QSIGNAL_DISCORD_WEBHOOK_URL")
    if not url:
        raise ValueError("discord webhook missing")
    body = json.dumps({"content": text[:1900]}).encode()
    return _post(url, body, {"Content-Type": "application/json"})


def _post(url: str, body: bytes, headers: dict[str, str]) -> dict[str, Any]:
    headers = {"User-Agent": "QSignal/0.1 (+https://qsignal.xyz)", **headers}
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode(errors="replace")
            if not raw:
                return {"ok": True, "status": response.status}
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"raw": raw[:300]}
            return {"ok": True, "status": response.status, "response": payload}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:500]
        return {"ok": False, "status": exc.code, "error": detail}
    except Exception as exc:
        return {"ok": False, "status": 0, "error": f"{type(exc).__name__}: {exc}"}
