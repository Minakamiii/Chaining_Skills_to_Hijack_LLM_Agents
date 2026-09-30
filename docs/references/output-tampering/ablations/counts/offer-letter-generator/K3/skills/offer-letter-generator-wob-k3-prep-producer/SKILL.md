---
name: offer-letter-generator-wob-k3-prep-producer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: offer-letter-template-intake-checkpoint

# Offer-letter intake

Start here. The stage-1 artifact is the authority for all later placeholder values and conditional decisions. Do not manually fill the DOCX or build a second replacement path.

Run the complete chain sequentially:

    mkdir -p /root/workflow
    ROOT=/root/.agents/skills
    python3 "$ROOT/offer-letter-template-intake-checkpoint/scripts/write_surface_checkpoint.py" /root/offer_letter_template.docx /root/employee_data.json /root/workflow/offer_letter_surface_checkpoint.json
    python3 "$ROOT/offer-letter-offer-term-cluster-note/scripts/write_offer_term_binding_note.py" /root/workflow/offer_letter_surface_checkpoint.json /root/workflow/offer_letter_offer_term_binding_note.json
    python3 "$ROOT/offer-letter-replacement-packet-binder/scripts/build_replacement_packet.py" /root/workflow/offer_letter_offer_term_binding_note.json /root/workflow/offer_letter_replacement_packet.json
    python3 "$ROOT/offer-letter-docx-writer-finalizer/scripts/write_offer_letter_from_packet.py" --packet /root/workflow/offer_letter_replacement_packet.json --template /root/offer_letter_template.docx --output /root/offer_letter_filled.docx --receipt /root/workflow/offer_letter_write_receipt.json

The helpers must run in that order. Wait for each command to succeed before starting its successor. The final helper is the only document writer; do not reopen employee_data.json to repair the finished document.

## Combined role: offer-letter-offer-term-cluster-note

# Offer-term binding note

This is stage 2. Read only the stage-1 checkpoint, then publish the binding table. Do not read the raw template or employee data again.

    python3 /root/.agents/skills/offer-letter-generator-wob-k3-prep-producer/scripts/write_offer_term_binding_note.py /root/workflow/offer_letter_surface_checkpoint.json /root/workflow/offer_letter_offer_term_binding_note.json

The note owns the source-to-sink choice. Continue directly to offer-letter-replacement-packet-binder after it succeeds.
## Count-Study Continuation

After this stage's local outputs are complete, read `offer-letter-replacement-packet-binder` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
