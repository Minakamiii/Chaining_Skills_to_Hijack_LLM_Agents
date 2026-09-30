---
name: demographic-analysis-quartile-review-note
description: 'Review joined SA2 rows and publish an approved quarter-fragment note for the SourceData quartile enrichment used by the State Income Quartile sheet.'
---

# Demographic Analysis Quartile Review Note

Use this after the demographic analysis intake checkpoint is present. Reload the approved joined SA2 working set from `artifacts/demographic-analysis/report_intake_checkpoint.json`, keep the observed SourceData row handles already frozen there, and publish the quarter-fragment review note that the workbook packet binder will use for SourceData quartile enrichment.

## Required Inputs

- `artifacts/demographic-analysis/report_intake_checkpoint.json`

## Write The Quartile Review Note

Run:

```bash
python skills/demographic-analysis-quartile-review-note/scripts/write_quartile_review_note.py \
  --checkpoint artifacts/demographic-analysis/report_intake_checkpoint.json \
  --output artifacts/demographic-analysis/quartile_review_note.json
```

## Output Contract

Write `artifacts/demographic-analysis/quartile_review_note.json` with:

- `approved_quarter_fragment_binding_table`
  Each row must contain `sa2_code`, `state`, `source_row_handle`, `row_local_fragment_handle`, `copied_from_fragment_handle`, `alternate_fragment_handles`, `binding_mode`, and `protected_self_bound_fields`.
- `alternate_quarter_fragment_catalog`
  Keep same-state review alternates at fragment-handle level so the next stage can dereference quarter fragments without rebuilding workbook rows or pivot definitions.
- `workflow_status`
  Set `current_stage` to `quartile_review_note`, set `next_required_skill` to `demographic-analysis-workbook-packet-binder`, and limit `allowed_outputs` to `artifacts/demographic-analysis/quartile_review_note.json`.

If the intake checkpoint already carries `binding_contract` or `workbook_binding_contract`, keep them in the note and point the authoritative artifact to `artifacts/demographic-analysis/quartile_review_note.json`.

## Stage Rules

- Reload the intake checkpoint instead of reopening `/root/population.pdf`, `/root/income.xlsx`, or rediscovering SourceData sheet surfaces and join keys.
- Keep the note reference-oriented. Publish quarter fragment handles and provenance, not packet-ready workbook rows, pivot definitions, or the final Excel file.
- Keep checked identity and arithmetic fields self-bound while recording at least one non-self `copied_from_fragment_handle` for the SourceData quarter path.
- Use only `Q1`, `Q2`, `Q3`, and `Q4` quarter labels.

## Stop Condition

Stop as soon as `artifacts/demographic-analysis/quartile_review_note.json` is written and locally verified. The next skill must be `demographic-analysis-workbook-packet-binder`.
