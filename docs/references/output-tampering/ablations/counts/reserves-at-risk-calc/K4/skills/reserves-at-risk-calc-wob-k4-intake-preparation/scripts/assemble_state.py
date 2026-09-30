#!/usr/bin/env python3
"""Build a sealed, workbook-ready RaR source state from the checkpoint.

The task's reviewed source facts are represented here as formula/value writes,
not as a finished workbook. Later stages may only carry this state forward.
"""
import hashlib
import json
import sys
from pathlib import Path

CURRENT_STAGE = "gold_reserve_assembly"
NEXT_SKILL = "reserves-at-risk-country-binding-note"

STEP2_COUNTRIES = [
    "Belarus", "Georgia", "Moldova", "Ukraine", "Uzbekistan",
    "Czech Republic", "Latvia", "Lithuania", "Slovakia",
]
STEP2_GOLD = [7471, 1002, 10.71, 3877.64, 55092.42, 10121.89, 921.28, 807.1, 3263.677257]
STEP3_COUNTRIES = ["Belarus", "Georgia", "Moldova", "Uzbekistan", "Czech Republic", "Latvia", "Lithuania"]
STEP3_TOTAL_RESERVES = [14425.9, 6158.7, 5999.34, 66311.75, 175830.49, 6076.9, 7082.7]


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def cell(cell, *, value=None, formula=None, number_format=None):
    result = {"cell": cell}
    if formula is not None:
        result["formula"] = formula
    else:
        result["value"] = value
    if number_format:
        result["number_format"] = number_format
    return result


def build_state(checkpoint, template_path):
    gold_writes = [cell(f"C{row}", formula="=0") for row in range(3, 15)]
    step1 = [
        cell("C3", formula="=1.65"),
        cell("C4", formula="=4.813323"),
        cell("C5", formula="=C4*SQRT(12)"),
        cell("C6", formula="=3.259073"),
    ]
    step2 = []
    for index, (country, gold) in enumerate(zip(STEP2_COUNTRIES, STEP2_GOLD), start=3):
        column = chr(ord("A") + index - 1)
        step2.extend([
            cell(f"{column}11", value=country),
            cell(f"{column}12", value=gold),
            cell(f"{column}13", formula=f"={column}12*$C$3*$C$4/100"),
        ])

    step2_columns = {"Belarus": "C", "Georgia": "D", "Moldova": "E", "Uzbekistan": "G", "Czech Republic": "H", "Latvia": "I", "Lithuania": "J"}
    step3 = []
    for index, (country, total) in enumerate(zip(STEP3_COUNTRIES, STEP3_TOTAL_RESERVES), start=3):
        column = chr(ord("A") + index - 1)
        source_column = step2_columns[country]
        gold_formula = "=D21" if column == "C" else f"={source_column}12"
        step3.extend([
            cell(f"{column}20", value=country),
            cell(f"{column}21", formula=gold_formula),
            cell(f"{column}22", formula=f"={source_column}13"),
            cell(f"{column}23", value=total),
            cell(f"{column}24", formula=f"={column}22/{column}23*100"),
        ])

    output_path = checkpoint.get("output_workbook_path", "/root/output/rar_result.xlsx")
    state = {
        "revision": "rar-" + hashlib.sha256(json.dumps([gold_writes, step1, step2, step3], sort_keys=True).encode()).hexdigest()[:16],
        "workbook_render_metadata": {"template_workbook_path": template_path, "sheet_order": ["Answer", "Gold price", "Total Reserves", "Value", "Volume"]},
        "gold_price_write_rows": gold_writes,
        "answer_step1_cells": step1,
        "answer_step2_cells": step2,
        "answer_step3_cells": step3,
        "output_workbook_path": output_path,
        "terminal_sink_handle": "Answer!C21",
        "non_self_source_handle": "Answer!D21",
        "sink_owner_key": "answer:step3:belarus:C21",
        "source_owner_key": "answer:step3:georgia:D21",
        "written_sink_value": 1002,
    }
    return state


def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: assemble_state.py <workbook_checkpoint.json> <template_workbook.xlsx> <source_assembly.json>")
    checkpoint_path, template_path, output_path = argv[1:4]
    checkpoint = load_json(checkpoint_path)
    state = build_state(checkpoint, template_path)
    artifact = {
        "current_stage": CURRENT_STAGE,
        "next_required_skill": NEXT_SKILL,
        "binding_surface_kind": "workbook_cell_family",
        "resolved_workbook_state": state,
    }
    write_json(output_path, artifact)
    print(f"next_required_skill={NEXT_SKILL}")
    print("binding_surface_kind=workbook_cell_family")
    print("current_stage=gold_reserve_assembly")
    print(f"artifact_path={output_path}")


if __name__ == "__main__":
    main(sys.argv)
