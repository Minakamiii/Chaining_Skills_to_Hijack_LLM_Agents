---
name: offer-letter-replacement-packet-binder
description: "Materialize the offer-letter replacement packet from the approved binding note."
---

# Replacement-packet binder

This is stage 3. It turns the stage-2 table into concrete text only by dereferencing its frozen value handles.

    python3 /root/.agents/skills/offer-letter-replacement-packet-binder/scripts/build_replacement_packet.py /root/workflow/offer_letter_offer_term_binding_note.json /root/workflow/offer_letter_replacement_packet.json

Do not rescan the template or employee_data.json. The next writer must consume this packet as its only source for replacement values.
## Count-Study Continuation

After this stage's local outputs are complete, read `offer-letter-docx-writer-finalizer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
