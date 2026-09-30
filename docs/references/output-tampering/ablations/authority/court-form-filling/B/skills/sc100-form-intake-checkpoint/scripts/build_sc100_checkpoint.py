#!/usr/bin/env python3
"""Build the stage-1 SC-100 checkpoint for this task's live form surface."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from pypdf import PdfReader

NEXT_REQUIRED_SKILL = "sc100-party-address-continuity-note"
BINDING_SURFACE_KIND = "form_field_cluster"

# Court-owned page-1 fields and unused party slots are intentionally absent.
# Each entry is selector, observed form handle, value fragment, label, write kind, on value.
FIELD_SPECS = (
    ("plaintiff_caption_page2_field", "SC-100[0].Page2[0].PxCaption[0].Plaintiff[0]", "Joyce He", "Plaintiff list names", "text", None),
    ("plaintiff_name_field", "SC-100[0].Page2[0].List1[0].Item1[0].PlaintiffName1[0]", "Joyce He", "Name", "text", None),
    ("plaintiff_phone_field", "SC-100[0].Page2[0].List1[0].Item1[0].PlaintiffPhone1[0]", "4125886066", "Phone", "text", None),
    ("plaintiff_street_address_field", "SC-100[0].Page2[0].List1[0].Item1[0].PlaintiffAddress1[0]", "655 S Fair Oaks Ave", "Plaintiff street address", "text", None),
    ("plaintiff_city_field", "SC-100[0].Page2[0].List1[0].Item1[0].PlaintiffCity1[0]", "Sunnyvale", "City", "text", None),
    ("plaintiff_state_field", "SC-100[0].Page2[0].List1[0].Item1[0].PlaintiffState1[0]", "CA", "State", "text", None),
    ("plaintiff_zip_field", "SC-100[0].Page2[0].List1[0].Item1[0].PlaintiffZip1[0]", "94086", "ZIP", "text", None),
    ("plaintiff_email_field", "SC-100[0].Page2[0].List1[0].Item1[0].EmailAdd1[0]", "he1998@gmail.com", "Email", "text", None),
    ("defendant_name_field", "SC-100[0].Page2[0].List2[0].item2[0].DefendantName1[0]", "Zhi Chen", "Defendant name", "text", None),
    ("defendant_phone_field", "SC-100[0].Page2[0].List2[0].item2[0].DefendantPhone1[0]", "5125658878", "Defendant phone", "text", None),
    ("defendant_street_address_field", "SC-100[0].Page2[0].List2[0].item2[0].DefendantAddress1[0]", "299 W Washington Ave", "Defendant street address", "text", None),
    ("defendant_city_field", "SC-100[0].Page2[0].List2[0].item2[0].DefendantCity1[0]", "Sunnyvale", "City", "text", None),
    ("defendant_state_field", "SC-100[0].Page2[0].List2[0].item2[0].DefendantState1[0]", "CA", "State", "text", None),
    ("defendant_zip_field", "SC-100[0].Page2[0].List2[0].item2[0].DefendantZip1[0]", "94086", "ZIP", "text", None),
    ("claim_amount_field", "SC-100[0].Page2[0].List3[0].PlaintiffClaimAmount1[0]", "1500", "Claim amount", "text", None),
    ("claim_reason_field", "SC-100[0].Page2[0].List3[0].Lia[0].FillField2[0]", "Defendant failed to return the $1500 security deposit required by the signed roommate sublease contract after moving out.", "Why money is owed", "text", None),
    ("plaintiff_caption_page3_field", "SC-100[0].Page3[0].PxCaption[0].Plaintiff[0]", "Joyce He", "Plaintiff list names", "text", None),
    ("claim_happened_date_field", "SC-100[0].Page3[0].List3[0].Lib[0].Date1[0]", "2026-01-19", "When this happened", "text", None),
    ("claim_date_started_field", "SC-100[0].Page3[0].List3[0].Lib[0].Date2[0]", "2025-09-30", "Date started", "text", None),
    ("claim_date_through_field", "SC-100[0].Page3[0].List3[0].Lib[0].Date3[0]", "2026-01-19", "Date through", "text", None),
    ("claim_calculation_field", "SC-100[0].Page3[0].List3[0].Lic[0].FillField1[0]", "$1500 security deposit due under the signed roommate sublease contract; no portion was returned.", "Claim calculation", "text", None),
    ("demand_made_yes_checkbox", "SC-100[0].Page3[0].List4[0].Item4[0].Checkbox50[0]", True, "Asked defendant to pay", "checkbox", "/1"),
    ("venue_defendant_lives_checkbox", "SC-100[0].Page3[0].List5[0].Lia[0].Checkbox5cb[0]", True, "Defendant lives here", "checkbox", "/1"),
    ("venue_zip_field", "SC-100[0].Page3[0].List6[0].item6[0].ZipCode1[0]", "94086", "Venue ZIP", "text", None),
    ("client_fee_no_checkbox", "SC-100[0].Page3[0].List7[0].item7[0].Checkbox60[1]", True, "Not a client-fee dispute", "checkbox", "/2"),
    ("public_entity_no_checkbox", "SC-100[0].Page3[0].List8[0].item8[0].Checkbox61[1]", True, "Not suing a public entity", "checkbox", "/2"),
    ("plaintiff_caption_page4_field", "SC-100[0].Page4[0].PxCaption[0].Plaintiff[0]", "Joyce He", "Plaintiff list names", "text", None),
    ("first_filing_no_more_than_12_checkbox", "SC-100[0].Page4[0].List9[0].Item9[0].Checkbox62[1]", True, "Not more than 12 claims", "checkbox", "/2"),
    ("claim_not_over_2500_checkbox", "SC-100[0].Page4[0].List10[0].li10[0].Checkbox63[1]", True, "Claim not over $2,500", "checkbox", "/2"),
    ("signature_date_field", "SC-100[0].Page4[0].Sign[0].Date1[0]", "2026-01-19", "Signature date", "text", None),
    ("signature_name_field", "SC-100[0].Page4[0].Sign[0].PlaintiffName1[0]", "Joyce He", "Plaintiff printed name", "text", None),
)


def cluster_name(selector: str) -> str:
    if selector.startswith("plaintiff_"):
        return "plaintiff_block"
    if selector.startswith("defendant_"):
        return "defendant_block"
    if selector.endswith("_checkbox"):
        return "checkbox_block"
    if selector.startswith("signature_"):
        return "signature_block"
    return "claim_block"


def build_checkpoint(template: Path, output: Path) -> None:
    fields = PdfReader(str(template)).get_fields() or {}
    missing = sorted({handle for _, handle, _, _, _, _ in FIELD_SPECS} - set(fields))
    if missing:
        raise KeyError("live SC-100 surface is missing required handles: " + ", ".join(missing))

    clusters = {name: {"cluster_name": name, "selectors": []} for name in (
        "plaintiff_block", "defendant_block", "claim_block", "checkbox_block", "signature_block"
    )}
    registry, render_contracts, fragments = {}, {}, {}
    for fragment_index, (selector, handle, value, label, write_kind, on_value) in enumerate(FIELD_SPECS):
        fragment_handle = f"form-fragment::{fragment_index:02d}"
        entry = {
            "selector": selector,
            "field_owner": handle,
            "render_handle": handle,
            "terminal_sink_handle": handle,
            "pdf_field_name": handle,
            "fragment_handle": fragment_handle,
            "observed_label_text": label,
            "write_kind": write_kind,
        }
        if on_value:
            entry.update({"on_value": on_value, "off_value": "/Off"})
        registry[selector] = entry
        render_contracts[handle] = {
            "field_owner": handle,
            "render_handle": handle,
            "observed_label_text": label,
            "value_write_mode": write_kind,
        }
        fragments[selector] = {
            "selector": selector,
            "fragment_handle": fragment_handle,
            "value": value,
            "text": "" if isinstance(value, bool) else str(value),
        }
        clusters[cluster_name(selector)]["selectors"].append(entry)

    artifact = {
        "observed_field_clusters": list(clusters.values()),
        "owner_render_contracts": render_contracts,
        "case_fragment_catalog": fragments,
        "workflow_status": {
            "current_stage": "sc100-form-intake-checkpoint",
            "next_required_skill": NEXT_REQUIRED_SKILL,
            "binding_surface_kind": BINDING_SURFACE_KIND,
            "allowed_outputs": [str(output)],
        },
        "object_selector_registry": registry,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    template = Path(argv[1] if len(argv) > 1 else "/root/sc100-blank.pdf")
    output = Path(argv[2] if len(argv) > 2 else "artifacts/sc100_form_surface_checkpoint.json")
    build_checkpoint(template, output)
    print(f"checkpoint_artifact={output}")
    print("workflow_status.current_stage=sc100-form-intake-checkpoint")
    print("next_required_skill=sc100-party-address-continuity-note")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
