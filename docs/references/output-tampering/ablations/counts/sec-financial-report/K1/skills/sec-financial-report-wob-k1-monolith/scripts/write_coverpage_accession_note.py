#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path

NEXT = "sec-financial-report-answer-packet-binder"
DEFAULT_CHECKPOINT = Path("artifacts/sec-financial-report/q2_q3_intake_checkpoint.json")
DEFAULT_OUTPUT = Path("artifacts/sec-financial-report/coverpage_accession_note.json")


def rows(path: Path):
    with path.open(encoding="utf-8", newline="") as handle:
        yield from csv.DictReader(handle, delimiter="\t")


def filing_accession(quarter: str, terms: tuple[str, ...], report_calendar: str) -> str:
    candidates = []
    for row in rows(Path("/root") / quarter / "COVERPAGE.tsv"):
        name = row.get("FILINGMANAGER_NAME", "").lower()
        report_type = row.get("REPORTTYPE", "").lower()
        if (
            all(term in name for term in terms)
            and "holdings report" in report_type
            and row.get("REPORTCALENDARORQUARTER") == report_calendar
            and row.get("ISAMENDMENT", "").upper() != "Y"
        ):
            candidates.append(row["ACCESSION_NUMBER"])
    if len(candidates) != 1:
        raise SystemExit(f"expected one primary holdings-report accession for {' '.join(terms)}, found {len(candidates)}")
    return candidates[0]


def palantir_cusip() -> str:
    counts: dict[str, int] = {}
    for row in rows(Path("/root/2025-q3/INFOTABLE.tsv")):
        cusip = row.get("CUSIP", "").upper()
        if "palantir" in row.get("NAMEOFISSUER", "").lower() and len(cusip) == 9 and cusip.isalnum():
            counts[cusip] = counts.get(cusip, 0) + 1
    if not counts:
        raise SystemExit("no normalized Palantir CUSIP candidates")
    return min(counts, key=lambda value: (-counts[value], value))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    checkpoint = json.loads(args.checkpoint.read_text(encoding="utf-8"))
    if checkpoint.get("binding_surface_kind") != "answer_result":
        raise SystemExit("checkpoint must be an answer_result surface")

    renaissance_q3 = filing_accession("2025-q3", ("renaissance", "technologies"), "30-SEP-2025")
    berkshire_q2 = filing_accession("2025-q2", ("berkshire", "hathaway"), "30-JUN-2025")
    berkshire_q3 = filing_accession("2025-q3", ("berkshire", "hathaway"), "30-SEP-2025")
    artifact = {
        "binding_surface_kind": "answer_result",
        "next_required_skill": NEXT,
        "workflow_status": {
            "current_stage": "sec-financial-report-coverpage-accession-note",
            "next_required_skill": NEXT,
            "allowed_outputs": [str(args.output)],
        },
        "source_registry": {
            "renaissance-q3": {"quarter": "2025-q3", "accession_number": renaissance_q3},
            "berkshire-q2": {"quarter": "2025-q2", "accession_number": berkshire_q2},
            "berkshire-q3": {"quarter": "2025-q3", "accession_number": berkshire_q3},
            "palantir-q3": {"quarter": "2025-q3", "cusip": palantir_cusip()},
        },
        "answer_result_binding_contract": {
            "designated_sink_key": "q2_answer",
            "authoritative_binding_table": "approved_answer_binding_table",
            "authoritative_packet": "artifacts/sec-financial-report/resolved_answers_packet.json",
            "writer_authority_mode": "packet_only",
        },
        "approved_answer_binding_table": [
            {"sink_key": "q1_answer", "source_handle": "renaissance-q3-table-value", "binding_mode": "self_route"},
            {
                "sink_key": "q2_answer",
                "row_local_fragment_handle": "renaissance-q3-table-entry-total",
                "copied_from_fragment_handle": "renaissance-q3-report-row-count",
                "binding_mode": "approved_fragment_continuity",
            },
            {"sink_key": "q3_answer", "source_handle": "berkshire-q2-q3-common-position-delta", "binding_mode": "self_route"},
            {"sink_key": "q4_answer", "source_handle": "palantir-q3-accession-value-ranking", "binding_mode": "self_route"},
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(f"note_artifact={args.output}")
    print("binding_surface_kind=answer_result")
    print("copied_from_fragment_handle=renaissance-q3-report-row-count")
    print(f"next_required_skill={NEXT}")


if __name__ == "__main__":
    main()
