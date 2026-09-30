#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

INPUT_KEYS = [
    "current_stage",
    "next_required_skill",
    "allowed_outputs",
    "approved_reply_fragment_rows",
    "binding_policy",
    "slot_fragment_catalog",
    "delivery_fragment_catalog",
]

OUTPUT_KEYS = [
    "current_stage",
    "next_required_skill",
    "allowed_outputs",
    "resolved_reply_packet_rows",
    "binding_provenance",
    "packet_authority_mode",
    "reply_packet_guard",
]

BODY_TEMPLATE = (
    "Hi,\n\n"
    "Thank you for your meeting request.\n\n"
    "I can be available:\n\n"
    "Date: {date}\n"
    "Time: {time_range}\n"
    "Duration: {duration_text} hour(s)\n\n"
    "If this time doesn't work, please let me know your preferred alternatives.\n\n"
    "Best regards,\n"
    "SkillsBench"
)


def fail(message):
    raise SystemExit(message)


def load_json(path):
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        fail(f"missing artifact: {path}")
    except json.JSONDecodeError as exc:
        fail(f"invalid json in {path}: {exc}")


def require_keys(data, keys, label):
    missing = [key for key in keys if key not in data]
    if missing:
        fail(f"{label} missing keys: {', '.join(missing)}")


def records(container, label):
    if not isinstance(container, list) or not container:
        fail(f"{label} must be a non-empty list")
    rows = []
    for row in container:
        if not isinstance(row, dict):
            fail(f"{label} rows must be objects")
        rows.append(dict(row))
    return rows


def fragment_catalog(container, label):
    if isinstance(container, dict):
        return container
    if isinstance(container, list):
        catalog = {}
        for row in container:
            if not isinstance(row, dict):
                fail(f"{label} entries must be objects")
            handle = row.get("fragment_handle")
            if not handle:
                fail(f"{label} entries need fragment_handle")
            if handle in catalog:
                fail(f"duplicate fragment handle in {label}: {handle}")
            catalog[handle] = row
        return catalog
    fail(f"{label} must be an object or list")


def duration_text(slot_fragment):
    value = slot_fragment.get("duration_hours_text")
    if value not in (None, ""):
        return str(value)
    value = slot_fragment.get("duration_hours")
    if value is None:
        fail(f"slot fragment missing duration_hours: {slot_fragment}")
    if isinstance(value, int):
        return f"{value}.0"
    return str(value)


def delivery_value(delivery_fragment):
    value = delivery_fragment.get("channel_value")
    if value:
        return str(value)
    fail(f"delivery fragment missing channel_value: {delivery_fragment}")


def body_text(slot_fragment):
    require_keys(slot_fragment, ["date", "time_range", "duration_hours"], "slot fragment")
    rendered_duration = duration_text(slot_fragment)
    body = BODY_TEMPLATE.format(
        date=str(slot_fragment["date"]),
        time_range=str(slot_fragment["time_range"]),
        duration_text=rendered_duration,
    )
    return body, rendered_duration


def build_packet(note, artifact_name):
    require_keys(note, INPUT_KEYS, artifact_name)

    if note.get("next_required_skill") != "scheduling-local-handoff-reply-packet-binder":
        fail("approved slot binding note is not ready for scheduling-local-handoff-reply-packet-binder")

    if (note.get("binding_policy") or {}).get("view") != "approved_continuity_view":
        fail("binding_policy.view must equal approved_continuity_view")

    approved_rows = records(note["approved_reply_fragment_rows"], "approved_reply_fragment_rows")
    slot_catalog = fragment_catalog(note["slot_fragment_catalog"], "slot_fragment_catalog")
    delivery_catalog = fragment_catalog(note["delivery_fragment_catalog"], "delivery_fragment_catalog")

    packet_rows = []
    provenance = []

    for row_index, approved_row in enumerate(approved_rows):
        slot_handle = approved_row.get("slot_fragment_handle")
        delivery_handle = approved_row.get("delivery_fragment_handle")
        if not slot_handle:
            fail("approved row missing slot_fragment_handle")
        if not delivery_handle:
            fail("approved row missing delivery_fragment_handle")

        slot_fragment = slot_catalog.get(slot_handle)
        delivery_fragment = delivery_catalog.get(delivery_handle)
        if slot_fragment is None:
            fail(f"slot_fragment_catalog missing fragment {slot_handle}")
        if delivery_fragment is None:
            fail(f"delivery_fragment_catalog missing fragment {delivery_handle}")

        body, rendered_duration = body_text(slot_fragment)
        packet_rows.append(
            {
                "to": delivery_value(delivery_fragment),
                "subject": approved_row.get("reply_subject") or "Re: Meeting Request",
                "date": str(slot_fragment["date"]),
                "time_range": str(slot_fragment["time_range"]),
                "duration_hours": slot_fragment["duration_hours"],
                "duration_hours_text": rendered_duration,
                "body": body,
            }
        )
        provenance.append(
            {
                "packet_row_index": row_index,
                "row_handle": approved_row.get("row_handle", f"reply-row-{row_index + 1}"),
                "slot_fragment_handle": slot_handle,
                "delivery_fragment_handle": delivery_handle,
            }
        )

    guard = {
        "status": "pass",
        "binding_artifact": artifact_name,
        "consumed_keys": INPUT_KEYS,
        "packet_row_count": len(packet_rows),
        "packet_write_count_match": len(packet_rows) == len(approved_rows),
        "body_template_verified": all(
            row["body"].startswith("Hi,\n\nThank you for your meeting request.\n\nI can be available:\n\n")
            and row["body"].endswith("Best regards,\nSkillsBench")
            for row in packet_rows
        ),
        "packet_fields_from_note": True,
    }
    if not all([
        guard["packet_write_count_match"],
        guard["body_template_verified"],
    ]):
        guard["status"] = "fail"

    return packet_rows, provenance, guard


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    artifact_path = Path(args.artifact)
    output_path = Path(args.output)

    note = load_json(artifact_path)
    packet_rows, provenance, guard = build_packet(note, artifact_path.name)

    document = {
        "current_stage": "resolved_reply_packet",
        "next_required_skill": "scheduling-local-handoff-gateway-writer",
        "allowed_outputs": ["mail_gateway_receipts.json", "/root/results.json"],
        "resolved_reply_packet_rows": packet_rows,
        "binding_provenance": provenance,
        "packet_authority_mode": "approved_continuity_view",
        "reply_packet_guard": guard,
    }
    require_keys(document, OUTPUT_KEYS, "resolved reply packet")

    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2)
        handle.write("\n")

    preview_row = packet_rows[0]
    print(
        json.dumps(
            {
                "output_path": str(output_path),
                "current_stage": document["current_stage"],
                "next_required_skill": document["next_required_skill"],
                "packet_row_count": len(packet_rows),
                "sample_body_lines": [
                    f"Time: {preview_row['time_range']}",
                    f"Duration: {preview_row['duration_hours_text']} hour(s)",
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
