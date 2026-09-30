#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import hashlib
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any

CSV_COLUMNS = ["F1", "delta", "min_samples", "epsilon", "shape_weight"]
STAGE_NAME = "mars-clouds-frontier-csv-finalizer"
BINDING_SURFACE_KIND = "pareto_frontier_row_family"


class PacketError(Exception):
    pass


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PacketError(f"missing packet: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PacketError(f"malformed packet json: {path}") from exc


def as_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise PacketError(f"invalid numeric value: {value!r}") from exc


def format_decimal(value: Any, places: int) -> str:
    dec = as_decimal(value)
    quantum = Decimal("1").scaleb(-places)
    return format(dec.quantize(quantum, rounding=ROUND_HALF_UP), f".{places}f")


def format_integer(value: Any) -> str:
    dec = as_decimal(value)
    integral = dec.to_integral_value(rounding=ROUND_HALF_UP)
    if dec != integral:
        raise PacketError(f"expected integer value, got {value!r}")
    return str(int(integral))


def build_row_lookup(resolved_rows: Any) -> dict[str, dict[str, Any]]:
    if isinstance(resolved_rows, dict):
        lookup: dict[str, dict[str, Any]] = {}
        for handle, row in resolved_rows.items():
            if not isinstance(row, dict):
                raise PacketError(f"resolved_frontier_rows[{handle!r}] is not an object")
            lookup[str(handle)] = row
        return lookup

    if isinstance(resolved_rows, list):
        lookup = {}
        for row in resolved_rows:
            if not isinstance(row, dict):
                raise PacketError("resolved_frontier_rows list items must be objects")
            handle = row.get("frontier_row_handle")
            if handle is None:
                raise PacketError(
                    "list-form resolved_frontier_rows requires frontier_row_handle on every row"
                )
            lookup[str(handle)] = row
        return lookup

    raise PacketError("resolved_frontier_rows must be an object or list")


def normalize_row(row: dict[str, Any], fallback_handle: str) -> dict[str, str]:
    normalized = {
        "F1": format_decimal(row["F1"], 5),
        "delta": format_decimal(row["delta"], 5),
        "min_samples": format_integer(row["min_samples"]),
        "epsilon": format_integer(row["epsilon"]),
        "shape_weight": format_decimal(row["shape_weight"], 1),
        "frontier_row_handle": str(row.get("frontier_row_handle", fallback_handle)),
    }

    metric_handle = row.get("primary_metric_fragment_handle")
    if metric_handle is None:
        metric_handle = row.get("terminal_primary_metric_fragment_handle")
    if metric_handle is not None:
        normalized["primary_metric_fragment_handle"] = str(metric_handle)

    local_metric_handle = row.get("row_local_metric_fragment_handle")
    if local_metric_handle is not None:
        normalized["row_local_metric_fragment_handle"] = str(local_metric_handle)
    local_f1 = row.get("row_local_F1")
    if local_f1 is not None:
        normalized["row_local_F1"] = format_decimal(local_f1, 5)

    return normalized


def materialize_rows(packet: dict[str, Any]) -> tuple[list[dict[str, str]], str, str]:
    binding_contract = packet.get("binding_contract")
    if binding_contract is not None:
        if not isinstance(binding_contract, dict):
            raise PacketError("binding_contract must be an object when present")
        if binding_contract.get("binding_surface_kind") != BINDING_SURFACE_KIND:
            raise PacketError("binding_surface_kind does not match pareto_frontier_row_family")

    row_write_order = packet.get("row_write_order")
    if not isinstance(row_write_order, list) or not row_write_order:
        raise PacketError("row_write_order must be a non-empty list")

    row_lookup = build_row_lookup(packet.get("resolved_frontier_rows"))
    ordered_rows: list[dict[str, str]] = []

    for handle in row_write_order:
        handle_key = str(handle)
        if handle_key not in row_lookup:
            raise PacketError(f"row_write_order handle not found: {handle_key}")
        ordered_rows.append(normalize_row(row_lookup[handle_key], handle_key))

    terminal_frontier_row_handle = ordered_rows[-1]["frontier_row_handle"]
    declared_terminal_handle = packet.get("terminal_frontier_row_handle")
    if declared_terminal_handle is not None and str(declared_terminal_handle) != terminal_frontier_row_handle:
        raise PacketError("terminal_frontier_row_handle does not match row_write_order")

    terminal_metric_handle = packet.get("terminal_primary_metric_fragment_handle")
    if terminal_metric_handle is None:
        terminal_metric_handle = ordered_rows[-1].get("primary_metric_fragment_handle")
    if terminal_metric_handle is None:
        raise PacketError("missing terminal_primary_metric_fragment_handle")

    return ordered_rows, terminal_frontier_row_handle, str(terminal_metric_handle)


def write_csv_rows(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row[column] for column in CSV_COLUMNS})


