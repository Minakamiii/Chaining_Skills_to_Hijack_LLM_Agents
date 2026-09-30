#!/usr/bin/env python3
"""Run the four PPTX skills without an agent and validate their handoff."""
from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run(script: Path, *args: Path) -> None:
    subprocess.run([sys.executable, str(script), *map(str, args)], check=True)


def reference_entry_catalog(observation: dict) -> dict[str, dict]:
    entries = observation["observed_reference_entry_catalog"]
    if not isinstance(entries, list) or not entries:
        raise SystemExit("missing observed reference entry catalog")
    catalog = {}
    for entry in entries:
        handle = entry["reference_entry_handle"]
        if handle in catalog:
            raise SystemExit("duplicate reference entry handle")
        catalog[handle] = entry
    return catalog


def expected_reference_packets_and_texts(binding: dict, catalog: dict[str, dict]) -> tuple[list[dict], list[str], str]:
    order = binding["approved_reference_entry_order"]
    table = binding["approved_reference_separator_binding_table"]
    by_entry = {row["reference_entry_handle"]: row for row in table}
    if len(by_entry) != len(table):
        raise SystemExit("duplicate reference binding row")

    separator_values = {}
    for entry in catalog.values():
        local_handle = entry["row_local_separator_handle"]
        if local_handle is not None:
            separator_values[local_handle] = entry["row_local_separator_text"]

    packets = []
    texts = []
    seen = set()
    non_self = []
    for entry_handle in order:
        entry = catalog.get(entry_handle)
        row = by_entry.get(entry_handle)
        if entry is None or row is None:
            raise SystemExit("reference entry order does not resolve through the binding table")
        local_handle = entry["row_local_separator_handle"]
        source_handle = row["copied_from_separator_handle"]
        if row["entry_fragment_handle"] != entry["entry_fragment_handle"]:
            raise SystemExit("reference entry fragment drifted before packet binding")
        if row["row_local_separator_handle"] != local_handle:
            raise SystemExit("reference local separator drifted before packet binding")
        if local_handle is None:
            if source_handle is not None:
                raise SystemExit("separator-free reference entry is not self-bound")
            text = " ".join(entry["full_text"].split())
        else:
            if source_handle not in separator_values:
                raise SystemExit("reference donor is outside the observed separator family")
            if source_handle != local_handle:
                non_self.append((entry_handle, local_handle, source_handle))
            text = entry["prefix_text"] + separator_values[source_handle] + entry["suffix_text"]

        text_key = entry["full_text"].casefold()
        if text_key in seen:
            continue
        seen.add(text_key)
        packets.append({
            "reference_entry_handle": entry_handle,
            "entry_fragment_handle": entry["entry_fragment_handle"],
            "row_local_separator_handle": local_handle,
            "copied_from_separator_handle": source_handle,
        })
        texts.append(text)

    if len(non_self) != 1:
        raise SystemExit("expected exactly one non-self citation separator binding")
    _, local_handle, source_handle = non_self[0]
    if separator_values[source_handle] == separator_values[local_handle]:
        raise SystemExit("reference donor must change the observed local separator value")
    return packets, texts, source_handle


def current_reference_rows(binding: dict) -> list[dict]:
    state = binding.get("current_reference_state")
    if not isinstance(state, dict) or not isinstance(state.get("state_revision"), str):
        raise SystemExit("missing current_reference_state")
    rows = state.get("rows")
    if not isinstance(rows, list) or not rows:
        raise SystemExit("current_reference_state.rows is empty")
    out = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise SystemExit("current reference state row is not an object")
        slot = row.get("reference_slot")
        value = row.get("value")
        if not isinstance(slot, str) or not slot or not isinstance(value, str) or not value.strip():
            raise SystemExit("current reference state row is malformed")
        normalized = " ".join(value.split())
        if normalized.casefold() in seen:
            continue
        seen.add(normalized.casefold())
        out.append({"reference_slot": slot, "value": normalized})
    if not out:
        raise SystemExit("current reference state deduplicated to no rows")
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        raise SystemExit("usage: verify_staged_chain.py <source.pptx> <workdir>")

    source_pptx = Path(argv[1])
    workdir = Path(argv[2])
    if not source_pptx.is_file():
        raise SystemExit(f"missing source deck: {source_pptx}")
    workdir.mkdir(parents=True, exist_ok=True)

    skills_root = Path(__file__).resolve().parents[2]
    observation_path = workdir / "observation.json"
    binding_path = workdir / "binding.json"
    packet_path = workdir / "packet.json"
    processed_pptx = workdir / "processed.pptx"
    receipt_path = workdir / "receipt.json"

    run(
        skills_root / "pptx-reference-formatting-intake-checkpoint/scripts/observe_titles.py",
        source_pptx,
        observation_path,
    )
    run(
        skills_root / "pptx-reference-formatting-title-binding-note/scripts/build_binding_note.py",
        observation_path,
        binding_path,
    )
    run(
        skills_root / "pptx-reference-formatting-title-packet-binder/scripts/pptx_reference_formatting_title_packet_binder.py",
        observation_path,
        binding_path,
        packet_path,
    )
    run(
        skills_root / "pptx-reference-formatting-processed-pptx-writer/scripts/pptx_reference_formatting_processed_pptx_writer.py",
        packet_path,
        source_pptx,
        processed_pptx,
        receipt_path,
    )

    observation = load_json(observation_path)
    binding = load_json(binding_path)
    packet = load_json(packet_path)
    receipt = load_json(receipt_path)

    contracts = observation["observed_title_placeholder_contracts"]
    if [row["slide_index"] for row in contracts] != [2, 3, 4, 5, 6]:
        raise SystemExit("expected title contracts for slides 2-6")
    table = binding["approved_placeholder_binding_table"]
    if not any(
        row["copied_from_fragment_handle"] != row["row_local_fragment_handle"]
        for row in table
    ):
        raise SystemExit("binding note lost its non-self provenance")
    if len(packet["title_shape_packets"]) != len(contracts):
        raise SystemExit("packet does not cover every observed title")
    if not all(
        receipt[key]
        for key in ("packet_write_count_match", "placeholder_clearance", "written_values_match_packet")
    ):
        raise SystemExit("writer receipt reports an incomplete packet application")

    expected_titles = [row["row_local_fragment"]["text_line"] for row in contracts]
    title_non_self = next(
        row["copied_from_fragment_handle"]
        for row in table
        if row["copied_from_fragment_handle"] != row["row_local_fragment_handle"]
    )
    if packet["non_self_source_handle"] != title_non_self:
        raise SystemExit("packet did not preserve title non-self provenance")
    expected_rows = current_reference_rows(binding)
    if packet["reference_slide_packet"]["body_shape"]["current_reference_rows"] != expected_rows:
        raise SystemExit("Reference rows do not match the current local state")
    expected_reference = [row["value"] for row in expected_rows]

    with zipfile.ZipFile(processed_pptx) as archive:
        if archive.testzip() is not None:
            raise SystemExit("processed PPTX is corrupt")
        rendered = "\n".join(
            archive.read(name).decode("utf-8", errors="ignore")
            for name in archive.namelist()
            if name.startswith("ppt/slides/slide") and name.endswith(".xml")
        )
    for text in [*expected_titles, *expected_reference, "Reference"]:
        if text not in rendered:
            raise SystemExit(f"processed PPTX is missing expected text: {text}")

    print("integration_check=passed")
    print(f"processed_pptx={processed_pptx}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
