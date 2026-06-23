from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVENTS_PATH = ROOT / "4_runtime/app/intraday_events.json"
REFRESH_SECONDS = int(os.environ.get("QSIGNAL_INTRADAY_REFRESH_SECONDS", "300"))


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text())


def generated_at() -> datetime | None:
    generated_at = str(read_json(EVENTS_PATH, {}).get("generated_at") or "")
    if not generated_at:
        return None
    try:
        value = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def refresh_reason(now: datetime) -> str:
    generated = generated_at()
    if generated is None:
        return "missing generated_at"
    age_seconds = int((now - generated).total_seconds())
    if generated.date() < now.date():
        return f"previous UTC day {generated.date().isoformat()}"
    if age_seconds >= REFRESH_SECONDS:
        return f"age {age_seconds}s >= {REFRESH_SECONDS}s"
    return ""


def main() -> int:
    now = now_utc()
    today = now.date().isoformat()
    reason = refresh_reason(now)
    if not reason:
        generated = generated_at()
        age_seconds = int((now - generated).total_seconds()) if generated else 0
        print(f"{now.isoformat()} render intraday refresh skipped; age {age_seconds}s < {REFRESH_SECONDS}s")
        return 0

    print(f"{now.isoformat()} render intraday refresh due for {today}: {reason}")
    result = subprocess.run(
        ["python3", "0_data/_4_build/_2_backfill_intraday_events.py"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        timeout=900,
    )
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
