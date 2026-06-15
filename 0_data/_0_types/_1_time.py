from __future__ import annotations

from datetime import datetime, timezone

MS_PER_HOUR = 60 * 60 * 1000


def parse_utc_ms(value: str) -> int:
    clean = value.replace("Z", "+00:00")
    return int(datetime.fromisoformat(clean).timestamp() * 1000)


def ms_to_iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def last_complete_hour_ms() -> int:
    now = datetime.now(timezone.utc)
    floored = now.replace(minute=0, second=0, microsecond=0)
    return int(floored.timestamp() * 1000) - MS_PER_HOUR


def iter_ms_windows(start_ms: int, end_ms: int, hours_per_window: int) -> list[tuple[int, int]]:
    windows: list[tuple[int, int]] = []
    step = hours_per_window * MS_PER_HOUR
    cursor = start_ms
    while cursor <= end_ms:
        window_end = min(cursor + step - MS_PER_HOUR, end_ms)
        windows.append((cursor, window_end))
        cursor = window_end + MS_PER_HOUR
    return windows

