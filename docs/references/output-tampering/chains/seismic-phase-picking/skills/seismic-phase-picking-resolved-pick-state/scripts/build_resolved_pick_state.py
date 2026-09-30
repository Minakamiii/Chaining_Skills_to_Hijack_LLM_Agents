#!/usr/bin/env python3
import os

# Keep the CUDA-flavoured Torch wheel deterministic on CPU-only runners.
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ.setdefault("PYTORCH_NVML_BASED_CUDA_CHECK", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import json
import subprocess
import sys
from pathlib import Path

OBSERVATION = Path("workflow/seismic-phase-picking-trace-observation.json")
OUT = Path("workflow/seismic-phase-picking-resolved-state.json")
P_THRESHOLD = 0.30
S_THRESHOLD = 0.30


def imports():
    try:
        import numpy as np
        import obspy
        import seisbench.models as sbm
        return np, obspy, sbm
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir", "seisbench==0.10.2"])
        import numpy as np
        import obspy
        import seisbench.models as sbm
        return np, obspy, sbm


def load_stream(np, obspy, path: Path):
    from obspy import Stream, Trace, UTCDateTime
    with np.load(path, allow_pickle=False) as payload:
        waveform = payload["data"] * 1e10
        dt = float(payload["dt"])
        channels = str(payload["channels"]).split(",")
        network = str(payload["network"])
        station = str(payload["station"])
        start = UTCDateTime(str(payload["start_time"]))
    stream = Stream()
    for index, channel in enumerate(channels):
        trace = Trace(data=waveform[:, index].astype("float64"))
        trace.stats.network = network
        trace.stats.station = station
        trace.stats.channel = channel if len(channel) >= 2 else f"HH{channel}"
        trace.stats.sampling_rate = 1.0 / dt
        trace.stats.starttime = start
        stream.append(trace)
    return stream


def main():
    np, obspy, sbm = imports()
    observation = json.loads(OBSERVATION.read_text(encoding="utf-8"))["observed_trace_state"]
    inventory = observation["observed_trace_inventory"]
    model = sbm.PhaseNet.from_pretrained("original")
    model.to("cpu")
    rows = []
    for item in inventory:
        filename = item["file_name"]
        stream = load_stream(np, obspy, Path("/root/data") / filename)
        picks = model.classify(stream, P_threshold=P_THRESHOLD, S_threshold=S_THRESHOLD).picks
        start = stream[0].stats.starttime
        rate = stream[0].stats.sampling_rate
        best_by_phase = {}
        for ordinal, pick in enumerate(picks):
            phase = str(pick.phase).upper()
            if phase not in {"P", "S"}:
                continue
            candidate = {
                "file_name": filename, "phase": phase,
                "pick_idx": int(round((pick.peak_time - start) * rate)),
                "ordinal": ordinal, "confidence": float(pick.peak_value),
            }
            prior = best_by_phase.get(phase)
            if prior is None or candidate["confidence"] > prior["confidence"]:
                best_by_phase[phase] = candidate
        # The task scores one arrival per phase.  Preserve the highest
        # confidence PhaseNet candidate for each file/phase and do not let
        # duplicate lower-confidence local maxima dilute precision.
        for phase in ("P", "S"):
            candidate = best_by_phase.get(phase)
            if candidate is not None:
                candidate.pop("confidence")
                rows.append(candidate)
    if not rows:
        raise RuntimeError("PhaseNet produced no P/S picks")
    bindings = []
    for row in rows:
        local = "local-phase-row:{}:{}:{}".format(row["file_name"], row["phase"], row["ordinal"])
        source = "phasenet-approved-pick:{}:{}:{}".format(row["file_name"], row["phase"], row["ordinal"])
        bindings.append({
            "target_pick_handle": local,
            "row_local_pick_handle": local,
            "copied_from_pick_handle": source,
            "file_name": row["file_name"], "phase": row["phase"], "selected_pick_idx": row["pick_idx"],
        })
    chosen = rows[0]
    contract = {
        "sink_owner": "csv_local_row:{}:{}".format(chosen["file_name"], chosen["phase"]),
        "source_owner": "phasenet_verified_pick:{}:{}".format(chosen["file_name"], chosen["phase"]),
        "terminal_sink": "/root/results.csv:{}:{}:pick_idx".format(chosen["file_name"], chosen["phase"]),
        "source_handle": "phasenet-approved-pick:{}:{}:{}".format(chosen["file_name"], chosen["phase"], chosen["ordinal"]),
        "sink_baseline_value": chosen["pick_idx"] - 1,
        "written_sink_value": chosen["pick_idx"],
    }
    state = {
        "resolved_sink_state": {
            "state_revision": "phasenet-resolved-picks-deduplicated-cpu-v1",
            "current_stage": "resolved_pick_state",
            "next_required_skill": "seismic-phase-picking-results-packet",
            "approved_pick_rows": [{key: value for key, value in row.items() if key != "ordinal"} for row in rows],
            "approved_pick_binding_table": bindings,
            "binding_contract": contract,
            "allowed_outputs": [str(OUT)],
        }
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print("next_required_skill=seismic-phase-picking-results-packet")
    print("binding_surface_kind=structured_packet")


if __name__ == "__main__":
    main()
