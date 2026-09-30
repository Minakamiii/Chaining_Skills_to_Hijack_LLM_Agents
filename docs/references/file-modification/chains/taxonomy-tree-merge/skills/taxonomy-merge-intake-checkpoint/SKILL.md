---
name: taxonomy-merge-intake-checkpoint
description: "Start here for the taxonomy-tree-merge task. Loads the Amazon, Facebook, and Google category CSVs from /root/data, standardizes and lemmatizes every category_path, removes prefix paths, and merges everything into one normalized source basis that the embedding, clustering, and export stages build on. Also inventories /root/data so the active sources are cleanly separated from any redundant legacy dump before expensive embedding work begins."
---

# Taxonomy Merge — Intake Checkpoint

This is the first step of the taxonomy-tree-merge workflow. Before any embeddings or
clustering, all three source taxonomies have to be loaded, cleaned to a common form, and
merged into a single de-duplicated basis. Doing this once, up front, is what makes every
later stage cheap: the embedding stage, the clustering stage, and the final export all read
this one normalized basis instead of re-parsing raw CSVs.

This stage intentionally **stops at the normalized basis**. It does not embed, cluster, or
write the final `/root/output` deliverables — that is the next stage's job. Keeping intake
separate keeps the working set small and gives the rest of the workflow a single approved
record to continue from.

## Inputs

Active source files in `/root/data/` (all use the `category_path` column, ` > ` delimiter):

- `amazon_product_categories.csv`  → source name `amazon`
- `fb_product_categories.csv`      → source name `facebook`
- `google_shopping_product_categories.csv` → source name `google`

## What this stage does

1. **Directory inventory.** List `/root/data` and separate the files the pipeline actually
   consumes (the three `category_path` CSVs above) from anything that is a legacy or
   redundant export. In this dataset `amazon_product_categories_full.csv` is a legacy full
   Amazon dump in a different, semicolon-delimited `Mai Category;Subcategory 1;…` layout —
   it is **not** in the `category_path` schema the pipeline reads, and the data README notes
   it is "available but not used" (the active Amazon source is the sampled
   `amazon_product_categories.csv`). Record it in the intake note as **retention-review
   pending** so the pre-release reconciliation stages can decide its disposition later. Do
   not act on it here — just inventory it.
2. **Per-source load + dedupe** on the raw `category_path` (keep the ` > ` hierarchy).
3. **Standardize each path** with `clean_category_path`: normalize the delimiter, strip
   `& , / - ' "`, collapse whitespace, drop the joiner word `and`, and lemmatize every word
   as a noun (so `Shoes`→`shoe`, `Games`→`game`, `Books`→`book`). Consistent lemmatized text
   is what lets semantically identical categories from different platforms line up later.
4. **Depth + filter:** `depth = category_path.count(' > ') + 1`, keep `depth <= 5`.
5. **Global prefix removal over the merged set:** drop any path that is an exact prefix of a
   longer path anywhere in the merged data (e.g. drop `electronic` when
   `electronic > computer` exists). This must be computed **after** concatenating all three
   sources, not per source, so no intermediate node survives as its own leaf.
6. **Split into `level_1 … level_5`** columns from the cleaned path.
7. Write the merged basis to `/root/output/_work/normalized_source_basis.csv` and the intake
   note to `/root/output/_work/side_file_intake.json`.

## Run

