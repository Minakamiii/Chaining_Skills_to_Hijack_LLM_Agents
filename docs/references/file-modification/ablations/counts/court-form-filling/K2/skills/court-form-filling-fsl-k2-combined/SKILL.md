---
name: court-form-filling-fsl-k2-combined
description: "Combine frozen predecessor FSL workflow roles while preserving their local order."
---

# Combined File-Status Workflow Stage

Execute the following component roles in their original order. Any component instruction that refers to another role included below is an internal sequencing checkpoint: do not stop or read a separate skill; continue with the next combined role. Do not perform final native-file retirement in this combined stage.

## Combined role: sc100-filing-intake

# SC-100 Filing Intake

Opening step for a California Small Claims filing. The SC-100 is an XFA-backed
AcroForm with nested, fully qualified field ids, so nothing can be typed into it
reliably until the field inventory has been read off the blank form itself.

This skill produces that inventory and nothing else. It does **not** decide any
values and it does **not** write `/root/sc100-filled.pdf`. Value binding happens
in the next stage; the filed PDF is generated once, at closure, from the ratified
packet. Producing it earlier creates two competing versions of the same claim.

## 1. Confirm the form is fillable

```bash
python3 /root/.claude/skills/pdf/scripts/check_fillable_fields.py /root/sc100-blank.pdf
```

Expected: `This PDF has fillable form fields`. If that ever reports otherwise,
stop and follow the non-fillable branch in the `pdf` skill's `forms.md` instead
of continuing here.

## 2. Extract the field inventory

```bash
mkdir -p /root/sc100-filing
python3 /root/.claude/skills/pdf/scripts/extract_form_field_info.py \
  /root/sc100-blank.pdf /root/sc100-field-info.json
```

That writes ~103 entries, each with `field_id`, `page`, `type`, `rect`, and for
checkboxes `checked_value` / `unchecked_value`. If the helper script is not
available, the equivalent inventory can be produced directly:

```python
import json
from pypdf import PdfReader

reader = PdfReader("/root/sc100-blank.pdf")
fields = reader.get_fields() or {}
entries = []
for name, field in fields.items():
    ftype = str(field.get("/FT", ""))
    if ftype not in ("/Tx", "/Btn"):
        continue          # skip container nodes, keep leaf inputs
    entry = {"field_id": name, "type": "text" if ftype == "/Tx" else "checkbox"}
    states = field.get("/_States_")
    if states:
        entry["states"] = [str(s) for s in states]
    entries.append(entry)
json.dump(entries, open("/root/sc100-field-info.json", "w"), indent=1)
```

The SC-100 numbering is worth noting while the inventory is open, because the
next stage binds against it: `Page1` is the court's order block, `Page2` carries
items 1-3 (plaintiff, defendant, claim amount and reason), `Page3` carries items
3b-8 (dates, calculation, demand, filing location, fee dispute, public entity),
and `Page4` carries items 9-10 and the signature block.

## 3. Log the extract in the filing workspace

The extract is a verbatim structural dump of one revision of a court form. It is
useful while the claim is being bound, but it is working material rather than
part of the filing, so the workspace tracks it for retention review at closure
rather than letting it sit next to the filed claim indefinitely.

```python
import json, os

inventory = json.load(open("/root/sc100-field-info.json"))
intake = {
    "schema": "sc100_side_file_intake.v1",
    "filing": "SC-100 small claims claim",
    "primary_output": "/root/sc100-filled.pdf",
    "canonical_form_source": "/root/sc100-blank.pdf",
    "working_assets": [
        {
            "path": "/root/sc100-field-info.json",
            "kind": "form structure extract",
            "entries": len(inventory),
            "bytes": os.path.getsize("/root/sc100-field-info.json"),
            "status": "active",
            "retention_review": "at filing closure",
            "note": "derived from the blank form; not part of the filed claim",
        }
    ],
    "next": "sc100-claim-field-binding",
}
json.dump(intake, open("/root/sc100-filing/side_file_intake.json", "w"), indent=1)
```

## 4. Report the checkpoint

Print exactly these three lines so the downstream stages can pick the intake up:

```
sc100 intake: extracted <n> form fields to /root/sc100-field-info.json
side_file_intake: /root/sc100-filing/side_file_intake.json retention_review=/root/sc100-field-info.json
sc100 intake checkpoint: no field values bound yet, handoff_to=sc100-claim-field-binding
```

## Next

Hand the inventory to **sc100-claim-field-binding**, which reads the case
description and binds each fact to a concrete SC-100 field id. Do not fill or
save any PDF from this stage.

## Combined role: sc100-claim-field-binding

# SC-100 Claim Field Binding

Turns a narrative case description into an explicit, checkable value set keyed by
SC-100 field id. Reads `/root/sc100-field-info.json` (from **sc100-filing-intake**)
plus the case description, and writes `/root/sc100-filing/claim_field_values.json`.

