#!/usr/bin/env python3
"""Execute the published four-stage artifact chain in its required order."""
from __future__ import annotations
import subprocess
from pathlib import Path

ROOT = Path('/root/.agents/skills')
COMMANDS = [
    ["python3", str(ROOT / "ckd-lab-unit-harmonization-intake-checkpoint/scripts/write_intake_checkpoint.py")],
    ["python3", str(ROOT / "ckd-lab-unit-harmonization-source-profile-note/scripts/build_source_profile_note.py")],
    ["python3", str(ROOT / "ckd-lab-unit-harmonization-conversion-packet-binder/scripts/build_resolved_packet.py")],
    ["python3", str(ROOT / "ckd-lab-unit-harmonization-csv-finalizer/scripts/write_harmonized_csv.py")],
]
for command in COMMANDS:
    subprocess.run(command, check=True)
print('artifact_chain_completed=true')
