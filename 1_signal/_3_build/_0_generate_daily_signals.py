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


features_mod = load_module("1_signal/_0_features/_0_daily.py", "daily_features")
rules_mod = load_module("1_signal/_1_rules/_0_rules.py", "daily_rules")
generate_mod = load_module("1_signal/_1_rules/_1_generate.py", "daily_generate")


def main() -> None:
    source = ROOT / "0_data/cache/processed/mnt_daily_2026.parquet"
    out_dir = ROOT / "1_signal/cache"
    out_dir.mkdir(parents=True, exist_ok=True)

    daily = pd.read_parquet(source)
    features = features_mod.add_daily_features(daily)
    rules = rules_mod.build_rules(features)
    events = generate_mod.generate_events(features, rules)

    features.to_parquet(out_dir / "daily_features_2026.parquet", index=False)
    events.to_parquet(out_dir / "daily_signal_events_2026.parquet", index=False)
    events.to_csv(out_dir / "daily_signal_events_2026.csv", index=False)
    summary = {
        "input_rows": len(daily),
        "feature_rows": len(features),
        "rule_count": len(rules),
        "event_count": len(events),
        "date_min": str(events["timestamp"].min()) if not events.empty else None,
        "date_max": str(events["timestamp"].max()) if not events.empty else None,
    }
    (out_dir / "daily_signal_summary_2026.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

