from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from _0_common import app_url, money, severity_rank, short_lines


def _title_case(value: Any) -> str:
    return str(value or "").replace("_", " ").strip().title()


def _best_yield(history: dict[str, Any]) -> str:
    best = history.get("yield_options", {}).get("best") or {}
    project = best.get("project")
    symbol = best.get("symbol")
    apy = best.get("apy")
    if not project or not symbol or apy is None:
        return "Yield route: unavailable"
    return f"Yield route: {symbol} on {project} at {float(apy):.2f}% APY"


def _yield_route(history: dict[str, Any]) -> str:
    best = history.get("yield_options", {}).get("best") or {}
    project = best.get("project")
    symbol = best.get("symbol")
    apy = best.get("apy")
    if not project or not symbol or apy is None:
        return "unavailable"
    return f"{symbol} on {project} at {float(apy):.2f}% APY"


def daily_message(history: dict[str, Any]) -> tuple[str, str] | None:
    days = history.get("past_signals", [])
    if not days:
        return None
    day = days[0]
    action = _title_case(day.get("action") or "watch")
    score = float(day.get("net_score") or 0)
    active = day.get("active_factors") or day.get("active_signals") or []
    rejected = day.get("rejected_factors") or []
    reasons = []
    for item in active[:3]:
        if isinstance(item, dict):
            reasons.append(f"{item.get('name', 'signal')} {item.get('horizon', '')}".strip())
        else:
            reasons.append(str(item))
    if not reasons and rejected:
        reasons.append(f"{len(rejected)} rejected diagnostic factor(s); no fired edge")
    if not reasons:
        reasons.append("No fired directional edge")
    key = f"daily:{day.get('date')}"
    text = (
        f"QSignal Daily Report - {day.get('date')}\n\n"
        f"Action: {action}\n"
        f"Score: {score:.0f}/100\n"
        f"Model: {len(active)} active / {len(rejected)} rejected\n"
        f"{_best_yield(history)}\n\n"
        f"Why:\n{short_lines(reasons)}\n\n"
        f"Report: {app_url('/reports')}"
    )
    return key, text


def demo_messages(history: dict[str, Any], live: dict[str, Any], ai: dict[str, Any]) -> list[tuple[str, str]]:
    days = history.get("past_signals", [])
    if not days:
        return []
    day = days[0]
    report = (ai.get("reports") or [{}])[0].get("report") or {}
    summary = report.get("summary") or "No fired directional edge. Maintain stable yield."
    signals = live.get("signals", [])
    onchain = live.get("state", {}).get("onchain", {})
    mnt = live.get("state", {}).get("mnt", {})
    active = day.get("active_factors") or day.get("active_signals") or []
    rejected = day.get("rejected_factors") or []
    date = day.get("date")
    action = _title_case(day.get("action") or "watch")
    route = _yield_route(history)
    daily = (
        f"QSignal Daily Report\n"
        f"Mantle portfolio signal | {date} close\n\n"
        f"Recommendation: {action}\n"
        f"Model score: {float(day.get('net_score') or 0):.0f}/100\n"
        f"Signal state: {len(active)} active / {len(rejected)} rejected\n"
        f"Yield route: {route}\n\n"
        f"AI read: {summary}\n\n"
        f"Live context:\n"
        f"- MNT 24h: {float(mnt.get('change_24h') or 0) * 100:+.2f}%\n"
        f"- Net on-chain flow: {money(onchain.get('net_flow_usd'))}\n"
        f"- On-chain alerts: {onchain.get('alerts_24h', 0)} in 24h\n\n"
        f"Full report: {app_url('/reports')}\n"
        f"Not financial advice."
    )
    lines = []
    for signal in signals[:5]:
        severity = str(signal.get("severity") or "").upper()
        lines.append(f"{signal.get('label')}: {signal.get('value')} ({severity})")
    live_text = (
        "QSignal Live Radar Snapshot\n"
        "Compact demo signal tape\n\n"
        f"{short_lines(lines, 5)}\n\n"
        f"Radar: {app_url('/live')}\n"
        "Small signals are context; daily model controls allocation."
    )
    return [(f"demo:daily:{date}", daily), (f"demo:live:{live.get('generated_at')}", live_text)]


def live_messages(live: dict[str, Any]) -> list[tuple[str, str]]:
    out = []
    for signal in live.get("signals", []):
        if severity_rank(signal.get("severity")) < 2:
            continue
        label = str(signal.get("label") or "Live signal")
        severity = str(signal.get("severity") or "medium").upper()
        day = str(signal.get("timestamp") or live.get("generated_at") or "")[:10]
        key = f"live:{day}:{signal.get('type')}:{label}:{severity}"
        text = (
            "QSignal Live Alert\n\n"
            f"{severity}: {label}\n"
            f"Value: {signal.get('value', '-')}\n"
            f"Detail: {signal.get('detail', '-')}\n"
            f"Action: {signal.get('proposed_action', 'Watch only')}\n\n"
            f"Live: {app_url('/live')}"
        )
        out.append((key, text))
    return out


def intraday_messages(intraday: dict[str, Any]) -> list[tuple[str, str]]:
    out = []
    seen = set()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    for alert in intraday.get("alerts", []):
        try:
            ts = datetime.strptime(str(alert.get("timestamp")), "%Y-%m-%d:%H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if ts < cutoff:
            continue
        rank = severity_rank(alert.get("severity"))
        value_usd = abs(float(alert.get("value_usd") or 0))
        if rank < 3 and not (rank == 2 and value_usd >= 5_000_000):
            continue
        tx_hash = str(alert.get("tx_hash") or "")
        signal = str(alert.get("signal") or "event")
        token = str(alert.get("token") or "")
        key = f"event:{tx_hash or alert.get('timestamp')}:{signal}:{token}"
        if key in seen:
            continue
        seen.add(key)
        tx_line = f"\nTx: https://mantlescan.xyz/tx/{tx_hash}" if tx_hash else ""
        text = (
            "QSignal On-Chain Alert\n\n"
            f"{str(alert.get('severity')).upper()}: {signal} {token}\n"
            f"Value: {alert.get('value') or money(alert.get('value_usd'))}\n"
            f"Action: {alert.get('proposed_action', 'Watch only')}\n"
            f"Detail: {alert.get('detail', '-')}{tx_line}\n\n"
            f"Live: {app_url('/live')}"
        )
        out.append((key, text))
    return out


def ai_message(ai: dict[str, Any]) -> tuple[str, str] | None:
    reports = ai.get("reports", [])
    if not reports:
        return None
    item = reports[0]
    report = item.get("report") or {}
    action = short_lines([str(x) for x in report.get("action", [])], 3)
    key = f"ai:{item.get('id')}"
    text = (
        "QSignal AI Analyst\n\n"
        f"Stance: {_title_case(report.get('stance'))}\n"
        f"Confidence: {float(report.get('confidence') or 0):.0f}/100\n"
        f"Summary: {report.get('summary', '-')}\n\n"
        f"Action:\n{action}\n\n"
        f"Live: {app_url('/live')}"
    )
    return key, text
