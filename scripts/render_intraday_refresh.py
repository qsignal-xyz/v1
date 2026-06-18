from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVENTS_PATH = ROOT / "4_runtime/app/intraday_events.json"


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text())


def generated_day() -> str:
    generated_at = str(read_json(EVENTS_PATH, {}).get("generated_at") or "")
    if not generated_at:
        return ""
    try:
        return datetime.fromisoformat(generated_at.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return ""


def main() -> int:
    today = now_utc().date().isoformat()
    if generated_day() >= today:
        print(f"{now_utc().isoformat()} render intraday refresh skipped; target {today} already current")
        return 0

    print(f"{now_utc().isoformat()} render intraday refresh due for {today}")
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
