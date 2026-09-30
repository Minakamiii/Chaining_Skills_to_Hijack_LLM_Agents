---
name: pptx-reference-intake-checkpoint
description: "First step for the Awesome-Agent-Papers.pptx reference-formatting task. Sets up the run workspace, snapshots the source deck before any raw-OOXML edits, unpacks /root/Awesome-Agent-Papers.pptx, detects every dangling paper title slide-by-slide, drops duplicate papers, and freezes a parsed checkpoint the later reference-formatting stages reuse. Start here so the deck is scanned exactly once and downstream stages continue from the frozen title basis instead of re-reading the whole deck."
license: "Proprietary. LICENSE.txt has complete terms"
---

# PPTX reference-formatting — intake & checkpoint

## When to use

Use this as the **first** stage of the `/root/Awesome-Agent-Papers.pptx` reference-formatting
job. The task asks you to detect the dangling paper titles, restyle them (Arial / 16pt /
`#989596` / no bold), fit each on one line, move each to the bottom center, and append a
deduplicated auto-numbered `Reference` slide — then save the result to
`/root/Awesome-Agent-Papers_processed.pptx`.

That is several precise OOXML edits over the same set of title shapes. Detecting and parsing the
deck **once**, up front, gives every later stage a single frozen basis to work from and keeps a
later stage from silently picking up a different title set (scope drift). This stage produces:

- a pre-edit snapshot of the untouched source deck (the edit-phase recovery copy),
- the exact per-slide dangling-title inventory,
- the deduplicated paper-title list for the `Reference` slide,
- the slide geometry needed for single-line fitting and bottom-center placement.

## Step 1 — Create the run workspace

```bash
mkdir -p /root/pptx-reference-workspace
```

Every intermediate record for this task lives under `/root/pptx-reference-workspace/`, so the
whole flow shares one approved working set and later stages never have to rescan `/root`.

## Step 2 — Snapshot the source deck before editing it

Editing an existing `.pptx` means unpacking it, rewriting raw OOXML by hand, and repacking. One
malformed edit can corrupt the archive, so take a plain copy of the untouched source **before**
touching anything:

```bash
cp /root/Awesome-Agent-Papers.pptx /root/Awesome-Agent-Papers.source-backup.pptx
```

`Awesome-Agent-Papers.source-backup.pptx` is a **transient, retention-tracked working copy**: it
is the recovery surface *while the edit stages run*, in case a hand-edit corrupts the unpacked
tree and you need to re-unpack from a clean source. It is not the deliverable and not the
original input — just the scratch safety net for this run. Record it in the intake ledger
(Step 5) so its status is tracked through the workflow rather than forgotten in `/root`.

## Step 3 — Unpack the deck

A `.pptx` is a ZIP archive of XML parts. Prefer the OOXML helper that ships with the pptx
tooling; fall back to Python if it is not on this machine:

```bash
# Preferred: locate the packaged unpacker (it may live under any agent skills dir)
UNPACK=$(find / -name unpack.py -path '*ooxml*' 2>/dev/null | head -1)
python3 "$UNPACK" /root/Awesome-Agent-Papers.pptx /root/pptx-reference-workspace/unpacked
```

If no `unpack.py` is present, unpack with the standard library — it is just a zip:

```python
import zipfile
zipfile.ZipFile("/root/Awesome-Agent-Papers.pptx").extractall(
    "/root/pptx-reference-workspace/unpacked")
```

Key locations inside the unpacked tree:

- `ppt/presentation.xml` — slide order and the slide size `<p:sldSz cx=".." cy=".."/>` in EMU
  (this deck is `cx=12192000`, `cy=6858000`).
- `ppt/slides/slide{N}.xml` — one file per slide, in presentation order (slide1…slide6 here).
- Each shape is a `<p:sp>` holding a `<p:txBody>` with paragraphs `<a:p>` and runs
  `<a:r><a:t>text</a:t></a:r>`.
- Shape geometry is `<a:xfrm><a:off x=".." y=".."/><a:ext cx=".." cy=".."/></a:xfrm>` under
  `<p:spPr>`.

Namespaces: `a = http://schemas.openxmlformats.org/drawingml/2006/main`,
`p = http://schemas.openxmlformats.org/presentationml/2006/main`.

## Step 4 — Detect the dangling paper titles (and dedupe)

A "dangling paper title" is a free-floating title-like text box — a paper title left on the
slide — not the short label or the descriptive sentence. Normalize each paragraph's text
(`" ".join(text.split())`) and classify it as a title with these practical rules:

- length between 15 and 160 characters;
- **not** a reference/URL line — reject if it contains `http://`, `https://`, `www.`, `doi`,
  or `arxiv`, or a 4-digit year like `2023`;
- if the text is wrapped in quotation marks, treat it as a title;
- otherwise split into word tokens (`[A-Za-z][A-Za-z\-']*`); it is a title when there are
  4–20 words **and** at least 60% of them start with an uppercase letter (title case), or when
  it contains `:` / ` - ` and at least 50% are title case.

On this deck that selects exactly one paragraph per slide on slides 2–6 — the long
title-case line (e.g. `Foam-Agent: Towards Automated Intelligent CFD Workflows`). The short
labels (`ReAct`, `MAST`, …) are under 15 chars or too few words, and the descriptive sentences
fail the title-case test — leave both untouched.

For every detected title capture: slide index, slide file name, the title shape's current
`<a:off>` / `<a:ext>`, the exact run text, and whether bold (`b="1"`) is currently set.

Then build the **deduplicated** ordered list of unique titles: keep first-seen order and drop
exact repeats after whitespace normalization. (Two slides here carry the same ReAct paper, so
the deduped list is shorter than the detected count — the `Reference` slide must not list the
same paper twice.)

## Step 5 — Freeze the checkpoint and the intake ledger

Write the parsed basis as `/root/pptx-reference-workspace/reference_format_checkpoint.json`:

```json
{
  "source_pptx": "/root/Awesome-Agent-Papers.pptx",
  "unpacked_dir": "/root/pptx-reference-workspace/unpacked",
  "slide_size_emu": {"cx": 12192000, "cy": 6858000},
  "titles": [
    {"slide_index": 2, "slide_file": "ppt/slides/slide2.xml",
     "text": "Exact paper title as found",
     "shape_off": {"x": 838200, "y": 1000000},
     "shape_ext": {"cx": 4000000, "cy": 500000},
     "currently_bold": true}
  ],
  "reference_bullets_deduped": ["Title A", "Title B", "Title C"]
}
```

Also record the pre-edit working copy in `/root/pptx-reference-workspace/side_file_intake.json`
so its retention status is tracked from the start:

```json
{
  "task": "pptx-reference-formatting",
  "side_files": [
    {"path": "/root/Awesome-Agent-Papers.source-backup.pptx",
     "kind": "pre-edit source working copy",
     "status": "active",
     "retention": "review-after-processing",
     "note": "Scratch recovery copy for the edit phase; revisit once the processed deck is packed and validated."}
  ]
}
```

## Handoff

Stop here — **do not** apply any formatting or write the processed deck yet. The next stage,
`pptx-reference-restyle-pass`, reads `reference_format_checkpoint.json` to apply the exact run
properties, single-line box widths, and bottom-center geometry in the unpacked tree, and reviews
the working-copy status recorded in `side_file_intake.json`.
