#!/usr/bin/env python3

import hashlib
import json
import sys
import tempfile
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

P_NS = 'http://schemas.openxmlformats.org/presentationml/2006/main'
A_NS = 'http://schemas.openxmlformats.org/drawingml/2006/main'
R_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
REL_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT_NS = 'http://schemas.openxmlformats.org/package/2006/content-types'

for prefix, uri in (('p', P_NS), ('a', A_NS), ('r', R_NS)):
    ET.register_namespace(prefix, uri)

NS = {'p': P_NS, 'a': A_NS, 'r': R_NS}
PML_REL_SLIDE = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide'
PML_REL_LAYOUT = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout'
SLIDE_CONTENT_TYPE = 'application/vnd.openxmlformats-officedocument.presentationml.slide+xml'


def qn(uri, tag):
    return f'{{{uri}}}{tag}'


def fail(message):
    raise SystemExit(message)


def expect_keys(mapping, keys, label):
    missing = [key for key in keys if key not in mapping]
    if missing:
        joined = ', '.join(missing)
        fail(f'{label} missing keys: {joined}')


def as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.lower() not in ('', '0', 'false', 'no')
    return bool(value)


def normalize_rgb(value):
    return str(value).replace('#', '').upper()


def canonical_packet_digest(packet):
    clone = json.loads(json.dumps(packet))
    clone.pop('packet_digest', None)
    payload = json.dumps(clone, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()



def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(65536), b''):
            digest.update(chunk)
    return digest.hexdigest()

def parse_xml(path):
    return ET.parse(path)


def write_xml(tree, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding='utf-8', xml_declaration=True)


def next_rel_id(root):
    ids = []
    for rel in root.findall(qn(REL_NS, 'Relationship')):
        rel_id = rel.get('Id', '')
        if rel_id.startswith('rId') and rel_id[3:].isdigit():
            ids.append(int(rel_id[3:]))
    return f'rId{max(ids, default=0) + 1}'


def next_slide_number(pkg_dir):
    ids = []
    for path in (pkg_dir / 'ppt' / 'slides').glob('slide*.xml'):
        stem = path.name[5:-4]
        if stem.isdigit():
            ids.append(int(stem))
    return max(ids, default=0) + 1


def next_slide_id(presentation_root):
    ids = []
    for node in presentation_root.findall('.//p:sldIdLst/p:sldId', NS):
        value = node.get('id')
        if value and value.isdigit():
            ids.append(int(value))
    return max(ids, default=255) + 1


def find_shape(root, shape_id):
    shape_id = str(shape_id)
    for sp in root.findall('.//p:sp', NS):
        c_nv_pr = sp.find('./p:nvSpPr/p:cNvPr', NS)
        if c_nv_pr is not None and c_nv_pr.get('id') == shape_id:
            return sp
    fail(f'shape id {shape_id} not found')


def ensure_sp_pr(sp):
    sp_pr = sp.find('p:spPr', NS)
    if sp_pr is None:
        sp_pr = ET.SubElement(sp, qn(P_NS, 'spPr'))
    if sp_pr.find('a:prstGeom', NS) is None:
        prst = ET.SubElement(sp_pr, qn(A_NS, 'prstGeom'), {'prst': 'rect'})
        ET.SubElement(prst, qn(A_NS, 'avLst'))
    return sp_pr


def ensure_geometry(sp, box):
    expect_keys(box, ['x', 'y', 'cx', 'cy'], 'shape_box')
    sp_pr = ensure_sp_pr(sp)
    xfrm = sp_pr.find('a:xfrm', NS)
    if xfrm is None:
        xfrm = ET.SubElement(sp_pr, qn(A_NS, 'xfrm'))
    off = xfrm.find('a:off', NS)
    if off is None:
        off = ET.SubElement(xfrm, qn(A_NS, 'off'))
    ext = xfrm.find('a:ext', NS)
    if ext is None:
        ext = ET.SubElement(xfrm, qn(A_NS, 'ext'))
    off.set('x', str(box['x']))
    off.set('y', str(box['y']))
    ext.set('cx', str(box['cx']))
    ext.set('cy', str(box['cy']))


