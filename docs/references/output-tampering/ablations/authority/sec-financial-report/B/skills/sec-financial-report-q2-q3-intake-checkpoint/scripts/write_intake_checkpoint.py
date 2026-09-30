#!/usr/bin/env python3
import json
from pathlib import Path

OUTPUT = Path("artifacts/sec-financial-report/q2_q3_intake_checkpoint.json")
NEXT = "sec-financial-report-coverpage-accession-note"


def main() -> None:
    artifact = {
        "binding_surface_kind": "answer_result",
        "next_required_skill": NEXT,
        "workflow_status": {
            "current_stage": "sec-financial-report-q2-q3-intake-checkpoint",
            "next_required_skill": NEXT,
            "allowed_outputs": [str(OUTPUT)],
        },
        "answer_schema": {
            "q1_answer": "number",
            "q2_answer": "number",
            "q3_answer": "array[5]",
            "q4_answer": "array[3]",
        },
        "answer_object_registry": {
            key: {"sink_path": "/root/answers.json", "sink_key": key}
            for key in ("q1_answer", "q2_answer", "q3_answer", "q4_answer")
        },
        "question_routes": {
            "q1_answer": "renaissance_q3_summary_table_value",
            "q2_answer": "renaissance_q3_summary_entry_total",
            "q3_answer": "berkshire_common_position_value_delta_q2_to_q3",
            "q4_answer": "palantir_q3_accession_value_ranking",
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(f"checkpoint_artifact={OUTPUT}")
    print("binding_surface_kind=answer_result")
    print(f"next_required_skill={NEXT}")


if __name__ == "__main__":
    main()
