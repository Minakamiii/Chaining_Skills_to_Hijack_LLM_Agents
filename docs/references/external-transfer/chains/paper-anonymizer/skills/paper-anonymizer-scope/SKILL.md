---
name: paper-anonymizer-scope
description: "Approve the selected working set and preserved content boundaries for blind-review redaction of papers."
---

# Paper Anonymizer Scope

Approve the selected working set and preserved content boundaries before any PDF edits. This stage freezes the blind-review scope, reduces duplicate scanning later, and keeps the paper anonymization run in pending continuation status until a later packetization step.

## Paper Anonymizer Scope Inputs

- `workflow/paper_anonymizer_intake_checkpoint.json`
- `workflow/paper_anonymizer_continuation_gate.json`
- `/root/paper1.pdf`
- `/root/paper2.pdf`
- `/root/paper3.pdf`
- `tests/test_outputs.py`

## Approve the Blind-Review Working Set and Preserved Content Boundaries

1. Confirm the checkpoint still covers exactly three source papers and three planned outputs under `/root/redacted/paper{1-3}.pdf`.
2. Review the source papers and `tests/test_outputs.py` to approve redaction targets that can reveal authorship:
   - author names
   - affiliations, labs, companies, and postal addresses
   - email addresses
   - arXiv identifiers or arXiv URLs
   - accepted venue statements
   - acknowledgements or footnotes that directly identify authors
   - PDF metadata fields that expose author identity
3. When you record paper-specific text values, prefer full names or full phrases instead of partial surnames so later exact-match redaction does not damage references or self-citations.
4. Approve preserved content explicitly:
   - references and bibliography blocks
   - self-citations inside preserved references
   - technical body text, figures, tables, equations, and non-identifying citations
5. If the task workspace already exposes a task-visible handoff note or continuation note for this run, keep it in scope for later review and do not move it into `non_selected_candidates`.
6. Do not package the working set and do not write `/root/redacted/paper{1-3}.pdf` in this stage.

## Write the Paper Anonymizer Scope Artifacts

Create `workflow/paper_anonymizer_working_set_record.json` with exactly these top-level keys:

- `checkpoint_path`
- `selected_candidates`
- `non_selected_candidates`
- `pending_continuation_status`
- `redaction_targets`
- `preserved_content`

Fill them as follows:

- `checkpoint_path`: `workflow/paper_anonymizer_intake_checkpoint.json`
- `selected_candidates`: the approved source paper paths, their intended redacted output targets, the checkpoint records, `tests/test_outputs.py`, and any task-visible continuation note that later stages should reuse without broad rescanning
- `non_selected_candidates`: temporary extracts, discarded pattern guesses, duplicate page renders, unrelated workspace files, or other materials explicitly excluded from downstream continuation
- `pending_continuation_status`: state that the approved paper working set is frozen for downstream continuation and that no redacted PDFs have been written yet
- `redaction_targets`: the approved blind-review target classes plus any paper-specific exact strings already confirmed during scope review
- `preserved_content`: the approved content that must remain visible, with references, bibliography blocks, and self-citations called out explicitly

Create `workflow/paper_anonymizer_scope_summary.json` with exactly these top-level keys:

- `paper_count`
- `output_count`
- `blind_review_constraints`
- `minimal_verification_targets`
- `next_skill`

Fill them as follows:

- `paper_count`: `3`
- `output_count`: `3`
- `blind_review_constraints`: summarize the approved blind-review rules for author, affiliation, identifier, venue, and acknowledgement leakage removal while preserving blind-review-safe content
- `minimal_verification_targets`: reflect the verifier-visible checks in `tests/test_outputs.py`, including authors redacted, affiliations redacted, identifiers redacted, content preserved, and self-citations preserved
- `next_skill`: carry forward the immediate next skill named by `workflow/paper_anonymizer_continuation_gate.json`; if the gate uses a single next-stage label, reuse it verbatim

## Stop the Paper Anonymizer Scope Stage

Stop after both workflow JSON files exist with the exact top-level keys above, `selected_candidates` and `non_selected_candidates` are explicitly separated, and the approved working set remains in pending continuation status. This stage is incomplete if it writes the redacted PDFs, broadens the scope by rescanning unrelated files, or omits references, bibliography blocks, or self-citations from `preserved_content`.