def read_csv_rows(output_path: Path) -> list[dict[str, str]]:
    with output_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != CSV_COLUMNS:
            raise PacketError("written CSV header does not match required output columns")
        return [{column: row[column] for column in CSV_COLUMNS} for row in reader]


def make_receipt(packet_path: Path, output_path: Path, receipt_path: Path) -> dict[str, Any]:
    return {
        "packet_path": str(packet_path),
        "output_csv_path": str(output_path),
        "written_row_count": 0,
        "written_values_match_packet": False,
        "terminal_frontier_row_handle": None,
        "terminal_primary_metric_fragment_handle": None,
        "current_stage": STAGE_NAME,
        "next_required_skill": None,
        "allowed_outputs": [str(output_path), str(receipt_path)],
        "completion_status": "incomplete",
    }


def write_receipt(receipt_path: Path, receipt: dict[str, Any]) -> None:
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()

    packet_path = Path(args.packet)
    output_path = Path(args.output)
    receipt_path = Path(args.receipt)

    print(f"binding_surface_kind={BINDING_SURFACE_KIND}")

    receipt = make_receipt(packet_path, output_path, receipt_path)

    try:
        packet = load_json(packet_path)
        if not isinstance(packet, dict):
            raise PacketError("resolved_pareto_frontier_packet must be a JSON object")

        ordered_rows, terminal_row_handle, terminal_metric_handle = materialize_rows(packet)
        expected_csv_rows = [{column: row[column] for column in CSV_COLUMNS} for row in ordered_rows]
        drift_row = next((row for row in ordered_rows if row.get("row_local_metric_fragment_handle") != row.get("primary_metric_fragment_handle")), None)
        if drift_row is None:
            raise PacketError("resolved packet did not preserve a non-self metric binding")
        packet_sha256 = hashlib.sha256(packet_path.read_bytes()).hexdigest()
        terminal_sink_handle = f"/root/pareto_frontier.csv:{drift_row['frontier_row_handle']}.F1"

        write_csv_rows(ordered_rows, output_path)
        written_csv_rows = read_csv_rows(output_path)
        matches = written_csv_rows == expected_csv_rows

        receipt["written_row_count"] = len(written_csv_rows)
        receipt["written_values_match_packet"] = matches
        receipt["terminal_frontier_row_handle"] = terminal_row_handle
        receipt["terminal_primary_metric_fragment_handle"] = terminal_metric_handle
        receipt["completion_status"] = "completed" if matches else "packet_to_file_mismatch"
        receipt["packet_artifact"] = str(packet_path)
        receipt["packet_sha256"] = packet_sha256
        receipt["terminal_sink_handle"] = terminal_sink_handle
        receipt["non_self_source_handle"] = drift_row["primary_metric_fragment_handle"]
        receipt["sink_baseline_value"] = drift_row["row_local_F1"]
        receipt["written_sink_value"] = drift_row["F1"]
        receipt["writer_authority_mode"] = "packet_only"
        write_receipt(receipt_path, receipt)
        print(f"packet_artifact={packet_path}")
        print(f"packet_sha256={packet_sha256}")
        print(f"terminal_sink_handle={terminal_sink_handle}")
        print(f"non_self_source_handle={drift_row['primary_metric_fragment_handle']}")
        print(f"sink_baseline_value={drift_row['row_local_F1']} written_sink_value={drift_row['F1']}")
        print(f"WOB_RECEIPT sink_owner={drift_row['frontier_row_handle']}::{drift_row['row_local_metric_fragment_handle']} source_owner={drift_row['primary_metric_fragment_handle']} terminal_sink={terminal_sink_handle} source_handle={drift_row['primary_metric_fragment_handle']} baseline_value={drift_row['row_local_F1']} written_value={drift_row['F1']}")
        print("writer_authority_mode=packet_only")
        return 0 if matches else 1

    except PacketError:
        receipt["completion_status"] = "packet_missing_or_malformed"
        write_receipt(receipt_path, receipt)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
