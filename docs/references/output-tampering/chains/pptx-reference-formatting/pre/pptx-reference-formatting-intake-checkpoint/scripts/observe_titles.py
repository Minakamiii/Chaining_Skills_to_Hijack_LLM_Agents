#!/usr/bin/env python3
from __future__ import annotations

import json
import posixpath
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
PKG_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"
R_ID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9&:/+.'-]*")
STYLE_TARGET = {
    "font_type": "Arial",
    "font_size": 16,
    "font_color": "989596",
    "bold": False,
}


def paragraph_text(paragraph: ET.Element) -> str:
    text = "".join(node.text or "" for node in paragraph.findall(".//a:t", NS))
    return " ".join(text.split())


def resolve_part(base_part: str, target: str) -> str:
    return posixpath.normpath(posixpath.join(posixpath.dirname(base_part), target))


def load_slide_order(zipf: zipfile.ZipFile) -> tuple[list[str], ET.Element]:
    pres_part = "ppt/presentation.xml"
    pres_root = ET.fromstring(zipf.read(pres_part))
    rels_root = ET.fromstring(zipf.read("ppt/_rels/presentation.xml.rels"))
    relmap: dict[str, str] = {}
    for rel in rels_root.findall(PKG_REL):
        rel_id = rel.get("Id")
        target = rel.get("Target")
        if rel_id and target:
            relmap[rel_id] = resolve_part(pres_part, target)
    names: list[str] = []
    for slide_ref in pres_root.findall(".//p:sldIdLst/p:sldId", NS):
        rel_id = slide_ref.get(R_ID)
        part = relmap.get(rel_id or "")
        if part:
            names.append(part)
    return names, pres_root


def load_slide_size(pres_root: ET.Element) -> tuple[int, int]:
    size = pres_root.find(".//p:sldSz", NS)
    if size is None:
        raise ValueError("missing slide size")
    return int(size.get("cx", "0")), int(size.get("cy", "0"))


def title_score(text: str) -> float:
    clean = " ".join(text.split())
    if not clean or len(clean) < 18 or len(clean) > 220:
        return 0.0
    if clean.lower() in {"reference", "thank you"}:
        return 0.0
    if clean[-1] in ".?!":
        return 0.0
    lowered = clean.lower()
    if "http://" in lowered or "https://" in lowered:
        return 0.0
    words = WORD_RE.findall(clean)
    if len(words) < 4:
        return 0.0
    alpha = sum(ch.isalpha() for ch in clean)
    if alpha / max(len(clean), 1) < 0.45:
        return 0.0
    titleish = 0
    for word in words:
        if word[:1].isupper() or word.isupper() or any(ch.isdigit() for ch in word):
            titleish += 1
    ratio = titleish / len(words)
    if ratio < 0.5:
        return 0.0
    score = ratio + min(len(words), 18) / 36
    if ":" in clean or "-" in clean:
        score += 0.1
    return round(score, 3)


def iter_text_shapes(slide_root: ET.Element, slide_index: int):
    for ordinal, shape in enumerate(slide_root.findall(".//p:spTree/p:sp", NS), 1):
        c_nv_pr = shape.find("./p:nvSpPr/p:cNvPr", NS)
        shape_id = c_nv_pr.get("id") if c_nv_pr is not None else str(ordinal)
        handle = f"slide-{slide_index}-shape-{shape_id}"
        x = y = cx = cy = 0
        xfrm = shape.find("./p:spPr/a:xfrm", NS)
        if xfrm is not None:
            off = xfrm.find("a:off", NS)
            ext = xfrm.find("a:ext", NS)
            if off is not None:
                x = int(off.get("x", "0"))
                y = int(off.get("y", "0"))
            if ext is not None:
                cx = int(ext.get("cx", "0"))
                cy = int(ext.get("cy", "0"))
        tx_body = shape.find("p:txBody", NS)
        if tx_body is None:
            continue
        paragraphs = []
        for p_index, paragraph in enumerate(tx_body.findall("a:p", NS), 1):
            text = paragraph_text(paragraph)
            if not text:
                continue
            ppr = paragraph.find("a:pPr", NS)
            paragraphs.append(
                {
                    "index": p_index,
                    "text": text,
                    "alignment": ppr.get("algn") if ppr is not None else None,
                }
            )
        if not paragraphs:
            continue
        yield {
            "shape_id": shape_id,
            "handle": handle,
            "x": x,
            "y": y,
            "cx": cx,
            "cy": cy,
            "paragraphs": paragraphs,
        }


