---
name: paper-anonymizer-checkpoint
description: "Freeze the three-paper anonymization job into a checkpoint before any PDF edits."
---

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
## Routing-Depth Continuation

After this stage's local outputs are complete, read the paper-anonymizer-scope skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
