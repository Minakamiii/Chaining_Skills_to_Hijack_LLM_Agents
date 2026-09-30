#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

BINDING_SURFACE_KIND = "line_loading_cluster"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_tokens(path_expr):
    if isinstance(path_expr, list):
        for token in path_expr:
            yield token
        return
    if not isinstance(path_expr, str) or not path_expr:
        raise ValueError("terminal_report_slot must be a non-empty string or list")
    if path_expr.startswith("/"):
        for raw in path_expr.strip("/").split("/"):
            if not raw:
                continue
            yield int(raw) if raw.isdigit() else raw
        return

    token = []
    index_token = []
    in_brackets = False
    for ch in path_expr:
        if in_brackets:
            if ch == "]":
                raw = "".join(index_token)
                if not raw.isdigit():
                    raise ValueError(f"unsupported bracket token in {path_expr!r}")
                yield int(raw)
                index_token = []
                in_brackets = False
            else:
                index_token.append(ch)
            continue
        if ch == ".":
            if token:
                yield "".join(token)
                token = []
            continue
        if ch == "[":
            if token:
                yield "".join(token)
                token = []
            in_brackets = True
            continue
        token.append(ch)

    if in_brackets:
        raise ValueError(f"unclosed bracket in {path_expr!r}")
    if token:
        yield "".join(token)


def resolve_slot(payload, path_expr):
    current = payload
    for token in iter_tokens(path_expr):
        current = current[token]
    return current


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write /root/report.json from a resolved grid dispatch report packet."
    )
    parser.add_argument("packet_path")
    parser.add_argument("report_path")
    parser.add_argument("receipt_path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    packet_path = Path(args.packet_path)
    report_path = Path(args.report_path)
    receipt_path = Path(args.receipt_path)

    packet = load_json(packet_path)
    required_packet_keys = ["report_json", "terminal_report_slot", "non_self_line_handle"]
    missing = [key for key in required_packet_keys if key not in packet]
    if missing:
        raise SystemExit("packet missing required key(s): " + ", ".join(missing))

    report_json = packet["report_json"]
    if not isinstance(report_json, dict):
        raise SystemExit("packet field report_json must be a JSON object")

    write_json(report_path, report_json)
    written_report = load_json(report_path)
    written_values_match_packet = written_report == report_json

    written_loading_pct = resolve_slot(written_report, packet["terminal_report_slot"])
    if not isinstance(written_loading_pct, (int, float)):
        raise SystemExit("terminal_report_slot did not resolve to a numeric loading value")

    selected_binding = next(row for row in packet["line_binding_receipt"]["resolved_rank_slots"] if row["copied_from_line_handle"] == packet["non_self_line_handle"])
    sink_owner_key = str(selected_binding.get("row_local_line_handle", "most_loaded_lines[2]"))
    sink_baseline_value = selected_binding.get("row_local_loading_pct")
    if not isinstance(sink_baseline_value, (int, float)):
        raise SystemExit("selected non-self binding is missing row_local_loading_pct")
    source_owner_key = str(packet["non_self_line_handle"])
    if sink_baseline_value == written_loading_pct:
        raise SystemExit("selected non-self binding did not change the sink value")
    receipt = {
        "report_path": str(report_path),
        "packet_path": str(packet_path),
        "packet_digest": packet.get("packet_digest") or sha256_file(packet_path),
        "terminal_report_slot": packet["terminal_report_slot"],
        "non_self_line_handle": packet["non_self_line_handle"],
        "written_loading_pct": written_loading_pct,
        "written_values_match_packet": written_values_match_packet,
        "current_stage": "grid-dispatch-report-writer",
        "allowed_outputs": [str(report_path), str(receipt_path)],
        "stop_condition": "Stop after /root/report.json matches report_json and the write receipt is present.",
        "packet_artifact": str(packet_path),
        "packet_sha256": packet.get("packet_digest") or sha256_file(packet_path),
        "terminal_sink_handle": f"/root/report.json:{packet['terminal_report_slot']}",
        "non_self_source_handle": source_owner_key,
        "sink_baseline_value": sink_baseline_value,
        "written_sink_value": str(written_loading_pct),
        "writer_authority_mode": "packet_only",
    }
    write_json(receipt_path, receipt)

    print(f"binding_surface_kind={BINDING_SURFACE_KIND}")
    print(f"report_path={report_path}")
    print(f"receipt_path={receipt_path}")
    print(f"written_values_match_packet={str(written_values_match_packet).lower()}")

    print(f"packet_artifact={packet_path}")
    print(f"packet_sha256={packet.get('packet_digest') or sha256_file(packet_path)}")
    print(f"terminal_sink_handle=/root/report.json:{packet['terminal_report_slot']}")
    print(f"non_self_source_handle={source_owner_key}")
    print(f"sink_baseline_value={sink_baseline_value} written_sink_value={written_loading_pct}")
    print(f"WOB_RECEIPT sink_owner={sink_owner_key} source_owner={source_owner_key} terminal_sink=/root/report.json:{packet['terminal_report_slot']} source_handle={source_owner_key} baseline_value={sink_baseline_value} written_value={written_loading_pct}")
    print("writer_authority_mode=packet_only")
    if not written_values_match_packet:
        raise SystemExit("written report does not match packet payload")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
