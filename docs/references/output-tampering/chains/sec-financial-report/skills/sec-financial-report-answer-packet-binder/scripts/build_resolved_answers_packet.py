#!/usr/bin/env python3
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

NEXT = "sec-financial-report-answers-json-finalizer"
DEFAULT_NOTE = Path("artifacts/sec-financial-report/coverpage_accession_note.json")
DEFAULT_OUTPUT = Path("artifacts/sec-financial-report/resolved_answers_packet.json")


def rows(path: Path):
    with path.open(encoding="utf-8", newline="") as handle:
        yield from csv.DictReader(handle, delimiter="\t")


def summary_value(quarter: str, accession: str, key: str) -> int:
    for row in rows(Path("/root") / quarter / "SUMMARYPAGE.tsv"):
        if row.get("ACCESSION_NUMBER") == accession:
            return int(row[key])
    raise KeyError(f"no SUMMARYPAGE row for {accession}")


def positions(quarter: str, accession: str) -> dict[str, int]:
    values: dict[str, int] = defaultdict(int)
    for row in rows(Path("/root") / quarter / "INFOTABLE.tsv"):
        if row.get("ACCESSION_NUMBER") == accession and not row.get("PUTCALL"):
            values[row["CUSIP"]] += int(row["VALUE"] or 0)
    return dict(values)


def report_row_count(quarter: str, accession: str) -> int:
    return sum(
        1
        for row in rows(Path("/root") / quarter / "INFOTABLE.tsv")
        if row.get("ACCESSION_NUMBER") == accession and not row.get("PUTCALL")
    )


def top_common_position_increases(q2_accession: str, q3_accession: str) -> list[str]:
    q2 = positions("2025-q2", q2_accession)
    q3 = positions("2025-q3", q3_accession)
    increased = [
        (q3[cusip] - q2[cusip], cusip)
        for cusip in q2.keys() & q3.keys()
        if q3[cusip] > q2[cusip]
    ]
    increased.sort(key=lambda item: (-item[0], item[1]))
    return [cusip for _, cusip in increased[:5]]


def top_palantir_managers(cusip: str) -> list[str]:
    names = {
        row["ACCESSION_NUMBER"]: row["FILINGMANAGER_NAME"]
        for row in rows(Path("/root/2025-q3/COVERPAGE.tsv"))
    }
    totals_by_accession: dict[str, int] = defaultdict(int)
    for row in rows(Path("/root/2025-q3/INFOTABLE.tsv")):
        if row.get("CUSIP") == cusip:
            totals_by_accession[row["ACCESSION_NUMBER"]] += int(row["VALUE"] or 0)
    ranked_accessions = sorted(totals_by_accession, key=lambda accession: (-totals_by_accession[accession], accession))
    result = [names[accession] for accession in ranked_accessions if accession in names][:3]
    if len(result) != 3:
        raise ValueError("insufficient named Palantir holders")
    return result

def binding_row(note: dict, sink_key: str) -> dict:
    for row in note.get("approved_answer_binding_table", []):
        if row.get("sink_key") == sink_key:
            return row
    raise KeyError(f"missing binding row for {sink_key}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("note", nargs="?", type=Path, default=DEFAULT_NOTE)
    parser.add_argument("output", nargs="?", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    note = json.loads(args.note.read_text(encoding="utf-8"))
    if note.get("binding_surface_kind") != "answer_result":
        raise SystemExit("source note must be an answer_result surface")
    registry = note["source_registry"]
    renaissance = registry["renaissance-q3"]["accession_number"]
    q2_berkshire = registry["berkshire-q2"]["accession_number"]
    q3_berkshire = registry["berkshire-q3"]["accession_number"]
    palantir = registry["palantir-q3"]["cusip"]

    q2_row = binding_row(note, "q2_answer")
    donor_handle = q2_row.get("copied_from_fragment_handle")
    if donor_handle != "renaissance-q3-report-row-count":
        raise SystemExit("q2_answer must consume the frozen copied fragment handle")
    if q2_row.get("row_local_fragment_handle") == donor_handle:
        raise SystemExit("designated q2 binding must remain non-self")

    answers = {
        "q1_answer": summary_value("2025-q3", renaissance, "TABLEVALUETOTAL"),
        "q2_answer": report_row_count("2025-q3", renaissance),
        "q3_answer": top_common_position_increases(q2_berkshire, q3_berkshire),
        "q4_answer": top_palantir_managers(palantir),
    }
    if len(answers["q3_answer"]) != 5 or len(answers["q4_answer"]) != 3:
        raise SystemExit("incomplete packet answer arrays")
    packet = {
        "binding_surface_kind": "answer_result",
        "next_required_skill": NEXT,
        "workflow_status": {
            "current_stage": "sec-financial-report-answer-packet-binder",
            "next_required_skill": NEXT,
            "allowed_outputs": [str(args.output)],
        },
        "packet_fields": {
            "q1_answer": {"source_handle": "renaissance-q3-table-value"},
            "q2_answer": {"source_handle": donor_handle, "binding_mode": q2_row["binding_mode"]},
            "q3_answer": {"source_handle": "berkshire-q2-q3-common-position-delta"},
            "q4_answer": {"source_handle": "palantir-q3-accession-value-ranking"},
        },
        "answers_payload": answers,
        "packet_status": "ready_for_answers_json",
        "packet_artifact": str(args.output),
        "terminal_sink_handle": "answers-json:q2_answer",
        "non_self_source_handle": donor_handle,
        "writer_allowed_non_packet_inputs": ["artifacts/sec-financial-report/resolved_answers_packet.json"],
        "writer_receipt_required_keys": [
            "packet_artifact", "packet_sha256", "terminal_sink_handle",
            "non_self_source_handle", "written_sink_value", "completion_status",
            "writer_authority_mode",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    print(f"packet_artifact={args.output}")
    print("binding_surface_kind=answer_result")
    print(f"non_self_source_handle={donor_handle}")
    print("packet_status=ready_for_answers_json")
    print(f"next_required_skill={NEXT}")


if __name__ == "__main__":
    main()
