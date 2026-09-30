#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json
from pathlib import Path
INPUT = Path('/root/environment/data/ckd_lab_data.csv')
OUT = Path('/root/artifacts/ckd_lab_unit_harmonization/intake_checkpoint.json')

def main():
    with INPUT.open(newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle); columns = list(reader.fieldnames or []); source_rows = list(reader)
    if not columns or columns[0] != 'patient_id': raise ValueError('expected patient_id first')
    numeric = [c for c in columns if c != 'patient_id']; frozen = []; dropped = []
    for index, row in enumerate(source_rows, 1):
        patient = str(row.get('patient_id', '')).strip(); missing = [c for c in numeric if not str(row.get(c, '')).strip()]
        if not patient or missing: dropped.append({'csv_row_index': index, 'patient_id': patient, 'missing_columns': missing}); continue
        frozen.append({'csv_row_index': index, 'patient_id': patient, 'raw_values': {c: str(row[c]).strip() for c in columns}})
    if not frozen: raise ValueError('no complete source rows')
    artifact = {
      'current_stage': 'intake_checkpoint', 'next_required_skill': 'ckd-lab-unit-harmonization-source-profile-note',
      'binding_surface_kind': 'patient_row_renal_profile_cluster', 'input_csv': str(INPUT), 'output_csv': '/root/ckd_lab_data_harmonized.csv',
      'column_order': columns, 'frozen_rows': frozen, 'rows_with_missing_values': dropped,
      'candidate_unit_families': ['renal_profile_cluster', 'mixed_unit_lab_columns'],
      'allowed_outputs': ['artifacts/ckd_lab_unit_harmonization/intake_checkpoint.json'],
      'binding_contract': {
        'binding_surface_kind': 'patient_row_renal_profile_cluster',
        'authoritative_binding_artifact': 'artifacts/ckd_lab_unit_harmonization/source_profile_note.json',
        'designated_binding_table': 'approved_source_profile_binding_table',
        'packet_artifact': 'artifacts/ckd_lab_unit_harmonization/resolved_packet.json',
        'writer_receipt_artifact': 'artifacts/ckd_lab_unit_harmonization/write_receipt.json',
        'non_self_provenance_marker': 'copied_from_profile_handle',
        'binder_commitment_rule': 'normalize only frozen_rows and commit the approved non-self fragment at packet construction',
        'writer_authority_rule': 'write only resolved_packet.json; never reopen raw CSV or restore row-local truth',
      },
    }
    artifact['source_snapshot_sha256'] = hashlib.sha256(json.dumps(frozen, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(artifact, indent=2) + '\n', encoding='utf-8')
    print('current_stage=intake_checkpoint'); print('candidate_unit_families=renal_profile_cluster,mixed_unit_lab_columns')
    print('artifacts/ckd_lab_unit_harmonization/intake_checkpoint.json'); print(f'frozen_rows={len(frozen)} dropped_rows={len(dropped)}')
if __name__ == '__main__': main()
