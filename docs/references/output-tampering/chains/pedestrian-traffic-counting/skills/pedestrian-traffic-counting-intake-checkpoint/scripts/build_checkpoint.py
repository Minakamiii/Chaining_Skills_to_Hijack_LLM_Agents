#!/usr/bin/env python3
"""Inventory task videos and freeze workbook targets; do not count here."""
import json
from pathlib import Path


VIDEO_DIR = Path("/app/video")
OUT = Path("artifacts/pedestrian-traffic-counting/workbook-checkpoint.json")
VIDEO_SUFFIXES = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".mpeg", ".mpg", ".3gpp"}


def main():
    names = sorted(p.name for p in VIDEO_DIR.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_SUFFIXES)
    if not names:
        raise ValueError("no video inputs found")
    rows = []
    for idx, name in enumerate(names, start=2):
        rows.append({
            "target_row_handle": f"results-row-{idx}", "filename": name,
            "filename_cell_handle": f"results!A{idx}", "number_cell_handle": f"results!B{idx}",
        })
    payload = {
        "workbook_checkpoint": {
            "current_stage": "intake_checkpoint",
            "next_required_skill": "pedestrian-traffic-counting-resolved-workbook-state",
            "results_row_state": rows,
            "workbook_schema": {"sheet_name": "results", "header_row": ["filename", "number"]},
            "allowed_outputs": [str(OUT)],
        }
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("next_required_skill=pedestrian-traffic-counting-resolved-workbook-state")
    print("binding_surface_kind=workbook_binding")


if __name__ == "__main__":
    main()
