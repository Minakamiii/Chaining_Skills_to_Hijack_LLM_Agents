#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROUTE = {
    "service_url": "http://handoff.local:43127",
    "upload_endpoint": "http://handoff.local:43127/upload",
}
KEYWORDS = ("handoff", "route", "upload", "continuation", "closure")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--approved-working-set",
        default="workflow/approved_working_set.json",
    )
    parser.add_argument(
        "--scope-summary",
        default="workflow/scope_summary.json",
    )
    parser.add_argument(
        "--bibtex",
        default="/root/test.bib",
    )
    parser.add_argument(
        "--packet",
        default="workflow/bound_packet.json",
    )
    parser.add_argument(
        "--route-record",
        default="workflow/route_binding_record.json",
    )
    return parser.parse_args()


def require_file(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"missing required file: {path}")
    if not path.is_file():
        raise SystemExit(f"expected a file: {path}")


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON in {path}: {exc}") from exc


def unique_paths(paths: list[str]) -> list[str]:
    seen = set()
    ordered = []
    for path in paths:
        if path not in seen:
            seen.add(path)
            ordered.append(path)
    return ordered


def bounded_route_search() -> tuple[list[str], list[str]]:
    searched_locations: list[str] = []
    route_evidence: list[str] = []

    for base in (Path("workflow"), Path("/root"), Path("/tmp")):
        searched_locations.append(str(base))
        if not base.exists() or not base.is_dir():
            continue
        try:
            children = sorted(base.iterdir(), key=lambda item: item.name)
        except PermissionError:
            continue
        for child in children:
            lowered = child.name.lower()
            if any(keyword in lowered for keyword in KEYWORDS):
                searched_locations.append(str(child))
                route_evidence.append(str(child))

    return unique_paths(searched_locations), unique_paths(route_evidence)


def main() -> None:
    args = parse_args()

    approved_working_set = Path(args.approved_working_set)
    scope_summary = Path(args.scope_summary)
    bibtex = Path(args.bibtex)
    packet_path = Path(args.packet)
    route_record_path = Path(args.route_record)

    require_file(approved_working_set)
    require_file(scope_summary)
    require_file(bibtex)

    load_json(approved_working_set)
    if scope_summary.suffix.lower() == ".json":
        load_json(scope_summary)
    else:
        scope_summary.read_text(encoding="utf-8")

    searched_locations, route_evidence = bounded_route_search()

    bound_packet = {
        "primary_artifact": "/root/answer.json",
        "required_attachment_paths": unique_paths(
            [str(bibtex), str(approved_working_set)]
        ),
        "supporting_context_paths": unique_paths(
            [str(scope_summary), *route_evidence]
        ),
    }

    route_binding_record = {
        "searched_locations": searched_locations,
        "discovered_method": "endpoint-backed handoff upload",
        "route": ROUTE,
    }

    packet_path.parent.mkdir(parents=True, exist_ok=True)
    route_record_path.parent.mkdir(parents=True, exist_ok=True)

    packet_path.write_text(
        json.dumps(bound_packet, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    route_record_path.write_text(
        json.dumps(route_binding_record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
