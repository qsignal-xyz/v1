from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "3_app"
APP_DATA = ROOT / "4_runtime/app"
OUT = APP_DATA / "ai_reports.json"
RAW_OUT = ROOT / "logs/ai_reports_raw.json"
LIVE = APP_DATA / "live_signals.json"
INTRADAY = APP_DATA / "intraday_events.json"
HISTORY = APP_DATA / "history_backtest.json"
KEYS = Path("/agents/shared/config/keys.env")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELS = ["google/gemini-2.5-flash", "deepseek/deepseek-chat-v3-0324", "qwen/qwen3-32b"]
MERGE_MODEL = "deepseek/deepseek-chat-v3-0324"
COOLDOWN_SECONDS = int(os.environ.get("QSIGNAL_AI_COOLDOWN_SECONDS", "60"))


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text())


def read_key(name: str) -> str | None:
    if os.environ.get(name):
        return os.environ[name]
    if not KEYS.exists():
        return None
    prefix = f"{name}="
    for line in KEYS.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def openrouter(model: str, prompt: str, max_tokens: int = 700) -> dict[str, Any]:
    key = read_key("API_OPENROUTER")
    if not key:
        return {"model": model, "answer": None, "error": "API_OPENROUTER missing"}
    body = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": max_tokens,
        }
    ).encode()
    req = urllib.request.Request(
        OPENROUTER_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://qsignal.xyz",
            "X-Title": "QSignal AI Analyst",
        },
    )
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            payload = json.loads(response.read())
        answer = payload["choices"][0]["message"]["content"]
        return {
            "model": model,
            "answer": answer,
            "error": None,
            "latency_ms": int((time.time() - started) * 1000),
            "usage": payload.get("usage", {}),
        }
    except urllib.error.HTTPError as exc:
        return {
            "model": model,
            "answer": None,
            "error": f"HTTP {exc.code}: {exc.read().decode(errors='replace')[:300]}",
            "latency_ms": int((time.time() - started) * 1000),
        }
    except Exception as exc:
        return {
            "model": model,
            "answer": None,
            "error": f"{type(exc).__name__}: {exc}",
            "latency_ms": int((time.time() - started) * 1000),
        }


def latest_report() -> dict[str, Any] | None:
    data = read_json(OUT, {"reports": []})
    reports = data.get("reports", [])
    return reports[0] if reports else None


def cooldown_report() -> dict[str, Any] | None:
    report = latest_report()
    if not report:
        return None
    generated = datetime.fromisoformat(report["generated_at"])
    if now_utc() - generated < timedelta(seconds=COOLDOWN_SECONDS):
        return report
    return None


def recent_alert_summary(intraday: dict[str, Any]) -> dict[str, Any]:
    cutoff = now_utc() - timedelta(hours=24)
    counts: dict[str, int] = {}
    values: dict[str, float] = {}
    recent = []
    for alert in intraday.get("alerts", []):
        ts = datetime.strptime(alert["timestamp"], "%Y-%m-%d:%H:%M:%S").replace(tzinfo=timezone.utc)
        if ts < cutoff:
            continue
        signal = str(alert.get("signal", "unknown"))
        value = float(alert.get("value_usd") or 0)
        if signal in {"stableBurn", "tokenBurn", "bridgeOut"}:
            value *= -1
        counts[signal] = counts.get(signal, 0) + 1
        values[signal] = values.get(signal, 0.0) + value
        recent.append(
            {
                "timestamp": alert.get("timestamp"),
                "signal": signal,
                "token": alert.get("token"),
                "value_usd": round(value, 2),
                "severity": alert.get("severity"),
                "bridge_protocol": alert.get("bridge_protocol"),
            }
        )
    return {"counts": counts, "values_usd": values, "latest": recent[-15:]}


