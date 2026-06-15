from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "0_data/cache/onchain"
RAW_LOGS = CACHE / "raw_logs"

RANGE_NAME = re.compile(r"^(.+)_(\d+)_(\d+)\.json$")
HEAD_NAME = re.compile(r"^(.+)_head_(\d+)\.json$")


def stale_raw_log(path: Path, start_block: int, latest_block: int, chunk_blocks: int) -> bool:
    match = RANGE_NAME.match(path.name)
    if match:
        left = int(match.group(2))
        right = int(match.group(3))
        return right < start_block or left > latest_block

    match = HEAD_NAME.match(path.name)
    if match:
        head_start = latest_block - (latest_block % chunk_blocks)
        return int(match.group(2)) != head_start

    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, default=CACHE / "summary_14d.json")
    parser.add_argument("--chunk-blocks", type=int, default=10_000)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.summary.exists():
        raise FileNotFoundError(f"missing onchain summary: {args.summary}")

    summary = json.loads(args.summary.read_text())
    start_block = int(summary["start_block"])
    latest_block = int(summary["latest_block"])

    stale = []
    for path in RAW_LOGS.glob("*.json"):
        if stale_raw_log(path, start_block, latest_block, args.chunk_blocks):
            stale.append(path)

    bytes_total = sum(path.stat().st_size for path in stale)
    if not args.dry_run:
        for path in stale:
            path.unlink()

    print(
        json.dumps(
            {
                "dry_run": args.dry_run,
                "start_block": start_block,
                "latest_block": latest_block,
                "stale_files": len(stale),
                "stale_bytes": bytes_total,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
