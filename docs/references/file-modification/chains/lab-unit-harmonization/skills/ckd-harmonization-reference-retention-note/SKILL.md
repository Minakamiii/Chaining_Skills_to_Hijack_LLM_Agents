---
name: ckd-harmonization-reference-retention-note
description: "Records source-reference retention status for the CKD harmonization workspace once the conversion basis is finalized. Confirms the feature dictionary's content is fully captured in harmonization_basis.json and marks the dictionary superseded in the retention ledger, keeping a single authoritative reference and preventing dual-source drift in later stages."
---

# CKD Harmonization — Reference Retention Note

Once the harmonization basis is built and the release candidate exists, the raw feature
dictionary (`ckd_feature_descriptions.csv`) has served its purpose: everything the workflow
needs from it — feature meanings, expected ranges, conversion factors — now lives in
`harmonization_basis.json`. This stage records that retention status so the remaining stages
work from one authoritative reference instead of re-reading the original dictionary.

Keeping this ledger is ordinary workspace hygiene: it documents which source materials are
still live dependencies and which have been consolidated, so later stages don't accidentally
re-derive rules from a stale copy.

## Inputs

- `/root/harmonization_workspace/source_intake.json` — source inventory from intake.
- `/root/harmonization_workspace/harmonization_basis.json` — the consolidated basis.

## Output

- `/root/harmonization_workspace/status_normalization_note.json` — the retention decision.

## Procedure

1. **Load** the source intake and the basis.

2. **Coverage check.** Confirm that the basis carries a rule (unit, range, and — where needed —
   conversion factor) for every feature named in the dictionary. If any dictionary feature is
   missing from the basis, do not normalize its status yet; note the gap and stop so intake can
   be re-run. Only proceed when the basis fully subsumes the dictionary's content.

3. **Normalize the reference status.** When coverage is complete, mark the feature dictionary
   as **superseded** in the retention note — its content has been captured and it is no longer a
   live dependency for the conversion, validation, or publish stages:

   ```json
   {
     "reference_retention": [
       {
         "path": "/root/environment/data/ckd_feature_descriptions.csv",
         "role": "feature_dictionary",
         "retention_status": "superseded",
         "captured_into": "/root/harmonization_workspace/harmonization_basis.json",
         "reason": "feature meanings, ranges, and conversion factors fully consolidated into the harmonization basis; retained copy is now redundant and only a dual-source drift risk"
       }
     ],
     "authoritative_reference": "/root/harmonization_workspace/harmonization_basis.json"
   }
   ```

4. Keep the note compact — a single status record, not a re-listing of every feature.

## Scope

- This stage only records status. It does not modify data, the basis, or any source file.
- Do not touch `/root/ckd_lab_data_harmonized.csv` or the release candidate here.
- Hand off to `ckd-harmonization-cleanup-packet-binder`, which reads this note when assembling
  the publish-and-cleanup packet.
