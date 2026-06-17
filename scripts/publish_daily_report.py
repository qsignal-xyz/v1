from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
APP_DATA = ROOT / "4_runtime/app"
HISTORY_PATH = APP_DATA / "history_backtest.json"
AI_PATH = APP_DATA / "ai_reports.json"
OUT_PATH = APP_DATA / "report_commits.json"
DEPLOYMENT_PATH = ROOT / "contracts/deployments/mantle-mainnet.json"
KEYS = Path("/agents/shared/config/keys.env")
CHAIN_ID = 5000
EXPLORER_TX = "https://mantlescan.xyz/tx/"


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text())


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))


def read_key(name: str) -> str | None:
    value = os.environ.get(name)
    if value:
        return value.strip().strip('"').strip("'")
    if not KEYS.exists():
        return None
    prefix = f"{name}="
    for raw in KEYS.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or not line.startswith(prefix):
            continue
        return line.split("=", 1)[1].strip().strip('"').strip("'") or None
    return None


def app_url(path: str) -> str:
    base = read_key("QSIGNAL_APP_URL") or "https://qsignal.xyz"
    return base.rstrip("/") + "/" + path.lstrip("/")


def deployment() -> dict[str, Any]:
    data = read_json(DEPLOYMENT_PATH, {})
    vanity = data.get("deployments", {}).get("vanity", {})
    return {
        "chain_id": int(data.get("chain_id") or CHAIN_ID),
        "rpc_url": read_key("QSIGNAL_MANTLE_RPC_URL") or read_key("MANTLE_RPC_URL") or data.get("rpc_url") or "https://rpc.mantle.xyz",
        "ledger_address": read_key("QSIGNAL_LEDGER_ADDRESS") or vanity.get("address") or "",
    }


def current_daily(date: str | None) -> dict[str, Any]:
    rows = read_json(HISTORY_PATH, {}).get("past_signals") or []
    if not rows:
        raise RuntimeError(f"no daily rows in {HISTORY_PATH}")
    if date is None:
        return rows[0]
    for row in rows:
        if str(row.get("date")) == date:
            return row
    raise RuntimeError(f"daily row {date} not found in {HISTORY_PATH}")


def ai_report_for(date: str) -> dict[str, Any] | None:
    reports = read_json(AI_PATH, {}).get("reports") or []
    for report in reports:
        if str(report.get("source_daily_date") or "") == date:
            return report
    return None


def canonical_report(day: dict[str, Any], report: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "schema": "qsignal.daily_report.v1",
        "date": day.get("date"),
        "daily": day,
        "ai_report": report,
    }


