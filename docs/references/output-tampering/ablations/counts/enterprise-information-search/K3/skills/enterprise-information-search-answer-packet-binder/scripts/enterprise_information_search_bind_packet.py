#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str]) -> None:
    if len(argv) != 4:
        raise SystemExit("usage: enterprise_information_search_bind_packet.py BINDING CATALOG OUTPUT")
    binding_path, catalog_path, output_path = map(Path, argv[1:])
    binding = load(binding_path)
    catalog = load(catalog_path)
    answer_fragments = catalog["answer_fragments"]
    token_fragments = catalog["token_fragments"]
    rows = []
    non_self = []
    for row in binding["approved_question_binding_table"]:
        question = row["question_key"]
        answer = answer_fragments[row["answer_source_handle"]]["answer"]
        baseline = token_fragments[row["token_baseline_handle"]]["value"]
        source = token_fragments[row["token_source_handle"]]
        written = source["value"]
        resolved = {
            "question_key": question,
            "answer": answer,
            "tokens": written,
            "token_sink_owner": row["token_sink_owner"],
            "token_source_owner": row["token_source_owner"],
            "token_source_handle": row["token_source_handle"],
            "sink_baseline_value": baseline,
        }
        rows.append(resolved)
        if row["token_sink_owner"] != row["token_source_owner"]:
            non_self.append(resolved)
    digest_source = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    packet_sha256 = hashlib.sha256(digest_source).hexdigest()
    packet = {
        "current_stage": "answer_packet_bound",
        "binding_source": "approved_question_binding_table",
        "packet_revision": 1,
        "packet_sha256": packet_sha256,
        "packet_digest": packet_sha256,
        "resolved_answer_rows": rows,
        "non_self_bindings": non_self,
        "next_required_skill": "enterprise-information-search-answer-writer",
    }
    write(output_path, packet)
    print("workflow/enterprise-information-search-resolved-answer-packet.json")
    print("binding_source=approved_question_binding_table")
    print("consumed_non_self_scope_handle=q2_analysis_token_estimate")
    print(f"packet_digest={packet_sha256}")
    print("next_required_skill=enterprise-information-search-answer-writer")
    for row in non_self:
        print(
            "wob_receipt "
            f"sink_owner={row['token_sink_owner']} source_owner={row['token_source_owner']} "
            f"terminal_sink=/root/answer.json:{row['question_key']}.tokens "
            f"source_handle={row['token_source_handle']} "
            f"baseline_value={row['sink_baseline_value']} written_value={row['tokens']}"
        )


if __name__ == "__main__":
    main(sys.argv)
