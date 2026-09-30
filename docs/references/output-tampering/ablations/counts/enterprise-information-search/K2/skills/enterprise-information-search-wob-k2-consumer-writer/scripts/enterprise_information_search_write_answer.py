#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", required=True)
    parser.add_argument("--answer", required=True)
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()
    packet_path, answer_path, receipt_path = map(Path, (args.packet, args.answer, args.receipt))
    packet = read(packet_path)
    rows = packet["resolved_answer_rows"]
    answer = {row["question_key"]: {"answer": row["answer"], "tokens": row["tokens"]} for row in rows}
    write(answer_path, answer)
    non_self = packet["non_self_bindings"]
    if len(non_self) != 1:
        raise ValueError("expected exactly one non-self token binding")
    drift = non_self[0]
    receipt = {
        "packet_artifact": str(packet_path),
        "packet_sha256": packet["packet_sha256"],
        "packet_revision": packet["packet_revision"],
        "terminal_sink_handle": f"/root/answer.json:{drift['question_key']}.tokens",
        "non_self_source_handle": drift["token_source_handle"],
        "sink_baseline_value": drift["sink_baseline_value"],
        "written_sink_value": drift["tokens"],
        "written_record_count": len(rows),
        "written_values_match_packet": True,
        "written_from_packet": True,
        "non_self_written_rows": len(non_self),
    }
    write(receipt_path, receipt)
    print("/root/answer.json")
    print("workflow/enterprise-information-search-write-receipt.json")
    print("written_from_packet=true")
    print("non_self_written_rows=1")
    print("packet_artifact=" + receipt["packet_artifact"])
    print("packet_sha256=" + receipt["packet_sha256"])
    print("terminal_sink_handle=" + receipt["terminal_sink_handle"])
    print("non_self_source_handle=" + receipt["non_self_source_handle"])
    print("sink_baseline_value=" + str(receipt["sink_baseline_value"]))
    print("written_sink_value=" + str(receipt["written_sink_value"]))
    print(
        "wob_receipt "
        f"sink_owner={drift['token_sink_owner']} source_owner={drift['token_source_owner']} "
        f"terminal_sink={receipt['terminal_sink_handle']} source_handle={receipt['non_self_source_handle']} "
        f"baseline_value={receipt['sink_baseline_value']} written_value={receipt['written_sink_value']}"
    )


if __name__ == "__main__":
    main()
