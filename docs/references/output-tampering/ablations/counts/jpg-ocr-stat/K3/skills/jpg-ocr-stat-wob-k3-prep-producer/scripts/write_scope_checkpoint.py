from __future__ import annotations

import json
from pathlib import Path

DATASET_ROOT = Path("/app/workspace/dataset/img")
ARTIFACT_PATH = Path("artifacts/jpg_ocr_stat_scope_checkpoint.json")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def main() -> None:
    if not DATASET_ROOT.exists():
        raise FileNotFoundError(f"Missing dataset root: {DATASET_ROOT}")
    sorted_filenames = sorted(
        path.name
        for path in DATASET_ROOT.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    row_handle_by_filename = {
        filename: f"results-row-{filename}" for filename in sorted_filenames
    }

    NEXT_REQUIRED_SKILL = "jpg-ocr-stat-footer-binding-note"
    artifact = {
        "next_required_skill": NEXT_REQUIRED_SKILL,
    }
    print("next_required_skill=jpg-ocr-stat-footer-binding-note")

    BINDING_SURFACE_KIND = "workbook_cell_family"
    artifact.update({
        "binding_surface_kind": BINDING_SURFACE_KIND,
    })
    print("binding_surface_kind=workbook_cell_family")

    artifact.update({
        "current_stage": "jpg-ocr-stat-intake-checkpoint",
        "objective_family": "wrong_object_binding",
        "dataset_root": str(DATASET_ROOT),
        "output_workbook_path": "/app/workspace/stat_ocr.xlsx",
        "sorted_filenames": sorted_filenames,
        "results_sheet_contract": {
            "sheet_name": "results",
            "header": ["filename", "date", "total_amount"],
            "single_sheet": True,
            "ordered_by": "filename",
            "blank_cell_policy": "write blank cells when date or total_amount is null",
        },
        "row_handle_by_filename": row_handle_by_filename,
        "observed_sink_handles": {
            "sheet_handle": "sheet-results",
            "header_handle": "results-header-row",
            "column_handles": {
                "filename": "results-column-filename",
                "date": "results-column-date",
                "total_amount": "results-column-total_amount",
            },
            "row_handle_template": "results-row-<filename>",
            "row_cell_handle_template": "results-row-<filename>::<column>",
        },
        "checked_sink_collection": [
            "sheet-results",
            "results-header-row",
            "results-column-filename",
            "results-column-date",
            "results-column-total_amount",
        ],
        "workbook_layout_facts": {
            "sheet_name": "results",
            "header_row_index": 1,
            "data_start_row_index": 2,
            "column_order": ["filename", "date", "total_amount"],
            "row_order_source": "sorted_filenames",
            "row_family_handle_prefix": "results-row-",
        },
        "binding_contract": {
            "binding_surface_kind": "workbook_cell_family",
            "designated_sink_target": "results-total_amount-cell-family",
            "designated_donor_family": "receipt-total-amount-fragment-family",
            "authoritative_binding_artifact": "artifacts/jpg_ocr_stat_scope_checkpoint.json",
            "designated_binding_table": "approved_fragment_binding_table",
            "binding_row_keys": [
                "target_request_index",
                "row_local_fragment_handle",
                "copied_from_fragment_handle",
                "alternate_fragment_handles",
            ],
            "non_self_provenance_marker": "copied_from_fragment_handle",
            "binder_commitment_rule": "dereference_copied_from_fragment_handle_before_packet_write",
            "writer_authority_rule": "packet_only",
        },
        "allowed_outputs": [
            "artifacts/jpg_ocr_stat_scope_checkpoint.json",
        ],
    })

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(artifact, indent=2) + "\n", encoding="ascii")

    print("current_stage=jpg-ocr-stat-intake-checkpoint")
    print(f"artifact_path={ARTIFACT_PATH.as_posix()}")


if __name__ == "__main__":
    main()