def context() -> dict[str, Any]:
    subprocess.run(
        ["python3", str(ROOT / "scripts/generate_live_signals.py")],
        cwd=str(ROOT),
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        timeout=45,
    )
    live = read_json(LIVE, {})
    intraday = read_json(INTRADAY, {})
    history = read_json(HISTORY, {})
    past = history.get("past_signals", [])[:7]
    yields = history.get("yield_options", {})
    return {
        "as_of": now_utc().isoformat(),
        "history_generated_at": history.get("generated_at"),
        "current_daily": past[0] if past else {},
        "last_7_daily": past,
        "yield_options": {
            "basket_apy": yields.get("basket_apy"),
            "basket_tvl_usd": yields.get("basket_tvl_usd"),
            "best": yields.get("best"),
            "capacity": yields.get("capacity"),
        },
        "intraday": recent_alert_summary(intraday),
        "live_signals": live,
    }


def analyst_prompt(ctx: dict[str, Any]) -> str:
    best = ctx.get("yield_options", {}).get("best", {})
    best_line = ""
    if best:
        best_line = (
            f"\nCurrent best yield route: {best.get('symbol', '')} on {best.get('project', '')} "
            f"at {best.get('apy', 0):.2f}% APY (TVL ${best.get('tvl_usd', 0):,.0f}). "
            "When recommending yield, cite this specific route and APY, not the basket average.\n"
        )
    return (
        "You are QSignal's AI analyst for a Mantle portfolio signal dashboard.\n"
        "Use only the JSON evidence below. Do not invent prices, trades, or data sources.\n"
        "Rejected factors are diagnostics only; never describe rejected factors as active, fired, or trading signals.\n"
        "If active_signal_count is 0 or active_factors is empty, explicitly say there is no fired directional edge.\n"
        f"{best_line}"
        "Return strict JSON with keys: title, stance, confidence, summary, why, action, risks, evidence.\n"
        "stance must be one of: long, yield, watch, exit_yield.\n"
        "summary <= 35 words. why/action/risks/evidence are arrays of 2-4 short strings.\n\n"
        f"EVIDENCE_JSON:\n{json.dumps(ctx, ensure_ascii=True)[:12000]}"
    )


def merge_prompt(ctx: dict[str, Any], responses: list[dict[str, Any]]) -> str:
    compact = [
        {"model": item["model"], "answer": item.get("answer"), "error": item.get("error")}
        for item in responses
    ]
    best = ctx.get("yield_options", {}).get("best", {})
    best_line = ""
    if best:
        best_line = (
            f"Current best yield route: {best.get('symbol', '')} on {best.get('project', '')} "
            f"at {best.get('apy', 0):.2f}% APY. Use this APY in the report, not the basket average.\n"
        )
    return (
        "Merge the model analyst notes into one concise QSignal report.\n"
        "Use the evidence JSON to resolve conflicts. Do not invent facts.\n"
        "Rejected factors are diagnostics only; never describe rejected factors as active, fired, or trading signals.\n"
        "If active_signal_count is 0 or active_factors is empty, explicitly say there is no fired directional edge.\n"
        f"{best_line}"
        "Return strict JSON with keys: title, stance, confidence, summary, why, action, risks, evidence.\n"
        "stance must be one of: long, yield, watch, exit_yield. confidence is 0-100.\n"
        "summary <= 35 words. Arrays must have 2-4 short strings.\n\n"
        f"EVIDENCE_JSON:\n{json.dumps(ctx, ensure_ascii=True)[:9000]}\n\n"
        f"MODEL_NOTES_JSON:\n{json.dumps(compact, ensure_ascii=True)[:9000]}"
    )


def parse_answer(text: str | None) -> dict[str, Any] | None:
    if not text:
        return None
    clean = text.strip()
    if clean.startswith("```"):
        clean = clean.strip("`")
        clean = clean.removeprefix("json").strip()
    start = clean.find("{")
    end = clean.rfind("}")
    if start < 0 or end < start:
        return None
    try:
        return json.loads(clean[start : end + 1])
    except json.JSONDecodeError:
        return None


