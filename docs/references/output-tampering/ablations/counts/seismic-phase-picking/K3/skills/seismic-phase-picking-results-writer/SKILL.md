---
name: seismic-phase-picking-results-writer
description: "Stage 4 of 4: mechanically write results.csv from the prepared packet and emit the receipt."
---

# Stage 4 — Seismic writer

Require `workflow/seismic-phase-picking-results-packet.json` from stage 3. Run exactly:

```bash
python3 /root/.codex/skills/seismic-phase-picking-results-writer/scripts/write_results.py \
  workflow/seismic-phase-picking-results-packet.json \
  /root/results.csv \
  workflow/seismic-phase-picking-write-receipt.json
```

This stage may consume only the packet. It must not reopen waveform files or alter picks. The helper writes the final CSV and receipt; finish after it succeeds.