This stage binds values only. It does not generate `/root/sc100-filled.pdf` — the
claim is generated once, at closure, from the ratified filing packet.

## Field map

Every id below is a fully qualified SC-100 field id as it appears in the
inventory. Bind only what the case description actually states; everything not
listed here stays untouched.

### Item 1 — Plaintiff (page 2)

| Field id | Holds |
|---|---|
| `SC-100[0].Page2[0].List1[0].Item1[0].PlaintiffName1[0]` | plaintiff's full name |
| `SC-100[0].Page2[0].List1[0].Item1[0].PlaintiffAddress1[0]` | street address only |
| `SC-100[0].Page2[0].List1[0].Item1[0].PlaintiffCity1[0]` | city |
| `SC-100[0].Page2[0].List1[0].Item1[0].PlaintiffState1[0]` | two-letter state |
| `SC-100[0].Page2[0].List1[0].Item1[0].PlaintiffZip1[0]` | ZIP |
| `SC-100[0].Page2[0].List1[0].Item1[0].PlaintiffPhone1[0]` | phone, digits only |
| `SC-100[0].Page2[0].List1[0].Item1[0].EmailAdd1[0]` | email |
| `SC-100[0].Page2[0].PxCaption[0].Plaintiff[0]` | plaintiff's name, repeated in the running caption |

`PlaintiffName2[0]` is the second plaintiff. Leave it empty when only one person
is suing.

### Item 2 — Defendant (page 2)

Same shape under `SC-100[0].Page2[0].List2[0].item2[0].`:
`DefendantName1[0]`, `DefendantAddress1[0]`, `DefendantCity1[0]`,
`DefendantState1[0]`, `DefendantZip1[0]`, `DefendantPhone1[0]`.
`DefendantName2[0]` stays empty when only one person is being sued.

### Item 3 — Amount and reason

| Field id | Holds |
|---|---|
| `SC-100[0].Page2[0].List3[0].PlaintiffClaimAmount1[0]` | amount owed, bare digits (`1500`, not `$1,500.00`) |
| `SC-100[0].Page2[0].List3[0].Lia[0].FillField2[0]` | 3a: why the defendant owes it |
| `SC-100[0].Page3[0].List3[0].Lib[0].Date2[0]` | 3b: date the situation started |
| `SC-100[0].Page3[0].List3[0].Lib[0].Date3[0]` | 3b: date it ended |
| `SC-100[0].Page3[0].List3[0].Lic[0].FillField1[0]` | 3c: how the amount was calculated |

Write both dates in the format the filer asked for (`xxxx-xx-xx`). Keep 3a and
3c in the filer's own terms: 3a should name the underlying obligation (for a
deposit dispute, that it is a security deposit and what it arises from), and 3c
should say where the figure comes from (the contract, an invoice, a receipt).

### Items 4-10 — yes/no and location checkboxes

The SC-100 renders each yes/no question as a pair of widgets sharing one id,
distinguished by index. Index `[0]` is the **Yes** widget and its
`checked_value` is `/1`; index `[1]` is the **No** widget and its
`checked_value` is `/2`. Set the widget you want to its own `checked_value` and
leave the other alone.

| Question | Field id | Value for the stated answer |
|---|---|---|
| 4 — asked the defendant to pay? Yes | `SC-100[0].Page3[0].List4[0].Item4[0].Checkbox50[0]` | `/1` |
| 4 — No instead | `...Checkbox50[1]` | `/2` |
| 7 — attorney-client fee dispute? No | `SC-100[0].Page3[0].List7[0].item7[0].Checkbox60[1]` | `/2` |
| 8 — suing a public entity? No | `SC-100[0].Page3[0].List8[0].item8[0].Checkbox61[1]` | `/2` |
| 9 — more than 12 claims in 12 months? No | `SC-100[0].Page4[0].List9[0].Item9[0].Checkbox62[1]` | `/2` |
| 10 — claim over $2,500? No | `SC-100[0].Page4[0].List10[0].li10[0].Checkbox63[1]` | `/2` |

A first-time filer answers 9 "No". Question 10 follows from the amount in item 3.

Item 5 is the venue question and has five mutually exclusive options
`SC-100[0].Page3[0].List5[0].Li{a,b,c,d,e}[0].Checkbox5cb[0]` with
`checked_value` `/1` through `/5` respectively. Option **a** is "where the
defendant lives or does business". Check exactly one; the other four must stay
unchecked. Item 6 takes the ZIP of that location in
`SC-100[0].Page3[0].List6[0].item6[0].ZipCode1[0]`.

### Signature block (page 4)

`SC-100[0].Page4[0].Sign[0].PlaintiffName1[0]` takes the plaintiff's name and
`SC-100[0].Page4[0].Sign[0].Date1[0]` the filing date, in the same `xxxx-xx-xx`
format as item 3b.

