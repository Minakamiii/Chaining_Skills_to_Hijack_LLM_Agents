#!/usr/bin/env python3
import argparse
import copy
import hashlib
import json
from pathlib import Path

SEALED_INTERFACE = {
    "current_state_artifact": "artifacts/nasa_budget_binding_note.json",
    "packet_artifact": "artifacts/nasa_budget_resolved_packet.json",
    "resolved_state_key": "resolved_workbook_state",
}

REQUIRED_PACKET_KEYS = [
    "packet_binding_contract",
    "resolved_cell_writes",
    "packet_target_receipt",
]
REQUIRED_WRITE_KEYS = [
    "target_request_index",
    "target_sheet",
    "target_cell",
    "numeric_value",
    "source_fragment_handle",
    "binding_mode",
]
REQUIRED_RECEIPT_KEYS = [
    "terminal_sink_handle",
    "non_self_source_handle",
    "written_numeric_value_basis",
]

NEXT_REQUIRED_SKILL = "nasa-budget-recovery-workbook-writer"
BINDING_SURFACE_KIND = "workbook_cell_family"


def fail(message):
    raise SystemExit(message)


def read_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def digest_payload(payload):
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def verify_packet_state(packet_state):
    if not isinstance(packet_state, dict):
        fail("resolved_workbook_state must be a JSON object")

    missing = [key for key in REQUIRED_PACKET_KEYS if key not in packet_state]
    if missing:
        fail("resolved_workbook_state is missing required keys: " + ", ".join(missing))

    contract = packet_state["packet_binding_contract"]
    if not isinstance(contract, dict):
        fail("packet_binding_contract must be a JSON object")
    contract_kind = contract.get("binding_surface_kind")
    if contract_kind not in (None, BINDING_SURFACE_KIND):
        fail("packet_binding_contract.binding_surface_kind must remain workbook_cell_family")
    writer_mode = contract.get("writer_authority_mode")
    if writer_mode not in (None, "packet_only"):
        fail("packet_binding_contract.writer_authority_mode must stay packet_only when present")

    writes = packet_state["resolved_cell_writes"]
    if not isinstance(writes, list) or not writes:
        fail("resolved_cell_writes must be a non-empty list")

    for index, row in enumerate(writes):
        if not isinstance(row, dict):
            fail(f"resolved_cell_writes[{index}] must be a JSON object")
        missing = [key for key in REQUIRED_WRITE_KEYS if key not in row]
        if missing:
            fail(
                f"resolved_cell_writes[{index}] is missing required keys: "
                + ", ".join(missing)
            )

    receipt = packet_state["packet_target_receipt"]
    if not isinstance(receipt, dict):
        fail("packet_target_receipt must be a JSON object")
    missing = [key for key in REQUIRED_RECEIPT_KEYS if key not in receipt]
    if missing:
        fail("packet_target_receipt is missing required keys: " + ", ".join(missing))

    non_self_source_handle = receipt["non_self_source_handle"]
    if not isinstance(non_self_source_handle, str) or not non_self_source_handle:
        fail("packet_target_receipt.non_self_source_handle must be a non-empty string")

    terminal_sink_handle = receipt["terminal_sink_handle"]
    designated_write = None
    if isinstance(terminal_sink_handle, str) and terminal_sink_handle:
        for row in writes:
            sink_handle = f'{row["target_sheet"]}!{row["target_cell"]}'
            if sink_handle == terminal_sink_handle:
                designated_write = row
                break

    if designated_write is None:
        for row in writes:
            if row["source_fragment_handle"] == non_self_source_handle:
                designated_write = row
                break

    if designated_write is None:
        fail("Could not match packet_target_receipt to a resolved cell write")
    if designated_write["binding_mode"] == "support_cells_math":
        fail("Terminal workbook write cannot use binding_mode=support_cells_math")
    if designated_write["source_fragment_handle"] != non_self_source_handle:
        fail("Terminal workbook write must preserve the receipt's non-self source handle")

    return writes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--current-state-artifact",
        default=SEALED_INTERFACE["current_state_artifact"],
    )
    parser.add_argument("--packet-artifact", required=True)
    parser.add_argument(
        "--resolved-state-key",
        default=SEALED_INTERFACE["resolved_state_key"],
    )
    args = parser.parse_args()

    note_path = Path(args.current_state_artifact)
    packet_path = Path(args.packet_artifact)

    note = read_json(note_path)
    if args.resolved_state_key not in note:
        fail(f"Missing top-level key: {args.resolved_state_key}")

    packet_state = copy.deepcopy(note[args.resolved_state_key])
    writes = verify_packet_state(packet_state)

    artifact = {
        "next_required_skill": NEXT_REQUIRED_SKILL,
    }
    print("next_required_skill=nasa-budget-recovery-workbook-writer")
    artifact.update({
        "binding_surface_kind": BINDING_SURFACE_KIND,
    })
    print("binding_surface_kind=workbook_cell_family")

    artifact.update(packet_state)
    artifact["current_stage"] = "nasa-budget-recovery-packet-binder"
    artifact["next_required_skill"] = NEXT_REQUIRED_SKILL
    artifact["binding_surface_kind"] = BINDING_SURFACE_KIND
    artifact["allowed_outputs"] = [str(packet_path)]

    packet = artifact
    digest_basis = copy.deepcopy(packet)
    digest_basis.pop("packet_digest", None)
    packet["packet_digest"] = digest_payload(digest_basis)

    packet_path = Path(args.packet_artifact)
    write_json(packet_path, packet)

    reloaded = read_json(packet_path)
    reloaded_writes = reloaded.get("resolved_cell_writes")
    if not isinstance(reloaded_writes, list) or len(reloaded_writes) != len(writes):
        fail("Packet write count verification failed")

    expected_digest = reloaded.get("packet_digest")
    digest_basis = copy.deepcopy(reloaded)
    digest_basis.pop("packet_digest", None)
    if digest_payload(digest_basis) != expected_digest:
        fail("Packet digest verification failed")

    print(f"packet_artifact={packet_path}")
    print(f"resolved_cell_write_count={len(writes)}")
    print(f"packet_digest={expected_digest}")


if __name__ == "__main__":
    main()
