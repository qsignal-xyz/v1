from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def load_module(rel_path: str, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, ROOT / rel_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {rel_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


forward_mod = load_module("2_backtest/_0_engine/_0_forward.py", "forward")
runner_mod = load_module("2_backtest/_0_engine/_1_runner.py", "runner")
metrics_mod = load_module("2_backtest/_1_metrics/_0_metrics.py", "metrics")
report_mod = load_module("2_backtest/_2_report/_0_markdown.py", "report")
health_mod = load_module("2_backtest/_3_walkforward/_0_health.py", "walkforward_health")
select_mod = load_module("2_backtest/_3_walkforward/_1_select.py", "walkforward_select")
replay_mod = load_module("2_backtest/_3_walkforward/_2_replay.py", "walkforward_replay")
wf_report_mod = load_module("2_backtest/_3_walkforward/_3_report.py", "walkforward_report")


def main() -> None:
    daily = pd.read_parquet(ROOT / "0_data/cache/processed/mnt_daily_2026.parquet")
    events_path = ROOT / "1_signal/cache/daily_signal_events_2026.parquet"
    if not events_path.exists():
        raise RuntimeError("Run 1_signal/_3_build/_0_generate_daily_signals.py first")
    events = pd.read_parquet(events_path)
    ensemble = runner_mod.ensemble_events(events)
    all_events = pd.concat([events, ensemble], ignore_index=True)

    paths = forward_mod.add_forward_paths(daily)
    event_returns = runner_mod.event_returns(all_events, paths)
    summary = metrics_mod.summarize(event_returns)
    ranked = metrics_mod.rank_signals(summary)

    out_dir = ROOT / "2_backtest/cache"
    out_dir.mkdir(parents=True, exist_ok=True)
    all_events.to_parquet(out_dir / "daily_signal_events_with_ensemble_2026.parquet", index=False)
    all_events.to_csv(out_dir / "daily_signal_events_with_ensemble_2026.csv", index=False)
    event_returns.to_parquet(out_dir / "daily_event_returns_2026.parquet", index=False)
    event_returns.to_csv(out_dir / "daily_event_returns_2026.csv", index=False)
    summary.to_csv(out_dir / "signal_summary_2026.csv", index=False)
    ranked.to_csv(out_dir / "signal_rankings_2026.csv", index=False)
    report_mod.write_report(ROOT / "reports/signal_backtest.md", all_events, event_returns, summary, ranked)
    report_mod.write_report(ROOT / "reports/signal_backtest_2026.md", all_events, event_returns, summary, ranked)
    health, recs = select_mod.build_walkforward(events, event_returns, health_mod, daily["timestamp"])
    replayed_recs = replay_mod.replay_recommendations(recs, paths)
    replay_summary = replay_mod.summarize_recommendations(replayed_recs)
    active_outcomes = replay_mod.active_signal_outcomes(health, event_returns)
    active_outcome_summary = replay_mod.summarize_active_signals(active_outcomes)
    health.to_csv(out_dir / "walkforward_signal_health.csv", index=False)
    recs.to_csv(out_dir / "walkforward_daily_recommendations.csv", index=False)
    replayed_recs.to_csv(out_dir / "walkforward_recommendation_replay.csv", index=False)
    replay_summary.to_csv(out_dir / "walkforward_replay_summary.csv", index=False)
    active_outcomes.to_csv(out_dir / "walkforward_active_signal_outcomes.csv", index=False)
    active_outcome_summary.to_csv(out_dir / "walkforward_active_signal_summary.csv", index=False)
    health.to_parquet(out_dir / "walkforward_signal_health.parquet", index=False)
    replayed_recs.to_parquet(out_dir / "walkforward_recommendation_replay.parquet", index=False)
    wf_report_mod.write_walkforward_report(
        ROOT / "reports/walkforward_signal_health.md",
        health,
        recs,
        replay_summary,
        active_outcome_summary,
    )

    payload = {
        "input_events": len(events),
        "ensemble_events": len(ensemble),
        "evaluated_rows": len(event_returns),
        "ranked_rows": len(ranked),
        "walkforward_active_recommendation_days": int((recs["direction"] != 0).sum()),
        "top": ranked.head(5).to_dict(orient="records"),
    }
    (out_dir / "daily_backtest_summary_2026.json").write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
