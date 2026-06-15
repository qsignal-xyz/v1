from __future__ import annotations

import json
import os
import subprocess
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
    "tx_activity.json",
}


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


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(APP), **kwargs)

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
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
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
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
