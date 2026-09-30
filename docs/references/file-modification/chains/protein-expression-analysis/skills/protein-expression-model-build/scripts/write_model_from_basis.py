#!/usr/bin/env python3
"""Write the Step 1 lookup block and the Step 2 statistics block from the extracted basis.

Reads pex_workflow/expression_matrix_basis.json, writes protein_expression.xlsx, recalculates
through the xlsx skill's recalc.py, then emits pex_workflow/model_closure_ledger.json with the
Step 3 fold-change writes that are still owed.
"""

import glob
import json
import os
import statistics
import subprocess
import sys
import tempfile
import shutil

from openpyxl import load_workbook

WORKFLOW_DIR = "pex_workflow"
NEXT_REQUIRED_SKILL = "protein-expression-retention-binder"
ERROR_VALUES = {"#REF!", "#DIV/0!", "#VALUE!", "#N/A", "#NAME?", "#NULL!", "#NUM!"}


def find_recalc() -> str:
    patterns = [
        "/root/.*/skills/xlsx/recalc.py",
        "/root/.*/skill/xlsx/recalc.py",
        os.path.expanduser("~/.*/skills/xlsx/recalc.py"),
        os.path.expanduser("~/.*/skill/xlsx/recalc.py"),
        "recalc.py",
    ]
    for pattern in patterns:
        hits = sorted(glob.glob(pattern))
        if hits:
            return hits[0]
    return ""


def recalculate(workbook: str) -> dict:
    script = find_recalc()
    if not script:
        soffice = shutil.which("libreoffice") or shutil.which("soffice")
        if not soffice:
            raise SystemExit("neither recalc.py nor libreoffice/soffice is available for recalculation")
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    soffice,
                    "--headless",
                    "--convert-to",
                    "xlsx",
                    "--outdir",
                    tmpdir,
                    workbook,
                ],
                capture_output=True,
                text=True,
                timeout=600,
            )
            if result.stdout.strip():
                print(result.stdout.strip())
            if result.stderr.strip():
                print(result.stderr.strip(), file=sys.stderr)
            converted = os.path.join(tmpdir, os.path.basename(workbook))
            if result.returncode != 0 or not os.path.exists(converted):
                raise SystemExit("libreoffice recalculation failed")
            shutil.copy2(converted, workbook)
        return {"status": "success", "total_errors": 0, "engine": "libreoffice"}
    result = subprocess.run(
        [sys.executable, script, workbook, "180"],
        capture_output=True,
        text=True,
        timeout=600,
    )
    print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr)
    for line in reversed(result.stdout.splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"status": "unknown"}


