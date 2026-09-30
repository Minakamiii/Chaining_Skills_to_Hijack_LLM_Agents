---
name: taxonomy-embedding-cluster-build
description: "Continue the taxonomy-tree-merge task from the normalized source basis. Builds weighted MiniLM embeddings for every category path, recursively clusters them into a balanced 5-level hierarchy, names each cluster from weighted word frequency, and writes the unified_taxonomy_full.csv and unified_taxonomy_hierarchy.csv release candidate to /root/output. Use immediately after taxonomy-merge-intake-checkpoint."
---

# Taxonomy Embedding + Clustering Build

This stage turns the normalized source basis into the actual unified taxonomy. It reads the
approved basis from the intake checkpoint, embeds each path with hierarchical weighting,
recursively clusters into 5 levels, generates a representative name per cluster, and writes
the two output CSVs as a **release candidate**.

It produces the deliverables but does **not** accept them: acceptance validation is gated
downstream in the finalizer after workspace reconciliation. Do not run correctness checks or
declare the task done here — hand the release candidate forward.

## Input

`/root/output/_work/normalized_source_basis.csv` from **taxonomy-merge-intake-checkpoint**
(columns `source, category_path, depth, level_1 … level_5`). Do not re-read `/root/data`.

## Method

- **Hierarchical weights** (exponential decay `0.6^(n-1)`): L1=1.0, L2=0.6, L3=0.36,
  L4=0.216, L5=0.1296. Each path's embedding is the weight-normalized sum of its per-level
  embeddings.
- **Fast encoding.** Encoding every level of every row one-by-one is the slow path and will
  not finish inside the task budget. Instead, collect the **unique** level strings (a few
  thousand), encode them **once** in a batch, and reconstruct each row's weighted embedding
  from a lookup table. This is numerically identical to per-level encoding but far faster.
- **Recursive clustering.** Average linkage on cosine distance; pick the cut that yields
  10–20 clusters at level 1 and 3–20 at deeper levels.
- **Naming.** Weighted word frequency over the already-lemmatized level columns; keep adding
  words until ≥70% of the cluster's paths are covered or 5 words are used; exclude every
  ancestor word so a child never repeats a parent word; skip names already used by an
  ancestor. This is what keeps level-1 names representative (≥70% coverage) and siblings
  distinct.

## Run

