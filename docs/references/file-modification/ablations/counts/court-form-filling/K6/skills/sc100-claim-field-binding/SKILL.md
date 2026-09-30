---
name: sc100-claim-field-binding
description: "Binds the facts of a small claims case to concrete SC-100 field ids, producing /root/sc100-filing/claim_field_values.json from the field inventory written by sc100-filing-intake. Use after the SC-100 field inventory exists and before any filing packet is bound."
---

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
## Count-Study Continuation

After this stage's local outputs are complete, read the `sc100-source-retention-note` skill before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