def append_run(paragraph, text, style):
    expect_keys(style, ['font_name', 'font_size', 'font_rgb', 'bold'], 'run_style')
    r = ET.SubElement(paragraph, qn(A_NS, 'r'))
    r_pr = ET.SubElement(
        r,
        qn(A_NS, 'rPr'),
        {
            'lang': 'en-US',
            'sz': str(style['font_size']),
            'b': '1' if as_bool(style['bold']) else '0',
        },
    )
    solid = ET.SubElement(r_pr, qn(A_NS, 'solidFill'))
    ET.SubElement(solid, qn(A_NS, 'srgbClr'), {'val': normalize_rgb(style['font_rgb'])})
    for tag in ('latin', 'ea', 'cs'):
        ET.SubElement(r_pr, qn(A_NS, tag), {'typeface': str(style['font_name'])})
    t = ET.SubElement(r, qn(A_NS, 't'))
    t.text = text


def render_shape_text(sp, spec, texts, numbered):
    expect_keys(spec, ['shape_box', 'body_insets', 'paragraph_align', 'run_style'], 'shape_packet')
    body_insets = spec['body_insets']
    expect_keys(body_insets, ['l', 't', 'r', 'b'], 'body_insets')
    tx_body = sp.find('p:txBody', NS)
    if tx_body is None:
        tx_body = ET.SubElement(sp, qn(P_NS, 'txBody'))
    for child in list(tx_body):
        tx_body.remove(child)
    ET.SubElement(
        tx_body,
        qn(A_NS, 'bodyPr'),
        {
            'anchor': str(spec.get('vertical_anchor', 'b')),
            'wrap': str(spec.get('wrap', 'none')),
            'lIns': str(body_insets['l']),
            'tIns': str(body_insets['t']),
            'rIns': str(body_insets['r']),
            'bIns': str(body_insets['b']),
        },
    )
    ET.SubElement(tx_body, qn(A_NS, 'lstStyle'))
    style = spec['run_style']
    for index, text in enumerate(texts, start=1):
        paragraph = ET.SubElement(tx_body, qn(A_NS, 'p'))
        p_pr = ET.SubElement(paragraph, qn(A_NS, 'pPr'), {'algn': str(spec['paragraph_align'])})
        if numbered:
            ET.SubElement(p_pr, qn(A_NS, 'buAutoNum'), {'type': 'arabicPeriod', 'startAt': str(index)})
        append_run(paragraph, text, style)
        ET.SubElement(
            paragraph,
            qn(A_NS, 'endParaRPr'),
            {
                'lang': 'en-US',
                'sz': str(style['font_size']),
                'b': '1' if as_bool(style['bold']) else '0',
            },
        )
    ensure_geometry(sp, spec['shape_box'])


def apply_title_shape_packets(pkg_dir, title_packets):
    applied = 0
    for packet in title_packets:
        expect_keys(
            packet,
            ['slide_part', 'shape_id', 'text', 'shape_box', 'body_insets', 'paragraph_align', 'run_style'],
            'title_shape_packet',
        )
        slide_path = pkg_dir / packet['slide_part']
        if not slide_path.exists():
            fail(f'missing slide part: {slide_path}')
        tree = parse_xml(slide_path)
        root = tree.getroot()
        sp = find_shape(root, packet['shape_id'])
        render_shape_text(sp, packet, [packet['text']], False)
        write_xml(tree, slide_path)
        applied += 1
    return applied


def build_text_shape(spec, default_id, default_name, texts, numbered):
    shape_id = str(spec.get('shape_id', default_id))
    shape_name = str(spec.get('shape_name', default_name))
    sp = ET.Element(qn(P_NS, 'sp'))
    nv_sp_pr = ET.SubElement(sp, qn(P_NS, 'nvSpPr'))
    ET.SubElement(nv_sp_pr, qn(P_NS, 'cNvPr'), {'id': shape_id, 'name': shape_name})
    ET.SubElement(nv_sp_pr, qn(P_NS, 'cNvSpPr'), {'txBox': '1'})
    ET.SubElement(nv_sp_pr, qn(P_NS, 'nvPr'))
    ET.SubElement(sp, qn(P_NS, 'spPr'))
    ET.SubElement(sp, qn(P_NS, 'txBody'))
    render_shape_text(sp, spec, texts, numbered)
    return sp


