from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
APP_DATA = ROOT / "4_runtime/app"
STATE_PATH = APP_DATA / "refresh_state.json"
HISTORY_PATH = APP_DATA / "history_backtest.json"
AI_PATH = APP_DATA / "ai_reports.json"
REPORT_COMMITS_PATH = APP_DATA / "report_commits.json"


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text())


def write_state(payload: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True))


def current_report_day(now: datetime) -> str:
    return now.date().isoformat()


def latest_history_day() -> str:
    history = read_json(HISTORY_PATH, {})
    rows = history.get("past_signals") or []
    if not rows:
        return ""
    return str(rows[0].get("date") or "")


def latest_ai_source_day() -> str:
    ai = read_json(AI_PATH, {})
    reports = ai.get("reports") or []
    if not reports:
        return ""
    report = reports[0]
    source_day = report.get("source_daily_date")
    if source_day:
        return str(source_day)
    return ""


def report_commit_due(target_day: str) -> bool:
    commits = read_json(REPORT_COMMITS_PATH, {})
    reports = commits.get("reports") or []
    for report in reports:
        if str(report.get("date") or "") != target_day:
            continue
        if report.get("tx_hash") and report.get("status") in {"committed", "submitted"}:
            return False
    return True


def refresh_due(target_day: str) -> bool:
    if latest_history_day() < target_day:
        return True
    if latest_ai_source_day() != target_day:
        return True
    return False


def run_daily(target_day: str) -> int:
    started = now_utc().isoformat()
    state = read_json(STATE_PATH, {})
    state.update(
        {
            "last_attempt_at": started,
            "last_attempt_target_day": target_day,
            "status": "running",
        }
    )
    write_state(state)

    result = subprocess.run(
        ["bash", "scripts/update_daily_app.sh"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        timeout=1800,
    )

    history_day = latest_history_day()
    ai_day = latest_ai_source_day()
    ok = result.returncode == 0 and history_day >= target_day and ai_day == target_day
    finished = now_utc().isoformat()
    state.update(
        {
            "last_finished_at": finished,
            "last_stdout_tail": result.stdout[-4000:],
            "last_stderr_tail": result.stderr[-4000:],
            "latest_history_day": history_day,
            "latest_ai_source_day": ai_day,
            "status": "ok" if ok else "failed",
        }
    )
    if ok:
        state["last_success_at"] = finished
        state["last_success_target_day"] = target_day
    write_state(state)

    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")
    if not ok and result.returncode == 0:
        print(
            f"daily refresh did not produce target day {target_day}: "
            f"history={history_day or '-'} ai={ai_day or '-'}"
        )
        return 1
    return result.returncode


def run_publish(target_day: str) -> int:
    result = subprocess.run(
        ["python3", "scripts/publish_daily_report.py", "--date", target_day],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        timeout=300,
    )
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")
    return result.returncode


def main() -> int:
    target_day = current_report_day(now_utc())
    if not refresh_due(target_day):
        if report_commit_due(target_day):
            print(f"{now_utc().isoformat()} render daily report commit due for {target_day}")
            return run_publish(target_day)
        print(f"{now_utc().isoformat()} render daily refresh skipped; target {target_day} already current")
        return 0
    print(f"{now_utc().isoformat()} render daily refresh due for {target_day}")
    result = run_daily(target_day)
    if result != 0:
        return result
    if report_commit_due(target_day):
        print(f"{now_utc().isoformat()} render daily report commit due for {target_day}")
        return run_publish(target_day)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
