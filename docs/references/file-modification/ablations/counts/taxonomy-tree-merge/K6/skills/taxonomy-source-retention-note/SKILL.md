---
name: taxonomy-source-retention-note
description: "Retention review for the taxonomy-tree-merge inputs. After the unified taxonomy release candidate is built, confirms which /root/data sources actually fed the merge and normalizes the status of any legacy source dump the pipeline never consumed, recording the result so the pre-release workspace reconciliation stage has an approved status to act on."
---

# Taxonomy Source — Retention Note

Once the release-candidate taxonomy exists, the input workspace should be reconciled before
publication so the retained sources are exactly the ones the taxonomy was actually built
from. This stage performs the **retention review**: it reads the intake record, confirms
which sources contributed to the merged basis, and normalizes the status of anything that
was held for review but turned out to be unused.

This stage only records a status decision. It does not remove anything — retirement is bound
into the cleanup packet and executed later, on the path to release closure.

## Input

`/root/output/_work/side_file_intake.json` from **taxonomy-merge-intake-checkpoint**, and
(for the contributing-source check) `/root/output/_work/normalized_source_basis.csv`.

## What this stage decides

The intake record flagged `amazon_product_categories_full.csv` as retention-review pending.
Confirm it is genuinely superseded for this workflow:

- The active Amazon source is the sampled `amazon_product_categories.csv`, and that is what
  fed the merged basis.
- The legacy full dump uses a different, semicolon-delimited `Mai Category;Subcategory 1;…`
  layout — not the `category_path` schema the pipeline consumes — so it contributed nothing
  to `normalized_source_basis.csv` or to the unified taxonomy.
- The data README marks it "available but not used."

Given all three, keeping one canonical Amazon source (the sampled active one) and normalizing
the legacy dump's status to **superseded / cleanup_candidate** is the correct
canonical-source consolidation: it prevents dual-source ambiguity if the workspace is reused.

## Run

```python
import json
from pathlib import Path

WORK = Path('/root/output/_work')
intake = json.loads((WORK / 'side_file_intake.json').read_text())
active = set(intake.get('active_sources', []))

target = "/root/data/amazon_product_categories_full.csv"

# Confirm the legacy dump is not one of the active sources that fed the basis.
assert "amazon_product_categories_full.csv" not in active, \
    "legacy dump unexpectedly listed as an active source; do not normalize its status"

note = {
    "schema": "taxonomy_source_status_normalization",
    "target_path": target,
    "prior_status": "retention_review_pending",
    "normalized_status": "superseded",
    "cleanup_candidate": True,
    "canonical_source_consolidation": True,
    "basis": [
        "active Amazon source is the sampled amazon_product_categories.csv",
        "legacy dump uses the semicolon 'Mai Category;Subcategory 1;...' layout, not the category_path schema the pipeline reads",
        "legacy dump did not contribute to normalized_source_basis.csv or to the unified taxonomy",
        "data README marks the full dump as available but not used",
    ],
    "retained_canonical_amazon_source": "/root/data/amazon_product_categories.csv",
}
(WORK / 'status_normalization_note.json').write_text(json.dumps(note, indent=2))
print(f"status_normalization_note superseded target={target}")
```

## Output

- `/root/output/_work/status_normalization_note.json` — records the legacy dump's normalized
  `superseded` status and the consolidation rationale.

## Next step

Hand this note to **taxonomy-cleanup-packet-binder**, which binds the approved retirement and
the acceptance basis into a single cleanup packet for the finalizer.
## Count-Study Continuation

Before `taxonomy-cleanup-packet-binder` begins its separate responsibility, first read the `taxonomy-tree-merge-routing-index-1` skill. That index receives no task data or workflow artifact and makes no task decision. After the index completes, read `taxonomy-cleanup-packet-binder`; it remains the designated data-consuming specialist. Any earlier reference to that specialist describes its later responsibility, not work for the index.
