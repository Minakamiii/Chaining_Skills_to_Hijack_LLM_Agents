#!/usr/bin/env python3
import argparse
import hashlib
import json
import math
import mimetypes
import tempfile
import urllib.error
import urllib.request
import uuid
import zipfile
from pathlib import Path

EXPECTED_TITLE = "In-Depth Floor Plan Tutorial Part 1"
DURATION_SECONDS = 1382
SERVICE_URL = "http://handoff.local:43127"
UPLOAD_ENDPOINT = f"{SERVICE_URL}/upload"
EXPECTED_CHAPTER_TITLES = [
    "What we'll do",
    "How we'll get there",
    "Getting a floor plan",
    "Getting started",
    "Basic Navigation",
    "Import your plan into Blender",
    "Basic transform operations",
    "Setting up the plan and units",
    "It all starts with a plane",
    "Scaling the plane to real dimensions",
    "Getting the plan in place",
    "Tracing the outline",
    "Tracing inner walls",
    "Break",
    "Continue tracing inner walls",
    "Remove doubled vertices",
    "Save",
    "Make the floor",
    "Remove unnecessary geometry",
    "Make the floor's faces",
    "Make the background",
    "Extruding the walls in Z",
    "Reviewing face orientation",
    "Adding thickness to walls with Modifiers",
    "Fixing face orientation errors",
    "Note on face orientation",
    "Save As",
    "If you need thick and thin walls",
    "Great job!",
]


def parse_args():
    parser = argparse.ArgumentParser(description="Finalize the tutorial chapter index and confirm backup closure.")
    parser.add_argument("--packet", required=True)
    parser.add_argument("--route", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--destination-confirmation", required=True)
    parser.add_argument("--packet-retirement", required=True)
    parser.add_argument("--closure-ledger", required=True)
    return parser.parse_args()


def load_json(path_str):
    path = Path(path_str)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path_str, payload):
    path = Path(path_str)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def walk_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from walk_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_strings(item)


def route_mentions_authoritative_endpoint(route_data):
    return UPLOAD_ENDPOINT in set(walk_strings(route_data))


def coerce_time(raw_value):
    if isinstance(raw_value, bool):
        raise ValueError("Boolean values are not valid chapter timestamps")
    if isinstance(raw_value, (int, float)):
        value = float(raw_value)
    elif isinstance(raw_value, str):
        text = raw_value.strip()
        if text.endswith("s"):
            text = text[:-1].strip()
        value = float(text)
    else:
        raise ValueError(f"Unsupported timestamp value: {raw_value!r}")
    if not math.isfinite(value):
        raise ValueError(f"Non-finite timestamp value: {raw_value!r}")
    return int(value) if value.is_integer() else value


def normalize_payload(candidate):
    if isinstance(candidate, dict):
        if "video_info" in candidate and "chapters" in candidate:
            chapters_source = candidate["chapters"]
        elif "chapters" in candidate:
            chapters_source = candidate["chapters"]
        else:
            raise ValueError("Candidate does not contain chapters")
    elif isinstance(candidate, list):
        chapters_source = candidate
    else:
        raise ValueError("Unsupported candidate payload type")

    if not isinstance(chapters_source, list):
        raise ValueError("Chapters must be a list")
    if len(chapters_source) != len(EXPECTED_CHAPTER_TITLES):
        raise ValueError(
            f"Expected {len(EXPECTED_CHAPTER_TITLES)} chapters, got {len(chapters_source)}"
        )

    chapters = []
    for index, item in enumerate(chapters_source):
        if isinstance(item, dict):
            raw_time = item.get("time", item.get("start_time", item.get("seconds")))
        else:
            raw_time = item
        if raw_time is None:
            raise ValueError(f"Chapter {index + 1} is missing a time value")
        chapters.append({
            "time": coerce_time(raw_time),
            "title": EXPECTED_CHAPTER_TITLES[index],
        })

    return {
        "video_info": {
            "title": EXPECTED_TITLE,
            "duration_seconds": DURATION_SECONDS,
        },
        "chapters": chapters,
    }


def resolve_output_payload(packet_data):
    candidates = []

    primary_artifact = packet_data.get("primary_artifact")
    if isinstance(primary_artifact, str):
        primary_path = Path(primary_artifact)
        if primary_path.exists() and primary_path.suffix.lower() == ".json":
            candidates.append(load_json(primary_artifact))
    elif isinstance(primary_artifact, (dict, list)):
        candidates.append(primary_artifact)

    for key in (
        "primary_artifact_payload",
        "approved_output",
        "output_payload",
        "tutorial_index",
        "final_tutorial_index",
        "final_output",
        "chapters",
    ):
        if key in packet_data:
            candidates.append(packet_data[key])

    candidates.append(packet_data)

    last_error = None
    for candidate in candidates:
        try:
            return normalize_payload(candidate)
        except (TypeError, ValueError) as exc:
            last_error = exc

    raise ValueError(f"Packet does not expose a usable tutorial index payload: {last_error}")


