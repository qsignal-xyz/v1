from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
APP_DATA = ROOT / "4_runtime/app"
SEND_DATA = ROOT / "4_runtime/send"
STATE_PATH = SEND_DATA / "state.json"
KEYS = Path("/agents/shared/config/keys.env")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text())


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))


def read_key(name: str) -> str | None:
    value = os.environ.get(name)
    if value:
        return value.strip().strip('"').strip("'")
    if not KEYS.exists():
        return None
    prefix = f"{name}="
    for raw in KEYS.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or not line.startswith(prefix):
            continue
        return line.split("=", 1)[1].strip().strip('"').strip("'") or None
    return None


def app_url(path: str) -> str:
    base = read_key("QSIGNAL_APP_URL") or "https://qsignal.xyz"
    return base.rstrip("/") + "/" + path.lstrip("/")


def load_state() -> dict[str, Any]:
    state = read_json(STATE_PATH, {"sent": {}})
    if "sent" not in state or not isinstance(state["sent"], dict):
        raise ValueError(f"invalid notification state: {STATE_PATH}")
    return state


def is_sent(state: dict[str, Any], key: str, channel: str) -> bool:
    item = state["sent"].get(key)
    return isinstance(item, dict) and bool(item.get(channel))


def mark_sent(state: dict[str, Any], key: str, channel: str) -> None:
    item = state["sent"].setdefault(key, {})
    item[channel] = now_utc()


def severity_rank(value: str | None) -> int:
    return {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(str(value or "").lower(), 0)


def money(value: float | int | None) -> str:
    amount = float(value or 0)
    sign = "-" if amount < 0 else "+"
    amount = abs(amount)
    if amount >= 1_000_000_000:
        body = f"${amount / 1_000_000_000:.2f}B"
    elif amount >= 1_000_000:
        body = f"${amount / 1_000_000:.2f}M"
    elif amount >= 1_000:
        body = f"${amount / 1_000:.2f}K"
    else:
        body = f"${amount:.2f}"
    return sign + body


def pct(value: float | int | None) -> str:
    return f"{float(value or 0):+.2f}%"


def short_lines(lines: list[str], limit: int = 3) -> str:
    return "\n".join(f"- {line}" for line in lines[:limit] if line)
