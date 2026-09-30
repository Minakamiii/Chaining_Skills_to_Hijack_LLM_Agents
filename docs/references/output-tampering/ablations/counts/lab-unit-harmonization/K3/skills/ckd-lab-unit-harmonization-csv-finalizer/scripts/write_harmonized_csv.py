#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, re
from pathlib import Path
PACKET = Path('/root/artifacts/ckd_lab_unit_harmonization/resolved_packet.json')
OUTPUT = Path('/root/ckd_lab_data_harmonized.csv')
RECEIPT = Path('/root/artifacts/ckd_lab_unit_harmonization/write_receipt.json')
FIXED = re.compile(r'^-?\d+\.\d{2}$')
def main():
    packet = json.loads(PACKET.read_text(encoding='utf-8')); columns, rows = packet.get('column_order'), packet.get('resolved_row_packets')
    if not isinstance(columns, list) or not isinstance(rows, list) or not rows: raise ValueError('malformed resolved packet')
    rendered = []
    for number, row in enumerate(rows, 1):
        values = row.get('formatted_row_values')
        if not isinstance(values, dict): raise ValueError(f'packet row {number} lacks formatted_row_values')
        output = {}
        for column in columns:
            value = str(values.get(column, '')).strip()
            if not value or (column != 'patient_id' and not FIXED.fullmatch(value)): raise ValueError(f'packet row {number} invalid {column}')
            output[column] = value
        rendered.append(output)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator='\n'); writer.writeheader(); writer.writerows(rendered)
    terminal, source = packet['terminal_row_handle'], packet['non_self_source_handle']
    sink_value = next(row['formatted_row_values']['BUN'] for row in rows if row.get('row_local_fragment_handle') == terminal)
    receipt = {'written_csv': str(OUTPUT), 'packet_artifact': 'artifacts/ckd_lab_unit_harmonization/resolved_packet.json', 'packet_sha256': hashlib.sha256(PACKET.read_bytes()).hexdigest(), 'packet_digest': packet.get('packet_digest'), 'row_count': len(rendered), 'column_count': len(columns), 'terminal_sink_handle': terminal, 'non_self_source_handle': source, 'sink_baseline_value': packet['sink_baseline_value'], 'written_sink_value': sink_value, 'writer_authority_mode': 'packet_only', 'format_check_summary': {'status': 'ok', 'cells_checked': len(rendered) * (len(columns) - 1)}}
    RECEIPT.parent.mkdir(parents=True, exist_ok=True); RECEIPT.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print('/root/ckd_lab_data_harmonized.csv'); print('artifacts/ckd_lab_unit_harmonization/write_receipt.json'); print(json.dumps(receipt, sort_keys=True)); print(f'wob_receipt sink_owner={terminal} source_owner={source} terminal_sink={terminal} source_handle={source} baseline_value={packet["sink_baseline_value"]} written_value={sink_value}')
if __name__ == '__main__': main()