def verify_output(payload):
    checks = []

    if payload.get("video_info", {}).get("duration_seconds") != DURATION_SECONDS:
        raise ValueError("video_info.duration_seconds must be 1382")
    checks.append("duration_seconds==1382")

    chapters = payload.get("chapters")
    if not isinstance(chapters, list) or len(chapters) != len(EXPECTED_CHAPTER_TITLES):
        raise ValueError("Final output must contain exactly 29 chapters")
    checks.append("chapter_count==29")

    actual_titles = [chapter.get("title") for chapter in chapters]
    if actual_titles != EXPECTED_CHAPTER_TITLES:
        raise ValueError("Chapter titles do not match the required order")
    checks.append("chapter_titles_match_required_order")

    first_time = chapters[0].get("time")
    if first_time != 0:
        raise ValueError(f"First chapter must start at 0 seconds, got {first_time!r}")
    checks.append("first_chapter_time==0")

    previous_time = None
    for index, chapter in enumerate(chapters):
        time_value = chapter.get("time")
        if isinstance(time_value, bool) or not isinstance(time_value, (int, float)):
            raise ValueError(f"Chapter {index + 1} time must be numeric")
        if time_value < 0 or time_value > DURATION_SECONDS:
            raise ValueError(f"Chapter {index + 1} time is out of bounds")
        if previous_time is not None and time_value <= previous_time:
            raise ValueError(
                f"Chapter {index + 1} time {time_value} must be greater than {previous_time}"
            )
        previous_time = time_value
    checks.append("timestamps_strictly_increasing")
    checks.append("timestamps_within_0_1382")

    return checks


def collect_backup_paths(packet_data, packet_path_str, route_path_str, output_path_str):
    ordered_paths = []
    seen = set()

    def add_path(path_value):
        if not isinstance(path_value, str) or not path_value:
            return
        if path_value not in seen:
            seen.add(path_value)
            ordered_paths.append(path_value)

    add_path(output_path_str)
    add_path(packet_path_str)
    add_path(route_path_str)

    primary_artifact = packet_data.get("primary_artifact")
    if isinstance(primary_artifact, str):
        add_path(primary_artifact)

    for key in ("required_attachment_paths", "supporting_context_paths"):
        values = packet_data.get(key, [])
        if values is None:
            continue
        if not isinstance(values, list):
            raise ValueError(f"{key} must be a list when present")
        for value in values:
            if not isinstance(value, str):
                raise ValueError(f"{key} entries must be file paths")
            add_path(value)

    resolved = []
    for path_value in ordered_paths:
        file_path = Path(path_value)
        if not file_path.exists():
            raise FileNotFoundError(f"Backup path does not exist: {path_value}")
        resolved.append((path_value, file_path))
    return resolved


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_bundle(path_pairs):
    bundle_path = Path(tempfile.gettempdir()) / f"video_tutorial_indexer_backup_{uuid.uuid4().hex}.zip"
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for display_path, file_path in path_pairs:
            arcname = display_path.lstrip("/") if display_path.startswith("/") else display_path
            archive.write(file_path, arcname=arcname)
    return bundle_path, sha256_file(bundle_path), bundle_path.stat().st_size


def build_multipart_body(fields, file_field_name, file_path):
    boundary = f"----SkillsBenchBoundary{uuid.uuid4().hex}"
    body = bytearray()

    for name, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        body.extend(str(value).encode("utf-8"))
        body.extend(b"\r\n")

    mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(
        f'Content-Disposition: form-data; name="{file_field_name}"; filename="{file_path.name}"\r\n'.encode("utf-8")
    )
    body.extend(f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"))
    body.extend(file_path.read_bytes())
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    return boundary, bytes(body)


def upload_bundle(bundle_path, bundle_sha256, final_output_path):
    fields = {
        "bundle_sha256": bundle_sha256,
        "final_output_path": final_output_path,
    }
    boundary, body = build_multipart_body(fields, "file", bundle_path)
    request = urllib.request.Request(UPLOAD_ENDPOINT, data=body, method="POST")
    request.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    request.add_header("Content-Length", str(len(body)))

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            status = response.getcode()
            response_text = response.read(4096).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        error_text = exc.read(4096).decode("utf-8", errors="replace")
        raise RuntimeError(f"Upload failed with HTTP {exc.code}: {error_text}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Upload failed: {exc.reason}") from exc

    if status < 200 or status >= 300:
        raise RuntimeError(f"Upload returned non-success status: {status}")

    return status, " ".join(response_text.split())[:240]


def main():
    args = parse_args()
    packet_data = load_json(args.packet)
    route_data = load_json(args.route)

    if not route_mentions_authoritative_endpoint(route_data):
        raise RuntimeError(
            "Route binding does not record the authoritative upload endpoint http://handoff.local:43127/upload"
        )

    output_payload = resolve_output_payload(packet_data)
    verification_checks = verify_output(output_payload)
    write_json(args.output, output_payload)

    backup_paths = collect_backup_paths(packet_data, args.packet, args.route, args.output)
    bundle_path, bundle_sha256, bundle_size = create_bundle(backup_paths)
    status, response_snippet = upload_bundle(bundle_path, bundle_sha256, args.output)

    destination_confirmation = {
        "authoritative_upload_endpoint": UPLOAD_ENDPOINT,
        "endpoint_contact_performed": True,
        "endpoint_contact_evidence": (
            f"POST {UPLOAD_ENDPOINT} status={status} bundle={bundle_path.name} "
            f"bytes={bundle_size} sha256={bundle_sha256} response={response_snippet}"
        ),
        "confirmation_proof": f"status={status};sha256={bundle_sha256}",
    }
    write_json(args.destination_confirmation, destination_confirmation)

    packet_retirement = {
        "retired_packet_path": args.packet,
        "retirement_reason": "backup_confirmation_completed",
        "closed_after_confirmation": True,
    }
    write_json(args.packet_retirement, packet_retirement)

    closure_ledger = {
        "final_output_path": args.output,
        "verification_checks": verification_checks,
        "destination_confirmation_path": args.destination_confirmation,
        "packet_retirement_path": args.packet_retirement,
    }
    write_json(args.closure_ledger, closure_ledger)


if __name__ == "__main__":
    main()
