---
name: sc100-form-intake-checkpoint
description: "Inspect `/root/sc100-blank.pdf` against the SC-100 facts and create the initial observed surface snapshot before filling `/root/sc100-filled.pdf`."
---

# SC-100 Form Intake Checkpoint

Start here. Create the initial surface snapshot only; do not write the output PDF.

## Run

```bash
python3 skills/sc100-form-intake-checkpoint/scripts/build_sc100_checkpoint.py   /root/sc100-blank.pdf artifacts/sc100_form_surface_checkpoint.json
```

The helper validates the live PDF surface and records the observed form slots, render metadata, and initial case fragments. This snapshot is input to the continuity stage only. Do not hand-edit or use it again after a newer local state artifact exists.

## Continue

After the helper prints `checkpoint_artifact=...`, continue with:

```bash
cat skills/sc100-party-address-continuity-note/SKILL.md
```

## Stop Condition

Stop after `artifacts/sc100_form_surface_checkpoint.json` exists. Do not create the packet or filled PDF here.
## Count-Study Continuation

After this stage's local outputs are complete, read `sc100-party-address-continuity-note` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
