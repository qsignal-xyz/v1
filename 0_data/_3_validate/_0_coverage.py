from __future__ import annotations

from pathlib import Path

import pandas as pd


def coverage_row(
    name: str,
    frame: pd.DataFrame,
    start_ms: int,
    end_ms: int,
    freq: str,
    required: list[str],
    source: str = "Bybit",
) -> dict[str, object]:
    expected_index = pd.date_range(
        pd.to_datetime(start_ms, unit="ms", utc=True),
        pd.to_datetime(end_ms, unit="ms", utc=True),
        freq=freq,
    )
    expected = len(expected_index)
    issues: list[str] = []
    if frame.empty:
        issues.append("empty")
        return {
            "dataset": name,
            "source": source,
            "interval": freq,
            "rows": 0,
            "expected": expected,
            "coverage_pct": 0.0,
            "first": "n/a",
            "last": "n/a",
            "issues": "; ".join(issues),
        }

    missing_cols = [col for col in required if col not in frame.columns]
    if missing_cols:
        issues.append(f"missing columns: {missing_cols}")
    duplicate_count = int(frame["timestamp"].duplicated().sum())
    if duplicate_count:
        issues.append(f"duplicate timestamps: {duplicate_count}")
    if not frame["timestamp"].is_monotonic_increasing:
        issues.append("timestamps not sorted")
    observed = pd.DatetimeIndex(frame["timestamp"].drop_duplicates())
    missing_count = len(expected_index.difference(observed))
    extra_count = len(observed.difference(expected_index))
    if missing_count:
        issues.append(f"missing expected timestamps: {missing_count}")
    if extra_count:
        issues.append(f"timestamps outside range: {extra_count}")
    null_required = int(frame[required].isna().sum().sum()) if not missing_cols else -1
    if null_required > 0:
        issues.append(f"null required values: {null_required}")
    numeric_cols = frame.select_dtypes(include="number").columns
    skip_negative_check = ("change", "ret", "pct", "basis")
    negative_bad = [
        col
        for col in numeric_cols
        if ("volume" in col or "interest" in col)
        and not any(token in col for token in skip_negative_check)
        and (frame[col] < 0).any()
    ]
    if negative_bad:
        issues.append(f"negative nonnegative fields: {negative_bad}")
    if {"high", "low"}.issubset(frame.columns) and (frame["high"] < frame["low"]).any():
        issues.append("high below low")
    if {"close", "high", "low"}.issubset(frame.columns):
        outside = (frame["close"] > frame["high"]) | (frame["close"] < frame["low"])
        if outside.any():
            issues.append("close outside high/low")

    rows = int(frame["timestamp"].nunique())
    coverage_pct = round((rows / expected) * 100, 2) if expected else 0.0
    return {
        "dataset": name,
        "source": source,
        "interval": freq,
        "rows": rows,
        "expected": expected,
        "coverage_pct": coverage_pct,
        "first": str(frame["timestamp"].min()),
        "last": str(frame["timestamp"].max()),
        "issues": "; ".join(issues) if issues else "none",
    }


def write_markdown(rows: list[dict[str, object]], output: Path, notes: list[str]) -> None:
    lines = [
        "# Data Coverage",
        "",
        "| Dataset | Source | Interval | Rows | Expected | Coverage | First | Last | Issues |",
        "| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {dataset} | {source} | {interval} | {rows} | {expected} | {coverage_pct}% | "
            "{first} | {last} | {issues} |".format(**row)
        )
    if notes:
        lines.extend(["", "## Notes", ""])
        lines.extend(f"- {note}" for note in notes)
    output.write_text("\n".join(lines) + "\n")
