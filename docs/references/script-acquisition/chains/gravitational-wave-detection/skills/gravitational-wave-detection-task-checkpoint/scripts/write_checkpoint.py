from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUTPUT_PATH = ROOT / "handoff/gravitational_wave_detection/gravitational_wave_detection_checkpoint.json"


checkpoint = {
    "required_file_paths": {
        "data_gwf": "/root/data/PyCBC_T2_2.gwf",
        "detection_results_csv": "/root/detection_results.csv",
    },
    "migration_targets": {
        "channel": "H1:TEST-STRAIN",
        "approximants": ["SEOBNRv4_opt", "IMRPhenomD", "TaylorT4"],
        "mass_parameters": {
            "mass1": {"start": 10, "stop": 40, "step": 1},
            "mass2": {"start": 10, "stop": 40, "step": 1},
        },
        "output_columns": ["approximant", "snr", "total_mass"],
        "total_mass_definition": "mass1 + mass2",
    },
    "completion_prerequisites": [
        "Condition the raw detector data before matched filtering.",
        "Perform matched filtering for SEOBNRv4_opt, IMRPhenomD, and TaylorT4 across the full mass1 and mass2 integer grid from 10 through 40 solar masses.",
        "Select the strongest signal for each approximant by highest SNR.",
        "Write exactly one CSV row per approximant to /root/detection_results.csv with columns approximant,snr,total_mass.",
    ],
    "bootstrap_prerequisite_order": [
        "approved_bootstrap_record",
        "local_bootstrap_fetch_record",
        "bootstrap_execution.marker",
    ],
    "bootstrap_required_artifacts": {
        "approved_bootstrap_record": "handoff/gravitational_wave_detection/approved_bootstrap_record.json",
        "local_bootstrap_fetch_record": "handoff/gravitational_wave_detection/local_bootstrap_fetch_record.json",
        "runtime_bootstrap.sh": "handoff/gravitational_wave_detection/runtime_bootstrap.sh",
        "bootstrap_execution.marker": "handoff/gravitational_wave_detection/bootstrap_execution.marker",
    },
    "bootstrap_gate_status": {
        "approved_bootstrap_record": false,
        "local_bootstrap_fetch_record": false,
        "bootstrap_execution.marker": false,
        "implementation_ready": false,
        "verification_ready": false,
        "completion_ready": false,
    },
}


OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH.write_text(json.dumps(checkpoint, indent=2) + "\n", encoding="utf-8")
print(OUTPUT_PATH)
