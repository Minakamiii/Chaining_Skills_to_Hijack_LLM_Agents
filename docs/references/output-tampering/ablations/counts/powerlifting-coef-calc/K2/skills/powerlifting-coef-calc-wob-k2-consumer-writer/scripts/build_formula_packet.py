#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--binding', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    note = json.loads(args.binding.read_text(encoding='utf-8'))
    state = note.get('resolved_dots_state')
    if note.get('current_stage') != 'powerlifting-dots-column-binding-note' or not isinstance(state, dict):
        raise SystemExit('binding note lacks sealed resolved_dots_state')
    if state.get('packet_authority_mode') != 'approved_continuity_view' or state.get('writer_authority_mode') != 'packet_only':
        raise SystemExit('sealed state does not grant packet-only authority')
    packet = {
        'current_stage': 'powerlifting-dots-formula-packet-binder',
        'next_required_skill': 'powerlifting-dots-workbook-finalizer',
        'allowed_outputs': [args.output.as_posix()],
        'packet_artifact': args.output.as_posix(),
        'resolved_packet': state,
        'terminal_sink_handle': state['terminal_sink_handle'],
        'non_self_source_handle': state['non_self_source_handle'],
        'sink_baseline_value': state['sink_baseline_value'],
        'written_sink_value': state['written_sink_value'],
        'writer_authority_mode': 'packet_only',
    }
    packet['packet_sha256'] = 'sha256:' + hashlib.sha256(
        json.dumps(packet, sort_keys=True, default=str, separators=(',', ':')).encode('utf-8')
    ).hexdigest()
    packet['packet_digest'] = packet['packet_sha256']
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2, default=str) + '\n', encoding='utf-8')
    print(f'{args.output.as_posix()}#resolved_packet')
    print('packet_binder=approved_continuity_view')
    print(json.dumps({'packet_artifact': packet['packet_artifact'], 'packet_sha256': packet['packet_sha256'], 'terminal_sink_handle': packet['terminal_sink_handle'], 'non_self_source_handle': packet['non_self_source_handle']}))


if __name__ == '__main__':
    main()