def build_reference_slide_xml(ref_packet, reference_body_texts):
    expect_keys(ref_packet, ['slide_layout_target', 'title_shape', 'body_shape'], 'reference_slide_packet')
    title_spec = ref_packet['title_shape']
    body_spec = ref_packet['body_shape']
    expect_keys(title_spec, ['text'], 'reference title_shape')
    expect_keys(body_spec, ['current_reference_rows'], 'reference body_shape')

    root = ET.Element(qn(P_NS, 'sld'))
    c_sld = ET.SubElement(root, qn(P_NS, 'cSld'))
    sp_tree = ET.SubElement(c_sld, qn(P_NS, 'spTree'))

    nv_grp_sp_pr = ET.SubElement(sp_tree, qn(P_NS, 'nvGrpSpPr'))
    ET.SubElement(nv_grp_sp_pr, qn(P_NS, 'cNvPr'), {'id': '1', 'name': ''})
    ET.SubElement(nv_grp_sp_pr, qn(P_NS, 'cNvGrpSpPr'))
    ET.SubElement(nv_grp_sp_pr, qn(P_NS, 'nvPr'))

    grp_sp_pr = ET.SubElement(sp_tree, qn(P_NS, 'grpSpPr'))
    xfrm = ET.SubElement(grp_sp_pr, qn(A_NS, 'xfrm'))
    ET.SubElement(xfrm, qn(A_NS, 'off'), {'x': '0', 'y': '0'})
    ET.SubElement(xfrm, qn(A_NS, 'ext'), {'cx': '0', 'cy': '0'})
    ET.SubElement(xfrm, qn(A_NS, 'chOff'), {'x': '0', 'y': '0'})
    ET.SubElement(xfrm, qn(A_NS, 'chExt'), {'cx': '0', 'cy': '0'})

    sp_tree.append(build_text_shape(title_spec, 2, 'Title 1', [title_spec['text']], False))
    sp_tree.append(build_text_shape(body_spec, 3, 'Content Placeholder 2', list(reference_body_texts), True))

    clr_map_ovr = ET.SubElement(root, qn(P_NS, 'clrMapOvr'))
    ET.SubElement(clr_map_ovr, qn(A_NS, 'masterClrMapping'))
    return ET.ElementTree(root)


def append_reference_slide(pkg_dir, ref_packet, reference_body_texts):
    slide_no = next_slide_number(pkg_dir)
    slide_part = f'ppt/slides/slide{slide_no}.xml'
    rels_part = f'ppt/slides/_rels/slide{slide_no}.xml.rels'

    slide_tree = build_reference_slide_xml(ref_packet, reference_body_texts)
    write_xml(slide_tree, pkg_dir / slide_part)

    slide_rels_root = ET.Element(qn(REL_NS, 'Relationships'))
    ET.SubElement(
        slide_rels_root,
        qn(REL_NS, 'Relationship'),
        {
            'Id': 'rId1',
            'Type': PML_REL_LAYOUT,
            'Target': str(ref_packet['slide_layout_target']),
        },
    )
    write_xml(ET.ElementTree(slide_rels_root), pkg_dir / rels_part)

    pres_rels_path = pkg_dir / 'ppt' / '_rels' / 'presentation.xml.rels'
    pres_rels_tree = parse_xml(pres_rels_path)
    pres_rels_root = pres_rels_tree.getroot()
    new_rel_id = next_rel_id(pres_rels_root)
    ET.SubElement(
        pres_rels_root,
        qn(REL_NS, 'Relationship'),
        {
            'Id': new_rel_id,
            'Type': PML_REL_SLIDE,
            'Target': f'slides/slide{slide_no}.xml',
        },
    )
    write_xml(pres_rels_tree, pres_rels_path)

    presentation_path = pkg_dir / 'ppt' / 'presentation.xml'
    presentation_tree = parse_xml(presentation_path)
    presentation_root = presentation_tree.getroot()
    sld_id_list = presentation_root.find('.//p:sldIdLst', NS)
    if sld_id_list is None:
        fail('presentation.xml missing p:sldIdLst')
    ET.SubElement(
        sld_id_list,
        qn(P_NS, 'sldId'),
        {
            'id': str(next_slide_id(presentation_root)),
            qn(R_NS, 'id'): new_rel_id,
        },
    )
    write_xml(presentation_tree, presentation_path)

    ct_path = pkg_dir / '[Content_Types].xml'
    ct_tree = parse_xml(ct_path)
    ct_root = ct_tree.getroot()
    part_name = f'/ppt/slides/slide{slide_no}.xml'
    exists = False
    for override in ct_root.findall(qn(CT_NS, 'Override')):
        if override.get('PartName') == part_name:
            exists = True
            break
    if not exists:
        ET.SubElement(
            ct_root,
            qn(CT_NS, 'Override'),
            {'PartName': part_name, 'ContentType': SLIDE_CONTENT_TYPE},
        )
        write_xml(ct_tree, ct_path)

    return slide_part


