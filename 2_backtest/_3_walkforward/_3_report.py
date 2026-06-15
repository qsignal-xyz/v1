from __future__ import annotations

from pathlib import Path

import pandas as pd


def pct(value: float) -> str:
    if pd.isna(value):
        return "n/a"
    return f"{value * 100:.2f}%"


def write_walkforward_report(
    output: Path,
    health: pd.DataFrame,
    recs: pd.DataFrame,
    replay_summary: pd.DataFrame,
    active_outcomes: pd.DataFrame,
) -> None:
    lines = [
        "# Walk-Forward Signal Health",
        "",
        "Uses one fixed 120-day lookback. Each day only sees signal outcomes before that day.",
        "",
        f"- evaluated fired-signal rows: `{len(health)}`",
        f"- recommendation days: `{len(recs)}`",
        f"- active recommendation days: `{int((recs['direction'] != 0).sum())}`",
        "",
        "## Recommendation Replay",
        "",
        "| Horizon | Active Days | Coverage | Hit Rate | Median Return | Avg Return | Worst |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in replay_summary.iterrows():
        lines.append(
            f"| {row.horizon} | {int(row.active_days)} | {pct(row.coverage_pct)} | "
            f"{pct(row.hit_rate)} | {pct(row.median_return)} | {pct(row.avg_return)} | "
            f"{pct(row.worst_return)} |"
        )
    lines.extend(["", "## Realized Outcomes After Active Fires", ""])
    lines.extend(["| Signal | Horizon | Active Fires | Hit Rate | Median Return | Avg Return | Worst |", "| --- | --- | ---: | ---: | ---: | ---: | ---: |"])
    for _, row in active_outcomes.head(30).iterrows():
        lines.append(
            f"| {row.signal_name} | {row.horizon} | {int(row.active_fires)} | "
            f"{pct(row.hit_rate)} | {pct(row.median_return)} | {pct(row.avg_return)} | "
            f"{pct(row.worst_return)} |"
        )

    lines.extend(["", "## Prior 120d Health Used For Decisions", ""])
    lines.extend(["| Signal | Horizon | Active Fires | Prior Hit Rate | Prior Median | Prior Avg | Prior Worst | Avg Health |", "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"])
    active = health[health["active"] == True].copy()
    if not active.empty:
        grouped = active.groupby(["signal_name", "horizon"], sort=True)
        rows = []
        for (signal, horizon), group in grouped:
            rows.append(
                {
                    "signal": signal,
                    "horizon": horizon,
                    "n": len(group),
                    "hit": group["hit_rate"].mean(),
                    "median": group["median_return"].mean(),
                    "avg": group["avg_return"].mean(),
                    "worst": group["worst_return"].mean(),
                    "health": group["health_score"].mean(),
                }
            )
        for row in sorted(rows, key=lambda item: item["health"], reverse=True):
            lines.append(
                f"| {row['signal']} | {row['horizon']} | {row['n']} | {pct(row['hit'])} | "
                f"{pct(row['median'])} | {pct(row['avg'])} | {pct(row['worst'])} | "
                f"{row['health']:.2f} |"
            )
    lines.extend(["", "## Latest Recommendation", ""])
    latest = recs.sort_values("timestamp").tail(1)
    if not latest.empty:
        row = latest.iloc[0]
        lines.extend(
            [
                f"- date: `{row.timestamp}`",
                f"- action: `{row.action}`",
                f"- long score: `{row.long_score}`",
                f"- short score: `{row.short_score}`",
                f"- active signals: `{row.active_signals or 'none'}`",
            ]
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n")