def report_hash(payload: dict[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return "0x" + hashlib.sha256(body).hexdigest()


def pad32(data: bytes) -> bytes:
    size = ((len(data) + 31) // 32) * 32
    return data + (b"\x00" * (size - len(data)))


def commit_calldata(signal_hash: str, report_uri: str) -> str:
    from eth_utils import keccak

    selector = keccak(text="commit(bytes32,string)")[:4]
    hash_bytes = bytes.fromhex(signal_hash.removeprefix("0x"))
    if len(hash_bytes) != 32:
        raise ValueError(f"signal hash must be bytes32, got {signal_hash}")
    uri = report_uri.encode()
    encoded = (
        selector
        + hash_bytes
        + (64).to_bytes(32, "big")
        + len(uri).to_bytes(32, "big")
        + pad32(uri)
    )
    return "0x" + encoded.hex()


def rpc(url: str, method: str, params: list[Any]) -> Any:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.loads(response.read())
    if payload.get("error"):
        raise RuntimeError(f"{method} failed: {payload['error']}")
    return payload.get("result")


def send_commit(rpc_url: str, ledger_address: str, signal_hash: str, report_uri: str, private_key: str) -> dict[str, Any]:
    from eth_account import Account
    from eth_utils import to_checksum_address

    account = Account.from_key(private_key)
    sender = account.address
    chain_id = int(rpc(rpc_url, "eth_chainId", []), 16)
    if chain_id != CHAIN_ID:
        raise RuntimeError(f"unexpected chain id {chain_id}, expected {CHAIN_ID}")
    to_address = to_checksum_address(ledger_address)
    data = commit_calldata(signal_hash, report_uri)
    nonce = int(rpc(rpc_url, "eth_getTransactionCount", [sender, "pending"]), 16)
    gas_price = int(rpc(rpc_url, "eth_gasPrice", []), 16)
    estimate = int(
        rpc(
            rpc_url,
            "eth_estimateGas",
            [{"from": sender, "to": to_address, "value": "0x0", "data": data}],
        ),
        16,
    )
    tx = {
        "chainId": chain_id,
        "nonce": nonce,
        "to": to_address,
        "value": 0,
        "data": data,
        "gas": int(estimate * 1.25) + 10_000,
        "gasPrice": gas_price,
    }
    signed = Account.sign_transaction(tx, private_key)
    raw = getattr(signed, "raw_transaction", None) or getattr(signed, "rawTransaction")
    raw_hex = raw.hex()
    if not raw_hex.startswith("0x"):
        raw_hex = "0x" + raw_hex
    tx_hash = rpc(rpc_url, "eth_sendRawTransaction", [raw_hex])
    receipt = None
    for _ in range(60):
        receipt = rpc(rpc_url, "eth_getTransactionReceipt", [tx_hash])
        if receipt:
            break
        time.sleep(2)
    if not receipt:
        return {"tx_hash": tx_hash, "status": "submitted", "oracle": sender}
    status = int(receipt.get("status", "0x0"), 16)
    if status != 1:
        raise RuntimeError(f"ledger tx reverted: {tx_hash}")
    return {
        "tx_hash": tx_hash,
        "status": "committed",
        "block_number": int(receipt.get("blockNumber", "0x0"), 16),
        "oracle": sender,
    }


def existing_records() -> dict[str, Any]:
    data = read_json(OUT_PATH, {"reports": []})
    if not isinstance(data.get("reports"), list):
        data["reports"] = []
    return data


def upsert_record(data: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    reports = [
        item
        for item in data.get("reports", [])
        if not (item.get("date") == record.get("date") and item.get("report_hash") == record.get("report_hash"))
    ]
    reports.insert(0, record)
    data["reports"] = reports[:365]
    data["generated_at"] = now_utc()
    return data


def run(date: str | None = None, dry_run: bool = False) -> dict[str, Any]:
    cfg = deployment()
    day = current_daily(date)
    day_date = str(day.get("date") or "")
    ai_report = ai_report_for(day_date)
    payload = canonical_report(day, ai_report)
    signal_hash = report_hash(payload)
    report_uri = app_url(f"reports#daily-{day_date}")
    data = existing_records()
    existing = next(
        (
            item
            for item in data.get("reports", [])
            if item.get("date") == day_date
            and item.get("report_hash") == signal_hash
            and item.get("tx_hash")
            and item.get("status") in {"committed", "submitted"}
        ),
        None,
    )
    if existing:
        return {"status": "already_committed", "record": existing}

    base = {
        "date": day_date,
        "report_hash": signal_hash,
        "report_uri": report_uri,
        "ledger_address": cfg["ledger_address"],
        "chain_id": cfg["chain_id"],
        "explorer_url": "",
        "committed_at": "",
        "tx_hash": "",
        "block_number": None,
        "oracle": "",
        "status": "dry_run" if dry_run else "pending",
    }
    if dry_run:
        record = base
    else:
        private_key = read_key("PK_MANTLE_QSIGNAL") or read_key("QSIGNAL_LEDGER_PRIVATE_KEY")
        if not private_key:
            record = {
                **base,
                "status": "pending",
                "note": "ledger transaction pending",
            }
        elif not cfg["ledger_address"]:
            record = {**base, "status": "failed", "error": "QSIGNAL_LEDGER_ADDRESS is not configured"}
        else:
            sent = send_commit(cfg["rpc_url"], cfg["ledger_address"], signal_hash, report_uri, private_key)
            tx_hash = sent["tx_hash"]
            record = {
                **base,
                **sent,
                "committed_at": now_utc(),
                "explorer_url": EXPLORER_TX + tx_hash,
            }
    write_json(OUT_PATH, upsert_record(data, record))
    status = "skipped_missing_key" if record["status"] == "pending" and not record.get("tx_hash") else record["status"]
    return {"status": status, "record": record}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = run(date=args.date, dry_run=args.dry_run)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result.get("status") == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
