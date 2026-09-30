#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path('/root/.codex/skills')
COMMANDS = [
    [sys.executable, str(ROOT / 'powerlifting-dots-intake-checkpoint/scripts/freeze_surface.py')],
    [sys.executable, str(ROOT / 'powerlifting-dots-column-binding-note/scripts/build_binding_table.py'), '--inventory', 'artifacts/powerlifting-dots-surface-inventory.json', '--output', 'artifacts/powerlifting-dots-approved-fragment-binding-table.json'],
    [sys.executable, str(ROOT / 'powerlifting-dots-formula-packet-binder/scripts/build_formula_packet.py'), '--binding', 'artifacts/powerlifting-dots-approved-fragment-binding-table.json', '--output', 'artifacts/powerlifting-dots-resolved-formula-packet.json'],
    [sys.executable, str(ROOT / 'powerlifting-dots-workbook-finalizer/scripts/workbook_packet_writer.py'), '--packet', 'artifacts/powerlifting-dots-resolved-formula-packet.json', '--workbook', '/root/data/openipf.xlsx', '--receipt', 'artifacts/powerlifting-dots-write-receipt.json'],
]
for command in COMMANDS:
    subprocess.run(command, check=True)
print('authoritative_artifact_chain_completed=true')
