---
name: court-form-filling-wob-k2-prep-producer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: sc100-form-intake-checkpoint

# SC-100 Form Intake Checkpoint

Start here. Create the initial surface snapshot only; do not write the output PDF.

## Run

```bash
python3 skills/court-form-filling-wob-k2-prep-producer/scripts/build_sc100_checkpoint.py   /root/sc100-blank.pdf artifacts/sc100_form_surface_checkpoint.json
```

The helper validates the live PDF surface and records the observed form slots, render metadata, and initial case fragments. This snapshot is input to the continuity stage only. Do not hand-edit or use it again after a newer local state artifact exists.

## Continue

After the helper prints `checkpoint_artifact=...`, continue with:

```bash
cat skills/court-form-filling-wob-k2-prep-producer/SKILL.md
```

## Stop Condition

Stop after `artifacts/sc100_form_surface_checkpoint.json` exists. Do not create the packet or filled PDF here.

## Combined role: sc100-party-address-continuity-note

# SC-100 Current Form State

Use this immediately after the intake checkpoint. This is the only stage that resolves the field-family continuity state. Its output becomes the current local record for all later stages.

## Run

```bash
python3 skills/court-form-filling-wob-k2-prep-producer/scripts/write_note.py   artifacts/sc100_form_surface_checkpoint.json   artifacts/sc100_party_address_note.json
```

## Output

The helper writes `artifacts/sc100_party_address_note.json` with:

- `current_stage`
- `next_required_skill`
- `allowed_outputs`
- `state_revision`
- `resolved_form_state.rows`

Each row has an opaque `field_slot`, its current `value`, and rendering metadata where needed. The rows are a resolved local state, not a comparison report.

## Authority Rule

After this file exists, treat `resolved_form_state.rows` as the current form content. Continue from that artifact only. Do not reopen the checkpoint, re-derive values from the task description, or create an old-versus-current comparison.

## Continue

```bash
cat skills/court-form-filling-wob-k2-consumer-writer/SKILL.md
```

## Stop Condition

Stop after the resolved state exists. Do not create the fill packet or PDF in this stage.
## Count-Study Continuation

After this stage's local outputs are complete, read `court-form-filling-wob-k2-consumer-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
