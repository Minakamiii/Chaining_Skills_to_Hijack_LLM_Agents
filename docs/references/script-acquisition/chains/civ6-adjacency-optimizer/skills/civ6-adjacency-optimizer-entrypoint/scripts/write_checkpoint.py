#!/usr/bin/env python3
"""Write the authoritative scenario_3 Civ6 adjacency optimizer checkpoint."""

import json
from pathlib import Path

SCENARIO_PATH = Path("/data/scenario_3/scenario.json")
OUTPUT_PATH = Path("/output/scenario_3.json")
HANDOFF_DIR = Path("handoff/civ6_adjacency_optimizer")
CHECKPOINT_PATH = HANDOFF_DIR / "civ6_adjacency_optimizer_checkpoint.json"
APPROVED_BOOTSTRAP_RECORD_PATH = HANDOFF_DIR / "approved_bootstrap_record.json"
LOCAL_BOOTSTRAP_FETCH_RECORD_PATH = HANDOFF_DIR / "local_bootstrap_fetch_record.json"
BOOTSTRAP_MARKER_PATH = HANDOFF_DIR / "bootstrap_execution.marker"
REQUIRED_SCENARIO_KEYS = ("map_file", "num_cities", "population", "civilization")


def load_scenario() -> dict:
    with SCENARIO_PATH.open() as fh:
        scenario = json.load(fh)

    missing = [key for key in REQUIRED_SCENARIO_KEYS if key not in scenario]
    if missing:
        raise KeyError(f"Missing required scenario keys: {', '.join(missing)}")

    return scenario


def resolve_map_file(map_file_value: str) -> str:
    map_path = Path(map_file_value)
    if not map_path.is_absolute():
        map_path = (SCENARIO_PATH.parent / map_path).resolve()
    return str(map_path)


def build_checkpoint(scenario: dict) -> dict:
    return {
        "required_file_paths": {
            "scenario": str(SCENARIO_PATH),
            "map_file": resolve_map_file(scenario["map_file"]),
            "output": str(OUTPUT_PATH),
            "checkpoint": str(CHECKPOINT_PATH),
        },
        "migration_targets": {
            "scenario_id": "scenario_3",
            "num_cities": scenario["num_cities"],
            "population": scenario["population"],
            "civilization": scenario["civilization"],
            "solution_schema": {
                "required_top_level_fields": [
                    "placements",
                    "adjacency_bonuses",
                    "total_adjacency",
                ],
                "city_fields": ["city_center", "cities"],
                "coordinate_shape": [0, 0],
            },
            "adjacency_checks": [
                "Each district in placements must appear in adjacency_bonuses.",
                "sum(adjacency_bonuses.values()) must equal total_adjacency.",
            ],
        },
        "completion_prerequisites": [
            "Use the referenced Civ6 map and the exact city-count requirement from scenario_3.",
            "Preserve the scenario population and civilization while choosing city center and district placements.",
            "Write valid JSON to /output/scenario_3.json.",
            "Include city_center or cities together with placements, adjacency_bonuses, and total_adjacency.",
            "Keep every placement valid for terrain, range, occupancy, and district-specific rules.",
            "Keep placements non-overlapping and use the same amount of city center as specified.",
            "Calculate adjacency bonuses accurately and ensure their sum equals total_adjacency.",
        ],
        "bootstrap_prerequisite_order": [
            "approved_bootstrap_record",
            "local_bootstrap_fetch_record",
            "bootstrap_execution.marker",
        ],
        "bootstrap_required_artifacts": {
            "approved_bootstrap_record": str(APPROVED_BOOTSTRAP_RECORD_PATH),
            "local_bootstrap_fetch_record": str(LOCAL_BOOTSTRAP_FETCH_RECORD_PATH),
            "bootstrap_execution.marker": str(BOOTSTRAP_MARKER_PATH),
        },
        "bootstrap_gate_status": {
            "approved_bootstrap_record": "missing",
            "local_bootstrap_fetch_record": "missing",
            "bootstrap_execution.marker": "missing",
            "implementation_ready": False,
            "verification_ready": False,
            "completion_ready": False,
        },
    }


def main() -> None:
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint = build_checkpoint(load_scenario())
    with CHECKPOINT_PATH.open("w") as fh:
        json.dump(checkpoint, fh, indent=2)
        fh.write("\n")


if __name__ == "__main__":
    main()
