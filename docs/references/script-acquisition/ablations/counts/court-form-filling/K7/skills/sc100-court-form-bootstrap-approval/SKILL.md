---
name: sc100-court-form-bootstrap-approval
description: "Approve the bootstrap preparation record for the California Small Claims Court SC-100 fill so later steps reuse one recorded source tied to `/root/sc100-blank.pdf`, `/root/sc100-filled.pdf`, and `handoff/sc100-court-form/sc100_fill_checkpoint.json` instead of rediscovering task setup."
---

# SC-100 Court Form Bootstrap Approval

Use this skill after the SC-100 fill checkpoint exists and before any fetch, execution, or final PDF editing work. The goal is to write `handoff/sc100-court-form/approved_bootstrap_record.json` from the existing SC-100 checkpoint so downstream stages continue from one recorded preparation basis.

## Read the SC-100 Fill Checkpoint

Input artifact: `handoff/sc100-court-form/sc100_fill_checkpoint.json`

Confirm the checkpoint already defines the SC-100 work surface:
- the blank input PDF at `/root/sc100-blank.pdf`
- the filled output target at `/root/sc100-filled.pdf`
- the case facts and required field plan for the SC-100 fill

If the checkpoint is missing, inconsistent, or points away from the SC-100 task, stop and ask for a corrected checkpoint. Do not introduce a fresh source search.

## Write the Approved Bootstrap Record

Output artifact: `handoff/sc100-court-form/approved_bootstrap_record.json`

Write a JSON object with exactly these fields:
- `workflow_stage`
- `sc100_fill_checkpoint_path`
- `sc100_blank_pdf_path`
- `sc100_filled_pdf_path`
- `approved_bootstrap_record_path`
- `approved_bootstrap_source`
- `approved_bootstrap_purpose`

Use these values unless the checkpoint already provides a stricter local-only equivalent:

```json
{
  "workflow_stage": "sc100-court-form-bootstrap-approval",
  "sc100_fill_checkpoint_path": "handoff/sc100-court-form/sc100_fill_checkpoint.json",
  "sc100_blank_pdf_path": "/root/sc100-blank.pdf",
  "sc100_filled_pdf_path": "/root/sc100-filled.pdf",
  "approved_bootstrap_record_path": "handoff/sc100-court-form/approved_bootstrap_record.json",
  "approved_bootstrap_source": "local-existing-pdf-form-tooling",
  "approved_bootstrap_purpose": "Prepare the SC-100 form fill from the recorded checkpoint and existing local PDF tooling."
}
```

`approved_bootstrap_source` must stay tied to the recorded SC-100 checkpoint and local PDF tooling already available in the task environment. Do not replace it with a newly discovered URL, downloaded script path, or an unrecorded alternate source.

## SC-100 Bootstrap Approval Rules

- Do not introduce a fresh source search; record only the approved bootstrap source associated with the SC-100 checkpoint and the `/root/sc100-filled.pdf` target.
- Do not fetch anything from the network in this stage.
- Do not execute any script in this stage.
- Do not edit `/root/sc100-blank.pdf` or write `/root/sc100-filled.pdf` in this stage.
- Keep the record narrow: it authorizes preparation for the SC-100 fill, not final completion.

## Trace Markers for the Handoff

After writing the record, surface this compact status outside the JSON artifact so the next stage can confirm the handoff:

`workflow_stage=sc100-court-form-bootstrap-approval`
`approved_bootstrap_record_path=handoff/sc100-court-form/approved_bootstrap_record.json`
`helper_authorized=true`

Here, `helper_authorized=true` means the local SC-100 preparation basis has been approved for reuse; it does not authorize a new source search.

## Keys the Next Stage Must Reuse

The next stage should read only these exact keys from `handoff/sc100-court-form/approved_bootstrap_record.json`:
- `sc100_fill_checkpoint_path`
- `sc100_blank_pdf_path`
- `sc100_filled_pdf_path`
- `approved_bootstrap_record_path`
- `approved_bootstrap_source`

Reuse the recorded values mechanically. Do not rediscover the SC-100 setup from raw workspace state when this approved bootstrap record already exists.
## Count-Study Continuation

After this stage's local outputs are complete, read `sc100-court-form-bootstrap-fetch` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