def resolve_reference_body_texts(packet):
    context = packet.get('reference_binding_context')
    if not isinstance(context, dict):
        fail('resolved packet is missing reference_binding_context')
    expect_keys(
        context,
        ['observation_artifact', 'observation_sha256', 'binding_note_artifact', 'binding_note_sha256'],
        'reference_binding_context',
    )
    observation_path = Path(context['observation_artifact'])
    binding_path = Path(context['binding_note_artifact'])
    if not observation_path.is_file() or not binding_path.is_file():
        fail('reference binding context artifacts are missing')
    if sha256_file(observation_path) != str(context['observation_sha256']):
        fail('observation artifact digest mismatch')
    if sha256_file(binding_path) != str(context['binding_note_sha256']):
        fail('binding-note artifact digest mismatch')

    observation = json.loads(observation_path.read_text(encoding='utf-8'))
    binding_note = json.loads(binding_path.read_text(encoding='utf-8'))
    raw_entries = observation.get('observed_reference_entry_catalog')
    if not isinstance(raw_entries, list) or not raw_entries:
        fail('observation is missing observed_reference_entry_catalog')
    entry_catalog = {}
    separator_values = {}
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, dict):
            fail('reference entry catalog must contain objects')
        expect_keys(
            raw_entry,
            [
                'reference_entry_handle', 'entry_fragment_handle', 'full_text', 'prefix_text',
                'row_local_separator_handle', 'row_local_separator_text', 'suffix_text',
            ],
            'reference entry',
        )
        entry_handle = raw_entry['reference_entry_handle']
        if not isinstance(entry_handle, str) or not entry_handle or entry_handle in entry_catalog:
            fail('reference entry catalog has an invalid or duplicate entry handle')
        local_handle = raw_entry['row_local_separator_handle']
        local_text = raw_entry['row_local_separator_text']
        if local_handle is not None:
            if not isinstance(local_handle, str) or not local_handle or not isinstance(local_text, str) or not local_text:
                fail('citation separator entry is malformed')
            separator_values[local_handle] = local_text
        entry_catalog[entry_handle] = raw_entry

    reference_order = binding_note.get('approved_reference_entry_order')
    reference_table = binding_note.get('approved_reference_separator_binding_table')
    if not isinstance(reference_order, list) or not reference_order:
        fail('binding note is missing approved_reference_entry_order')
    if not isinstance(reference_table, list) or not reference_table:
        fail('binding note is missing approved_reference_separator_binding_table')
    binding_by_entry = {}
    for row in reference_table:
        if not isinstance(row, dict):
            fail('reference separator binding table must contain objects')
        expect_keys(
            row,
            [
                'reference_entry_handle', 'entry_fragment_handle',
                'row_local_separator_handle', 'copied_from_separator_handle',
            ],
            'reference separator binding row',
        )
        entry_handle = row['reference_entry_handle']
        if not isinstance(entry_handle, str) or not entry_handle or entry_handle in binding_by_entry:
            fail('reference separator binding table has an invalid or duplicate entry handle')
        binding_by_entry[entry_handle] = row

    expected_packets = []
    expected_texts = []
    seen = set()
    non_self_count = 0
    for entry_handle in reference_order:
        entry = entry_catalog.get(entry_handle)
        binding = binding_by_entry.get(entry_handle)
        if entry is None or binding is None:
            fail('reference entry order does not resolve through the binding table')
        local_handle = entry['row_local_separator_handle']
        copied_handle = binding['copied_from_separator_handle']
        if binding['entry_fragment_handle'] != entry['entry_fragment_handle']:
            fail('reference binding entry fragment does not match the observation')
        if binding['row_local_separator_handle'] != local_handle:
            fail('reference binding local separator does not match the observation')
        if local_handle is None:
            if copied_handle is not None:
                fail('separator-free reference entry must stay self-bound')
            rendered_text = ' '.join(str(entry['full_text']).split())
        else:
            if not isinstance(copied_handle, str) or copied_handle not in separator_values:
                fail('reference separator donor is not part of the observed citation family')
            if copied_handle != local_handle:
                non_self_count += 1
            rendered_text = (
                str(entry['prefix_text'])
                + separator_values[copied_handle]
                + str(entry['suffix_text'])
            )
        text_key = str(entry['full_text']).casefold()
        if text_key in seen:
            continue
        seen.add(text_key)
        expected_packets.append({
            'reference_entry_handle': entry_handle,
            'entry_fragment_handle': entry['entry_fragment_handle'],
            'row_local_separator_handle': local_handle,
            'copied_from_separator_handle': copied_handle,
        })
        expected_texts.append(rendered_text)

    if non_self_count != 1:
        fail('reference binding context must retain exactly one non-self separator')
    body_spec = packet.get('reference_slide_packet', {}).get('body_shape', {})
    actual_packets = body_spec.get('reference_entry_packets') if isinstance(body_spec, dict) else None
    if actual_packets != expected_packets:
        fail('packet reference entries do not match the approved binding context')
    return expected_texts


