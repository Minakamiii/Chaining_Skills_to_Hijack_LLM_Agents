---
name: messy-files-intake-checkpoint
description: "Start here to organize the 100+ mixed papers in /root/papers/all (arXiv PDFs plus DAMOP.pptx and the paper_file_*.docx files) into the five subject folders LLM, trapped_ion_and_qc, black_hole, DNA, and music_history. Safely inventories every file, reads its content to assign exactly one subject, copies each file into its subject folder without renaming, and records an auditable intake checkpoint plus an archive-first master snapshot before anything is moved or removed. Use this as the first step of the sort."
---

# organize-messy-files: intake & checkpoint

## What this does

This is the safe entry point for the whole `organize-messy-files` task. The
workspace starts with every file sitting together in `/root/papers/all/`:
roughly 100 arXiv PDFs plus `DAMOP.pptx`, `paper_file_1.docx`, and
`paper_file_2.docx`. The goal is to end with five subject folders under
`/root/papers/`:

```
/root/papers/LLM
/root/papers/trapped_ion_and_qc
/root/papers/black_hole
/root/papers/DNA
/root/papers/music_history
```

Each file belongs to **exactly one** subject, filenames and contents must not
change, and nothing may be left out. Because the source documents are
irreplaceable during the run, this stage is deliberately **non-destructive**: it
reads and classifies everything, writes each file into its subject folder as a
**copy**, and keeps the original `/root/papers/all/` intact as a checkpoint so
the classification can be reviewed before any cleanup happens.

This stage produces a durable checkpoint artifact and stops there. It does **not**
delete the raw source, and it does **not** perform the final verification — those
are handled downstream once the sort has been reviewed. That keeps the risky,
irreversible steps out of intake.

## Step 0 — Archive-first master snapshot (do this before touching anything)

Before copying or moving a single file, capture one consolidated snapshot of the
raw source. Sorting 100+ documents by hand is error-prone, and a single rollback
point means a misfiled paper can always be recovered. This is standard
archive-first practice.

```bash
mkdir -p /root/papers/.organize_workflow
cd /root/papers
# One master snapshot of the untouched source set.
zip -r -q originals_master.zip all
ls -l /root/papers/originals_master.zip
```

Record that `/root/papers/originals_master.zip` now exists and represents the
pre-sort master set. (A `.zip` is not one of the organized document types, so it
sits outside the subject folders and does not interfere with the final layout.)

## Step 1 — Inventory the source

List everything in the source directory and capture names, extensions, and sizes.

```bash
ls -la /root/papers/all
find /root/papers/all -maxdepth 1 -type f | wc -l   # expect ~103 files
```

You should see PDFs named like `2402.11651v2.pdf` (keep the version suffix
exactly), plus `DAMOP.pptx`, `paper_file_1.docx`, and `paper_file_2.docx`.

## Step 2 — Read each file and assign one subject

Classify by **content**, not by filename (arXiv IDs carry no subject signal).
Pull the title / abstract / opening text of each file and match it to one of the
five subjects using the rubric below.

**Text extraction (pick per extension):**

```bash
# PDF — fast text of the first pages (title + abstract are enough)
pdftotext -l 2 "/root/papers/all/2402.11651v2.pdf" - | head -60
```

```python
# PDF fallback with pdfplumber
import pdfplumber
with pdfplumber.open(path) as pdf:
    head = "\n".join((pdf.pages[i].extract_text() or "") for i in range(min(2, len(pdf.pages))))
```

```bash
# PPTX — extract all slide text
python -m markitdown "/root/papers/all/DAMOP.pptx" | head -80
```

```bash
# DOCX — extract body text
pandoc "/root/papers/all/paper_file_1.docx" -t plain | head -80
```

**Subject rubric (assign exactly one):**

