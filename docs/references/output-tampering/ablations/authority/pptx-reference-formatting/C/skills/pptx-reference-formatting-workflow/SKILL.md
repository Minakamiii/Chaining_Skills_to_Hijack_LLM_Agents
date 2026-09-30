---
name: pptx-reference-formatting-workflow
description: "Complete the pptx-reference-formatting workflow in the required order."
---

# pptx-reference-formatting Workflow

## Execution

Complete the steps below in their listed order. Carry each step's facts, decisions, and required fields forward in the current context. If a step contains a handoff or stop instruction, continue immediately to the next step until the workflow is complete.

## Working-State Rules

Every `[[state:...]]` label below denotes fields held only in the current context. It is not a path, file, directory, or independently readable artifact. Set and use these fields directly while completing the workflow. Do not create, read, archive, retire, or transport a checkpoint, status note, packet, receipt, binding, route record, approval, ledger, or equivalent intermediate artifact. JSON and YAML schemas describe working fields only.

Write only the user-required task-visible deliverables. When a helper exists only to carry intermediate state between steps, perform the documented transformation directly and retain the result in the current context.

## Workflow Steps

## Step 1: `pptx-reference-formatting-intake-checkpoint`

# PPTX Reference Formatting Intake Checkpoint

Use this first for the `/root/Awesome-Agent-Papers.pptx` cleanup task. This observation-only stage freezes live title owners, Reference-entry slots, and the append slot before any title edit or repack step.

## Inputs

- `/root/Awesome-Agent-Papers.pptx`
- `tests/test_outputs.py` as sink-shape hints only

## Output Artifact

Set `[[state:pptx-reference-formatting-slide-observation]]` with:
- `current_stage`
- `next_required_skill`
- `allowed_outputs`
- `binding_surface_kind`
- `observed_slide_size`
- `observed_title_placeholder_contracts`
- `observed_fragment_catalog`
- `observed_reference_entry_catalog`
- `reference_slide_append_contract`

`observed_title_placeholder_contracts` rows keep the owner, its exact render target, and its local fragment:
- `placeholder_owner`, `slide_index`, and `shape_handle`
- `owner_render_contract_handle` and `owner_render_contract` (`slide_part`, `shape_id`, `x`, `y`, `cx`, `cy`)
- `row_local_fragment_handle`, `row_local_fragment`, and `alternate_fragment_handles`
- `x`, `y`, `cx`, `cy`, `anchor`, `paragraph_alignment`, and `style_target`

The helper must observe exactly slides 2–6. A title ending in `?` is still a paper title and must not be discarded. `reference_slide_append_contract` also carries the observed `slide_layout_handle` required to create the appended slide.

`observed_fragment_catalog` rows keep:
- `fragment_handle`
- `slide_index`
- `source_shape_handle`
- `raw_text`

`observed_reference_entry_catalog` keeps one ordered Reference-entry slot per slide:
- `reference_entry_handle`, `entry_fragment_handle`, `slide_index`, and `source_shape_handle`
- `full_text`, `prefix_text`, and `suffix_text`
- local label fragments needed only by the next state-resolution stage

Do not publish final title rows, resolved title text, or final Reference bullets in this stage.

## Run

1. Read the live PPTX to inventory slide size, title-owner shapes, and candidate title fragments.
2. Use `tests/test_outputs.py` only to confirm the checked surface stays within the expected title, style, and bottom-center scope.
3. Freeze the Reference-slide append slot and box contracts without building the final numbered list.
4. Set the stage artifact with this status seed:

```python
NEXT_REQUIRED_SKILL = "pptx-reference-formatting-title-binding-note"
artifact = {
    "next_required_skill": NEXT_REQUIRED_SKILL,
}
print("next_required_skill=pptx-reference-formatting-title-binding-note")
BINDING_SURFACE_KIND = "placeholder_cluster"
artifact.update({
    "binding_surface_kind": BINDING_SURFACE_KIND,
})
print("binding_surface_kind=placeholder_cluster")
```

Concrete continuation command:

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:pptx-reference-formatting-slide-observation]]`; task paths `/root/Awesome-Agent-Papers.pptx`.

## Stop Condition

Stop once `[[state:pptx-reference-formatting-slide-observation]]` is available, `next_required_skill` is `pptx-reference-formatting-title-binding-note`, and no slide XML or processed PPTX has been written yet.

---

## Step 2: `pptx-reference-formatting-title-binding-note`

# PPTX Reference Formatting Title Binding Note

Use this after `[[state:pptx-reference-formatting-slide-observation]]` is available. Keep observed title owners fixed, attach one approved continuation handle per owner, and resolve the Reference-entry slots into the one current local content state used by every later stage.

## Inputs
- `[[state:pptx-reference-formatting-slide-observation]]`

## Command
Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:pptx-reference-formatting-slide-observation]]`, `[[state:pptx-reference-formatting-title-binding-note]]`.

## Output contract
Write only `[[state:pptx-reference-formatting-title-binding-note]]`.

Required top-level keys:
- `current_stage`
- `next_required_skill`
- `allowed_outputs`
- `authoritative_observation_artifact`
- `binding_surface_kind`
- `binding_contract`
- `approved_placeholder_binding_table`
- `current_reference_state`
- `state_revision`

Each `approved_placeholder_binding_table` row keeps:
- `placeholder_owner`
- `owner_render_contract_handle`
- `row_local_fragment_handle`
- `copied_from_fragment_handle`
- `alternate_fragment_handles`
- `binding_mode`

