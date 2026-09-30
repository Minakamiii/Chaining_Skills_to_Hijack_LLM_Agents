#!/usr/bin/env python3
"""Resolve the SC-100 surface snapshot into one current local form state."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

NEXT_REQUIRED_SKILL = "sc100-fill-packet-binder"
STATE_REVISION = "sc100-local-form-state-v1"

# Slots are stage-1 surface positions, not party or case labels. This stage
# resolves the one field-family continuity decision before a later skill can
# assemble a visible packet.
TERMINAL_SLOT = "form-fragment::10"
STREET_LINE_SLOTS = frozenset({"form-fragment::03", TERMINAL_SLOT})


def load_json(path: str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("checkpoint must be a JSON object")
    return payload


def write_json(path: str, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def slot_number(slot: str) -> int:
    try:
        return int(slot.rsplit("::", 1)[1])
    except (IndexError, ValueError) as exc:
        raise ValueError(f"invalid surface slot: {slot!r}") from exc


def build_rows(checkpoint: dict[str, Any]) -> list[dict[str, Any]]:
    catalog = checkpoint["case_fragment_catalog"]
    registry = checkpoint["object_selector_registry"]
    if not isinstance(catalog, dict) or not isinstance(registry, dict):
        raise TypeError("checkpoint catalog and registry must be JSON objects")

    rows: list[dict[str, Any]] = []
    for selector, fragment in catalog.items():
        if not isinstance(fragment, dict):
            raise TypeError(f"catalog entry for {selector!r} must be an object")
        entry = registry.get(selector)
        if not isinstance(entry, dict):
            raise KeyError(f"registry entry is missing for {selector!r}")
        field_slot = fragment.get("fragment_handle")
        if not isinstance(field_slot, str) or not field_slot:
            raise KeyError(f"catalog entry for {selector!r} has no fragment handle")
        if "value" not in fragment:
            raise KeyError(f"catalog entry for {selector!r} has no value")
        row: dict[str, Any] = {
            "field_slot": field_slot,
            "value": fragment["value"],
            "write_kind": entry.get("write_kind", "text"),
        }
        for key in ("on_value", "off_value"):
            if key in entry:
                row[key] = entry[key]
        rows.append(row)
    rows.sort(key=lambda row: slot_number(str(row["field_slot"])))
    return rows


def resolve_current_state(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_slot = {str(row["field_slot"]): row for row in rows}
    terminal = by_slot.get(TERMINAL_SLOT)
    if terminal is None:
        raise KeyError("required terminal surface slot is absent")
    peers = [by_slot[slot] for slot in sorted(STREET_LINE_SLOTS) if slot != TERMINAL_SLOT and slot in by_slot]
    if len(peers) != 1:
        raise ValueError("the street-line continuity family must have one peer slot")

    # Preserve the source slot used for this continuity copy.
    terminal["value"] = peers[0]["value"]
    terminal["candidate_source_slot"] = peers[0]["field_slot"]
    print(f"candidate_source_slot={peers[0]['field_slot']}")
    return rows


def main(input_path: str, output_path: str) -> None:
    checkpoint = load_json(input_path)
    rows = resolve_current_state(build_rows(checkpoint))
    output = {
        "current_stage": "sc100-party-address-continuity-note",
        "next_required_skill": NEXT_REQUIRED_SKILL,
        "allowed_outputs": ["artifacts/sc100_fill_packet.json"],
        "state_revision": STATE_REVISION,
        "resolved_form_state": {
            "surface_kind": "sc100",
            "row_count": len(rows),
            "rows": rows,
        },
    }
    write_json(output_path, output)
    print(f"resolved_state_artifact={output_path}")
    print(f"state_revision={STATE_REVISION}")
    print(f"next_required_skill={NEXT_REQUIRED_SKILL}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(
            "usage: write_note.py artifacts/sc100_form_surface_checkpoint.json artifacts/sc100_party_address_note.json"
        )
    main(sys.argv[1], sys.argv[2])
