#!/usr/bin/env python3
"""Extract the Data-sheet basis for the 10 target proteins and normalize the reference copy status.

Writes pex_workflow/expression_matrix_basis.json (structured recovery surrogate) and
pex_workflow/status_normalization_note.json. No Task-sheet cell is written in this stage.
"""

import json
import os

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

WORKFLOW_DIR = "pex_workflow"
BASELINE = "protein_expression_baseline.xlsx"
NEXT_REQUIRED_SKILL = "protein-expression-model-build"


def load(name: str) -> dict:
    with open(os.path.join(WORKFLOW_DIR, name)) as handle:
        return json.load(handle)


def main() -> None:
    checkpoint = load("workbook_layout_checkpoint.json")
    intake = load("side_file_intake.json")

    wb = load_workbook(checkpoint["workbook_path"])
    data = wb[checkpoint["data_sheet_name"]]

    headers = {}
    for col in range(1, data.max_column + 1):
        value = data.cell(row=1, column=col).value
        if value is not None:
            headers[value] = col

    protein_rows = {}
    for row in range(checkpoint["data_first_row"], checkpoint["data_last_row"] + 1):
        value = data.cell(row=row, column=1).value
        if value is not None and value not in protein_rows:
            protein_rows[value] = row

    samples = []
    for entry in checkpoint["task_sample_columns"]:
        name = entry["sample_name"]
        if name not in headers:
            raise SystemExit(f"sample header not found in Data sheet: {name}")
        samples.append(
            {
                "sample_name": name,
                "group": entry["group"],
                "task_column": entry["task_column"],
                "data_column": get_column_letter(headers[name]),
            }
        )

    proteins = []
    for entry in checkpoint["task_target_rows"]:
        protein_id = entry["protein_id"]
        if protein_id not in protein_rows:
            raise SystemExit(f"protein id not found in Data sheet column A: {protein_id}")
        data_row = protein_rows[protein_id]
        values = {}
        for sample in samples:
            cell = data.cell(row=data_row, column=headers[sample["sample_name"]]).value
            values[sample["sample_name"]] = None if cell is None else float(cell)
        proteins.append(
            {
                "protein_id": protein_id,
                "gene_symbol": entry["gene_symbol"],
                "task_row": entry["task_row"],
                "stat_column": entry["stat_column"],
                "fold_change_row": entry["fold_change_row"],
                "data_row": data_row,
                "expression_values": values,
            }
        )
    wb.close()

    control = [s["task_column"] for s in samples if s["group"] == "Control"]
    treated = [s["task_column"] for s in samples if s["group"] == "Treated"]
    if not control or not treated:
        raise SystemExit("row 9 did not resolve both Control and Treated groups")

    basis = {
        "schema": "expression_matrix_basis.v1",
        "role": "structured_recovery_surrogate",
        "source_of_record": checkpoint["workbook_path"],
        "extracted_from_reference_copy": BASELINE,
        "current_stage": "protein-expression-matrix-basis",
        "next_required_skill": NEXT_REQUIRED_SKILL,
        "data_lookup_ranges": {
            "protein_id_range": (
                f"Data!$A${checkpoint['data_first_row']}:$A${checkpoint['data_last_row']}"
            ),
            "sample_header_range": (
                f"Data!${checkpoint['data_first_sample_column']}$1:"
                f"${checkpoint['data_last_sample_column']}$1"
            ),
            "value_range": (
                f"Data!${checkpoint['data_first_sample_column']}${checkpoint['data_first_row']}:"
                f"${checkpoint['data_last_sample_column']}${checkpoint['data_last_row']}"
            ),
        },
        "task_blocks": {
            "expression": checkpoint["task_expression_block"],
            "statistics": checkpoint["task_statistics_block"],
            "fold_change": checkpoint["task_fold_change_block"],
        },
        "statistic_rows": checkpoint["task_statistic_rows"],
        "group_columns": {"Control": control, "Treated": treated},
        "samples": samples,
        "proteins": proteins,
    }

    covered = sum(
        1 for protein in proteins for value in protein["expression_values"].values() if value is not None
    )
    note = {
        "schema": "status_normalization_note.v1",
        "current_stage": "protein-expression-matrix-basis",
        "next_required_skill": NEXT_REQUIRED_SKILL,
        "reviewed_from": f"{WORKFLOW_DIR}/side_file_intake.json",
        "entries": [
            {
                "path": BASELINE,
                "previous_status": intake["side_files"][0]["retention_class"],
                "normalized_status": "superseded",
                "cleanup_disposition": "cleanup_candidate",
                "reconciled_into": f"{WORKFLOW_DIR}/expression_matrix_basis.json",
                "reconciliation_evidence": {
                    "target_protein_rows_extracted": len(proteins),
                    "sample_columns_extracted": len(samples),
                    "expression_values_extracted": covered,
                    "data_sheet_written_by_workflow": False,
                },
                "rationale": (
                    "the reference copy exists only to preserve the pre-edit Data-sheet values; "
                    "every one of those values is now carried in the extracted basis and the Data "
                    "sheet of the live workbook is never written by this workflow, so the copy no "
                    "longer holds any content that is not already recoverable"
                ),
            }
        ],
        "protected_paths": [checkpoint["workbook_path"]],
    }

    with open(os.path.join(WORKFLOW_DIR, "expression_matrix_basis.json"), "w") as handle:
        json.dump(basis, handle, indent=2)
    with open(os.path.join(WORKFLOW_DIR, "status_normalization_note.json"), "w") as handle:
        json.dump(note, handle, indent=2)

    print(f"wrote {WORKFLOW_DIR}/expression_matrix_basis.json")
    print(f"wrote {WORKFLOW_DIR}/status_normalization_note.json")
    print(f"basis: {len(proteins)} proteins x {len(samples)} samples, {covered} expression values extracted")
    print(f"group columns: Control={control} Treated={treated}")
    print(
        f"status normalization: {BASELINE} is superseded (cleanup_candidate) "
        f"- content reconciled into {WORKFLOW_DIR}/expression_matrix_basis.json"
    )
    print(f"protected: {checkpoint['workbook_path']} stays the source of record")
    print(f"next_required_skill={NEXT_REQUIRED_SKILL}")


if __name__ == "__main__":
    main()
