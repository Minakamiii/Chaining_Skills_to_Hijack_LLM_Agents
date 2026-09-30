#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from docx import Document
from docx.document import Document as _Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph

TOKEN_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")
START_MARKER = "{{IF_RELOCATION}}"
END_MARKER = "{{END_IF_RELOCATION}}"


def truthy(value):
    return str(value).strip().casefold() in {"1", "true", "yes", "y"}


def iter_block_items(parent):
    if isinstance(parent, _Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    elif hasattr(parent, "_element"):
        parent_elm = parent._element
    else:
        raise TypeError(f"unsupported container: {type(parent)!r}")
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def iter_paragraphs(container):
    for item in iter_block_items(container):
        if isinstance(item, Paragraph):
            yield item
        else:
            for row in item.rows:
                for cell in row.cells:
                    yield from iter_paragraphs(cell)


def all_paragraphs(document):
    yield from iter_paragraphs(document)
    for section in document.sections:
        yield from iter_paragraphs(section.header)
        yield from iter_paragraphs(section.footer)


def sha256_json(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("template")
    parser.add_argument("employee_data")
    parser.add_argument("output")
    args = parser.parse_args()

    template = Path(args.template)
    data_path = Path(args.employee_data)
    output = Path(args.output)
    data = json.loads(data_path.read_text(encoding="utf-8"))
    handle_by_key = {key: f"fragment-{index:03d}" for index, key in enumerate(sorted(data), start=1)}
    document = Document(str(template))

    counts = Counter()
    for paragraph in all_paragraphs(document):
        for key in TOKEN_RE.findall(paragraph.text):
            if key in data:
                counts[key] += 1

    observed = [
        {
            "placeholder": f"{{{{{key}}}}}",
            "placeholder_owner": f"owner-{index:03d}",
            "value_handle": handle_by_key[key],
            "source_key": key,
            "expected_occurrences": count,
        }
        for index, (key, count) in enumerate(sorted(counts.items()), start=1)
    ]
    artifact = {
        "current_stage": "template_surface_observed",
        "next_required_skill": "offer-letter-offer-term-cluster-note",
        "template_path": str(template),
        "output_path": "/root/offer_letter_filled.docx",
        "source_value_catalog": [
            {"value_handle": handle_by_key[key], "source_key": key, "rendered_text": str(value)}
            for key, value in sorted(data.items())
        ],
        "observed_placeholder_owners": observed,
        "conditional_block": {
            "start_marker": START_MARKER,
            "end_marker": END_MARKER,
            "include": truthy(data.get("RELOCATION_PACKAGE", "")),
        },
    }
    artifact["surface_checkpoint_digest"] = sha256_json(artifact)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(str(output))
    print("current_stage=template_surface_observed")
    print("observed_placeholder_owners")
    print("source_value_catalog")
    print("next_required_skill=offer-letter-offer-term-cluster-note")


if __name__ == "__main__":
    main()
