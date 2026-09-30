---
name: subject-folder-scope
description: "Approve the selected working set for subject sorting by separating selected files, non-selected candidates, and mandatory context needed for the five destination folders."
---

# Approve the Subject Sorting Working Set

Use this stage before any document moves. Its job is to freeze which files are in scope for sorting into `LLM`, `trapped_ion_and_qc`, `black_hole`, `DNA`, and `music_history`, reduce duplicate scanning, and preserve later review and traceability.

## Inputs

Read:
- `workflow/subject_intake_checkpoint.json`
- `workflow/subject_continuation_gate.json`

Take `task_root` from the intake checkpoint and keep the same path style already used there.

## Write `workflow/subject_working_set_record.json`

Build one approved working record with these exact keys:

```json
{
  "task_root": "string",
  "selected_candidates": [
    {
      "path": "string",
      "extension": "string",
      "pending_subject_folder": ""
    }
  ],
  "non_selected_candidates": [
    {
      "path": "string",
      "exclusion_reason": "string"
    }
  ],
  "mandatory_context_paths": [
    "string"
  ],
  "required_subject_folders": [
    "LLM",
    "trapped_ion_and_qc",
    "black_hole",
    "DNA",
    "music_history"
  ],
  "working_set_status": "approved_pending_continuation"
}
```

Selection rules:
- Put every in-scope `.pdf`, `.docx`, and `.pptx` file that still needs subject sorting into `selected_candidates`.
- Keep each selected file exactly once.
- Leave `pending_subject_folder` empty at this stage unless the intake checkpoint already carries a decisive folder assignment that should be preserved without reclassification.
- If a document's subject is not yet obvious, keep it selected and pending here instead of excluding it.
- Put only truly out-of-scope files into `non_selected_candidates`, with a short `exclusion_reason`.
- Do not exclude continuation records, task-local operational notes, or other local context that later classification or completion stages still need. Keep those in `mandatory_context_paths`.
- `mandatory_context_paths` should include the two input workflow records and any real local references needed later to classify or verify the five subject folders, such as task-local test or instruction files when present.
- Do not move or rename files in this stage.

Common exclusions:
- subject folders already created for output structure
- workflow sidecars that are not part of the document set
- unsupported extensions
- helper scripts and benchmark tests

## Write `workflow/subject_scope_summary.json`

Write this exact shape:

```json
{
  "selected_count": 0,
  "non_selected_count": 0,
  "counts_by_extension": {
    ".pdf": 0,
    ".docx": 0,
    ".pptx": 0
  },
  "scope_reason": "standardize approved sorting set and preserve later review/traceability",
  "next_required_stage": "subject-folder-binder"
}
```

Count only `selected_candidates` in `counts_by_extension`. Always include all three extension keys, even when a count is zero.

## Continue With Subject Folder Binder

Use the approved scope artifacts as the only authoritative inputs:

```text
subject-folder-binder workflow/subject_working_set_record.json workflow/subject_scope_summary.json
```

## Stop Condition

Stop when both workflow files exist, `selected_candidates` and `non_selected_candidates` are explicitly separated, `working_set_status` is `approved_pending_continuation`, the five required folder names are present exactly as listed above, the summary counts match the approved working record, and no selected file has been moved or renamed.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the subject-folder-binder skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