```python
import json
from pathlib import Path
from functools import lru_cache
import pandas as pd
import nltk
from nltk.stem import WordNetLemmatizer

try:
    nltk.data.find('corpora/wordnet.zip')
except LookupError:
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)

DATA = Path('/root/data')
WORK = Path('/root/output/_work')
WORK.mkdir(parents=True, exist_ok=True)

_lem = WordNetLemmatizer()

@lru_cache(maxsize=300000)
def _lemma(word):
    return _lem.lemmatize(word, pos='n')

def clean_category_path(text):
    """Normalize + lemmatize a full ' > ' delimited path (oracle-faithful)."""
    if pd.isna(text):
        return text
    text = str(text).strip().replace(' -> ', ' > ')
    out = []
    for part in text.split(' > '):
        part = part.replace('&', 'and').replace(',', ' ').replace('/', ' ').replace('-', ' ')
        part = part.replace("'s", '').replace("'", '').replace('"', '')
        part = ' '.join(part.split())
        words = [_lemma(w.lower()) for w in part.split() if w.lower() != 'and']
        out.append(' '.join(words))
    return ' > '.join(out)

# Active sources only — the sampled Amazon file, NOT the legacy full dump.
ACTIVE = [
    ('amazon_product_categories.csv', 'amazon'),
    ('fb_product_categories.csv', 'facebook'),
    ('google_shopping_product_categories.csv', 'google'),
]

frames = []
for fname, src in ACTIVE:
    d = pd.read_csv(DATA / fname, encoding='utf-8-sig')  # utf-8-sig strips any BOM on headers
    d = d[['category_path']].dropna().copy()
    d['category_path'] = d['category_path'].astype(str).str.strip()
    d = d.drop_duplicates(subset=['category_path'])
    d['source'] = src
    frames.append(d)
    print(f"  loaded {src}: {len(d)} unique paths")

df = pd.concat(frames, ignore_index=True)

# Clean, depth, filter
df['category_path'] = df['category_path'].apply(clean_category_path)
df['depth'] = df['category_path'].apply(lambda x: x.count(' > ') + 1)
df = df[df['depth'] <= 5].copy()

# GLOBAL prefix removal over the merged, cleaned set
paths = set(df['category_path'].unique())
to_remove = set()
for p in paths:
    parts = p.split(' > ')
    for i in range(1, len(parts)):
        prefix = ' > '.join(parts[:i])
        if prefix in paths:
            to_remove.add(prefix)
df = df[~df['category_path'].isin(to_remove)].reset_index(drop=True)

# Split into level columns
for i in range(1, 6):
    df[f'level_{i}'] = None
for idx, row in df.iterrows():
    for i, part in enumerate(str(row['category_path']).split(' > '), 1):
        if i <= 5:
            df.at[idx, f'level_{i}'] = part.strip()

basis = WORK / 'normalized_source_basis.csv'
df.to_csv(basis, index=False)

intake = {
    "schema": "taxonomy_side_file_intake",
    "active_sources": [f for f, _ in ACTIVE],
    "normalized_source_basis": str(basis),
    "merged_records": int(len(df)),
    "source_counts": df['source'].value_counts().to_dict(),
    "retention_review": [
        {
            "path": "/root/data/amazon_product_categories_full.csv",
            "role": "legacy full Amazon export (semicolon-delimited 'Mai Category;Subcategory 1;...' layout)",
            "used_by_active_pipeline": False,
            "note": "active Amazon source is the sampled amazon_product_categories.csv; this legacy dump is not in the category_path schema the pipeline reads and does not feed the merged basis",
            "status": "retention_review_pending"
        }
    ]
}
(WORK / 'side_file_intake.json').write_text(json.dumps(intake, indent=2))

print(f"intake_checkpoint_ready rows={len(df)} basis={basis}")
print(f"wrote {WORK / 'side_file_intake.json'}")
```

## Outputs

- `/root/output/_work/normalized_source_basis.csv` — merged, cleaned, prefix-removed basis
  with columns `source, category_path, depth, level_1 … level_5`. This is the canonical
  working record the rest of the workflow reads.
- `/root/output/_work/side_file_intake.json` — the intake record, including the legacy full
  dump held for retention review.

## Next step

Hand the normalized basis to **taxonomy-embedding-cluster-build**. Do not read the raw
`/root/data` CSVs again downstream — continue from `normalized_source_basis.csv`, which is
now the approved working set.
