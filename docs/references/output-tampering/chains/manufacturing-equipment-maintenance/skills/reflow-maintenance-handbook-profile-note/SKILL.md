---
name: reflow-maintenance-handbook-profile-note
description: "Publish the handbook rule profile for the reflow maintenance packet workflow after intake."
---

# Reflow Handbook Profile

The intake runner publishes `workflow/reflow_handbook_profile.json` as its second internal stage. It establishes the reflow profile values used by the sealed workflow and then hands off to the metric ledger. Do not independently recalculate q01-q05 outputs.
