#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

WRITER_AUTHORITY_MODE = "packet_only"
REQUIRED_ANSWER_KEYS = ["q1_answer", "q2_answer", "q3_answer", "q4_answer"]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure(condition, message):
    if not condition:
        raise SystemExit(message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()

    packet_path = Path(args.packet)
    output_path = Path(args.output)
    receipt_path = Path(args.receipt)

    packet = load_json(packet_path)
    answers_payload = packet.get("answers_payload")
    ensure(isinstance(answers_payload, dict), "packet missing answers_payload")
    ensure(sorted(answers_payload.keys()) == sorted(REQUIRED_ANSWER_KEYS), "answers_payload keys mismatch")

    canonical_packet_artifact = "artifacts/sec-financial-report/resolved_answers_packet.json"
    accepted_packet_artifacts = {canonical_packet_artifact, str(packet_path), str(packet_path.resolve())}
    ensure(packet.get("packet_artifact") in accepted_packet_artifacts, "packet_artifact mismatch")
    ensure(packet.get("writer_allowed_non_packet_inputs") == [canonical_packet_artifact], "writer_allowed_non_packet_inputs mismatch")

    receipt_keys = packet.get("writer_receipt_required_keys")
    ensure(isinstance(receipt_keys, list) and receipt_keys, "writer_receipt_required_keys missing")

    terminal_sink_handle = packet.get("terminal_sink_handle")
    non_self_source_handle = packet.get("non_self_source_handle")
    ensure(isinstance(terminal_sink_handle, str) and terminal_sink_handle, "terminal_sink_handle missing")
    ensure(isinstance(non_self_source_handle, str) and non_self_source_handle, "non_self_source_handle missing")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(answers_payload, fh, indent=2)
        fh.write("\n")

    packet_sha256 = sha256_file(packet_path)
    written_sink_value = answers_payload["q2_answer"]

    receipt = {
        "packet_artifact": str(packet_path),
        "packet_sha256": packet_sha256,
        "terminal_sink_handle": terminal_sink_handle,
        "non_self_source_handle": non_self_source_handle,
        "written_sink_value": written_sink_value,
        "completion_status": "answers_json_written",
        "writer_authority_mode": WRITER_AUTHORITY_MODE,
    }

    missing = [key for key in receipt_keys if key not in receipt]
    ensure(not missing, "receipt missing required keys: " + ", ".join(missing))

    with receipt_path.open("w", encoding="utf-8") as fh:
        json.dump(receipt, fh, indent=2)
        fh.write("\n")


if __name__ == "__main__":
    main()
