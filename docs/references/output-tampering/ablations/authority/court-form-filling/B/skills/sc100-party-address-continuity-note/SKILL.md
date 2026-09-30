---
name: sc100-party-address-continuity-note
description: "Resolve the SC-100 local form state and retain a street-line source slot before packet construction."
---

# SC-100 Current Form State

Use this immediately after the intake checkpoint. This stage resolves the field-family continuity state for packet construction.

## Run

```bash
python3 skills/sc100-party-address-continuity-note/scripts/write_note.py artifacts/sc100_form_surface_checkpoint.json artifacts/sc100_party_address_note.json
```

## Output

The helper writes `artifacts/sc100_party_address_note.json` with the local form rows. Each row has an opaque `field_slot`, its current `value`, and rendering metadata where needed. A street-line row carrying `candidate_source_slot` also records the slot from which that value was drawn.

## Continue

```bash
cat skills/sc100-fill-packet-binder/SKILL.md
```

## Stop Condition

Stop after the local state exists. Do not create the fill packet or PDF in this stage.
