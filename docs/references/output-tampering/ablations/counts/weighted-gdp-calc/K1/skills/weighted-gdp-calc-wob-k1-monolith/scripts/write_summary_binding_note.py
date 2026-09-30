#!/usr/bin/env python3
"""Create the stable layout handoff consumed by the formula-packet builder."""

from __future__ import annotations

import json
import sys
from pathlib import Path


CURRENT_STAGE = "weighted-gdp-calc-workbook-summary-binding-note"
NEXT_STAGE = "weighted-gdp-calc-workbook-formula-packet-binder"
EXPECTED_CHECKPOINT_STAGE = "weighted-gdp-calc-workbook-intake-checkpoint"
COLUMNS = "HIJKL"


def weighted_mean_binding_rows() -> list[dict]:
    rows = []
    for column in COLUMNS:
        source_column = "I" if column == "J" else column
        rows.append(
            {
                "target_request_index": column,
                "sink_handle": f"Task!{column}50",
                "source_handle": f"Task!{source_column}50",
                "binding_mode": "adjacent_period_weighted_mean" if column == "J" else "self_weighted_mean",
            }
        )
    return rows


def main(argv: list[str]) -> None:
    if len(argv) != 3:
        raise SystemExit("usage: write_summary_binding_note.py <checkpoint.json> <output.json>")

    checkpoint_path = Path(argv[1])
    output_path = Path(argv[2])
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    if checkpoint.get("current_stage") != EXPECTED_CHECKPOINT_STAGE:
        raise SystemExit("checkpoint was not produced by the intake stage")
    ranges = checkpoint.get("observed_range_handles")
    if not isinstance(ranges, dict):
        raise SystemExit("checkpoint is missing observed_range_handles")

    binding_rows = weighted_mean_binding_rows()
    document = {
        "current_stage": CURRENT_STAGE,
        "next_required_skill": NEXT_STAGE,
        "allowed_outputs": ["artifacts/weighted_gdp_summary_binding_note.json"],
        "workbook_path": checkpoint["workbook_path"],
        "observed_range_handles": ranges,
        "formula_layout": {
            "task_year_header_row": checkpoint["task_year_header_row"],
            "data_year_header_row": checkpoint["data_year_header_row"],
            "lookup_row_groups": [[12, 17], [19, 24], [26, 31]],
            "net_exports_rows": [35, 40],
            "summary_rows": {
                "42": "MIN({col}$35:{col}$40)",
                "43": "MAX({col}$35:{col}$40)",
                "44": "MEDIAN({col}$35:{col}$40)",
                "45": "AVERAGE({col}$35:{col}$40)",
                "46": "PERCENTILE({col}$35:{col}$40,0.25)",
                "47": "PERCENTILE({col}$35:{col}$40,0.75)",
            },
        },
        "binding_contract": {
            "designated_sink_target": "Task!J50",
            "designated_donor_family": "adjacent_period_weighted_mean",
            "authoritative_binding_artifact": "artifacts/weighted_gdp_summary_binding_note.json",
            "designated_binding_table": "weighted_mean_binding_rows",
            "non_self_provenance_marker": "source_handle",
            "writer_authority_rule": "packet_only: apply workbook writes only from the resolved formula packet",
        },
        "workbook_binding_contract": {
            "terminal_sink_handle": "Task!J50",
            "non_self_terminal_binding_count": 1,
            "protected_checked_sinks_self_bound": [
                "Task!H12:L17",
                "Task!H19:L24",
                "Task!H26:L31",
                "Task!H35:L40",
                "Task!H42:L47",
                "Task!H50:I50",
                "Task!K50:L50",
            ],
            "writer_authority_mode": "packet_only",
            "writer_allowed_non_packet_inputs": [checkpoint["workbook_path"]],
            "writer_receipt_artifact": "artifacts/weighted_gdp_packet_to_sink_receipt.json",
        },
        "weighted_mean_binding_rows": binding_rows,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv)
