from __future__ import annotations

from pathlib import Path

import pandas as pd


def _fmt_pct(value: float) -> str:
    if pd.isna(value):
        return "n/a"
    return f"{value * 100:.2f}%"


def write_report(
    output: Path,
    events: pd.DataFrame,
    event_returns: pd.DataFrame,
    summary: pd.DataFrame,
    ranked: pd.DataFrame,
) -> None:
    date_min = str(events["timestamp"].min()) if not events.empty else "n/a"
    date_max = str(events["timestamp"].max()) if not events.empty else "n/a"
    lines = [
        "# Signal Backtest",
        "",
        "This is a research ranking, not a deployable trading claim. Rules are simple and explainable; "
        "later work should add out-of-sample validation before using weights live.",
        "",
        f"- date range: `{date_min}` -> `{date_max}`",
        f"- signal events: `{len(events)}`",
        f"- evaluated event-horizon rows: `{len(event_returns)}`",
        f"- unique signals: `{events['signal_name'].nunique() if not events.empty else 0}`",
        "",
        "## Top Ranked Signal-Horizons",
        "",
        "| Rank | Signal | Horizon | N | Hit Rate | Median Return | Avg Return | Worst | PF | Score |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for idx, row in ranked.head(20).iterrows():
        pf = row["profit_factor"]
        pf_text = "inf" if pf == float("inf") else f"{pf:.2f}"
        lines.append(
            f"| {idx + 1} | {row.signal_name} | {row.horizon} | {row.sample_count} | "
            f"{_fmt_pct(row.hit_rate)} | {_fmt_pct(row.median_directional_return)} | "
            f"{_fmt_pct(row.avg_directional_return)} | {_fmt_pct(row.worst_directional_return)} | "
            f"{pf_text} | {row.score:.2f} |"
        )

    lines.extend(["", "## Per-Signal Best Horizon", ""])
    best = ranked.sort_values("score", ascending=False).drop_duplicates("signal_name")
    lines.extend(["| Signal | Best Horizon | N | Hit Rate | Median Return | Score |", "| --- | --- | ---: | ---: | ---: | ---: |"])
    for _, row in best.head(20).iterrows():
        lines.append(
            f"| {row.signal_name} | {row.horizon} | {row.sample_count} | "
            f"{_fmt_pct(row.hit_rate)} | {_fmt_pct(row.median_directional_return)} | {row.score:.2f} |"
        )

    lines.extend(["", "## Caveats", ""])
    lines.extend(
        [
            "- Ranking is in-sample. Do not treat top scores as production alpha yet.",
            "- Next step is train/test or rolling validation across this full-history dataset.",
            "- Mantle-native metrics are daily context; no fake hourly interpolation is used.",
            "- CoinGecko market-cap context is partial and should not drive core signals.",
        ]
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n")