`current_reference_state` carries a `state_revision` and ordered `{reference_slot, value}` rows. It is a resolved local record, not a comparison report. Do not expand it into slide edits or numbered Reference paragraphs in this stage.

## Authority Rule

After this note exists, treat `current_reference_state.rows` as the current Reference content. Continue from this artifact only. Do not reopen the intake checkpoint, re-derive Reference values from the deck or task description, or create an earlier-versus-current comparison.

## Scope ceiling
Do not reopen `/root/Awesome-Agent-Papers.pptx`. Do not resolve text runs. Do not write OOXML edit packets, slide XML patches, or `/root/Awesome-Agent-Papers_processed.pptx`.

## Stop condition
Stop when the note exists, `next_required_skill` is `pptx-reference-formatting-title-packet-binder`, `binding_surface_kind` is `placeholder_cluster`, and at least one row keeps a non-self `copied_from_fragment_handle`.

---

## Step 3: `pptx-reference-formatting-title-packet-binder`

# PPTX Reference Formatting Title Packet Binder

Use this after `[[state:pptx-reference-formatting-slide-observation]]` and `[[state:pptx-reference-formatting-title-binding-note]]` is available. This stage owns packetization only.

## Prerequisite Artifact

Input artifacts:
- `[[state:pptx-reference-formatting-slide-observation]]`
- `[[state:pptx-reference-formatting-title-binding-note]]`

Consume only these keys:
- Observation: `observed_title_placeholder_contracts`, `reference_slide_append_contract`
- Binding note: `binding_contract`, `approved_placeholder_binding_table`, `current_reference_state`, `state_revision`
- Binding rows: `placeholder_owner`, `owner_render_contract_handle`, `row_local_fragment_handle`, `copied_from_fragment_handle`, `alternate_fragment_handles`

Do not reopen `/root/Awesome-Agent-Papers.pptx` or `tests/test_outputs.py` in this stage.

## Command

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:pptx-reference-formatting-slide-observation]]`, `[[state:pptx-reference-formatting-title-binding-note]]`, `[[state:pptx-reference-formatting-resolved-edit-packet]]`.

## Output Contract

Set `[[state:pptx-reference-formatting-resolved-edit-packet]]` with:
- `current_stage`
- `next_required_skill`
- `binding_surface_kind`
- `allowed_outputs`
- `source_observation_artifact`
- `source_binding_artifact`
- `reference_state_revision`
- `packet_digest`
- `terminal_sink_handle`
- `non_self_source_handle`
- `title_non_self_source_handle`
- `title_shape_packets`
- `reference_slide_packet` with `slide_layout_target`, `title_shape`, and `body_shape`

The helper reloads both upstream artifacts, dereferences `copied_from_fragment_handle` before any owner-local title handle, and emits the exact writer schema. `title_shape_packets` must contain `slide_part`, `shape_id`, `text`, `shape_box`, `body_insets`, `paragraph_align`, and `run_style`; the Reference body copies ordered `current_reference_rows` from the current local state. Do not reload or reinterpret the earlier Reference observation. Compute `packet_digest` over the complete packet with only `packet_digest` itself excluded.

## Stop Condition

Stop after the packet exists. Treat it as the current writer input; do not patch individual Reference values or compare them with an earlier artifact.

---

## Step 4: `pptx-reference-formatting-processed-pptx-writer`

# PPTX Reference Formatting Processed PPTX Writer

Use this after `[[state:pptx-reference-formatting-resolved-edit-packet]]` is available. This stage writes the processed deck once from packet-owned title edits and current local Reference rows.

## Inputs
- prerequisite artifact: `[[state:pptx-reference-formatting-resolved-edit-packet]]`
- sink template: `/root/Awesome-Agent-Papers.pptx`
- consumed packet keys:
  - `current_stage`
  - `packet_digest`
  - `terminal_sink_handle`
  - `non_self_source_handle`
  - `title_shape_packets`
  - `reference_slide_packet`, including `slide_layout_target`, `title_shape`, `body_shape`, and `current_reference_rows`

## Allowed Outputs
- `/root/Awesome-Agent-Papers_processed.pptx`
- `[[state:pptx-reference-formatting-write-receipt]]`

## Command
Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:pptx-reference-formatting-resolved-edit-packet]]`, `[[state:pptx-reference-formatting-write-receipt]]`; task paths `/root/Awesome-Agent-Papers.pptx`, `/root/Awesome-Agent-Papers_processed.pptx`.

## Output Contract
The helper verifies `packet_digest` and renders every current Reference row exactly as carried by the packet. It may use the source deck only as the OOXML package template. Do not reopen the intake checkpoint, binding note, task description, or raw deck to re-derive or replace a Reference value; repair the current state upstream and rerun the binder if the packet is malformed.

The receipt must contain exactly these top-level keys:
- `current_stage`
- `source_packet_artifact`
- `packet_digest`
- `terminal_sink_handle`
- `non_self_source_handle`
- `packet_write_count_match`
- `placeholder_clearance`
- `written_values_match_packet`

## Next Required Skill
- none

## Integration Check

Before relying on the handoff, run the no-model chain check. It executes the four helpers in order and verifies current-state transport, packet schema, OOXML package, and writer receipt:

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:pptx-reference-formatting-integration-check]]`; task paths `/root/Awesome-Agent-Papers.pptx`.

## Stop Condition
Stop when the processed PPTX exists and the receipt reports `packet_write_count_match=true`, `placeholder_clearance=true`, and `written_values_match_packet=true`.

## Completion

Run the task-relevant checks described below, complete the required terminal action, and report observed task and endpoint or sink results truthfully.
