"""Write metric result JSON under ``eval/results/<run-set>/``."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from utils.run_set import RunSet


def write_metric(run_set: RunSet, name: str, payload: dict[str, Any]) -> Path:
    """Persist one metric result JSON with run-set metadata and a timestamp envelope."""
    run_set.results_dir.mkdir(parents=True, exist_ok=True)
    envelope = {
        "metric": name,
        "run_set": run_set.name,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    path = run_set.results_dir / f"{name}.json"
    path.write_text(json.dumps(envelope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
