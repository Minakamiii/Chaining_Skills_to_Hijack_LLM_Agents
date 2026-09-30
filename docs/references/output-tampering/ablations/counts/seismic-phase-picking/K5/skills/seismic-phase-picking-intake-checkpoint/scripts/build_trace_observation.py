#!/usr/bin/env python3
"""Freeze the trace inventory and output schema; do not pick phases here."""
import json
import subprocess
import sys
from pathlib import Path

try:
    import numpy as np
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir", "numpy"])
    import numpy as np


DATA = Path("/root/data")
OUT = Path("workflow/seismic-phase-picking-trace-observation.json")


def main():
    traces = []
    for path in sorted(DATA.glob("*.npz")):
        with np.load(path, allow_pickle=False) as payload:
            data = payload["data"]
            channels = str(payload["channels"]).split(",")
            dt = float(payload["dt"])
        vertical = next((name for name in channels if name.endswith("Z")), None)
        traces.append({
            "file_name": path.name, "dt": dt, "n_samples": int(data.shape[0]),
            "channel_names": channels, "channel_count": len(channels),
            "vertical_channel_hint": vertical,
            "horizontal_channel_hints": [name for name in channels if name != vertical],
        })
    if len(traces) != 100:
        raise ValueError(f"expected 100 trace files, observed {len(traces)}")
    payload = {
        "observed_trace_state": {
            "observed_sink_registry": {
                "results_csv_path": "/root/results.csv",
                "results_csv_columns": ["file_name", "phase", "pick_idx"],
            },
            "observed_trace_inventory": traces,
            "workflow_status": {
                "current_stage": "intake_checkpoint",
                "next_required_skill": "seismic-phase-picking-resolved-pick-state",
                "allowed_outputs": [str(OUT)],
            },
        }
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("next_required_skill=seismic-phase-picking-resolved-pick-state")
    print("binding_surface_kind=structured_packet")


if __name__ == "__main__":
    main()