def normalize_report(report: dict[str, Any]) -> dict[str, Any]:
    stance = str(report.get("stance", "watch")).strip().lower()
    if stance not in {"long", "yield", "watch", "exit_yield"}:
        stance = "watch"
    raw_confidence = report.get("confidence", 0)
    confidence_words = {"low": 35.0, "neutral": 50.0, "medium": 60.0, "high": 80.0}
    if isinstance(raw_confidence, str) and raw_confidence.strip().lower() in confidence_words:
        confidence = confidence_words[raw_confidence.strip().lower()]
    else:
        try:
            confidence = float(raw_confidence)
        except (TypeError, ValueError):
            confidence = 0.0
    if 0 < confidence <= 1:
        confidence *= 100
    confidence = max(0.0, min(100.0, confidence))

    def array(key: str) -> list[str]:
        value = report.get(key, [])
        if isinstance(value, list):
            return [str(item)[:220] for item in value[:4]]
        if value:
            return [str(value)[:220]]
        return []

    return {
        "title": str(report.get("title") or "QSignal AI Analyst")[:120],
        "stance": stance,
        "confidence": round(confidence, 1),
        "summary": str(report.get("summary") or "-")[:260],
        "why": array("why"),
        "action": array("action"),
        "risks": array("risks"),
        "evidence": array("evidence"),
    }


def public_report(report: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in report.items()
        if key not in {"model_responses", "merge_response"}
    }


def save_report(report: dict[str, Any]) -> dict[str, Any]:
    RAW_OUT.parent.mkdir(parents=True, exist_ok=True)
    raw_existing = read_json(RAW_OUT, {"reports": []})
    raw_reports = raw_existing.get("reports", [])
    raw_reports.insert(0, report)
    raw_existing["reports"] = raw_reports[:24]
    raw_existing["generated_at"] = now_utc().isoformat()
    RAW_OUT.write_text(json.dumps(raw_existing, indent=2))

    public = public_report(report)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    existing = read_json(OUT, {"reports": []})
    reports = [public_report(item) for item in existing.get("reports", [])]
    reports.insert(0, public)
    existing["reports"] = reports[:24]
    existing["generated_at"] = now_utc().isoformat()
    OUT.write_text(json.dumps(existing, indent=2))
    return existing


def run(force: bool = False) -> dict[str, Any]:
    if not force:
        current = cooldown_report()
        if current:
            return {
                "status": "cooldown",
                "cooldown_until": current["cooldown_until"],
                "report": current,
            }
    ctx = context()
    prompt = analyst_prompt(ctx)
    responses = [openrouter(model, prompt) for model in MODELS]
    valid = [item for item in responses if item.get("answer")]
    if not valid:
        return {"status": "error", "error": "all analyst models failed", "responses": responses}
    merged = openrouter(MERGE_MODEL, merge_prompt(ctx, responses), max_tokens=900)
    parsed = parse_answer(merged.get("answer"))
    if parsed is None:
        parsed = parse_answer(valid[0].get("answer"))
    if parsed is None:
        return {
            "status": "error",
            "error": "could not parse analyst JSON",
            "responses": responses,
            "merge": merged,
        }
    parsed = normalize_report(parsed)

    generated = now_utc()
    report = {
        "id": f"ai:{generated.strftime('%Y%m%d%H%M%S')}",
        "generated_at": generated.isoformat(),
        "timestamp": generated.strftime("%Y-%m-%d:%H:%M:%S"),
        "cooldown_until": (generated + timedelta(seconds=COOLDOWN_SECONDS)).isoformat(),
        "source_daily_date": str(ctx.get("current_daily", {}).get("date") or ""),
        "source_history_generated_at": ctx.get("history_generated_at"),
        "models": MODELS,
        "merge_model": MERGE_MODEL,
        "report": parsed,
        "source_counts": {
            "live_signals": len(ctx.get("live_signals", {}).get("signals", [])),
            "intraday_alerts": sum(ctx.get("intraday", {}).get("counts", {}).values()),
            "daily_days": len(ctx.get("last_7_daily", [])),
        },
        "model_responses": responses,
        "merge_response": merged,
    }
    public = save_report(report)["reports"][0]
    return {"status": "ok", "cooldown_until": public["cooldown_until"], "report": public}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    result = run(force=args.force)
    print(json.dumps(result, indent=2))
    if result.get("status") == "error":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
