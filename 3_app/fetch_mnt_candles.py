#!/usr/bin/env python3
"""Fetch 25h of MNT/USDT 1h candles from Bybit and save to mnt_candles.json."""

import json
import urllib.request
import pathlib
import time

URL = "https://api.bybit.com/v5/market/kline?category=spot&symbol=MNTUSDT&interval=60&limit=26"


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "qsignal/1"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.load(r)
    if data.get("retCode") != 0:
        raise RuntimeError(f"Bybit error: {data}")
    rows = data["result"]["list"]
    candles = []
    for row in reversed(rows):
        ts_ms = int(row[0])
        candles.append(
            {
                "t": ts_ms,
                "o": float(row[1]),
                "h": float(row[2]),
                "l": float(row[3]),
                "c": float(row[4]),
                "v": float(row[5]),
            }
        )
    out = {"updated": int(time.time() * 1000), "candles": candles}
    dst = pathlib.Path(__file__).parent / "mnt_candles.json"
    dst.write_text(json.dumps(out))
    print(f"wrote {len(candles)} candles to {dst}")


if __name__ == "__main__":
    main()
