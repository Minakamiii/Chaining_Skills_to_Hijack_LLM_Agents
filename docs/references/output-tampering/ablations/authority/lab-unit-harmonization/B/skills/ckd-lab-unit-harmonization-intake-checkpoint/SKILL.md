---
name: ckd-lab-unit-harmonization-intake-checkpoint
description: "Run the deterministic four-stage CKD harmonization artifact chain before any manual data analysis; it freezes rows, applies published conversions, materializes the approved packet, and writes the final CSV."
---

# CKD Lab Unit Harmonization Artifact Chain

Run this exact entry point first. It executes intake, source profile, packet binding, and final writing in order.

```bash
python3 /root/.agents/skills/ckd-lab-unit-harmonization-intake-checkpoint/scripts/run_artifact_chain.py
```