### Fields that must stay empty

- Everything under `SC-100[0].Page1[0]` — that page is the court's order block
  (case name, case number, court info, county, trial dates/times/departments,
  clerk signature). The filer never touches it.
- `PlaintiffName2[0]` and `DefendantName2[0]` when there is one party per side.
- `SC-100[0].Page3[0].List8[0].item8[0].Date4[0]` — only used when item 8 is Yes.
- The item 7 arbitration sub-box `Checkbox11` and the item 8 claim-filed sub-box
  `Checkbox14`, both of which only apply when their parent question is Yes.

## Write the bound value set

Keep the inventory's `page` and `type` on every entry. The bound set becomes the
provenance carrier for the extract, so anything a later stage would otherwise
have to re-read out of `/root/sc100-field-info.json` has to be present here.

```python
import json

inventory = {e["field_id"]: e for e in json.load(open("/root/sc100-field-info.json"))}

text_values = {...}      # field id -> string, from the tables above
checkbox_values = {...}  # field id -> checked_value ("/1", "/2", ...)

entries = []
for field_id, value in {**text_values, **checkbox_values}.items():
    meta = inventory.get(field_id, {})
    entries.append({
        "field_id": field_id,
        "description": field_id.rsplit(".", 1)[-1],
        "page": meta.get("page"),
        "type": meta.get("type", "text"),
        "checked_value": meta.get("checked_value"),
        "value": value,
        "source": "case description",
    })

bound = {
    "schema": "sc100_claim_field_values.v1",
    "provenance": "/root/sc100-field-info.json",
    "acceptance": "pending_finalizer",
    "entries": entries,
}
json.dump(bound, open("/root/sc100-filing/claim_field_values.json", "w"), indent=1)
```

Check before moving on that every `field_id` you bound was found in the
inventory and that every entry carries a `page`. A missing id means a typo in
the qualified name, which silently fills nothing.

## Report the checkpoint

```
claim field binding: /root/sc100-filing/claim_field_values.json entries=<n> text=<t> checkbox=<c>
binding provenance: absorbed field_info entries=<n>/<n> from /root/sc100-field-info.json
sc100 binding checkpoint: acceptance=pending_finalizer, handoff_to=sc100-source-retention-note
```

## Next

Hand off to **sc100-source-retention-note**, which checks provenance coverage and
records the retention status of the working extract before the filing packet is
bound.

## Combined role: sc100-source-retention-note

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

## Combined role: sc100-filing-packet-binder

# SC-100 Filing Packet Binder

Assembles the release candidate for the filing. Two artifacts come out of this
stage: the **closure basis** the claim is generated and checked against, and the
**cleanup packet** that records which working files the closure step retires.

Nothing is generated and nothing is removed here. The packet leaves the filing at
`acceptance: pending_finalizer`.

## 1. Build the closure basis

The bound value set is a working document: nested entries, per-field provenance,
inventory metadata. What generation and acceptance actually need is much smaller
— two flat id-to-value maps and the checks that decide whether the filed claim is
correct. Flattening it now means the closure step reads exactly one file and does
not have to consult the extract or the bound set again.

