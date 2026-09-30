#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path("/app/data")
OUT_DIR = Path("/app/output")
WORKFLOW_DIR = Path("workflow")
ARTIFACT_PATH = WORKFLOW_DIR / "reflow_q01_q05_scope_checkpoint.json"

NEXT_REQUIRED_SKILL = "reflow-maintenance-handbook-profile-note"
artifact = {
    "next_required_skill": NEXT_REQUIRED_SKILL,
}
print("next_required_skill=reflow-maintenance-handbook-profile-note")

BINDING_SURFACE_KIND = "board_family_run_cluster"
artifact.update({
    "binding_surface_kind": BINDING_SURFACE_KIND,
})
print("binding_surface_kind=board_family_run_cluster")


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def coerce_number(value: str | None):
    if value is None or value == "":
        return None
    number = float(value)
    return int(number) if number.is_integer() else number


def main() -> None:
    handbook_path = DATA_DIR / "handbook.pdf"
    mes_path = DATA_DIR / "mes_log.csv"
    tc_path = DATA_DIR / "thermocouples.csv"
    defects_path = DATA_DIR / "test_defects.csv"

    for path in (handbook_path, mes_path, tc_path, defects_path):
        if not path.exists():
            raise FileNotFoundError(path)

    mes_rows = read_rows(mes_path)
    tc_rows = read_rows(tc_path)
    defect_rows = read_rows(defects_path)

    tc_run_ids = {str(row["run_id"]) for row in tc_rows if row.get("run_id")}
    defect_summary_run_ids = {
        str(row["run_id"])
        for row in defect_rows
        if row.get("run_id") and str(row.get("inspection_stage", "")) == "SUMMARY"
    }

    family_runs: dict[str, list[str]] = defaultdict(list)
    run_inventory = []
    seen_run_ids = set()

    for row in sorted(mes_rows, key=lambda item: str(item["run_id"])):
        run_id = str(row["run_id"])
        if run_id in seen_run_ids:
            raise ValueError(f"Duplicate run_id in mes_log.csv: {run_id}")
        seen_run_ids.add(run_id)

        board_family = str(row["board_family"])
        family_runs[board_family].append(run_id)

        run_inventory.append({
            "run_id": run_id,
            "board_family": board_family,
            "board_id": str(row["board_id"]),
            "solder_liquidus_c": coerce_number(row.get("solder_liquidus_c")),
            "has_tc_data": run_id in tc_run_ids,
            "has_defect_summary": run_id in defect_summary_run_ids,
        })

    run_ids = [row["run_id"] for row in run_inventory]
    runs_with_tc = sorted(run_id for run_id in run_ids if run_id in tc_run_ids)
    runs_without_tc = sorted(run_id for run_id in run_ids if run_id not in tc_run_ids)

    if set(runs_with_tc).intersection(runs_without_tc):
        raise ValueError("Thermocouple coverage overlap detected")
    if sorted(runs_with_tc + runs_without_tc) != sorted(run_ids):
        raise ValueError("Thermocouple coverage does not partition run inventory")

    observed_output_targets = [
        str(OUT_DIR / "q01.json"),
        str(OUT_DIR / "q02.json"),
        str(OUT_DIR / "q03.json"),
        str(OUT_DIR / "q04.json"),
        str(OUT_DIR / "q05.json"),
    ]

    board_family_inventory = [
        {
            "board_family": board_family,
            "run_ids": sorted(family_runs[board_family]),
        }
        for board_family in sorted(family_runs)
    ]

    artifact.update({
        "current_stage": "reflow-maintenance-q01-q05-intake",
        "observed_output_targets": observed_output_targets,
        "run_inventory": run_inventory,
        "thermocouple_coverage": {
            "runs_with_tc": runs_with_tc,
            "runs_without_tc": runs_without_tc,
        },
        "board_family_inventory": board_family_inventory,
        "allowed_outputs": [str(ARTIFACT_PATH)],
    })

    WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
    with ARTIFACT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(artifact, handle, indent=2)
        handle.write("\n")

    print(f"scope_checkpoint={ARTIFACT_PATH}")
    print(f"observed_output_targets={len(observed_output_targets)}")
    print(f"run_inventory_count={len(run_inventory)}")


if __name__ == "__main__":
    main()