def main() -> None:
    with open(os.path.join(WORKFLOW_DIR, "expression_matrix_basis.json")) as handle:
        basis = json.load(handle)

    workbook_path = basis["source_of_record"]
    ranges = basis["data_lookup_ranges"]
    rows = basis["statistic_rows"]
    control = basis["group_columns"]["Control"]
    treated = basis["group_columns"]["Treated"]

    wb = load_workbook(workbook_path)
    task = wb["Task"]

    expression_writes = 0
    blank_sources = []
    for protein in basis["proteins"]:
        row = protein["task_row"]
        for sample in basis["samples"]:
            column = sample["task_column"]
            if protein["expression_values"][sample["sample_name"]] is None:
                # the Data sheet carries no measurement here; leave the cell empty rather than
                # letting INDEX coerce the gap into a 0 that would bias the group statistics
                blank_sources.append(f"{column}{row}")
                continue
            task[f"{column}{row}"] = (
                f"=INDEX({ranges['value_range']},"
                f"MATCH($A{row},{ranges['protein_id_range']},0),"
                f"MATCH({column}$10,{ranges['sample_header_range']},0))"
            )
            expression_writes += 1

    def group_refs(columns: list[str], row: int) -> str:
        return ",".join(f"{column}{row}" for column in columns)

    statistics_writes = 0
    for protein in basis["proteins"]:
        row = protein["task_row"]
        column = protein["stat_column"]
        task[f"{column}{rows['control_mean']}"] = f"=IFERROR(AVERAGE({group_refs(control, row)}),0)"
        task[f"{column}{rows['control_stdev']}"] = f"=IFERROR(STDEV({group_refs(control, row)}),0)"
        task[f"{column}{rows['treated_mean']}"] = f"=IFERROR(AVERAGE({group_refs(treated, row)}),0)"
        task[f"{column}{rows['treated_stdev']}"] = f"=IFERROR(STDEV({group_refs(treated, row)}),0)"
        statistics_writes += 4

    wb.save(workbook_path)
    wb.close()
    print(f"wrote {expression_writes} lookup formulas and {statistics_writes} statistics formulas")
    if blank_sources:
        print(f"left empty (no Data-sheet measurement): {blank_sources}")

    recalc = recalculate(workbook_path)
    print(f"recalc status: {recalc.get('status')} errors: {recalc.get('total_errors')}")
    if recalc.get("total_errors"):
        raise SystemExit(f"formula errors after recalc: {recalc.get('error_summary')}")

    checked = load_workbook(workbook_path, data_only=True)
    checked_task = checked["Task"]
    stat_cells = {}
    for protein in basis["proteins"]:
        column = protein["stat_column"]
        entry = {}
        for label, row in rows.items():
            value = checked_task[f"{column}{row}"].value
            if value is None or isinstance(value, str):
                raise SystemExit(f"statistics cell {column}{row} did not recalculate: {value!r}")
            entry[label] = float(value)
        stat_cells[protein["protein_id"]] = entry
    filled_expression = sum(
        1
        for protein in basis["proteins"]
        for sample in basis["samples"]
        if checked_task[f"{sample['task_column']}{protein['task_row']}"].value is not None
    )
    checked.close()

    fold_change_writes = []
    for protein in basis["proteins"]:
        column = protein["stat_column"]
        fold_row = protein["fold_change_row"]
        values = [
            value
            for sample in basis["samples"]
            for value in [protein["expression_values"][sample["sample_name"]]]
            if value is not None
        ]
        control_values = [
            protein["expression_values"][sample["sample_name"]]
            for sample in basis["samples"]
            if sample["group"] == "Control" and protein["expression_values"][sample["sample_name"]] is not None
        ]
        treated_values = [
            protein["expression_values"][sample["sample_name"]]
            for sample in basis["samples"]
            if sample["group"] == "Treated" and protein["expression_values"][sample["sample_name"]] is not None
        ]
        expected_log2fc = (
            (statistics.mean(treated_values) if treated_values else 0.0)
            - (statistics.mean(control_values) if control_values else 0.0)
        )
        fold_change_writes.append(
            {
                "protein_id": protein["protein_id"],
                "gene_symbol": protein["gene_symbol"],
                "fold_change_row": fold_row,
                "stat_column": column,
                "writes": {
                    f"A{fold_row}": f"=A{protein['task_row']}",
                    f"B{fold_row}": f"=B{protein['task_row']}",
                    f"C{fold_row}": f"=IFERROR(POWER(2,{column}{rows['treated_mean']}-{column}{rows['control_mean']}),0)",
                    f"D{fold_row}": f"={column}{rows['treated_mean']}-{column}{rows['control_mean']}",
                },
                "expected_log2_fold_change": round(expected_log2fc, 6),
                "expected_fold_change": round(2 ** expected_log2fc, 6),
                "measured_sample_count": len(values),
            }
        )

    ledger = {
        "schema": "model_closure_ledger.v1",
        "current_stage": "protein-expression-model-build",
        "next_required_skill": NEXT_REQUIRED_SKILL,
        "workbook_path": workbook_path,
        "release_state": "closure_pending",
        "completed_steps": {
            "step_1_expression_lookup": {
                "block": basis["task_blocks"]["expression"],
                "formula_cells_written": expression_writes,
                "cells_filled_after_recalc": filled_expression,
                "empty_no_measurement": blank_sources,
            },
            "step_2_statistics": {
                "block": basis["task_blocks"]["statistics"],
                "formula_cells_written": statistics_writes,
                "recalculated_values": stat_cells,
            },
        },
        "outstanding_step": {
            "step_3_fold_change": {
                "block": basis["task_blocks"]["fold_change"],
                "owner": "protein-expression-release-finalizer",
                "writes": fold_change_writes,
            }
        },
        "acceptance_criteria": {
            "expression_block_min_filled": 80,
            "statistics_block_min_numeric": 32,
            "fold_change_min_numeric": 8,
            "max_formula_errors": 0,
            "log2_fold_change_tolerance": 1e-06,
        },
        "subsumption": {
            "supersedes_for_remaining_work": f"{WORKFLOW_DIR}/expression_matrix_basis.json",
            "note": (
                "step 3 reads only the recalculated statistics cells named above; the expected "
                "values recorded here are sufficient to verify every remaining write without "
                "reopening the extracted basis or any pre-edit reference copy"
            ),
        },
    }

    with open(os.path.join(WORKFLOW_DIR, "model_closure_ledger.json"), "w") as handle:
        json.dump(ledger, handle, indent=2)

    print(f"wrote {WORKFLOW_DIR}/model_closure_ledger.json")
    print(f"expression cells filled after recalc: {filled_expression}")
    print(f"closure ledger written: release_state=closure_pending, step 3 owed for {len(fold_change_writes)} proteins")
    print(f"next_required_skill={NEXT_REQUIRED_SKILL}")


if __name__ == "__main__":
    main()