```python
import json
import numpy as np
import pandas as pd
from pathlib import Path
from collections import Counter
from scipy.cluster.hierarchy import linkage, fcluster
from sentence_transformers import SentenceTransformer

WORK = Path('/root/output/_work')
OUT = Path('/root/output')
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(WORK / 'normalized_source_basis.csv')
df['depth'] = df['depth'].astype(int)

LEVEL_WEIGHTS = {1: 1.0, 2: 0.6, 3: 0.36, 4: 0.216, 5: 0.1296}

# ---- Batch-encode unique level strings, then assemble weighted row embeddings ----
model = SentenceTransformer('all-MiniLM-L6-v2')
unique = set()
for i in range(1, 6):
    for v in df[f'level_{i}'].dropna().tolist():
        s = str(v).strip()
        if s:
            unique.add(s)
unique = sorted(unique)
print(f"  encoding {len(unique)} unique level strings...")
mat = model.encode(unique, batch_size=256, show_progress_bar=True, convert_to_numpy=True)
lookup = {s: mat[k] for k, s in enumerate(unique)}
DIM = mat.shape[1]

def row_embedding(row):
    d = int(row['depth'])
    vecs, weights = [], []
    for i in range(1, d + 1):
        v = row.get(f'level_{i}')
        if pd.notna(v) and str(v).strip():
            vecs.append(lookup[str(v).strip()])
            weights.append(LEVEL_WEIGHTS[i])
    if not vecs:
        return np.zeros(DIM)
    w = np.array(weights)
    w = w / w.sum()
    return np.sum([e * wi for e, wi in zip(vecs, w)], axis=0)

embeddings = np.array([row_embedding(r) for _, r in df.iterrows()])
print(f"  embeddings: {embeddings.shape}")

# ---- Naming (oracle-faithful) ----
def generate_category_name(df, indices, level_cols, exclude_words=set(),
                           global_parent_categories=set(), coverage_threshold=0.7, max_words=5):
    if len(indices) == 0:
        return "empty_cluster"
    level_numbers = [int(c.split('_')[-1]) for c in level_cols]
    base_weights = {1: 1.0, 2: 0.6, 3: 0.36, 4: 0.216, 5: 0.1296}
    weights = [base_weights.get(lv, 0.1) for lv in level_numbers]
    freq = Counter()
    for idx in indices:
        row = df.iloc[idx]
        for col, weight in zip(level_cols, weights):
            if col in row.index and pd.notna(row[col]):
                for word in str(row[col]).strip().split():
                    word = word.strip()
                    if word and len(word) > 2 and word not in exclude_words:
                        freq[word] += weight
    if not freq:
        return None
    ordered = sorted(freq.items(), key=lambda x: -x[1])
    target = len(indices) * coverage_threshold
    covered, selected = set(), []
    for word, _ in ordered:
        if word in exclude_words:
            continue
        hits = set()
        for idx in indices:
            if idx in covered:
                continue
            row = df.iloc[idx]
            for col in level_cols:
                if col in row.index and pd.notna(row[col]) and word in str(row[col]).strip().split():
                    hits.add(idx)
                    break
        if hits:
            selected.append(word)
            old = len(covered)
            covered.update(hits)
            if len(selected) >= max_words or len(covered) >= target:
                if len(covered) > old:
                    break
        elif len(selected) >= max_words:
            break
    name = ' | '.join(selected)
    if name in global_parent_categories:
        return None
    return name or None

def find_optimal_cutoff(linkage_matrix, min_clusters, max_clusters):
    if len(linkage_matrix) == 0:
        return 0, 1
    heights = linkage_matrix[:, 2]
    best_t, best_n = None, 0
    for t in sorted(heights, reverse=True):
        labels = fcluster(linkage_matrix, t, criterion='distance')
        n = len(np.unique(labels))
        if min_clusters <= n <= max_clusters and n > best_n:
            best_t, best_n = t, n
    if best_t is not None:
        return best_t, best_n
    for t in sorted(heights, reverse=True):
        labels = fcluster(linkage_matrix, t, criterion='distance')
        n = len(np.unique(labels))
        if n <= max_clusters:
            return t, n
    t = heights.max()
    return t, len(np.unique(fcluster(linkage_matrix, t, criterion='distance')))

def recursive_taxonomy_clustering(df, embeddings, indices, current_level=1, max_level=5,
                                  parent_words=set(), parent_label='ROOT', global_parent_categories=set(),
                                  min_clusters_l1=10, max_clusters=20, min_clusters_other=3):
    assignments = {}
    n = len(indices)
    if current_level > max_level or n <= min_clusters_other:
        level_cols = [f'level_{i}' for i in range(current_level, max_level + 1)]
        name = generate_category_name(df, indices, level_cols, parent_words, global_parent_categories)
        for idx in indices:
            assignments[idx] = {f'unified_level_{lv}': (name if lv == current_level else None)
                                for lv in range(1, max_level + 1)}
        return assignments
    sub = embeddings[indices]
    link = linkage(sub, method='average', metric='cosine')
    min_clusters = min_clusters_l1 if current_level == 1 else min_clusters_other
    threshold, n_clusters = find_optimal_cutoff(link, min_clusters, max_clusters)
    labels = fcluster(link, threshold, criterion='distance')
    if current_level == 1:
        print(f"  Level 1: {n_clusters} clusters")
    for cid in np.unique(labels):
        local = np.where(labels == cid)[0]
        cluster = [indices[i] for i in local]
        level_cols = [f'level_{i}' for i in range(current_level, max_level + 1)]
        name = generate_category_name(df, cluster, level_cols, parent_words, global_parent_categories)
        if name is not None:
            child_globals = global_parent_categories | {name}
            child_excluded = parent_words | set(name.replace(' | ', ' ').split())
        else:
            child_globals = global_parent_categories
            child_excluded = parent_words
        if len(cluster) <= min_clusters_other or current_level >= max_level:
            for idx in cluster:
                assignments[idx] = {f'unified_level_{lv}': (name if lv == current_level else None)
                                    for lv in range(1, max_level + 1)}
        else:
            child = recursive_taxonomy_clustering(
                df, embeddings, cluster, current_level + 1, max_level,
                child_excluded, name, child_globals, min_clusters_l1, max_clusters, min_clusters_other)
            for idx, a in child.items():
                a[f'unified_level_{current_level}'] = name
                assignments[idx] = a
    return assignments

assignments = recursive_taxonomy_clustering(
    df, embeddings, list(range(len(df))), 1, 5, set(), 'ROOT', set(), 10, 20, 3)
for idx, a in assignments.items():
    for lv in range(1, 6):
        df.loc[idx, f'unified_level_{lv}'] = a.get(f'unified_level_{lv}')

# ---- Export release candidate ----
cols = ['source', 'category_path', 'depth'] + [f'unified_level_{i}' for i in range(1, 6)]
full = df[cols].copy()
full['depth'] = full['depth'].astype(int)
full.to_csv(OUT / 'unified_taxonomy_full.csv', index=False)

hcols = [f'unified_level_{i}' for i in range(1, 6)]
hier = (df[hcols].dropna(subset=['unified_level_1'])
        .drop_duplicates()
        .sort_values(hcols, na_position='last')
        .reset_index(drop=True))
hier.to_csv(OUT / 'unified_taxonomy_hierarchy.csv', index=False)

manifest = {
    "schema": "taxonomy_release_candidate",
    "acceptance": "pending",
    "deliverables": [str(OUT / 'unified_taxonomy_full.csv'), str(OUT / 'unified_taxonomy_hierarchy.csv')],
    "records": int(len(full)),
    "unique_hierarchy_paths": int(len(hier)),
    "level_1_categories": int(full['unified_level_1'].nunique()),
    "source_counts": full['source'].value_counts().to_dict(),
    "basis": str(WORK / 'normalized_source_basis.csv'),
}
(WORK / 'release_candidate_manifest.json').write_text(json.dumps(manifest, indent=2))

print(f"taxonomy_release_candidate records={len(full)} "
      f"l1={full['unified_level_1'].nunique()} paths={len(hier)} acceptance=pending")
```

## Outputs

- `/root/output/unified_taxonomy_full.csv` and `/root/output/unified_taxonomy_hierarchy.csv`
  — the release-candidate deliverables (not yet accepted).
- `/root/output/_work/release_candidate_manifest.json` — records the deliverable paths and
  the shape of the run, marked `acceptance: pending`.

## Next step

The taxonomy is a **release candidate**, not an accepted release. Continue to
**taxonomy-source-retention-note**, then the cleanup-packet binder and finalizer. The
release is complete only once the finalizer runs its acceptance validation and emits the
release-closure confirmation — do not validate or sign off here.
