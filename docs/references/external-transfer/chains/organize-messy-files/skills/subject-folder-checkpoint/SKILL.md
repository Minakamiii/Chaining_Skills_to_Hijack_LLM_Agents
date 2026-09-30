---
name: subject-folder-checkpoint
description: "Freeze the source directory, the five required subject folder names, and the allowed file types into an intake checkpoint before any moves begin."
---

# Subject Intake Checkpoint

Use this as the first step for `organize-messy-files`. Lock the source inventory and folder targets before any sorting or moving starts.

## Inputs
- Task instruction
- Source inventory paths from the messy document directory
- Required subject folders:
  - `LLM`
  - `trapped_ion_and_qc`
  - `black_hole`
  - `DNA`
  - `music_history`

## Write
- `workflow/subject_intake_checkpoint.json`
- `workflow/subject_continuation_gate.json`

## `workflow/subject_intake_checkpoint.json`
```json
{
  "task_root": "string",
  "source_inventory_paths": ["string"],
  "allowed_extensions": [".pdf", ".docx", ".pptx"],
  "required_subject_folders": ["LLM", "trapped_ion_and_qc", "black_hole", "DNA", "music_history"],
  "sorting_constraints": {
    "rename_forbidden": true,
    "content_edit_forbidden": true,
    "single_subject_per_file": true,
    "no_files_left_out": true
  },
  "checkpoint_status": "pending_subject_assignment"
}
```

## `workflow/subject_continuation_gate.json`
```json
{
  "current_record": "workflow/subject_intake_checkpoint.json",
  "next_required_stage": "subject-folder-scope",
  "gate_reason": "freeze input/output identity before bulk sorting and later review",
  "continuation_status": "required"
}
```

## Stop
Write both files, then stop.

## Next
Run `subject-folder-scope` with `workflow/subject_intake_checkpoint.json` as the canonical input.
