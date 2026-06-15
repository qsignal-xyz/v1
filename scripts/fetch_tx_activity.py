import json
import time
import urllib.request
from pathlib import Path

RPC = "https://rpc.mantle.xyz"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "4_runtime/app/tx_activity.json"
BLOCK_TIME = 2  # ~2s per block on Mantle
SAMPLES_PER_HOUR = 12  # sample every 5 min


def rpc(method, params=None):
    body = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []}
    ).encode()
    req = urllib.request.Request(RPC, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())["result"]


def tx_count(block_hex):
    blk = rpc("eth_getBlockByNumber", [block_hex, False])
    if not blk:
        return 0
    return len(blk.get("transactions", []))


latest = int(rpc("eth_blockNumber"), 16)
blocks_per_hour = 3600 // BLOCK_TIME
step = blocks_per_hour // SAMPLES_PER_HOUR

hours = []
errors = []
for h in range(24):
    offset_blocks = (23 - h) * blocks_per_hour
    start_block = latest - offset_blocks
    total_txs = 0
    samples = 0
    for s in range(SAMPLES_PER_HOUR):
        bn = start_block + s * step
        if bn > latest:
            break
        try:
            count = tx_count(hex(bn))
            total_txs += count
            samples += 1
        except Exception as exc:
            errors.append({"hour": h, "block": bn, "error": str(exc)})
        time.sleep(0.05)
    estimated_hourly = int(total_txs * (blocks_per_hour / max(samples * step, 1))) if samples else 0
    hours.append(
        {
            "hour": h,
            "tx_count_sampled": total_txs,
            "tx_count_estimated": estimated_hourly,
            "samples": samples,
        }
    )
    print(f"h{h:02d}: {total_txs} txs sampled ({samples} blocks), ~{estimated_hourly} estimated/hr")

result = {
    "latest_block": latest,
    "timestamp": int(time.time()),
    "block_time_assumed": BLOCK_TIME,
    "hours": hours,
    "errors": errors,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2))
print(f"Saved to {OUT}")
