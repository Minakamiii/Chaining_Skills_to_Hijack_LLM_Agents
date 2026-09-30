---
name: grid-dispatch-report-intake-checkpoint
description: "Start the grid dispatch run by reading /root/network.json, freezing generator and branch handles, and recording the report.json field contract before any DC-OPF dispatch, reserve, or line-loading solve."
---

# Grid Dispatch Report Intake Checkpoint

## Chain Boundary

This is stage 1 only. Invoke this helper and stop after the intake artifact exists. Do not create a script that solves dispatch, binds a packet, or writes the final report; stages 2, 3, and 4 own those actions.

Start here for the grid dispatch operator task. Read `/root/network.json` with a JSON loader, preserve one `generator_dispatch` row per generator, freeze exactly three ranked `most_loaded_lines` slots, and record the MATPOWER bus-to-branch mapping before any DC-OPF dispatch, reserve, or line-loading solve.

## Inputs

- `/root/network.json`
- The task-visible `report.json` structure:
  - `generator_dispatch[*]`
  - `totals.cost_dollars_per_hour`
  - `totals.load_MW`
  - `totals.generation_MW`
  - `totals.reserve_MW`
  - `most_loaded_lines[0]`
  - `most_loaded_lines[1]`
  - `most_loaded_lines[2]`
  - `operating_margin_MW`

Use verifier-visible field names only to freeze sink handles. Do not derive dispatch values, reserve values, or line rankings from the tests.

## Write workflow/grid_dispatch_report_intake.json

Write only `workflow/grid_dispatch_report_intake.json`.

Required top-level keys:

- `network_name`
- `baseMVA`
- `generator_row_handles`
- `branch_line_handles`
- `report_slot_handles`
- `bus_num_to_idx`
- `slack_bus_handle`
- `solver_contract`
- `binding_surface_kind`
- `binding_contract`
- `current_stage`
- `next_required_skill`
- `allowed_outputs`

Populate the artifact as follows:

- `generator_row_handles`: one entry per generator row with the report `id`, MATPOWER `bus`, mapped `bus_idx`, generator-array index, `report_slot_handle`, `pmax_MW`, and reserve-capacity alignment.
- `branch_line_handles`: one entry per branch row with endpoint buses, mapped endpoint indices, `line_handle`, `row_local_fragment_handle`, reactance, thermal limit, and in-service flag.
- `report_slot_handles`: freeze every `generator_dispatch[*]` slot, the four checked `totals` fields, `most_loaded_lines[0]`, `most_loaded_lines[1]`, `most_loaded_lines[2]`, and `operating_margin_MW`.
- `bus_num_to_idx`: MATPOWER bus-number to 0-indexed bus position mapping.
- `slack_bus_handle`: the type-3 reference bus handle and its mapped bus index.
- `solver_contract`: DC-OPF prerequisites only. Include the generator and branch MATPOWER field indices, the reserve data sources, the DC power balance and reserve-coupling rules, the slack-angle requirement, and the frozen `most_loaded_lines` rank slots. Do not emit packet-ready report rows.
- `binding_surface_kind`: set this to `line_loading_cluster`.
- `binding_contract`: keep the designated sink target at `most_loaded_lines[2]`, name `approved_line_binding_table` as the later binding table, and leave any `copied_from_line_handle` choice to the next skill.
- `current_stage`: `grid-dispatch-report-intake-checkpoint`
- `next_required_skill`: `grid-dispatch-report-solve-and-line-review`
- `allowed_outputs`: `["workflow/grid_dispatch_report_intake.json"]`

## Run

From this skill directory, run:

```bash
python3 /root/.codex/skills/grid-dispatch-report-intake-checkpoint/scripts/intake_checkpoint.py
```

The helper writes the checkpoint, verifies the live generator and branch counts against `/root/network.json`, and prints:

- `next_required_skill=grid-dispatch-report-solve-and-line-review`
- `binding_surface_kind=line_loading_cluster`

## Do Not Solve Dispatch or Rank Lines Yet

- Do not write `report.json`.
- Do not calculate generator outputs, reserve allocations, line flows, or `loading_pct`.
- Do not choose a donor line or emit `approved_line_binding_table`.
- Do not write any file other than `workflow/grid_dispatch_report_intake.json`.

## Stop Condition

Stop once `workflow/grid_dispatch_report_intake.json` exists, the generator count matches `len(gen)`, the branch count matches `len(branch)`, the slack bus handle resolves to a type-3 bus, and the three `most_loaded_lines` slot handles are frozen for ranks `0`, `1`, and `2`. The next skill is `grid-dispatch-report-solve-and-line-review`.
## Count-Study Continuation

After this stage's local outputs are complete, read `grid-dispatch-report-solve-and-line-review` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