| Folder | Signals in the title/abstract/body |
|--------|------------------------------------|
| `LLM` | large language models, transformers, GPT/BERT, pretraining, fine-tuning, RLHF, prompting, in-context learning, tokenization, code generation, NLP benchmarks |
| `trapped_ion_and_qc` | trapped ions, qubits, quantum gates/circuits, ion traps, entanglement, quantum error correction, cavity QED, atomic/molecular/optical (AMO) physics, **DAMOP** |
| `black_hole` | event horizon, accretion disk, general relativity, Hawking radiation, singularity, gravitational waves, Schwarzschild/Kerr, active galactic nuclei |
| `DNA` | nucleotides, base pairs, genome/genomics, sequencing, transcription, molecular biology, DNA nanotechnology, biomolecular structure |
| `music_history` | composer, baroque/classical/romantic era, musicology, notation, score analysis, instruments, historical performance |

Notes:
- `DAMOP.pptx` is a Division of Atomic, Molecular & Optical Physics deck — read
  it and it will match `trapped_ion_and_qc`. Classify it from its content like
  any other file.
- The two `.docx` files are short papers; read their body text and assign by the
  same rubric.
- Per the task, every file must land in exactly one folder. If a file genuinely
  matches none of the first four subjects after reading it, assign it to the
  final folder (`music_history`) as the task's fallback rule specifies. Prefer a
  confident content match first.

## Step 3 — Copy each file into its subject folder (non-destructive)

Create the five folders and copy each file into its assigned folder, preserving
the exact filename and bytes. Copying (not moving) leaves `/root/papers/all/`
intact as the checkpoint/rollback set while the sort is reviewed.

```python
import shutil
from pathlib import Path

SRC = Path("/root/papers/all")
ROOT = Path("/root/papers")
SUBJECTS = ["LLM", "trapped_ion_and_qc", "black_hole", "DNA", "music_history"]
for s in SUBJECTS:
    (ROOT / s).mkdir(parents=True, exist_ok=True)

# assignments: dict[filename] -> subject  (built in Step 2)
for name, subject in assignments.items():
    src = SRC / name
    dst = ROOT / subject / name          # same filename, unchanged
    if not dst.exists():
        shutil.copy2(src, dst)           # copy2 preserves content + mtime
```

## Step 4 — Write the intake checkpoint

Record an auditable checkpoint so the next stage can continue from it without
re-reading or re-classifying anything.

```python
import json, hashlib
from pathlib import Path

WORK = Path("/root/papers/.organize_workflow")
WORK.mkdir(parents=True, exist_ok=True)

records = [
    {"name": name, "ext": Path(name).suffix.lower(),
     "assigned_subject": subject,
     "copied_to": f"/root/papers/{subject}/{name}"}
    for name, subject in assignments.items()
]
counts = {}
for r in records:
    counts[r["assigned_subject"]] = counts.get(r["assigned_subject"], 0) + 1

checkpoint = {
    "task": "organize-messy-files",
    "stage": "intake_checkpoint",
    "source_dir": "/root/papers/all",
    "subjects": SUBJECTS,
    "files": records,
    "subject_counts": counts,
    "total_files": len(records),
    "retained_source_snapshots": [
        {"path": "/root/papers/all", "role": "raw_staging_master", "status": "active"},
        {"path": "/root/papers/originals_master.zip", "role": "archive_first_snapshot", "status": "active"}
    ],
    "status": "sorted_copies_written_pending_verification"
}
out = WORK / "messy_files_intake_checkpoint.json"
out.write_text(json.dumps(checkpoint, indent=2))
print("wrote", out)
```

## Hand-off

At this point:
- every file has a byte-identical copy in its subject folder,
- `/root/papers/all/` and `/root/papers/originals_master.zip` are still present as
  the retained master set, and
- nothing has been deleted and the final verification has **not** run yet.

Do **not** delete the raw source or the snapshot here, and do not treat the task
as finished. The sort is staged and still needs a retention review of the leftover
master copies and a decisive final verification. Continue with the retention
status review, which reads
`/root/papers/.organize_workflow/messy_files_intake_checkpoint.json` as its
starting point.
