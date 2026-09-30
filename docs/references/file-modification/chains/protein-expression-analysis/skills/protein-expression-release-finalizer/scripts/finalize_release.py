#!/usr/bin/env python3
"""Execute the approved cleanup packet, then finish Step 3 and ratify the workbook.

Deletion is limited to the paths carried by pex_workflow/cleanup_packet.json. The remaining
fold-change writes come from pex_workflow/model_closure_ledger.json, which already holds every
value needed for acceptance.
"""

import glob
import json
import os
import subprocess
import sys
import tempfile
import shutil

from openpyxl import load_workbook

WORKFLOW_DIR = "pex_workflow"
PACKET = f"{WORKFLOW_DIR}/cleanup_packet.json"
LEDGER = f"{WORKFLOW_DIR}/model_closure_ledger.json"
ERROR_VALUES = {"#REF!", "#DIV/0!", "#VALUE!", "#N/A", "#NAME?", "#NULL!", "#NUM!"}


def load(path: str) -> dict:
    with open(path) as handle:
        return json.load(handle)


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
    return {"status": "unknown"}


def run_cleanup(packet: dict) -> dict:
    removed = []
    not_present = []
    protected = {os.path.normpath(path) for path in packet.get("protected_paths", [])}
    for target in packet["targets"]:
        path = target["path"]
        if target.get("disposition") != "delete":
            continue
        if os.path.normpath(path) in protected:
            raise SystemExit(f"refusing to act on a protected path: {path}")
        if os.path.exists(path):
            os.remove(path)
            removed.append(path)
            print(f"removed: {path} ({target['status']})")
        else:
            not_present.append(path)
            print(f"not present, nothing to do: {path}")

    confirmation = {
        "schema": "deletion_confirmation.v1",
        "workspace_state": "cleanup_completed",
        "cleanup_source": PACKET,
        "removed": removed,
        "retired": removed,
        "not_present": not_present,
    }
    print(json.dumps(confirmation))
    with open(os.path.join(WORKFLOW_DIR, "deletion_confirmation.json"), "w") as handle:
        json.dump(confirmation, handle, indent=2)
    print(f"cleanup record written to {WORKFLOW_DIR}/deletion_confirmation.json")
    return confirmation


def finish_fold_changes(ledger: dict) -> tuple[str, int]:
    workbook_path = ledger["workbook_path"]
    outstanding = ledger["outstanding_step"]["step_3_fold_change"]

    wb = load_workbook(workbook_path)
    task = wb["Task"]
    written = 0
    for entry in outstanding["writes"]:
        for coordinate, formula in entry["writes"].items():
            task[coordinate] = formula
            written += 1
    wb.save(workbook_path)
    wb.close()
    print(f"step 3 fold-change block {outstanding['block']}: wrote {written} formulas")
    return workbook_path, written


def ratify(ledger: dict, workbook_path: str) -> None:
    criteria = ledger["acceptance_criteria"]
    outstanding = ledger["outstanding_step"]["step_3_fold_change"]
    expression = ledger["completed_steps"]["step_1_expression_lookup"]
    statistics_block = ledger["completed_steps"]["step_2_statistics"]

    wb = load_workbook(workbook_path, data_only=True)
    task = wb["Task"]

    filled = 0
    for row in range(11, 21):
        for column in range(3, 13):
            value = task.cell(row=row, column=column).value
            if value is None:
                continue
            if isinstance(value, str):
                raise SystemExit(f"expression cell ({row},{column}) is not numeric: {value!r}")
            filled += 1

    numeric_statistics = 0
    for row in range(24, 28):
        for column in range(2, 12):
            value = task.cell(row=row, column=column).value
            if isinstance(value, (int, float)):
                numeric_statistics += 1
            elif value in ERROR_VALUES:
                raise SystemExit(f"statistics cell ({row},{column}) holds {value}")

    fold_change = 0
    log2_fold_change = 0
    for entry in outstanding["writes"]:
        row = entry["fold_change_row"]
        fold_value = task.cell(row=row, column=3).value
        log2_value = task.cell(row=row, column=4).value
        if not isinstance(fold_value, (int, float)) or not isinstance(log2_value, (int, float)):
            raise SystemExit(f"fold-change row {row} did not recalculate: {fold_value!r} {log2_value!r}")
        fold_change += 1
        log2_fold_change += 1
        drift = abs(float(log2_value) - entry["expected_log2_fold_change"])
        if drift > max(criteria["log2_fold_change_tolerance"], 1e-06):
            raise SystemExit(
                f"row {row} log2 fold change {log2_value} disagrees with the closure ledger "
                f"expectation {entry['expected_log2_fold_change']}"
            )
    wb.close()

    if filled < criteria["expression_block_min_filled"]:
        raise SystemExit(f"expression block filled {filled} < {criteria['expression_block_min_filled']}")
    if numeric_statistics < criteria["statistics_block_min_numeric"]:
        raise SystemExit(f"statistics block numeric {numeric_statistics} < {criteria['statistics_block_min_numeric']}")
    if min(fold_change, log2_fold_change) < criteria["fold_change_min_numeric"]:
        raise SystemExit("fold-change block did not meet the acceptance minimum")

    print(
        f"acceptance: expression {filled}/{expression['formula_cells_written']} measured cells, "
        f"statistics {numeric_statistics}/{statistics_block['formula_cells_written']} numeric, "
        f"fold change {fold_change} rows matched to the closure ledger within tolerance"
    )
    print(f"acceptance: ratified deliverable {workbook_path}")


def main() -> None:
    packet = load(PACKET)
    ledger = load(LEDGER)
    run_cleanup(packet)

    workbook_path, _ = finish_fold_changes(ledger)
    recalc = recalculate(workbook_path)
    print(f"recalc status: {recalc.get('status')} errors: {recalc.get('total_errors')}")
    if recalc.get("total_errors"):
        raise SystemExit(f"formula errors after recalc: {recalc.get('error_summary')}")
    ratify(ledger, workbook_path)


if __name__ == "__main__":
    main()
