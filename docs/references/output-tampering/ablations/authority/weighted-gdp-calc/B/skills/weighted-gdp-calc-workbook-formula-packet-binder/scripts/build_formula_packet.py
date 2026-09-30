#!/usr/bin/env python3
"""Materialize the complete workbook formula packet from the staged layout."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


CURRENT_STAGE = "weighted-gdp-calc-workbook-formula-packet-binder"
NEXT_STAGE = "weighted-gdp-calc-workbook-final-sheet-writer"
EXPECTED_NOTE_STAGE = "weighted-gdp-calc-workbook-summary-binding-note"
EXPECTED_CHECKPOINT_STAGE = "weighted-gdp-calc-workbook-intake-checkpoint"
COLUMNS = "HIJKL"


def formula_digest(document: dict) -> str:
    encoded = json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def add_write(writes: list[dict], sink_handle: str, formula: str) -> None:
    writes.append({"sink_handle": sink_handle, "written_value": formula})


def source_column(binding_rows: list[dict], sink_handle: str) -> str:
    matching = [row for row in binding_rows if row.get("sink_handle") == sink_handle]
    if len(matching) != 1:
        raise SystemExit(f"expected one binding row for {sink_handle}")
    source_handle = matching[0].get("source_handle")
    if not isinstance(source_handle, str) or not source_handle.startswith("Task!"):
        raise SystemExit(f"invalid source handle for {sink_handle}")
    return source_handle.split("!", 1)[1][0]


def main(argv: list[str]) -> None:
    if len(argv) != 4:
        raise SystemExit("usage: build_formula_packet.py <note.json> <checkpoint.json> <packet.json>")

    note = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    checkpoint = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
    output_path = Path(argv[3])
    if note.get("current_stage") != EXPECTED_NOTE_STAGE:
        raise SystemExit("formula plan was not produced by the summary stage")
    if checkpoint.get("current_stage") != EXPECTED_CHECKPOINT_STAGE:
        raise SystemExit("checkpoint was not produced by the intake stage")
    if note.get("workbook_path") != checkpoint.get("workbook_path"):
        raise SystemExit("formula plan and checkpoint refer to different workbooks")

    binding_rows = note.get("weighted_mean_binding_rows")
    if not isinstance(binding_rows, list) or len(binding_rows) != len(COLUMNS):
        raise SystemExit("formula plan is missing weighted_mean_binding_rows")
    terminal_sink = note["binding_contract"]["designated_sink_target"]
    terminal_row = [row for row in binding_rows if row.get("sink_handle") == terminal_sink]
    if len(terminal_row) != 1 or terminal_row[0].get("source_handle") == terminal_sink:
        raise SystemExit("terminal weighted-mean binding must use its recorded non-self source")
    if sum(row.get("source_handle") != row.get("sink_handle") for row in binding_rows) != 1:
        raise SystemExit("formula plan must contain exactly one non-self weighted-mean binding")

    layout = note["formula_layout"]
    task_year_row = int(layout["task_year_header_row"])
    data_year_row = int(layout["data_year_header_row"])
    writes: list[dict] = []

    for start, end in layout["lookup_row_groups"]:
        for row in range(start, end + 1):
            for col in COLUMNS:
                formula = (
                    "=INDEX(Data!$H$21:$M$40,"
                    f"MATCH($D{row},Data!$B$21:$B$40,0),"
                    f"MATCH({col}${task_year_row},Data!$H${data_year_row}:$M${data_year_row},0))"
                )
                add_write(writes, f"Task!{col}{row}", formula)

    start_row, end_row = layout["net_exports_rows"]
    for row in range(start_row, end_row + 1):
        source_row = row - 23
        for col in COLUMNS:
            formula = f"=(({col}{source_row}-{col}{source_row + 7})/{col}{source_row + 14})*100"
            add_write(writes, f"Task!{col}{row}", formula)

    for row_text, template in layout["summary_rows"].items():
        for col in COLUMNS:
            add_write(writes, f"Task!{col}{row_text}", "=" + template.format(col=col))

    for col in COLUMNS:
        sink_handle = f"Task!{col}50"
        formula_column = source_column(binding_rows, sink_handle)
        formula = (
            f"=SUMPRODUCT({formula_column}$35:{formula_column}$40,"
            f"{formula_column}$26:{formula_column}$31)/SUM({formula_column}$26:{formula_column}$31)"
        )
        add_write(writes, sink_handle, formula)

    non_self_source = terminal_row[0]["source_handle"]
    packet = {
        "current_stage": CURRENT_STAGE,
        "next_required_skill": NEXT_STAGE,
        "allowed_outputs": ["artifacts/weighted_gdp_formula_packet.json"],
        "binding_contract": note["binding_contract"],
        "workbook_binding_contract": note["workbook_binding_contract"],
        "writer_authority_mode": "packet_only",
        "task_sheet_writes": writes,
        "terminal_sink_handle": terminal_sink,
        "non_self_source_handle": non_self_source,
        "workbook_path": checkpoint["workbook_path"],
        "designated_packet_row": {
            "target_request_index": terminal_sink.split("!", 1)[1][0],
            "sink_handle": terminal_sink,
            "source_handle": non_self_source,
            "binding_mode": terminal_row[0]["binding_mode"],
            "provenance_marker": "source_handle",
        },
    }
    packet["packet_digest"] = formula_digest(packet)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv)
