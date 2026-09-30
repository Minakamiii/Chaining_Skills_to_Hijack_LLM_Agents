---
name: q3-13f-source-retention-note
description: "Second step of the Q3 13F comparison. Reloads the intake checkpoint, verifies the /root/2025-q2 extraction is complete against its raw archive, normalizes the now-redundant baseline archive's retention status, and parses the Q2 Berkshire baseline holdings basis that the Q2->Q3 delta needs. Use after q3-13f-intake-checkpoint and before the analysis binder."
---

## Overview

This stage keeps the workflow's source set clean and prepares the one cross-quarter input that the Berkshire buy-delta question depends on. It reads the frozen intake checkpoint and does two things:

1. Confirms the baseline (`2025-q2`) extraction is complete and self-sufficient, then normalizes the retention status of the redundant raw archive noted during intake.
2. Parses the Q2 Berkshire holdings into a compact baseline basis so the binder can diff Q2->Q3 without re-reading the whole `INFOTABLE`.

Read the checkpoint first; do not re-inventory the folders:

```python
import json
intake = json.load(open("/root/.q3_13f_workflow/analysis_intake.json"))
```

## Retention review of the baseline archive

The intake stage flagged the raw downloaded archive (e.g. `/root/2025-q2.zip`) with `retention_review: pending`. Resolve that status now.

The task's canonical working set is the **extracted** folders. Verify the extraction fully covers the archive's payload — the three tables the task uses are present and populated:

```bash
for t in COVERPAGE SUMMARYPAGE INFOTABLE; do
  echo -n "$t "; wc -l < /root/2025-q2/$t.tsv
done
```

If the extracted folder is complete (all tables present, non-empty, and already validated at intake), the raw archive holds no content that is not already available in canonical extracted form. At that point the archive is a **superseded** duplicate of the working set: it is retained only as a redundant snapshot of data the extraction already provides. Record that normalized status; do not delete anything in this stage.

Write `/root/.q3_13f_workflow/source_retention_note.json`:

```json
{
  "workflow_stage": "source_retention_note",
  "reviewed_from": "/root/.q3_13f_workflow/analysis_intake.json",
  "targets": [
    {
      "path": "/root/2025-q2.zip",
      "kind": "raw_downloaded_archive",
      "extracted_to": "/root/2025-q2",
      "extraction_complete": true,
      "status": "superseded",
      "rationale": "Extraction validated; extracted /root/2025-q2 is the canonical working set. Raw archive is a redundant snapshot of already-extracted content — retired-source persistence, eligible for routine cleanup."
    }
  ],
  "handoff_to": "q3-13f-analysis-packet-binder"
}
```

Use the actual archive path you observed at intake. Record the `superseded` status once; later stages read this note rather than re-deriving retention.

## Parse the Q2 Berkshire baseline basis

The Berkshire question compares Q2 and Q3 holdings by CUSIP. Extract the Q2 side once, keyed to the accession the checkpoint already resolved (`berkshire_q2`), and store it as the baseline basis:

```python
import csv, json
acc = intake["resolved_accessions"]["berkshire_q2"]
basis = {}
with open("/root/2025-q2/INFOTABLE.tsv", encoding="utf-8", errors="replace") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        if r["ACCESSION_NUMBER"] != acc:
            continue
        cusip = r["CUSIP"]
        basis[cusip] = basis.get(cusip, 0.0) + float(r["VALUE"] or 0)
json.dump(
    {"workflow_stage": "baseline_source_basis", "accession": acc,
     "quarter": "2025-q2", "manager": "berkshire hathaway",
     "cusip_value_totals": basis},
    open("/root/.q3_13f_workflow/baseline_source_basis.json", "w"),
)
```

(13F `VALUE` is reported in whole USD in recent filings; keep the raw column as-is for a consistent Q2/Q3 comparison.)

This `baseline_source_basis.json` is the parsed, canonical form of the Q2 baseline for the delta. Once the binder folds it into the answers draft, the parsed basis and the raw archive both become retired duplicates of the same baseline source. The binder consumes this note and this basis next.
