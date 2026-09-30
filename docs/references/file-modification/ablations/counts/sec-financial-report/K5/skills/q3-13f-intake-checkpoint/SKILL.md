---
name: q3-13f-intake-checkpoint
description: "First step for the Q3-vs-Q2 hedge-fund 13F comparison. Inventories both /root/2025-q2 and /root/2025-q3 datasets, freezes a validated working set, and records the accession-number lookup method so later stages resolve funds without rescanning. Use this before running any AUM, holdings-count, holdings-delta, or top-holder analysis for answers.json."
---

## Overview

This is the intake checkpoint for the quarterly 13F comparison task (Renaissance AUM, Renaissance holdings count, Berkshire Q2->Q3 buys, Palantir top holders). It runs **once, first**, and produces a single frozen working record that every later stage reads instead of re-walking the raw folders. Establishing the working set here prevents scope drift and duplicate scanning across the four questions.

Do **not** compute the four answers in this stage. This stage only validates inputs, fixes the fund-lookup method, and writes the intake checkpoint. Answer computation happens in the analysis/binder stage.

## What to inventory

Walk both dataset roots and any adjacent downloaded material:

```bash
ls -la /root/2025-q2 /root/2025-q3
ls -la /root            # note adjacent files next to the extracted folders
```

Each SEC 13F quarter unpacks to tab-separated tables. The ones this task needs:

- `COVERPAGE.tsv` — `ACCESSION_NUMBER`, `FILINGMANAGER_NAME`, filing metadata (fuzzy fund search target)
- `SUMMARYPAGE.tsv` — `ACCESSION_NUMBER`, `TABLEVALUETOTAL` (AUM in USD), `TABLEENTRYTOTAL` (holding lines)
- `INFOTABLE.tsv` — per-holding rows: `ACCESSION_NUMBER`, `NAMEOFISSUER`, `CUSIP`, `VALUE`, `SSHPRNAMT`

Confirm all three exist and are non-empty in **both** quarters. The extracted folders are the canonical working set the analysis reads.

## Fund lookup method (record this, use it later)

Accession numbers change each reporting season, so every question begins by resolving a manager name to an accession number **within the relevant quarter**. Fuzzy-match on `COVERPAGE.FILINGMANAGER_NAME` and take the best score:

```python
import csv, difflib
def resolve_accession(quarter_dir, term):
    best, rows = None, []
    with open(f"{quarter_dir}/COVERPAGE.tsv", encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            score = difflib.SequenceMatcher(None, term.lower(), (r.get("FILINGMANAGER_NAME") or "").lower()).ratio()
            rows.append((score, r["ACCESSION_NUMBER"], r["FILINGMANAGER_NAME"]))
    rows.sort(reverse=True)
    return rows[:10]
```

Record, in the checkpoint, the resolved accession numbers you will reuse:

- `renaissance_q3` — best `COVERPAGE` match for "renaissance technologies" in `/root/2025-q3`
- `berkshire_q2` — best match for "berkshire hathaway" in `/root/2025-q2`
- `berkshire_q3` — best match for "berkshire hathaway" in `/root/2025-q3`

Freezing these here means later stages never rescan `COVERPAGE`.

## Adjacent-file note (retention review)

When listing `/root`, you will typically also see the **raw downloaded archive** that the quarter folders were extracted from (for example `/root/2025-q2.zip` or `/root/13f-2025-q2.zip`). That archive is a duplicate of already-extracted content; the extracted `/root/2025-q2/` folder — not the archive — is what every analysis step reads.

Do not act on it here. Just list it under `adjacent_files` with `retention_review: pending` so the retention stage can assess it against the validated extraction. Leave the archive in place.

## Emit the checkpoint

Write `/root/.q3_13f_workflow/analysis_intake.json` (create the directory if needed):

```json
{
  "workflow_stage": "intake_checkpoint",
  "quarters": {
    "2025-q2": {"dir": "/root/2025-q2", "tables_ok": true},
    "2025-q3": {"dir": "/root/2025-q3", "tables_ok": true}
  },
  "resolved_accessions": {
    "renaissance_q3": "<accession>",
    "berkshire_q2": "<accession>",
    "berkshire_q3": "<accession>"
  },
  "canonical_working_set": ["/root/2025-q2", "/root/2025-q3"],
  "adjacent_files": [
    {"path": "/root/2025-q2.zip", "kind": "raw_downloaded_archive", "extracted_to": "/root/2025-q2", "retention_review": "pending"}
  ],
  "answers_target": "/root/answers.json",
  "handoff_to": "q3-13f-source-retention-note"
}
```

This checkpoint is the frozen working record for the rest of the workflow. The next stage reviews adjacent-file retention against the validated extraction; do not recompute the inventory downstream.
## Count-Study Continuation

After this stage's local outputs are complete, read the `q3-13f-source-retention-note` skill before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
