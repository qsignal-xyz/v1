from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "3_app"
APP_DATA = ROOT / "4_runtime/app"
GENERATED_PAYLOADS = {
    "ai_reports.json",
    "history_backtest.json",
    "intraday_events.json",
    "live_signals.json",
    "report_commits.json",
    "tx_activity.json",
}
DAILY_REFRESH_PATHS = {
    "/",
    "/reports",
    "/reports/",
    "/history_backtest.json",
    "/ai_reports.json",
    "/intraday_events.json",
    "/report_commits.json",
}
DAILY_REFRESH_LOCK = threading.Lock()
DAILY_REFRESH_LAST_ATTEMPT = 0.0
DAILY_REFRESH_RETRY_SECONDS = 300


def parse_script_json(stdout: str) -> dict:
    clean = stdout.strip()
    if not clean:
        raise json.JSONDecodeError("empty stdout", stdout, 0)
    try:
        payload = json.loads(clean)
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    objects: list[dict] = []
    index = 0
    while True:
        start = clean.find("{", index)
        if start < 0:
            break
        try:
            payload, end = decoder.raw_decode(clean[start:])
        except json.JSONDecodeError:
            index = start + 1
            continue
        if isinstance(payload, dict):
            objects.append(payload)
        index = start + max(end, 1)
    for payload in reversed(objects):
        if "status" in payload:
            return payload
    if objects:
        return objects[-1]
    raise json.JSONDecodeError("no JSON object in stdout", stdout, 0)


def read_runtime_json(name: str) -> dict:
    path = APP_DATA / name
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        print(f"runtime JSON decode failed for {name}: {exc}", flush=True)
        return {}
    return payload if isinstance(payload, dict) else {}


def utc_today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def latest_history_day() -> str:
    rows = read_runtime_json("history_backtest.json").get("past_signals") or []
    if not rows:
        return ""
    return str(rows[0].get("date") or "")


def latest_ai_day() -> str:
    reports = read_runtime_json("ai_reports.json").get("reports") or []
    if not reports:
        return ""
    return str(reports[0].get("source_daily_date") or "")


def report_commit_due() -> bool:
    today = utc_today()
    reports = read_runtime_json("report_commits.json").get("reports") or []
    for report in reports:
        if str(report.get("date") or "") != today:
            continue
        if report.get("tx_hash") and report.get("status") in {"committed", "submitted"}:
            return False
    return True


def daily_runtime_stale() -> bool:
    today = utc_today()
    return latest_history_day() < today or latest_ai_day() != today or report_commit_due()


def maybe_refresh_daily_runtime(path: str) -> None:
    global DAILY_REFRESH_LAST_ATTEMPT
    if path not in DAILY_REFRESH_PATHS or not daily_runtime_stale():
        return
    now = time.monotonic()
    if now - DAILY_REFRESH_LAST_ATTEMPT < DAILY_REFRESH_RETRY_SECONDS:
        return
    if not DAILY_REFRESH_LOCK.acquire(blocking=False):
        return
    DAILY_REFRESH_LAST_ATTEMPT = now
    try:
        print(f"{datetime.now(timezone.utc).isoformat()} stale daily runtime; refreshing before serving {path}", flush=True)
        result = subprocess.run(
            ["python3", "scripts/render_daily_refresh.py"],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            timeout=1800,
        )
        if result.stdout:
            print(result.stdout[-4000:], end="", flush=True)
        if result.stderr:
            print(result.stderr[-4000:], end="", flush=True)
        if result.returncode != 0:
            print(
                f"{datetime.now(timezone.utc).isoformat()} daily refresh before serve exited {result.returncode}; "
                f"history={latest_history_day() or '-'} ai={latest_ai_day() or '-'}",
                flush=True,
            )
    except subprocess.TimeoutExpired:
        print(f"{datetime.now(timezone.utc).isoformat()} daily refresh before serve timed out", flush=True)
    except Exception as exc:
        print(f"{datetime.now(timezone.utc).isoformat()} daily refresh before serve failed: {type(exc).__name__}: {exc}", flush=True)
    finally:
        DAILY_REFRESH_LOCK.release()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self._sent_no_cache = False
        super().__init__(*args, directory=str(APP), **kwargs)

    def send_no_cache_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, max-age=0, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self._sent_no_cache = True

    def end_headers(self) -> None:
        path = urlparse(self.path).path
        suffix = Path(path).suffix
        if not self._sent_no_cache and (suffix in {".html", ".js", ".css", ".json"} or path in {"/", "/live", "/reports", "/backtest", "/docs"}):
            self.send_no_cache_headers()
        super().end_headers()

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_no_cache_headers()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_runtime_file(self, path: Path) -> None:
        if not path.exists():
            self.send_error(404, "runtime payload not found")
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_no_cache_headers()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        maybe_refresh_daily_runtime(path)
        name = Path(path).name
        if name in GENERATED_PAYLOADS:
            self.send_runtime_file(APP_DATA / name)
            return
        local = APP / path.lstrip("/")
        is_route = path in {
            "/",
            "/live",
            "/live/",
            "/signal",
            "/signal/",
            "/signals",
            "/signals/",
            "/reports",
            "/reports/",
            "/past-signals",
            "/past-signals/",
            "/backtest",
            "/backtest/",
            "/docs",
            "/docs/",
        }
        if is_route or (not local.exists() and "." not in Path(path).name):
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:
        if self.path != "/api/ai/analyze":
            self.send_json(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(length) if length else b"{}"
            body = json.loads(raw or b"{}")
            cmd = ["python3", str(ROOT / "scripts/ai_analyze.py")]
            if body.get("force"):
                cmd.append("--force")
            result = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, timeout=300)
            if result.returncode != 0:
                self.send_json(500, {"status": "error", "stderr": result.stderr[-2000:], "stdout": result.stdout[-2000:]})
                return
            self.send_json(200, parse_script_json(result.stdout))
        except subprocess.TimeoutExpired:
            self.send_json(504, {"status": "error", "error": "AI analyst timed out"})
        except Exception as exc:
            self.send_json(500, {"status": "error", "error": f"{type(exc).__name__}: {exc}"})


def main() -> None:
    port = int(os.environ.get("PORT", "3008"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"QSignal app/API server listening on http://0.0.0.0:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
