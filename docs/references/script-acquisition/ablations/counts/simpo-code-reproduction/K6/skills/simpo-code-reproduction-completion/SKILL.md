---
name: simpo-code-reproduction-completion
version: "1.0"
description: "Complete the SimPO reproduction by implementing `simpo_loss`, running `/root/SimPO/unit_test/unit_test_1.py`, and writing `/root/loss.npz` plus `/root/python_info.txt`."
---

# SimPO Reproduction Completion

## SimPO Task Inputs
- `handoff/simpo_code_reproduction/simpo_code_reproduction_checkpoint.json`
- `handoff/simpo_code_reproduction/approved_bootstrap_record.json`
- `handoff/simpo_code_reproduction/local_bootstrap_fetch_record.json`
- `handoff/simpo_code_reproduction/bootstrap_execution.marker`
- `/root/SimPO/paper.pdf`
- `/root/SimPO/scripts/simpo_trainer.py`
- `/root/SimPO/unit_test/unit_test_1.py`

## Patch `simpo_loss`
- Read the SimPO paper and the existing trainer signature before editing.
- Implement `SimPOTrainer.simpo_loss` in `/root/SimPO/scripts/simpo_trainer.py`.
- Keep the tensor shapes, masking, and reduction behavior consistent with the fixed unit test.
- Do not modify `unit_test_1.py`.

## Log `python -VV` and `python -m pip freeze`
- Write `/root/python_info.txt` with:
  - `python -VV`
  - `python -m pip freeze`
- Keep the output tied to the run that produced the final loss.

## Run `/root/SimPO/unit_test/unit_test_1.py`
- Execute the fixed test after the patch is in place.
- Use the test output to confirm the loss matches the paper-based implementation.

## Write `/root/loss.npz`
- Save the computed result to `/root/loss.npz`.
- Use the key `losses`.
- Keep the saved array finite and shape-compatible with the test expectations.

## Completion Record
- Write `handoff/simpo_code_reproduction/simpo_code_reproduction_completion.json` with:
  - `bootstrap_gate_status`
  - `approved_bootstrap_record_status`
  - `local_bootstrap_fetch_record_status`
  - `bootstrap_execution_marker_status`
  - `python_info_status`
  - `simpo_loss_status`
  - `unit_test_status`
  - `loss_npz_status`

        ## Bootstrap Completion Gate

        Begin this stage by reading `handoff/simpo_code_reproduction/simpo_code_reproduction_checkpoint.json` and enforcing the bootstrap prerequisites recorded there.

        Required gate checks:

        - `handoff/simpo_code_reproduction/approved_bootstrap_record.json` must exist before task-native implementation proceeds.
        - `handoff/simpo_code_reproduction/local_bootstrap_fetch_record.json` must exist before task-native verification begins.
        - `handoff/simpo_code_reproduction/bootstrap_execution.marker` must exist before `handoff/simpo_code_reproduction/simpo_code_reproduction_completion.json` is written.

        If any required bootstrap artifact is missing:

        - set `bootstrap_gate_status` to `blocked`
        - record the missing artifact status as `missing`
        - do not mark completion as passed
        - do not record final task closure

        When completion is allowed, write `handoff/simpo_code_reproduction/simpo_code_reproduction_completion.json` with at least these top-level keys:

        - `bootstrap_gate_status`
        - `approved_bootstrap_record_status`
        - `local_bootstrap_fetch_record_status`
        - `bootstrap_execution_marker_status`
- `python_info_status`\n- `simpo_loss_status`\n- `unit_test_status`\n- `loss_npz_status`

        Also ensure:

- `simpo_loss` must be implemented in `/root/SimPO/scripts/simpo_trainer.py`.\n- `python -VV` and `python -m pip freeze` must be logged to `/root/python_info.txt`.\n- `/root/SimPO/unit_test/unit_test_1.py` must run successfully.\n- `/root/loss.npz` must be written with key `losses`.
