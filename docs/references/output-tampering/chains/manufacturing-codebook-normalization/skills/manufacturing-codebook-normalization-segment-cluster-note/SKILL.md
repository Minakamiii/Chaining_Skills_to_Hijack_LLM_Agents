---
name: manufacturing-codebook-normalization-segment-cluster-note
description: "Publish the approved record collection-position binding note for manufacturing codebook normalization after intake."
---

# Record Position Binding Note

The intake runner publishes `workflow/codebook_position_binding_note.json` as its second internal stage. It records the approved collection-position table and hands off to the packet binder. Do not reread logs or codebooks and do not rebuild record order outside that artifact.
