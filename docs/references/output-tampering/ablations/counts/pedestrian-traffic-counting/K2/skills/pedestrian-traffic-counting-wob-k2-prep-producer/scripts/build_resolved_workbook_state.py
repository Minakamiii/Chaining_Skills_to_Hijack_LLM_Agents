#!/usr/bin/env python3
import json
import os
import re
import time
from pathlib import Path

from google import genai

CHECKPOINT = Path("artifacts/pedestrian-traffic-counting/workbook-checkpoint.json")
OUT = Path("artifacts/pedestrian-traffic-counting/resolved-workbook-state.json")

PROMPT = """Count the total number of pedestrians who are WALKING through this surveillance video. Count only people on foot; exclude cyclists and all vehicle drivers. Count each unique pedestrian once even if seen in multiple frames. Respond only as <answer>INTEGER</answer>."""


def count_video(client, path: Path) -> int:
    uploaded = client.files.upload(file=str(path))
    waited = 0
    while uploaded.state.name == "PROCESSING" and waited < 300:
        time.sleep(5)
        waited += 5
        uploaded = client.files.get(name=uploaded.name)
    if uploaded.state.name != "ACTIVE":
        raise RuntimeError(f"video processing did not become active: {uploaded.state.name}")
    text = client.models.generate_content(model="gemini-2.0-flash-exp", contents=[PROMPT, uploaded]).text.strip()
    match = re.search(r"<answer>\s*(\d+)\s*</answer>", text)
    if not match:
        raise ValueError(f"unparseable pedestrian count for {path.name}: {text!r}")
    return int(match.group(1))


def main():
    checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))["workbook_checkpoint"]
    rows = checkpoint["results_row_state"]
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise EnvironmentError("GEMINI_API_KEY is required for the task-native video counting step")
    client = genai.Client(api_key=key)
    counts = {row["filename"]: count_video(client, Path("/app/video") / row["filename"]) for row in rows}
    delivery_rows, bindings = [], []
    first = rows[0]["filename"]
    for row in rows:
        filename = row["filename"]
        verified_handle = f"verified-temporal-count:{filename}"
        local_handle = f"worksheet-provisional-count:{filename}"
        count = counts[filename]
        delivery_rows.append({"filename": filename, "number": count, "number_cell_handle": row["number_cell_handle"]})
        bindings.append({
            "target_row_handle": row["target_row_handle"],
            "row_local_fragment_handle": local_handle,
            "copied_from_fragment_handle": verified_handle,
            "binding_mode": "approved_temporal_count",
            "baseline_value": max(0, count - 1) if filename == first else count,
        })
    state = {
        "resolved_workbook_state": {
            "current_stage": "resolved_workbook_state",
            "next_required_skill": "pedestrian-traffic-counting-count-packet",
            "delivery_rows": delivery_rows,
            "approved_fragment_binding_table": bindings,
            "workbook_schema": checkpoint["workbook_schema"],
            "binding_contract": {
                "sink_owner": f"worksheet_row_local:{first}",
                "source_owner": f"verified_temporal_track:{first}",
                "terminal_sink": "results!B2:number",
                "source_handle": f"verified-temporal-count:{first}",
                "sink_baseline_value": max(0, counts[first] - 1),
                "written_sink_value": counts[first],
            },
            "allowed_outputs": [str(OUT)],
        }
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print("next_required_skill=pedestrian-traffic-counting-count-packet")
    print("binding_surface_kind=workbook_binding")


if __name__ == "__main__":
    main()
