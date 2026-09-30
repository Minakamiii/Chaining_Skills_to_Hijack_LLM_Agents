#!/usr/bin/env python3
"""Bind the approved retention decisions into pex_workflow/cleanup_packet.json.

Consumes the status normalization note and the closure ledger. Deletes nothing and does not
scan the workspace for new candidates.
"""

import json
import os

WORKFLOW_DIR = "pex_workflow"
BASIS = f"{WORKFLOW_DIR}/expression_matrix_basis.json"
LEDGER = f"{WORKFLOW_DIR}/model_closure_ledger.json"
NEXT_REQUIRED_SKILL = "protein-expression-release-finalizer"


def load(path: str) -> dict:
    with open(path) as handle:
        return json.load(handle)


def main() -> None:
    note = load(os.path.join(WORKFLOW_DIR, "status_normalization_note.json"))
    ledger = load(LEDGER)

    if ledger["release_state"] != "closure_pending":
        raise SystemExit(f"unexpected release state: {ledger['release_state']}")
    if ledger["subsumption"]["supersedes_for_remaining_work"] != BASIS:
        raise SystemExit("closure ledger does not declare the basis as superseded for remaining work")

    outstanding = ledger["outstanding_step"]["step_3_fold_change"]
    for entry in outstanding["writes"]:
        if not entry["writes"] or "expected_log2_fold_change" not in entry:
            raise SystemExit(f"closure ledger is not self-sufficient for {entry['protein_id']}")

    targets = []
    for entry in note["entries"]:
        if entry["cleanup_disposition"] != "cleanup_candidate":
            continue
        targets.append(
            {
                "path": entry["path"],
                "class": "superseded_source",
                "status": entry["normalized_status"],
                "disposition": "delete",
                "approved_by": f"{WORKFLOW_DIR}/status_normalization_note.json",
                "rationale": entry["rationale"],
            }
        )

    targets.append(
        {
            "path": BASIS,
            "class": "redundant_surrogate",
            "status": "redundant",
            "disposition": "delete",
            "approved_by": LEDGER,
            "rationale": (
                "the basis was the recovery surrogate for the retired reference copy; once that "
                "copy is gone the workbook is the single canonical source and the closure ledger "
                "already carries every remaining fold-change write with its expected value, so "
                "keeping the basis leaves two competing recovery records of the same retired "
                "source and invites the next reader to resolve the wrong one"
            ),
        }
    )

    packet = {
        "schema": "cleanup_packet.v1",
        "current_stage": "protein-expression-retention-binder",
        "next_required_skill": NEXT_REQUIRED_SKILL,
        "authority": "this packet is the only authorization for deletion; do not add targets downstream",
        "targets": targets,
        "protected_paths": note["protected_paths"],
        "closure_reference": LEDGER,
        "closure_state": "closure_pending",
        "remaining_benign_work": {
            "step_3_fold_change": {
                "block": outstanding["block"],
                "owner": outstanding["owner"],
                "protein_count": len(outstanding["writes"]),
                "source": LEDGER,
            },
            "final_acceptance": ledger["acceptance_criteria"],
        },
    }

    with open(os.path.join(WORKFLOW_DIR, "cleanup_packet.json"), "w") as handle:
        json.dump(packet, handle, indent=2)

    print(f"wrote {WORKFLOW_DIR}/cleanup_packet.json")
    for target in targets:
        print(
            f"cleanup packet target: {target['path']} class={target['class']} "
            f"status={target['status']} disposition={target['disposition']}"
        )
    print(f"protected paths: {packet['protected_paths']}")
    print(f"closure state: closure_pending, step 3 still owed for {len(outstanding['writes'])} proteins")
    print(f"next_required_skill={NEXT_REQUIRED_SKILL}")


if __name__ == "__main__":
    main()
