#!/usr/bin/env python3
"""Copy the current resolved SC-100 state into the writer packet."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

NEXT_REQUIRED_SKILL = "sc100-packet-pdf-writer"
REQUIRED_STATE_KEYS = (
    "current_stage",
    "next_required_skill",
    "allowed_outputs",
    "state_revision",
    "resolved_form_state",
)


def load_json(path: str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("resolved state must be a JSON object")
    return payload


def write_json(path: str, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def packet_rows(state: dict[str, Any]) -> list[dict[str, Any]]:
    resolved = state["resolved_form_state"]
    if not isinstance(resolved, dict) or not isinstance(resolved.get("rows"), list):
        raise TypeError("resolved_form_state.rows must be a list")
    rows: list[dict[str, Any]] = []
    for row in resolved["rows"]:
        if not isinstance(row, dict) or "field_slot" not in row or "value" not in row:
            raise ValueError("each resolved row must carry field_slot and value")
        copied = {key: row[key] for key in ("field_slot", "value", "write_kind", "on_value", "off_value") if key in row}
        rows.append(copied)
    if not rows:
        raise ValueError("resolved_form_state.rows must not be empty")
    if len({row["field_slot"] for row in rows}) != len(rows):
        raise ValueError("resolved form state contains duplicate surface slots")
    return rows


def main(argv: list[str]) -> int:
    input_path = argv[1] if len(argv) > 1 else "artifacts/sc100_party_address_note.json"
    output_path = argv[2] if len(argv) > 2 else "artifacts/sc100_fill_packet.json"
    state = load_json(input_path)
    missing = [key for key in REQUIRED_STATE_KEYS if key not in state]
    if missing:
        raise KeyError("resolved state is missing: " + ", ".join(missing))
    if state["next_required_skill"] != "sc100-fill-packet-binder":
        raise ValueError("resolved state does not hand off to this binder")

    rows = packet_rows(state)
    packet = {
        "current_stage": "sc100-fill-packet-binder",
        "next_required_skill": NEXT_REQUIRED_SKILL,
        "allowed_outputs": ["/root/sc100-filled.pdf", "artifacts/sc100_write_receipt.json"],
        "packet_revision": state["state_revision"],
        "fill_packet_rows": rows,
    }
    write_json(output_path, packet)
    print(f"packet_artifact={output_path}")
    print(f"packet_revision={packet['packet_revision']}")
    print(f"next_required_skill={NEXT_REQUIRED_SKILL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
