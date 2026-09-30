#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path


TREND_HEADER = ["slope", "p-value"]
DOMINANT_HEADER = ["variable", "contribution"]


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_parent(path_str):
    Path(path_str).parent.mkdir(parents=True, exist_ok=True)


def first_present(mapping, keys):
    for key in keys:
        if key in mapping:
            return mapping[key]
    raise KeyError(f"Missing required key from candidates: {keys}")


def coerce_single_row(packet_value, required_header):
    if isinstance(packet_value, list):
        if len(packet_value) != 1 or not isinstance(packet_value[0], dict):
            raise ValueError("Expected a single-row list of objects")
        row = packet_value[0]
    elif isinstance(packet_value, dict):
        if "rows" in packet_value:
            rows = packet_value["rows"]
            if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
                raise ValueError("Expected packet rows to contain exactly one object")
            row = rows[0]
        elif all(col in packet_value for col in required_header):
            row = packet_value
        elif "row" in packet_value and isinstance(packet_value["row"], dict):
            row = packet_value["row"]
        else:
            raise ValueError("Could not locate a single output row in packet value")
    else:
        raise ValueError("Unsupported packet row container")

    normalized = {}
    for col in required_header:
        if col not in row:
            raise KeyError(f"Missing required column '{col}' in packet row")
        normalized[col] = row[col]
    return normalized


def packet_handle(packet_value, fallback):
    if isinstance(packet_value, dict):
        for key in ("terminal_sink_handle", "sink_handle", "output_handle"):
            if key in packet_value:
                return packet_value[key]
    return fallback


def source_fragment_handle(packet_value, row, fallback):
    if isinstance(packet_value, dict):
        for key in ("source_fragment_handle", "copied_from_fragment_handle", "row_local_fragment_handle"):
            if key in packet_value:
                return packet_value[key]
        nested = packet_value.get("provenance")
        if isinstance(nested, dict):
            for key in ("source_fragment_handle", "copied_from_fragment_handle", "row_local_fragment_handle"):
                if key in nested:
                    return nested[key]
    if isinstance(row, dict):
        for key in ("source_fragment_handle", "copied_from_fragment_handle", "row_local_fragment_handle"):
            if key in row:
                return row[key]
    return fallback


def write_csv(path_str, header, row):
    ensure_parent(path_str)
    with open(path_str, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerow({key: row[key] for key in header})


def verify_header(path_str, expected_header):
    with open(path_str, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
    if header != expected_header:
        raise ValueError(f"Header mismatch for {path_str}: expected {expected_header}, got {header}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", required=True)
    parser.add_argument("--trend-out", required=True)
    parser.add_argument("--dominant-out", required=True)
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()

    packet = load_json(args.packet)

    trend_packet = first_present(packet, ["trend_result_packet", "trend_packet", "trend_result"])
    dominant_packet = first_present(packet, ["dominant_factor_packet", "dominant_packet", "dominant_factor"])

    trend_row = coerce_single_row(trend_packet, TREND_HEADER)
    dominant_row = coerce_single_row(dominant_packet, DOMINANT_HEADER)

    write_csv(args.trend_out, TREND_HEADER, trend_row)
    write_csv(args.dominant_out, DOMINANT_HEADER, dominant_row)

    verify_header(args.trend_out, TREND_HEADER)
    verify_header(args.dominant_out, DOMINANT_HEADER)

    trend_sink_handle = packet_handle(trend_packet, "trend_result.csv")
    dominant_sink_handle = packet_handle(dominant_packet, "dominant_factor.csv")
    dominant_source_handle = source_fragment_handle(dominant_packet, dominant_row, "dominant_factor_packet")
    trend_source_handle = source_fragment_handle(trend_packet, trend_row, "trend_result_packet")

    receipt = {
        "written_outputs": [
            {
                "output_file": args.trend_out,
                "row_count": 1,
                "source_packet_key": "trend_result_packet",
            },
            {
                "output_file": args.dominant_out,
                "row_count": 1,
                "source_packet_key": "dominant_factor_packet",
            },
        ],
        "packet_path": args.packet,
        "terminal_sink_handles": [trend_sink_handle, dominant_sink_handle],
        "written_values": [
            {
                "output_file": args.trend_out,
                "terminal_sink_handle": trend_sink_handle,
                "source_fragment_handle": trend_source_handle,
                "row": trend_row,
            },
            {
                "output_file": args.dominant_out,
                "terminal_sink_handle": dominant_sink_handle,
                "source_fragment_handle": dominant_source_handle,
                "row": dominant_row,
            },
        ],
        "workflow_status": {
            "current_stage": "lake-warming-attribution-csv-finalizer",
            "next_required_skill": None,
            "allowed_outputs": [
                "/root/output/trend_result.csv",
                "/root/output/dominant_factor.csv",
                "artifacts/lake_warming_write_receipt.json",
            ],
            "status": "completed",
        },
    }

    ensure_parent(args.receipt)
    with open(args.receipt, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2, ensure_ascii=True)


if __name__ == "__main__":
    main()
