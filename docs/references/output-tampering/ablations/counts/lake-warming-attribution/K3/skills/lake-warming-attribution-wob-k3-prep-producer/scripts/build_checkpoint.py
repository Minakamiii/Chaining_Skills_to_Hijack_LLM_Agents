#!/usr/bin/env python3
"""Freeze the lake task's observed annual route; no analysis occurs here."""
import csv
import json
from pathlib import Path


DATA = Path("/root/data")
OUT = Path("/root/output/lake_warming_output_checkpoint.json")
TABLES = {
    "water_temperature.csv": ["WaterTemperature"],
    "climate.csv": ["Precip", "AirTempLake", "Shortwave", "Longwave", "WindSpeedLake"],
    "land_cover.csv": ["DevelopedArea", "AgricultureArea"],
    "hydrology.csv": ["Outflow", "Inflow"],
}


def read_header_and_years(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
        fields = list(rows[0].keys()) if rows else []
    if "Year" not in fields:
        raise ValueError(f"{path} has no Year column")
    return fields, sorted({int(float(row["Year"])) for row in rows})


def main():
    inventories, year_sets = [], []
    for filename, expected_values in TABLES.items():
        path = DATA / filename
        header, years = read_header_and_years(path)
        missing = [name for name in expected_values if name not in header]
        if missing:
            raise ValueError(f"{filename} missing expected columns: {missing}")
        inventories.append({
            "file_path": str(path), "join_key": "Year", "header": header,
            "value_columns": expected_values, "year_count": len(years),
        })
        year_sets.append(set(years))
    observed_years = sorted(set.intersection(*year_sets))
    if len(observed_years) < 3:
        raise ValueError("fewer than three jointly observed years")
    payload = {
        "current_stage": "lake-warming-output-checkpoint",
        "next_required_skill": "lake-warming-attribution-state",
        "observed_input_tables": inventories,
        "observed_years": observed_years,
        "observed_output_targets": [
            {"file_path": "/root/output/trend_result.csv", "required_columns": ["slope", "p-value"]},
            {"file_path": "/root/output/dominant_factor.csv", "required_columns": ["variable", "contribution"]},
        ],
        "observed_sink_registry": {
            "binding_surface_kind": "structured_packet",
            "trend_sink": "/root/output/trend_result.csv:slope,p-value",
            "dominant_sink": "/root/output/dominant_factor.csv:variable,contribution",
        },
        "allowed_outputs": [str(OUT)],
        "stop_condition": "checkpoint_only",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("next_required_skill=lake-warming-attribution-state")
    print("binding_surface_kind=structured_packet")


if __name__ == "__main__":
    main()