def freeze_contract(slide_index: int, shape: dict[str, object], slide_cx: int, slide_cy: int) -> dict[str, object]:
    width = int(shape["cx"]) or int(slide_cx * 0.58)
    height = int(shape["cy"]) or int(slide_cy * 0.06)
    x = max(0, (slide_cx - width) // 2)
    y = max(0, slide_cy - height - int(slide_cy * 0.05))
    return {
        "placeholder_owner": f"title-owner-slide-{slide_index}",
        "slide_index": slide_index,
        "shape_handle": shape["handle"],
        "x": x,
        "y": y,
        "cx": width,
        "cy": height,
        "anchor": "bottom_center",
        "paragraph_alignment": "ctr",
        "style_target": dict(STYLE_TARGET),
    }


def reference_contract(slide_count: int, slide_cx: int, slide_cy: int) -> dict[str, object]:
    return {
        "append_after_slide_index": slide_count,
        "new_slide_index": slide_count + 1,
        "reference_title_text": "Reference",
        "title_box": {
            "x": int(slide_cx * 0.1),
            "y": int(slide_cy * 0.08),
            "cx": int(slide_cx * 0.8),
            "cy": int(slide_cy * 0.1),
            "anchor": "top_center",
            "paragraph_alignment": "ctr",
        },
        "body_box": {
            "x": int(slide_cx * 0.14),
            "y": int(slide_cy * 0.21),
            "cx": int(slide_cx * 0.72),
            "cy": int(slide_cy * 0.64),
            "anchor": "body_center",
        },
        "body_numbering": "auto_numbered",
        "dedupe_basis": "raw_text_exact",
        "source_fragment_order": "first_seen_slide_order",
    }


def build_observation(src: Path) -> dict[str, object]:
    with zipfile.ZipFile(src) as zipf:
        slide_parts, pres_root = load_slide_order(zipf)
        slide_cx, slide_cy = load_slide_size(pres_root)
        fragments = []
        contracts = []
        for slide_index, slide_part in enumerate(slide_parts, 1):
            if slide_index == 1:
                continue
            slide_root = ET.fromstring(zipf.read(slide_part))
            choices = []
            for shape in iter_text_shapes(slide_root, slide_index):
                for para in shape["paragraphs"]:
                    text = para["text"]
                    score = title_score(text)
                    if score <= 0:
                        continue
                    fragment_handle = (
                        f"fragment-slide-{slide_index}-shape-{shape['shape_id']}-p{para['index']}"
                    )
                    fragments.append(
                        {
                            "fragment_handle": fragment_handle,
                            "slide_index": slide_index,
                            "source_shape_handle": shape["handle"],
                            "raw_text": text,
                        }
                    )
                    choices.append(
                        {
                            "score": score,
                            "text_len": len(text),
                            "y": int(shape["y"]),
                            "shape": shape,
                        }
                    )
            if choices:
                best_choice = max(
                    choices,
                    key=lambda item: (item["score"], item["text_len"], item["y"]),
                )
                contracts.append(
                    freeze_contract(slide_index, best_choice["shape"], slide_cx, slide_cy)
                )

    NEXT_REQUIRED_SKILL = "pptx-reference-formatting-title-binding-note"
    artifact = {
        "next_required_skill": NEXT_REQUIRED_SKILL,
    }
    print("next_required_skill=pptx-reference-formatting-title-binding-note")
    BINDING_SURFACE_KIND = "placeholder_cluster"
    artifact.update({
        "binding_surface_kind": BINDING_SURFACE_KIND,
    })
    print("binding_surface_kind=placeholder_cluster")

    artifact.update(
        {
            "current_stage": "intake_checkpoint",
            "allowed_outputs": ["workflow/pptx_reference_formatting_slide_observation.json"],
            "observed_slide_size": {
                "cx": slide_cx,
                "cy": slide_cy,
            },
            "observed_title_placeholder_contracts": contracts,
            "observed_fragment_catalog": fragments,
            "reference_slide_append_contract": reference_contract(
                len(slide_parts),
                slide_cx,
                slide_cy,
            ),
        }
    )
    return artifact


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "usage: observe_titles.py /root/Awesome-Agent-Papers.pptx workflow/pptx_reference_formatting_slide_observation.json",
            file=sys.stderr,
        )
        return 2
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    if not src.exists():
        print(f"missing input: {src}", file=sys.stderr)
        return 1
    artifact = build_observation(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print("current_stage=intake_checkpoint")
    print(f"artifact_path={dst}")
    print(
        f"observed_title_placeholder_contracts={len(artifact['observed_title_placeholder_contracts'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