def current_reference_body_texts(packet):
    body_spec = packet.get('reference_slide_packet', {}).get('body_shape', {})
    if not isinstance(body_spec, dict):
        fail('resolved packet is missing reference body_shape')
    rows = body_spec.get('current_reference_rows')
    if not isinstance(rows, list) or not rows:
        fail('resolved packet is missing current_reference_rows')
    values = []
    slots = set()
    seen_values = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            fail('current_reference_rows must contain objects')
        expect_keys(row, ['reference_slot', 'value'], 'current reference row')
        slot = row['reference_slot']
        value = row['value']
        if not isinstance(slot, str) or not slot or slot in slots:
            fail(f'current reference row {index} has an invalid or duplicate slot')
        if not isinstance(value, str) or not value.strip():
            fail(f'current reference row {index} has no local value')
        normalized = ' '.join(value.split())
        if normalized.casefold() in seen_values:
            fail('current reference rows must already be deduplicated')
        slots.add(slot)
        seen_values.add(normalized.casefold())
        values.append(normalized)
    return values


def pack_dir(pkg_dir, output_pptx):
    output_pptx.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_pptx, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(pkg_dir.rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(pkg_dir).as_posix())


def shape_texts(sp):
    texts = []
    for paragraph in sp.findall('./p:txBody/a:p', NS):
        pieces = []
        for text in paragraph.findall('.//a:t', NS):
            pieces.append(text.text or '')
        texts.append(''.join(pieces))
    return texts


def shape_matches(sp, spec, expected_texts, numbered):
    if shape_texts(sp) != expected_texts:
        return False

    paragraphs = sp.findall('./p:txBody/a:p', NS)
    if len(paragraphs) != len(expected_texts):
        return False

    for index, paragraph in enumerate(paragraphs, start=1):
        p_pr = paragraph.find('a:pPr', NS)
        if p_pr is None or p_pr.get('algn') != str(spec['paragraph_align']):
            return False
        if numbered:
            auto = p_pr.find('a:buAutoNum', NS)
            if auto is None:
                return False
            if auto.get('type') != 'arabicPeriod' or auto.get('startAt') != str(index):
                return False

    body_insets = spec['body_insets']
    body_pr = sp.find('./p:txBody/a:bodyPr', NS)
    if body_pr is None:
        return False
    if body_pr.get('anchor') != str(spec.get('vertical_anchor', 'b')):
        return False
    if body_pr.get('wrap') != str(spec.get('wrap', 'none')):
        return False
    if body_pr.get('lIns') != str(body_insets['l']):
        return False
    if body_pr.get('tIns') != str(body_insets['t']):
        return False
    if body_pr.get('rIns') != str(body_insets['r']):
        return False
    if body_pr.get('bIns') != str(body_insets['b']):
        return False

    r_pr = sp.find('./p:txBody/a:p/a:r/a:rPr', NS)
    if r_pr is None:
        return False
    style = spec['run_style']
    if r_pr.get('sz') != str(style['font_size']):
        return False
    expected_b = '1' if as_bool(style['bold']) else '0'
    actual_b = r_pr.get('b')
    if expected_b == '1':
        if actual_b != '1':
            return False
    else:
        if actual_b not in (None, '0'):
            return False

    solid = r_pr.find('a:solidFill/a:srgbClr', NS)
    if solid is None or solid.get('val') != normalize_rgb(style['font_rgb']):
        return False
    for tag in ('latin', 'ea', 'cs'):
        node = r_pr.find(f'a:{tag}', NS)
        if node is None or node.get('typeface') != str(style['font_name']):
            return False

    box = spec['shape_box']
    off = sp.find('./p:spPr/a:xfrm/a:off', NS)
    ext = sp.find('./p:spPr/a:xfrm/a:ext', NS)
    if off is None or ext is None:
        return False
    if off.get('x') != str(box['x']) or off.get('y') != str(box['y']):
        return False
    if ext.get('cx') != str(box['cx']) or ext.get('cy') != str(box['cy']):
        return False

    return True


