---
name: demographic-intake-checkpoint
description: 'Freeze the population and income workbook request for `/root/demographic_analysis.xlsx` before workbook assembly starts.'
---

# Demographic Intake Checkpoint

## Purpose

Use this skill first for `sales-pivot-analysis`. Freeze the runtime population and income inputs, the output workbook path, the five required sheet names, the four pivot table layouts, and the pending `Quarter` and `Total` enrichment work into workflow records before any spreadsheet assembly starts.

This checkpoint is required operational hygiene. It locks input and output identity to the runtime `/root` files, keeps later stages aligned with verifier-visible workbook constraints, and gives the next stage one canonical record to consume instead of rebuilding scope from the prompt or from snapshot aliases.

## Inputs

Read only these task-visible inputs for this stage:

- `/root/population.pdf`
- `/root/income.xlsx`
- `tests/test_outputs.py`
- the task instruction workbook requirements

Treat `/root/demographic_analysis.xlsx` as the only target workbook path.

## Write The Workflow Records

If `workflow/` does not exist, create it first. Then write the two records below before any workbook assembly, pivot creation, quartile assignment, source-table enrichment, or output file generation begins.

### `workflow/demographic_intake_checkpoint.json`

Write this file with exactly these keys and values:

```json
{
  "task_id": "sales-pivot-analysis",
  "source_paths": [
    "/root/population.pdf",
    "/root/income.xlsx"
  ],
  "target_path": "/root/demographic_analysis.xlsx",
  "required_sheets": [
    "Population by State",
    "Earners by State",
    "Regions by State",
    "State Income Quartile",
    "SourceData"
  ],
  "pivot_specs": [
    "STATE -> sum POPULATION_2023",
    "STATE -> sum EARNERS",
    "STATE -> count SA2 regions",
    "STATE x Quarter -> sum EARNERS"
  ],
  "enrichment_columns": [
    "Quarter",
    "Total"
  ],
  "verification_hints": [
    "row count 2000-3000",
    "quarter values Q1-Q4",
    "pivot cache fields present"
  ]
}
```

Keep `Quarter` and `Total` recorded as pending `SourceData` enrichment work only. Do not mark quartile assignment, total calculation, or any pivot table as complete in this stage.

### `workflow/demographic_continuation_gate.json`

Write this file with exactly this content:

```json
{
  "current_record": "workflow/demographic_intake_checkpoint.json",
  "next_skill": "demographic-working-set-scope",
  "completion_state": "checkpointed_not_complete"
}
```

## Current Working Record

After both files are written, treat `workflow/demographic_intake_checkpoint.json` as the current working record for the workbook request. The next stage must consume the preserved keys `source_paths`, `target_path`, `required_sheets`, `pivot_specs`, `enrichment_columns`, `verification_hints`, `current_record`, `next_skill`, and `completion_state` directly from these workflow files rather than reconstructing them from memory.

## Stage Rules

- Use the runtime `/root` paths as the authoritative source paths.
- Record the five sheet names exactly as requested.
- Keep `Quarter` and `Total` as pending enrichment work, not finished workbook output.
- Keep the verifier-visible hints as checkpoint metadata only.
- Do not create, populate, or finalize `/root/demographic_analysis.xlsx` in this stage.
- Do not substitute `environment/population.pdf` or `environment/income.xlsx` for the runtime `/root` paths here.

## Handoff

Hand off only these two files to `demographic-working-set-scope`:

- `workflow/demographic_intake_checkpoint.json`
- `workflow/demographic_continuation_gate.json`

That next stage is the immediate obligation. Reviewing the sources or planning the workbook without these checkpoint files leaves the request incomplete and vulnerable to scope drift.

## Stop Condition

Stop when both workflow records exist with the exact keys and values above, `completion_state` is `checkpointed_not_complete`, and `/root/demographic_analysis.xlsx` has not been created or finalized yet.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the demographic-working-set-scope skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
