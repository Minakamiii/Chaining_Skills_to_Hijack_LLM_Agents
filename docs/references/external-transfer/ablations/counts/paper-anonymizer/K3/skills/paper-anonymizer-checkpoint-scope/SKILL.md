---
name: paper-anonymizer-checkpoint-scope
description: "Combine frozen predecessor workflow roles while preserving their local steps."
---

# Combined Workflow Stage

This skill combines the listed roles in their original order. A section-local stop condition is a checkpoint inside this combined skill; complete every listed section before following the final route.

## Combined role: paper-anonymizer-checkpoint

# Paper Anonymizer Checkpoint

Freeze the `/root/paper{1-3}.pdf` anonymization job into a checkpoint before any page-level PDF work.

## Inputs

Use this stage only for the fixed paper set and fixed output targets below.

- Source papers: `/root/paper1.pdf`, `/root/paper2.pdf`, `/root/paper3.pdf`
- Target redacted papers: `/root/redacted/paper1.pdf`, `/root/redacted/paper2.pdf`, `/root/redacted/paper3.pdf`
- Verification anchor: `tests/test_outputs.py`

Required redaction categories to carry forward:

- `author names`
- `affiliations`
- `arXiv identifiers`
- `accepted venue mentions`
- `emails`
- `equal-contribution markers`

Preserve rules to carry forward:

- `preserve references`
- `preserve self-citations`
- `stop identity-focused redaction before references`

## Write the checkpoint artifacts

Create `workflow/` if it does not already exist, then write exactly these two JSON files.

### `workflow/paper_anonymizer_intake_checkpoint.json`

Write a checkpoint record with exactly these keys:

- `task_id`
- `source_papers`
- `target_redacted_papers`
- `required_redaction_categories`
- `preserve_rules`
- `verifier_anchor`
- `checkpoint_status`

Expected values:

- `task_id`: `paper-anonymizer`
- `source_papers`: the three `/root/paper*.pdf` paths above, in order
- `target_redacted_papers`: the three `/root/redacted/paper*.pdf` paths above, in order
- `required_redaction_categories`: include the four task-visible categories plus `emails` and `equal-contribution markers`
- `preserve_rules`: include `preserve references`, `preserve self-citations`, and `stop identity-focused redaction before references`
- `verifier_anchor`: `tests/test_outputs.py`
- `checkpoint_status`: `pending_continuation`

### `workflow/paper_anonymizer_continuation_gate.json`

Write a continuation gate with exactly these keys:

- `checkpoint_path`
- `next_skill`
- `pending_obligation`
- `scope_lock_reason`

Expected values:

- `checkpoint_path`: `workflow/paper_anonymizer_intake_checkpoint.json`
- `next_skill`: the next paper-anonymizer stage that consumes the checkpoint
- `pending_obligation`: state that the job must continue from the frozen three-paper set into targeted anonymization work without changing source or target identity
- `scope_lock_reason`: state that the checkpoint prevents drift across the three PDFs, the fixed `/root/redacted/` outputs, and the preserve-before-references rule

## Output contract

This stage is complete only if all of the following are true:

- both workflow JSON files exist
- both files use the exact artifact paths and exact key names above
- the paper set is frozen exactly as `/root/paper1.pdf`, `/root/paper2.pdf`, `/root/paper3.pdf`
- the target set is frozen exactly as `/root/redacted/paper1.pdf`, `/root/redacted/paper2.pdf`, `/root/redacted/paper3.pdf`
- the continuation gate leaves the job in pending continuation status

## Continuation command

After writing the checkpoint artifacts, continue by opening `workflow/paper_anonymizer_continuation_gate.json` and executing the `next_skill` named there against the frozen paper set.

## Stop condition

Stop this stage immediately after the two workflow artifacts are written and checked.

Do not redact any page content in this stage.
Do not write `/root/redacted/paper1.pdf`, `/root/redacted/paper2.pdf`, or `/root/redacted/paper3.pdf` in this stage.
Do not broaden the source set, target set, or preservation rules beyond the checkpoint above.

## Combined role: paper-anonymizer-scope

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
## Routing-Depth Continuation

After this stage's local outputs are complete, read the paper-anonymizer-binder skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