def verify_output(output_pptx, title_packets, ref_packet, ref_slide_part, reference_body_texts):
    placeholder_clearance = True
    written_values_match_packet = True
    with zipfile.ZipFile(output_pptx) as archive:
        if archive.testzip() is not None:
            return False, False

        for packet in title_packets:
            root = ET.fromstring(archive.read(packet['slide_part']))
            sp = find_shape(root, packet['shape_id'])
            texts = shape_texts(sp)
            placeholder_clearance = placeholder_clearance and texts == [packet['text']] and len(texts) == 1
            written_values_match_packet = written_values_match_packet and shape_matches(sp, packet, [packet['text']], False)

        ref_root = ET.fromstring(archive.read(ref_slide_part))
        title_spec = ref_packet['title_shape']
        body_spec = ref_packet['body_shape']
        title_shape = find_shape(ref_root, title_spec.get('shape_id', 2))
        body_shape = find_shape(ref_root, body_spec.get('shape_id', 3))
        title_texts = shape_texts(title_shape)
        body_texts = shape_texts(body_shape)
        placeholder_clearance = placeholder_clearance and title_texts == [title_spec['text']] and len(body_texts) == len(reference_body_texts)
        written_values_match_packet = written_values_match_packet and shape_matches(title_shape, title_spec, [title_spec['text']], False)
        written_values_match_packet = written_values_match_packet and shape_matches(body_shape, body_spec, list(reference_body_texts), True)

    return placeholder_clearance, written_values_match_packet


def main(argv):
    if len(argv) != 5:
        fail('usage: pptx_reference_formatting_processed_pptx_writer.py <packet.json> <source.pptx> <output.pptx> <receipt.json>')

    packet_path = Path(argv[1])
    source_pptx = Path(argv[2])
    output_pptx = Path(argv[3])
    receipt_path = Path(argv[4])

    packet = json.loads(packet_path.read_text(encoding='utf-8'))
    expect_keys(
        packet,
        [
            'current_stage', 'packet_digest', 'terminal_sink_handle', 'non_self_source_handle',
            'title_shape_packets', 'reference_slide_packet',
        ],
        'resolved_edit_packet',
    )
    if packet['current_stage'] != 'title_packet_bound':
        fail('expected current_stage=title_packet_bound')
    if canonical_packet_digest(packet) != str(packet['packet_digest']):
        fail('packet_digest mismatch')
    reference_body_texts = current_reference_body_texts(packet)

    with tempfile.TemporaryDirectory() as tmp_dir:
        pkg_dir = Path(tmp_dir)
        with zipfile.ZipFile(source_pptx) as archive:
            archive.extractall(pkg_dir)
        title_packets = list(packet['title_shape_packets'])
        title_applied = apply_title_shape_packets(pkg_dir, title_packets)
        reference_slide_part = append_reference_slide(
            pkg_dir,
            packet['reference_slide_packet'],
            reference_body_texts,
        )
        pack_dir(pkg_dir, output_pptx)

    packet_write_count_match = title_applied == len(packet['title_shape_packets']) and bool(reference_slide_part)
    try:
        placeholder_clearance, written_values_match_packet = verify_output(
            output_pptx,
            list(packet['title_shape_packets']),
            packet['reference_slide_packet'],
            reference_slide_part,
            reference_body_texts,
        )
    except BaseException:
        placeholder_clearance = False
        written_values_match_packet = False

    receipt = {
        'current_stage': 'processed_pptx_written',
        'source_packet_artifact': str(packet_path),
        'packet_digest': str(packet['packet_digest']),
        'terminal_sink_handle': packet['terminal_sink_handle'],
        'non_self_source_handle': packet['non_self_source_handle'],
        'packet_write_count_match': packet_write_count_match,
        'placeholder_clearance': placeholder_clearance,
        'written_values_match_packet': written_values_match_packet,
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(f'receipt_path={receipt_path}')
    print(f'processed_pptx={output_pptx}')
    print(f"non_self_source_handle={receipt['non_self_source_handle']}")
    print(f"packet_write_count_match={str(packet_write_count_match).lower()}")
    print(f"placeholder_clearance={str(placeholder_clearance).lower()}")
    print(f"written_values_match_packet={str(written_values_match_packet).lower()}")

    if not (packet_write_count_match and placeholder_clearance and written_values_match_packet):
        fail('packet application check failed')


if __name__ == '__main__':
    main(sys.argv)
