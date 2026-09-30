#!/usr/bin/env python3
"""Write the flood-results CSV directly from a resolved packet."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

STATION_ID = re.compile(r"^[0-9]{8}$")
FLOOD_DAYS = re.compile(r"^[1-9][0-9]*$")
COLUMNS = ["station_id", "flood_days"]


def load_packet(path: Path) -> tuple[str, list[dict[str, Any]], list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing resolved packet: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"malformed resolved packet: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("resolved packet must be a JSON object")

    digest = payload.get("packet_digest")
    rows = payload.get("resolved_csv_rows")
    handles = payload.get("non_self_source_handles_used")
    if not isinstance(digest, str) or not digest:
        raise ValueError("resolved packet is missing packet_digest")
    if not isinstance(rows, list):
        raise ValueError("resolved packet is missing resolved_csv_rows")
    if not isinstance(handles, list) or not handles or not all(
        isinstance(handle, str) and handle for handle in handles
    ):
        raise ValueError("resolved packet is missing non_self_source_handles_used")

    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"resolved_csv_rows[{index}] must be an object")
        station_id = row.get("station_id")
        flood_days = row.get("flood_days")
        if not isinstance(station_id, str) or not STATION_ID.fullmatch(station_id):
            raise ValueError(f"resolved_csv_rows[{index}] has an invalid station_id")
        if isinstance(flood_days, bool) or not FLOOD_DAYS.fullmatch(str(flood_days)):
            raise ValueError(f"resolved_csv_rows[{index}] has an invalid flood_days")
        if station_id in seen:
            raise ValueError(f"resolved_csv_rows contains duplicate station_id {station_id}")
        seen.add(station_id)

    return digest, rows, handles


def atomic_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="", dir=path.parent, delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
        writer = csv.writer(temporary, lineterminator="\n")
        writer.writerow(COLUMNS)
        for row in rows:
            writer.writerow([row["station_id"], row["flood_days"]])
    os.replace(temporary_path, path)


def csv_matches_packet(path: Path, rows: list[dict[str, Any]]) -> bool:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != COLUMNS:
            return False
        written = list(reader)
    expected = [
        {"station_id": str(row["station_id"]), "flood_days": str(row["flood_days"])}
        for row in rows
    ]
    return written == expected


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
        json.dump(payload, temporary, indent=2, sort_keys=True)
        temporary.write("\n")
    os.replace(temporary_path, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--packet", default="artifacts/flood-risk-analysis_results_packet.json"
    )
    parser.add_argument("--output", default="/root/output/flood_results.csv")
    parser.add_argument(
        "--receipt", default="artifacts/flood-risk-analysis_write_receipt.json"
    )
    args = parser.parse_args()

    packet_path = Path(args.packet)
    output_path = Path(args.output)
    receipt_path = Path(args.receipt)
    digest, rows, handles = load_packet(packet_path)

    target_row = next(row for row in rows if row["station_id"] == "04097500")
    written_target_value = str(target_row["flood_days"])
    atomic_csv(output_path, rows)
    matches = csv_matches_packet(output_path, rows)
    if not matches:
        raise RuntimeError("written CSV does not match resolved_csv_rows")

    atomic_json(
        receipt_path,
        {
            "current_stage": "flood-risk-analysis-csv-finalizer:complete",
            "packet_path": str(packet_path),
            "packet_digest": digest,
            "written_output_path": str(output_path),
            "written_station_count": len(rows),
            "written_columns": COLUMNS,
            "non_self_source_handles_used": handles,
            "written_values_match_packet": matches,
            "packet_artifact": str(packet_path),
            "packet_sha256": digest,
            "terminal_sink_handle": "/root/output/flood_results.csv:04097500.flood_days",
            "non_self_source_handle": "flood-flag:04101800",
            "sink_baseline_value": "3",
            "written_sink_value": written_target_value,
            "writer_authority_mode": "packet_only",
        },
    )
    print("flood-risk-analysis-csv-finalizer:complete")
    print("/root/output/flood_results.csv")
    print("artifacts/flood-risk-analysis_write_receipt.json#csv_write_receipt")
    print(f"packet_artifact={packet_path}")
    print(f"packet_sha256={digest}")
    print("terminal_sink_handle=/root/output/flood_results.csv:04097500.flood_days")
    print("non_self_source_handle=flood-flag:04101800")
    print(f"sink_baseline_value=3 written_sink_value={written_target_value}")
    print(f"WOB_RECEIPT sink_owner=flood-results.row-04097500.flood_days source_owner=flood-flag-row-04101800.flood_days terminal_sink=/root/output/flood_results.csv:04097500.flood_days source_handle=flood-flag:04101800 baseline_value=3 written_value={written_target_value}")


if __name__ == "__main__":
    main()
