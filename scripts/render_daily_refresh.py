from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
APP_DATA = ROOT / "4_runtime/app"
STATE_PATH = APP_DATA / "refresh_state.json"
HISTORY_PATH = APP_DATA / "history_backtest.json"
AI_PATH = APP_DATA / "ai_reports.json"
REPORT_COMMITS_PATH = APP_DATA / "report_commits.json"
REPORT_COMMIT_START_DAY = "2026-06-14"


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text())


def write_state(payload: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))


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


def sync_public_report_commits() -> None:
    url = "https://qsignal.xyz/report_commits.json"
    try:
        with urllib.request.urlopen(f"{url}?sync={int(now_utc().timestamp())}", timeout=30) as response:
            public = json.loads(response.read())
    except Exception as exc:
        print(f"{now_utc().isoformat()} public report commit sync failed: {exc}")
        return

    data = read_json(REPORT_COMMITS_PATH, {"reports": []})
    reports = list(data.get("reports") or [])
    existing = {
        (str(item.get("date") or ""), str(item.get("report_hash") or ""))
        for item in reports
        if item.get("tx_hash") and item.get("status") in {"committed", "submitted"}
    }
    added = 0
    for record in public.get("reports") or []:
        if not record.get("tx_hash") or record.get("status") not in {"committed", "submitted"}:
            continue
        key = (str(record.get("date") or ""), str(record.get("report_hash") or ""))
        if not key[0] or not key[1] or key in existing:
            continue
        reports.append(record)
        existing.add(key)
        added += 1

    if added:
        reports.sort(key=lambda item: str(item.get("date") or ""), reverse=True)
        data["reports"] = reports[:365]
        data["generated_at"] = now_utc().isoformat()
        write_json(REPORT_COMMITS_PATH, data)
        print(f"{now_utc().isoformat()} synced {added} public report commit(s)")


def report_commit_backlog(target_day: str) -> list[str]:
    dates = {target_day}
    for row in read_json(HISTORY_PATH, {}).get("past_signals") or []:
        day = str(row.get("date") or "")
        if REPORT_COMMIT_START_DAY <= day <= target_day:
            dates.add(day)
    for report in read_json(AI_PATH, {}).get("reports") or []:
        source_day = str(report.get("source_daily_date") or "")
        if source_day and source_day <= target_day:
            dates.add(source_day)
    return [day for day in sorted(dates) if report_commit_due(day)]


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
        env={**os.environ, "QSIGNAL_SKIP_PUBLISH": "1"},
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


def run_publish_backlog(target_day: str) -> int:
    for day in report_commit_backlog(target_day):
        print(f"{now_utc().isoformat()} render daily report commit due for {day}")
        result = run_publish(day)
        if result != 0:
            return result
    return 0


def main() -> int:
    sync_public_report_commits()
    target_day = current_report_day(now_utc())
    if not refresh_due(target_day):
        result = run_publish_backlog(target_day)
        if result != 0:
            return result
        message = f"{now_utc().isoformat()} render daily refresh skipped; target {target_day} already current"
        state = read_json(STATE_PATH, {})
        state.update(
            {
                "last_checked_at": now_utc().isoformat(),
                "last_attempt_target_day": target_day,
                "last_stdout_tail": message,
                "last_stderr_tail": "",
                "latest_history_day": latest_history_day(),
                "latest_ai_source_day": latest_ai_source_day(),
                "status": "current",
            }
        )
        write_state(state)
        print(message)
        return 0
    print(f"{now_utc().isoformat()} render daily refresh due for {target_day}")
    result = run_daily(target_day)
    if result != 0:
        return result
    return run_publish_backlog(target_day)


if __name__ == "__main__":
    raise SystemExit(main())
