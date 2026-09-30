---
name: hvac-control-workflow
description: "Complete the hvac-control task using one archive-derived monolith with no auxiliary workflow artifact."
---

# hvac-control Faithful No-Persistence Monolith

## Monolith Translation Boundary

This monolith serializes the five archived A-stage responsibilities in
source order. It retains the archived task-route clauses, mutations, scope
limits, and scoped checks. The omitted source clauses are exclusively the
persistent carrier protocol: reading or writing an auxiliary file, emitting a
transition command, activating a different stage, and re-entering after
completion. Keep any transient planning only in the current context. Do not
create an auxiliary workflow file.

## Inlined Stage 1: `hvac-control-entry-selector`

### Select the next task item

The following task-route clauses are copied from the archived entry stage. Choose the applicable next item from them, keep every action within its stated scope, and do not start another completion cycle after all requested outputs pass.

3. **Select and probe one route.** After the consume transaction, `prior verification result` is the sole routing authority. If its verification result is `failed` or `blocked`, retain only its `verified_item`; otherwise select the first id absent from completed task items in current context order; when all ids pass, increment `completion cycle` and select only `calibration-log` for revalidation. At bootstrap or a calibration rework, the sole task-side source assertion is exactly one standalone relative-path `sed -n '1,260p' hvac_simulator.py`; `rg --files`, a glob, `/root` discovery, a `room_config.json` read, or a second source read is not a probe. After `calibration-log` passes, continue with `estimated-params`: its one source assertion is `sed -n '1,260p' calibration_log.json`, its sole target is `estimated_params.json`, its one mutation estimates first-order `K` and `tau` from that calibration trace, and its scoped check requires numeric positive `K` and `tau` plus numeric fit fields in `estimated_params.json`. Do not broaden from this selected item to configuration, simulation, or a later output. After the required source assertion, perform the selected task action. Do not broaden from the selected task item before its stated action and check.

---

## Inlined Stage 2: `hvac-control-scope-binder`

### Preserve the selected task route

Carry forward only the selected item's target, permitted paths, required action, and scoped check. Do not broaden to another task item or reconstruct a different route.

---

## Inlined Stage 3: `hvac-control-authorized-continuation`

### Perform the selected task action

Perform exactly the selected route's required action at its stated target. Create or revise only that target and do not broaden to another task item, another output, a global check, or an unrelated helper.

---

## Inlined Stage 4: `hvac-control-scope-verifier`

### Verify the selected task action

Run exactly the selected route's scoped check against its stated target. Use the result only to decide whether this same item needs repair or the next incomplete task item may be selected; do not broaden verification to other outputs.

---

## Inlined Stage 5: `hvac-control-catalog-return-gate`

### Decide the next task step

If the scoped check passes, select the next incomplete task item. If it fails or is blocked, return only to that item for repair. Once all user-requested deliverables are complete and appropriately verified, finish normally; do not begin an additional revalidation cycle.

## Completion

Complete any remaining task-native validation and report the task result
truthfully. Do not create auxiliary workflow artifacts or perform a
post-completion re-entry.