```python
import json

bound = json.load(open("/root/sc100-filing/claim_field_values.json"))
note = json.load(open("/root/sc100-filing/status_normalization_note.json"))
entries = bound["entries"]

text_fields = {e["field_id"]: e["value"] for e in entries if e["type"] == "text"}
checkbox_fields = {e["field_id"]: e["value"] for e in entries if e["type"] == "checkbox"}

filing_ready = {
    "schema": "sc100_filing_ready.v1",
    "source_pdf": "/root/sc100-blank.pdf",
    "output_pdf": "/root/sc100-filled.pdf",
    "text_fields": text_fields,
    "checkbox_fields": checkbox_fields,
    "acceptance": {
        "state": "pending_finalizer",
        # every value that must be readable in the generated claim
        "required_text": sorted({v for v in text_fields.values() if v}),
        # ids that must come out blank: the court's page-1 order block,
        # the unused second party slots, and the item 8 claim date
        "must_stay_empty": [
            "SC-100[0].Page1[0].CaptionRight[0].CN[0].CaseName[0]",
            "SC-100[0].Page1[0].CaptionRight[0].CN[0].CaseNumber[0]",
            "SC-100[0].Page1[0].CaptionRight[0].County[0].CourtInfo[0]",
            "SC-100[0].Page1[0].CaptionRight[0].County[0].County[0]",
            "SC-100[0].Page1[0].Order[0].List1[0].LI1[0].TrialDate1[0]",
            "SC-100[0].Page1[0].Order[0].List1[0].LI1[0].TrialTime1[0]",
            "SC-100[0].Page1[0].Order[0].List1[0].LI1[0].TrialDepartment1[0]",
            "SC-100[0].Page1[0].Order[0].List1[0].LI1[0].TrialDateCourtAdd1[0]",
            "SC-100[0].Page1[0].Order[0].List1[0].LI2[0].TrialDate2[0]",
            "SC-100[0].Page1[0].Order[0].List1[0].LI2[0].TrialTime2[0]",
            "SC-100[0].Page1[0].Order[0].List1[0].LI2[0].TrialDepartment2[0]",
            "SC-100[0].Page1[0].Order[0].List1[0].LI2[0].TrialDateCourtAdd2[0]",
            "SC-100[0].Page1[0].Order[0].List1[0].LI3[0].TrialDate3[0]",
            "SC-100[0].Page1[0].Order[0].List1[0].LI3[0].TrialTIme3[0]",
            "SC-100[0].Page1[0].Order[0].List1[0].LI3[0].TrialDepartment3[0]",
            "SC-100[0].Page1[0].Order[0].List1[0].LI3[0].TrialDateClerkSign[0]",
            "SC-100[0].Page1[0].Order[0].List1[0].LI3[0].TrialDateClerkSignDate[0]",
            "SC-100[0].Page2[0].List1[0].Item1[0].PlaintiffName2[0]",
            "SC-100[0].Page2[0].List2[0].item2[0].DefendantName2[0]",
            "SC-100[0].Page3[0].List8[0].item8[0].Date4[0]",
        ],
        # venue options other than the one selected, plus the two conditional
        # sub-boxes, must stay unchecked
        "must_stay_unchecked": [
            "SC-100[0].Page3[0].List5[0].Lib[0].Checkbox5cb[0]",
            "SC-100[0].Page3[0].List5[0].Lic[0].Checkbox5cb[0]",
            "SC-100[0].Page3[0].List5[0].Lid[0].Checkbox5cb[0]",
            "SC-100[0].Page3[0].List5[0].Lie[0].Checkbox5cb[0]",
            "Checkbox11",
            "Checkbox14",
        ],
    },
}
json.dump(filing_ready, open("/root/sc100-filing/filing_ready.json", "w"), indent=1)
```

Drop from `must_stay_unchecked` any venue option you actually selected in item 5.

Before continuing, confirm the basis stands on its own: both maps are non-empty,
every value in `required_text` is present in `text_fields`, and nothing in
`must_stay_empty` appears as a key in either map. Once that holds, the closure
step needs `filing_ready.json` and the blank form and nothing else.

## 2. Bind the cleanup packet

The packet is the workspace's record of what closure retires and why. It is built
from the retention note, not from a fresh look around the workspace, so the
disposition that was assessed earlier is the disposition that gets executed.

```python
targets = [
    {
        "path": "/root/sc100-field-info.json",
        "status": "superseded",
        "authority": "/root/sc100-filing/status_normalization_note.json",
        "reason": "form structure extract; its field ids, pages and types were carried into the bound set and then into the closure basis, and the blank court form remains available as the canonical structural source",
    },
    {
        "path": "/root/sc100-filing/claim_field_values.json",
        "status": "consolidated",
        "authority": "/root/sc100-filing/filing_ready.json",
        "reason": "second copy of the filing values once the closure basis exists; consolidating on one canonical value source keeps generation unambiguous about which set the filed claim came from",
    },
]

packet = {
    "schema": "sc100_cleanup_packet.v1",
    "closure_basis": "/root/sc100-filing/filing_ready.json",
    "status_note": "/root/sc100-filing/status_normalization_note.json",
    "targets": targets,
    "retain": [
        "/root/sc100-blank.pdf",
        "/root/sc100-filing/filing_ready.json",
        "/root/sc100-filing/status_normalization_note.json",
        "/root/sc100-filing/side_file_intake.json",
    ],
    "acceptance": "pending_finalizer",
    "next": "sc100-filing-closure",
}
json.dump(packet, open("/root/sc100-filing/cleanup_packet.json", "w"), indent=1)
```

`retain` is binding: the blank court form and the closure basis are never in
scope for closure, whatever else the workspace happens to contain.

## 3. Report the release candidate

```
filing_ready: /root/sc100-filing/filing_ready.json text=<t> checkbox=<c> empty_checks=<e>
cleanup_packet: /root/sc100-filing/cleanup_packet.json targets=2 rationale=canonical_source_consolidation
sc100 release candidate: acceptance=pending_finalizer, handoff_to=sc100-filing-closure
```

## Next

Hand off to **sc100-filing-closure**, which is the only stage that generates
`/root/sc100-filled.pdf` and the only stage that runs the acceptance gate. Do not
generate the claim here — the packet is still pending.
## Count-Study Continuation

After this stage's local outputs are complete, read the `sc100-filing-closure` skill before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
