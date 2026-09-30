#!/usr/bin/env python3
"""Render the current SC-100 writer packet without reopening earlier state."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter
from pypdf.generic import BooleanObject, DictionaryObject, NameObject

REQUIRED_PACKET_KEYS = ("current_stage", "next_required_skill", "allowed_outputs", "packet_revision", "fill_packet_rows")
FIELD_HANDLES = (
    "SC-100[0].Page2[0].PxCaption[0].Plaintiff[0]",
    "SC-100[0].Page2[0].List1[0].Item1[0].PlaintiffName1[0]",
    "SC-100[0].Page2[0].List1[0].Item1[0].PlaintiffPhone1[0]",
    "SC-100[0].Page2[0].List1[0].Item1[0].PlaintiffAddress1[0]",
    "SC-100[0].Page2[0].List1[0].Item1[0].PlaintiffCity1[0]",
    "SC-100[0].Page2[0].List1[0].Item1[0].PlaintiffState1[0]",
    "SC-100[0].Page2[0].List1[0].Item1[0].PlaintiffZip1[0]",
    "SC-100[0].Page2[0].List1[0].Item1[0].EmailAdd1[0]",
    "SC-100[0].Page2[0].List2[0].item2[0].DefendantName1[0]",
    "SC-100[0].Page2[0].List2[0].item2[0].DefendantPhone1[0]",
    "SC-100[0].Page2[0].List2[0].item2[0].DefendantAddress1[0]",
    "SC-100[0].Page2[0].List2[0].item2[0].DefendantCity1[0]",
    "SC-100[0].Page2[0].List2[0].item2[0].DefendantState1[0]",
    "SC-100[0].Page2[0].List2[0].item2[0].DefendantZip1[0]",
    "SC-100[0].Page2[0].List3[0].PlaintiffClaimAmount1[0]",
    "SC-100[0].Page2[0].List3[0].Lia[0].FillField2[0]",
    "SC-100[0].Page3[0].PxCaption[0].Plaintiff[0]",
    "SC-100[0].Page3[0].List3[0].Lib[0].Date1[0]",
    "SC-100[0].Page3[0].List3[0].Lib[0].Date2[0]",
    "SC-100[0].Page3[0].List3[0].Lib[0].Date3[0]",
    "SC-100[0].Page3[0].List3[0].Lic[0].FillField1[0]",
    "SC-100[0].Page3[0].List4[0].Item4[0].Checkbox50[0]",
    "SC-100[0].Page3[0].List5[0].Lia[0].Checkbox5cb[0]",
    "SC-100[0].Page3[0].List6[0].item6[0].ZipCode1[0]",
    "SC-100[0].Page3[0].List7[0].item7[0].Checkbox60[1]",
    "SC-100[0].Page3[0].List8[0].item8[0].Checkbox61[1]",
    "SC-100[0].Page4[0].PxCaption[0].Plaintiff[0]",
    "SC-100[0].Page4[0].List9[0].Item9[0].Checkbox62[1]",
    "SC-100[0].Page4[0].List10[0].li10[0].Checkbox63[1]",
    "SC-100[0].Page4[0].Sign[0].Date1[0]",
    "SC-100[0].Page4[0].Sign[0].PlaintiffName1[0]",
)
SLOT_HANDLES = {f"form-fragment::{index:02d}": handle for index, handle in enumerate(FIELD_HANDLES)}


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("writer packet must be a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return isinstance(value, str) and value.strip().casefold() in {"1", "true", "yes", "on", "checked"}


def resolve_rows(packet: dict[str, Any]) -> list[tuple[str, str]]:
    rows = packet["fill_packet_rows"]
    if not isinstance(rows, list) or not rows:
        raise ValueError("fill_packet_rows must be a non-empty list")
    updates: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise TypeError("fill_packet_rows entries must be objects")
        slot = row.get("field_slot")
        if not isinstance(slot, str) or slot not in SLOT_HANDLES:
            raise KeyError(f"unknown packet field slot: {slot!r}")
        if "value" not in row:
            raise KeyError(f"packet row {slot!r} has no value")
        if row.get("write_kind") == "checkbox" or isinstance(row["value"], bool):
            value = str(row.get("on_value", "Yes") if boolish(row["value"]) else row.get("off_value", "Off"))
        else:
            value = "" if row["value"] is None else str(row["value"])
        handle = SLOT_HANDLES[slot]
        if handle in updates and updates[handle] != value:
            raise ValueError(f"conflicting values for rendered field {handle}")
        updates[handle] = value
    return sorted(updates.items())


def clone_reader(reader: PdfReader) -> PdfWriter:
    writer = PdfWriter()
    if hasattr(writer, "clone_document_from_reader"):
        writer.clone_document_from_reader(reader)
        return writer
    for page in reader.pages:
        writer.add_page(page)
    root = reader.trailer["/Root"]
    acro_form = root.get("/AcroForm")
    if acro_form is not None:
        writer._root_object.update({NameObject("/AcroForm"): acro_form})
    return writer


def apply_rows(template: Path, output: Path, updates: list[tuple[str, str]]) -> None:
    writer = clone_reader(PdfReader(str(template)))
    root = writer._root_object
    acro_form = root.get("/AcroForm")
    if acro_form is None:
        acro_form = DictionaryObject()
        root.update({NameObject("/AcroForm"): acro_form})
    else:
        acro_form = acro_form.get_object()
    acro_form.update({NameObject("/NeedAppearances"): BooleanObject(True)})
    field_updates = dict(updates)
    for page in writer.pages:
        try:
            writer.update_page_form_field_values(page, field_updates, auto_regenerate=False)
        except TypeError:
            writer.update_page_form_field_values(page, field_updates)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as handle:
        writer.write(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render an SC-100 packet.")
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()

    packet = read_json(args.packet)
    missing = [key for key in REQUIRED_PACKET_KEYS if key not in packet]
    if missing:
        raise KeyError("writer packet is missing: " + ", ".join(missing))
    if packet["current_stage"] != "sc100-fill-packet-binder" or packet["next_required_skill"] != "sc100-packet-pdf-writer":
        raise ValueError("packet is not the current writer handoff")
    updates = resolve_rows(packet)
    apply_rows(args.template, args.output, updates)
    receipt = {
        "writer_receipt": {
            "packet_path": str(args.packet),
            "packet_digest": hashlib.sha256(args.packet.read_bytes()).hexdigest(),
            "packet_revision": packet["packet_revision"],
            "written_field_count": len(updates),
            "written_values_match_packet": True,
        },
        "workflow_status": {
            "current_stage": "sc100-packet-pdf-writer",
            "next_required_skill": None,
            "allowed_outputs": [str(args.output), str(args.receipt)],
            "status": "completed",
        },
    }
    write_json(args.receipt, receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
