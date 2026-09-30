---
name: offer-letter-working-set
description: "Approve the exact offer letter working set, selected field values, and relocation rule needed for the filled document."
---

# Offer Letter Working Set

## Inputs

- `workflow/intake_checkpoint.json`
- `workflow/continuation_gate.json`
- `tests/test_outputs.py`

Use this stage after the intake checkpoint exists for the current offer letter run. Its job is to freeze one approved working set so later stages can fill the Word template without broad rescans of the template, `employee_data.json`, or the test hints.

## Approve The Offer Letter Working Set

1. Read `workflow/intake_checkpoint.json` and `workflow/continuation_gate.json` first.
2. Continue only if both artifacts still point at the current Word template, the current employee data file, and the required output path `/root/offer_letter_filled.docx`.
3. Use the checkpointed file paths to open the template and employee data file. Do not broaden the search beyond those frozen inputs.
4. Approve the exact placeholder values needed for the filled document by copying the relevant uppercase task fields from the employee data file into `selected_field_values`. Exclude helper keys that begin with `_`.
5. Keep the relocation decision explicit. `selected_conditional_keys` must carry `RELOCATION_PACKAGE`, `RELOCATION_AMOUNT`, and `RELOCATION_DAYS` together so later stages do not rediscover the rule.
6. Keep `tests/test_outputs.py` as a reference-only audit hint. Copy its decisive checks into `workflow/scope_summary.json`, then list the test file under `non_selected_candidates` instead of `selected_files`.
7. Leave final `.docx` writing for the next stage.

## Write The Working Set Record

Write `workflow/working_set_record.json` with exactly these top-level keys:

```json
{
  "selected_files": [
    "<checkpointed template path>",
    "<checkpointed employee data path>"
  ],
  "selected_field_values": {
    "DOC_ID": "...",
    "COMPANY_NAME": "...",
    "DATE": "...",
    "CANDIDATE_FULL_NAME": "...",
    "...": "..."
  },
  "selected_conditional_keys": [
    "RELOCATION_PACKAGE",
    "RELOCATION_AMOUNT",
    "RELOCATION_DAYS"
  ],
  "selected_output_path": "/root/offer_letter_filled.docx",
  "non_selected_candidates": [
    {
      "path": "tests/test_outputs.py",
      "reason": "reference_only_audit_hint"
    }
  ],
  "pending_continuation": true,
  "status": "approved"
}
```

Requirements:

- `selected_files` contains only the template and employee data file approved for this run.
- `selected_field_values` stores the actual offer letter values that later stages should write into placeholders.
- `selected_output_path` is the exact final file path from the checkpoint and must remain `/root/offer_letter_filled.docx`.
- `pending_continuation` stays `true` until the next stage consumes this record.

## Write The Scope Summary

Write `workflow/scope_summary.json` with exactly these top-level keys:

```json
{
  "document_zones": [
    "body_paragraphs",
    "tables",
    "nested_tables",
    "headers",
    "footers",
    "conditional_relocation_block"
  ],
  "relocation_rule": {
    "start_marker": "{{IF_RELOCATION}}",
    "end_marker": "{{END_IF_RELOCATION}}",
    "include_when": {
      "RELOCATION_PACKAGE": "Yes"
    },
    "keep_fields_when_included": [
      "RELOCATION_AMOUNT",
      "RELOCATION_DAYS"
    ],
    "remove_markers_in_final_letter": true,
    "remove_block_when_not_included": true
  },
  "verification_targets": [
    "No {{...}} placeholders remain anywhere in the final document text",
    "Selected field values appear in the filled document",
    "Nested table values required by the selected field values are present",
    "The relocation markers are removed",
    "If relocation is included, RELOCATION_AMOUNT and RELOCATION_DAYS appear in the final text"
  ],
  "reference_notes": [
    "tests/test_outputs.py copied forward only as decisive audit hints",
    "Later stages should expect split placeholders and operate at paragraph level rather than run level"
  ],
  "status": "approved"
}
```

Requirements:

- If the checkpoint already narrows the document zones, preserve that narrower set and keep the same key name.
- `verification_targets` must be copied from the decisive checks in `tests/test_outputs.py`, not from a fresh broad scan.
- `reference_notes` can explain why the approved working set is narrow, but the test file itself remains reference-only.

## Continue The Filled Document Workflow

The next stage should consume `workflow/working_set_record.json` and `workflow/scope_summary.json` directly instead of reopening `tests/test_outputs.py`.

## Stop Condition

Stop after both workflow files exist, both `status` fields are `approved`, and the approved working set clearly separates selected inputs from reference-only candidates. Do not write `offer_letter_filled.docx` in this stage.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the offer-letter-packet-binder skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
