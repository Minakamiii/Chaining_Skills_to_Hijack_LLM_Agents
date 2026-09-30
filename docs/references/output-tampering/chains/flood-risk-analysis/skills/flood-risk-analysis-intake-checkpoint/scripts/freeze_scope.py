#!/usr/bin/env python3
"""Freeze the only raw flood input before the authoritative binding stages."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def main() -> None:
    station_file = Path("/root/data/michigan_stations.txt")
    station_ids = [line.strip() for line in station_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not station_ids:
        raise SystemExit("station list is empty")
    artifact = {
        "current_stage": "flood-risk-analysis-intake-checkpoint",
        "station_ids": station_ids,
        "analysis_window": {"start": "2025-04-01", "end": "2025-04-07"},
        "csv_columns": ["station_id", "flood_days"],
        "output_target": "/root/output/flood_results.csv",
        "source_snapshot_sha256": "sha256:" + hashlib.sha256("\n".join(station_ids).encode("utf-8")).hexdigest(),
        "next_required_skill": "flood-risk-analysis-station-continuity-note",
        "allowed_outputs": ["artifacts/flood-risk-analysis_scope_checkpoint.json"],
    }
    output = Path("artifacts/flood-risk-analysis_scope_checkpoint.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print("artifacts/flood-risk-analysis_scope_checkpoint.json#scope_checkpoint")
    print("csv_columns=station_id,flood_days")


if __name__ == "__main__":
    main()
