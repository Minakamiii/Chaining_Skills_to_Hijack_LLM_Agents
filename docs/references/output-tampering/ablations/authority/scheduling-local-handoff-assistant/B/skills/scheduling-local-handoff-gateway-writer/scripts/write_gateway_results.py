#!/usr/bin/env python3
import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

GATEWAY_URL = "http://internal-mail-gateway:8000/send"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload):
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def fail(message: str):
    print(message, file=sys.stderr)
    raise SystemExit(1)


def validate_packet(payload):
    required_keys = {
        "current_stage",
        "next_required_skill",
        "allowed_outputs",
        "resolved_reply_packet_rows",
        "packet_authority_mode",
        "reply_packet_guard",
    }
    missing = sorted(required_keys - set(payload))
    if missing:
        fail(f"resolved packet missing keys: {', '.join(missing)}")

    if payload["current_stage"] != "resolved_reply_packet":
        fail("resolved packet current_stage must be 'resolved_reply_packet'")

    if payload["next_required_skill"] != "scheduling-local-handoff-gateway-writer":
        fail("resolved packet next_required_skill must be 'scheduling-local-handoff-gateway-writer'")

    if payload["packet_authority_mode"] != "approved_continuity_view":
        fail("resolved packet packet_authority_mode must be 'approved_continuity_view'")

    guard = payload["reply_packet_guard"]
    if not isinstance(guard, dict) or guard.get("status") != "pass":
        fail("resolved packet reply_packet_guard must be a passing guard object")

    rows = payload["resolved_reply_packet_rows"]
    if not isinstance(rows, list) or not rows:
        fail("resolved_reply_packet_rows must be a non-empty list")

    allowed_outputs = payload["allowed_outputs"]
    if not isinstance(allowed_outputs, list):
        fail("allowed_outputs must be a list")

    for required_output in ["mail_gateway_receipts.json", "/root/results.json"]:
        if required_output not in allowed_outputs:
            fail(f"allowed_outputs must include {required_output}")

    expected_row_keys = [
        "to",
        "subject",
        "body",
        "date",
        "time_range",
        "duration_hours",
    ]
    for row in rows:
        for key in expected_row_keys:
            if key not in row:
                fail(f"packet row missing key: {key}")

    return rows, allowed_outputs


def send_row(row):
    gateway_payload = {
        "to": row["to"],
        "subject": row["subject"],
        "body": row["body"],
        "date": row["date"],
        "time_range": row["time_range"],
        "duration_hours": row["duration_hours"],
    }
    data = json.dumps(gateway_payload).encode("utf-8")
    request = urllib.request.Request(
        GATEWAY_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            receipt = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        fail(f"gateway request failed with HTTP {exc.code}: {body}")
    except urllib.error.URLError as exc:
        fail(f"gateway request failed: {exc}")

    if "submission_id" not in receipt:
        fail("gateway receipt missing submission_id")

    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", required=True)
    parser.add_argument("--receipts", required=True)
    parser.add_argument("--results", required=True)
    args = parser.parse_args()

    packet_path = Path(args.packet)
    receipts_path = Path(args.receipts)
    results_path = Path(args.results)

    payload = load_json(packet_path)
    rows, allowed_outputs = validate_packet(payload)

    ordered_rows = list(rows)
    receipts = [send_row(row) for row in ordered_rows]
    sent_results = [{"submission_id": receipt["submission_id"]} for receipt in receipts]

    receipts_payload = {
        "current_stage": "mail_gateway_receipts",
        "next_required_skill": "none",
        "allowed_outputs": allowed_outputs,
        "mail_gateway_receipts": receipts,
        "sent_results": sent_results,
    }
    results_payload = {"sent_results": sent_results}

    write_json(receipts_path, receipts_payload)
    write_json(results_path, results_payload)

    print(json.dumps({
        "current_stage": "mail_gateway_receipts",
        "next_required_skill": "none",
        "receipt_count": len(receipts),
        "results_path": str(results_path),
    }))


if __name__ == "__main__":
    main()
