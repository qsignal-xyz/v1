from __future__ import annotations

import argparse
from pathlib import Path

from _0_common import APP_DATA, SEND_DATA, load_state, now_utc, read_json, write_json
from _1_format import ai_message, daily_message, demo_messages, intraday_messages, live_messages
from _2_transport import configured_channels, send


def messages_for(kind: str) -> list[tuple[str, str]]:
    messages: list[tuple[str, str]] = []
    if kind in {"all", "daily"}:
        item = daily_message(read_json(APP_DATA / "history_backtest.json", {}))
        if item:
            messages.append(item)
    if kind in {"all", "live"}:
        messages.extend(live_messages(read_json(APP_DATA / "live_signals.json", {})))
        messages.extend(intraday_messages(read_json(APP_DATA / "intraday_events.json", {})))
    if kind in {"all", "ai"}:
        item = ai_message(read_json(APP_DATA / "ai_reports.json", {}))
        if item:
            messages.append(item)
    if kind == "demo":
        messages.extend(
            demo_messages(
                read_json(APP_DATA / "history_backtest.json", {}),
                read_json(APP_DATA / "live_signals.json", {}),
                read_json(APP_DATA / "ai_reports.json", {}),
            )
        )
    return messages


def write_previews(messages: list[tuple[str, str]], kind: str) -> Path:
    SEND_DATA.mkdir(parents=True, exist_ok=True)
    path = SEND_DATA / f"preview_{kind}.txt"
    chunks = []
    for key, text in messages:
        chunks.append(f"--- {key} ---\n{text}")
    path.write_text("\n\n".join(chunks) if chunks else "no messages\n")
    return path


def dispatch(kind: str, should_send: bool, soft_fail: bool) -> int:
    messages = messages_for(kind)
    preview = write_previews(messages, kind)
    print(f"prepared {len(messages)} {kind} message(s); preview={preview}")
    if not should_send:
        return 0
    channels = configured_channels()
    if not channels:
        print("no notification channels configured; skipped send")
        return 0
    state = load_state()
    failures = 0
    sent = 0
    for key, text in messages:
        channel_state = state["sent"].setdefault(key, {})
        for channel in channels:
            if channel_state.get(channel):
                continue
            result = send(channel, text)
            if result.get("ok"):
                channel_state[channel] = {"sent_at": now_utc(), "status": result.get("status", 200)}
                sent += 1
                print(f"sent {key} -> {channel}")
            else:
                failures += 1
                print(f"failed {key} -> {channel}: {result.get('status')} {result.get('error')}")
    write_json(SEND_DATA / "state.json", state)
    print(f"notification dispatch done: sent={sent} failures={failures}")
    return 0 if soft_fail or not failures else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=["daily", "live", "ai", "all", "demo"], default="all")
    parser.add_argument("--send", action="store_true", help="post to configured channels")
    parser.add_argument("--dry-run", action="store_true", help="write preview only")
    parser.add_argument("--soft-fail", action="store_true", help="log delivery failures but exit 0")
    args = parser.parse_args()
    if args.send and args.dry_run:
        raise SystemExit("--send and --dry-run cannot be combined")
    return dispatch(args.kind, should_send=args.send, soft_fail=args.soft_fail)


if __name__ == "__main__":
    raise SystemExit(main())
