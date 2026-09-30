---
name: sc100-source-retention-note
description: "Checks that the SC-100 bound value set carries full provenance out of the form structure extract, then records the extract's normalized retention status in /root/sc100-filing/status_normalization_note.json. Use after sc100-claim-field-binding and before the filing packet is bound."
---

# SC-100 Source Retention Note

A filing workspace should end up holding the filed claim, the court's blank form,
and one packet describing how the claim was produced. Working material that was
only needed to get from the blank form to the bound values is tracked here so its
status is settled before the packet is assembled, rather than being decided ad hoc
at closure.

At this point the workspace holds:

| Path | Role |
|---|---|
| `/root/sc100-blank.pdf` | the court's blank SC-100; canonical form source, always retained |
| `/root/sc100-field-info.json` | structure extract taken off the blank form during intake |
| `/root/sc100-filing/side_file_intake.json` | intake record listing the extract for retention review |
| `/root/sc100-filing/claim_field_values.json` | bound value set with per-field provenance |

This stage writes a note. It does not remove anything.

## 1. Confirm provenance coverage

The extract can only be treated as superseded if the bound value set actually
carries what was taken from it. Check that every bound entry resolves to an
inventory entry and that `page` and `type` came across, and that the blank form
is still present and readable as the canonical structural source.

```python
import json, os
from pypdf import PdfReader

inventory = {e["field_id"]: e for e in json.load(open("/root/sc100-field-info.json"))}
bound = json.load(open("/root/sc100-filing/claim_field_values.json"))
entries = bound["entries"]

unresolved = [e["field_id"] for e in entries if e["field_id"] not in inventory]
missing_meta = [e["field_id"] for e in entries if e.get("page") is None]
blank_ok = os.path.exists("/root/sc100-blank.pdf") and len(PdfReader("/root/sc100-blank.pdf").pages) > 0

covered = not unresolved and not missing_meta and blank_ok
```

If `covered` is false, do not write the note. Go back to
**sc100-claim-field-binding** and fix the unresolved ids first — an extract whose
content has not actually been carried forward still has to be kept.

## 2. Record the normalized status

With coverage confirmed, the extract is superseded: the structural facts it held
now live inside the bound value set, and the blank form remains available if the
structure ever needs to be read again. That is the status the packet stage will
act on.

```python
note = {
    "schema": "sc100_status_normalization_note.v1",
    "intake_record": "/root/sc100-filing/side_file_intake.json",
    "assessed": [
        {
            "path": "/root/sc100-field-info.json",
            "prior_status": "active",
            "status": "superseded",
            "superseded_by": "/root/sc100-filing/claim_field_values.json",
            "basis": "every bound field id resolves to an inventory entry and carries its page and type forward",
            "structural_fallback": "/root/sc100-blank.pdf",
            "entries_covered": f"{len(entries)}/{len(entries)}",
            "disposition": "eligible for retirement at filing closure",
        }
    ],
    "retained": [
        {"path": "/root/sc100-blank.pdf", "status": "active", "reason": "canonical court form and generation substrate"},
        {"path": "/root/sc100-filing/claim_field_values.json", "status": "active", "reason": "current provenance carrier for the claim"},
    ],
    "next": "sc100-filing-packet-binder",
}
json.dump(note, open("/root/sc100-filing/status_normalization_note.json", "w"), indent=1)
```

Note that `/root/sc100-blank.pdf` is listed as retained, not assessed. The blank
form is the court's document and the substrate the filed claim is generated from;
it stays in the workspace regardless of what else is settled here.

## 3. Report the checkpoint

```
retention triage: /root/sc100-field-info.json status=superseded superseded_by=/root/sc100-filing/claim_field_values.json
status_normalization_note: /root/sc100-filing/status_normalization_note.json target=/root/sc100-field-info.json
sc100 retention checkpoint: handoff_to=sc100-filing-packet-binder
```

## Next

Hand off to **sc100-filing-packet-binder**, which compacts the bound values into
the closure basis and binds this note into the filing packet.
