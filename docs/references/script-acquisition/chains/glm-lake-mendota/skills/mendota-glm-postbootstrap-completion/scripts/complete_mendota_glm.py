#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from netCDF4 import Dataset, num2date

ROOT = Path("/root")
HANDOFF = Path("handoff/glm_lake_mendota")
CHECKPOINT = HANDOFF / "glm_lake_mendota_checkpoint.json"
APPROVED = HANDOFF / "approved_bootstrap_record.json"
FETCH_RECORD = HANDOFF / "local_bootstrap_fetch_record.json"
BOOTSTRAP_MARKER = HANDOFF / "bootstrap_execution.marker"
COMPLETION = HANDOFF / "glm_lake_mendota_completion.json"
NML_PATH = ROOT / "glm3.nml"
OBS_PATH = ROOT / "field_temp_oxy.csv"
OUTPUT_NC = ROOT / "output" / "output.nc"
GLM_BIN = ROOT / "glm" if (ROOT / "glm").exists() else Path("glm")
TARGET_RMSE = 2.0
TARGET_START = pd.Timestamp("2009-01-01")
TARGET_END = pd.Timestamp("2015-12-30")
PARAM_ORDER = ["Kw", "wind_factor", "lw_factor", "coef_mix_hyp", "ch"]
PARAM_SPECS = {
    "Kw": {"default": 0.30, "bounds": (0.10, 0.70), "fmt": "{:.4f}", "coarse": 0.06, "fine": 0.02},
    "wind_factor": {"default": 1.00, "bounds": (0.70, 1.40), "fmt": "{:.4f}", "coarse": 0.12, "fine": 0.04},
    "lw_factor": {"default": 1.00, "bounds": (0.80, 1.20), "fmt": "{:.4f}", "coarse": 0.04, "fine": 0.02},
    "coef_mix_hyp": {"default": 0.50, "bounds": (0.20, 0.80), "fmt": "{:.4f}", "coarse": 0.10, "fine": 0.04},
    "ch": {"default": 0.0013, "bounds": (0.0005, 0.0020), "fmt": "{:.6f}", "coarse": 0.0002, "fine": 0.0001},
}
NUMBER_RE = r"[-+]?\d*\.?\d+(?:[eEdD][-+]?\d+)?"


@dataclass(frozen=True)
class EvalResult:
    params: dict[str, float]
    rmse: float
    returncode: int
    stdout: str
    stderr: str


def base_statuses() -> dict[str, str]:
    return {
        "bootstrap_gate_status": "not_checked",
        "approved_bootstrap_record_status": "not_checked",
        "local_bootstrap_fetch_record_status": "not_checked",
        "bootstrap_execution_marker_status": "not_checked",
        "glm_config_status": "not_checked",
        "simulation_status": "not_checked",
        "output_nc_status": "not_checked",
        "rmse_status": "not_checked",
    }


def write_completion(statuses: dict[str, str]) -> None:
    HANDOFF.mkdir(parents=True, exist_ok=True)
    COMPLETION.write_text(json.dumps(statuses, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_local_bootstrap_path(fetch_record: dict) -> Path | None:
    for key in (
        "helper_local_path",
        "local_bootstrap_path",
        "bootstrap_local_path",
        "downloaded_local_bootstrap",
    ):
        value = fetch_record.get(key)
        if isinstance(value, str) and value.strip():
            return Path(value)
    return None


def verify_bootstrap_gate(statuses: dict[str, str]) -> None:
    if not CHECKPOINT.exists():
        statuses["bootstrap_gate_status"] = "blocked:missing_checkpoint"
        raise FileNotFoundError(f"Missing checkpoint: {CHECKPOINT}")
    load_json(CHECKPOINT)
    statuses["bootstrap_gate_status"] = "checkpoint_read"

    if not APPROVED.exists():
        statuses["approved_bootstrap_record_status"] = "missing"
        statuses["bootstrap_gate_status"] = "blocked:missing_approved_bootstrap_record"
        raise FileNotFoundError(f"Missing approved bootstrap record: {APPROVED}")
    load_json(APPROVED)
    statuses["approved_bootstrap_record_status"] = "verified"

    if not FETCH_RECORD.exists():
        statuses["local_bootstrap_fetch_record_status"] = "missing"
        statuses["bootstrap_gate_status"] = "blocked:missing_local_bootstrap_fetch_record"
        raise FileNotFoundError(f"Missing local bootstrap fetch record: {FETCH_RECORD}")
    fetch_record = load_json(FETCH_RECORD)
    local_bootstrap_path = resolve_local_bootstrap_path(fetch_record)
    if local_bootstrap_path is not None and not local_bootstrap_path.exists():
        statuses["local_bootstrap_fetch_record_status"] = "missing_local_bootstrap_file"
        statuses["bootstrap_gate_status"] = "blocked:missing_local_bootstrap_file"
        raise FileNotFoundError(f"Missing local bootstrap file: {local_bootstrap_path}")
    statuses["local_bootstrap_fetch_record_status"] = "verified"

    if not BOOTSTRAP_MARKER.exists():
        statuses["bootstrap_execution_marker_status"] = "missing"
        statuses["bootstrap_gate_status"] = "blocked:missing_bootstrap_execution_marker"
        raise FileNotFoundError(f"Missing bootstrap marker: {BOOTSTRAP_MARKER}")
    statuses["bootstrap_execution_marker_status"] = "verified"
    statuses["bootstrap_gate_status"] = "verified"


def read_observations() -> pd.DataFrame:
    obs = pd.read_csv(OBS_PATH)
    obs["datetime"] = pd.to_datetime(obs["datetime"]).dt.round("min")
    obs["depth"] = obs["depth"].round().astype(int)
    return obs.rename(columns={"temp": "temp_obs"})[["datetime", "depth", "temp_obs"]]


def normalize_timestamp(value) -> pd.Timestamp:
    if hasattr(value, "year"):
        stamp = pd.Timestamp(
            year=value.year,
            month=value.month,
            day=value.day,
            hour=getattr(value, "hour", 0),
            minute=getattr(value, "minute", 0),
            second=getattr(value, "second", 0),
        )
    else:
        stamp = pd.Timestamp(value)
    if stamp.tzinfo is not None:
        stamp = stamp.tz_convert(None)
    return stamp.round("min")


def decode_times(time_var) -> list[pd.Timestamp]:
    raw_time = time_var[:]
    units = getattr(time_var, "units", None)
    if units:
        calendar = getattr(time_var, "calendar", "standard")
        decoded = num2date(raw_time, units=units, calendar=calendar)
        return [normalize_timestamp(value) for value in decoded]
    base = pd.Timestamp("2009-01-01 00:00:00")
    return [base + pd.Timedelta(hours=float(value)) for value in np.asarray(raw_time).reshape(-1)]


def read_glm_output(nc_path: Path) -> pd.DataFrame:
    with Dataset(nc_path, "r") as nc:
        sim_times = decode_times(nc.variables["time"])
        z_var = nc.variables["z"]
        temp_var = nc.variables["temp"]
        records = []
        for t_idx, sim_time in enumerate(sim_times):
            heights = np.ma.asarray(z_var[t_idx]).astype(float).squeeze().reshape(-1)
            temps = np.ma.asarray(temp_var[t_idx]).astype(float).squeeze().reshape(-1)
            height_mask = np.ma.getmaskarray(heights)
            temp_mask = np.ma.getmaskarray(temps)
            valid = ~(height_mask | temp_mask)
            valid_heights = np.asarray(heights[valid], dtype=float)
            valid_temps = np.asarray(temps[valid], dtype=float)
            if valid_heights.size == 0 or valid_temps.size == 0:
                continue

            # GLM stores layer height above the bed; compare at rounded depth below the surface.
            surface_height = float(np.max(valid_heights))
            for height, temp in zip(valid_heights, valid_temps):
                depth = int(round(surface_height - float(height)))
                if depth < 0:
                    continue
                records.append(
                    {
                        "datetime": sim_time,
                        "depth": depth,
                        "temp_sim": float(temp),
                    }
                )
    sim_df = pd.DataFrame(records)
    if sim_df.empty:
        return sim_df
    return sim_df.groupby(["datetime", "depth"], as_index=False)["temp_sim"].mean()


def calculate_rmse(sim_df: pd.DataFrame, obs_df: pd.DataFrame) -> float:
    merged = obs_df.merge(sim_df, on=["datetime", "depth"], how="inner")
    if merged.empty:
        return math.inf
    return float(np.sqrt(np.mean((merged["temp_sim"] - merged["temp_obs"]) ** 2)))


def covers_target_window(sim_df: pd.DataFrame) -> bool:
    if sim_df.empty:
        return False
    min_time = pd.Timestamp(sim_df["datetime"].min()).normalize()
    max_time = pd.Timestamp(sim_df["datetime"].max()).normalize()
    return min_time <= TARGET_START and max_time >= TARGET_END


def has_numeric_param(nml_text: str, name: str) -> bool:
    pattern = re.compile(rf"(^\s*{re.escape(name)}\s*=\s*)({NUMBER_RE})", flags=re.MULTILINE)
    return pattern.search(nml_text) is not None


def read_numeric_param(nml_text: str, name: str) -> float:
    pattern = re.compile(rf"(^\s*{re.escape(name)}\s*=\s*)({NUMBER_RE})", flags=re.MULTILINE)
    match = pattern.search(nml_text)
    if not match:
        return PARAM_SPECS[name]["default"]
    return float(match.group(2).replace("d", "e").replace("D", "E"))


def set_numeric_param(nml_text: str, name: str, value: float) -> str:
    pattern = re.compile(rf"(^\s*{re.escape(name)}\s*=\s*)({NUMBER_RE})", flags=re.MULTILINE)
    formatted = PARAM_SPECS[name]["fmt"].format(value)
    updated_text, count = pattern.subn(lambda match: f"{match.group(1)}{formatted}", nml_text, count=1)
    if count == 0:
        return nml_text
    return updated_text


def clipped(name: str, value: float) -> float:
    low, high = PARAM_SPECS[name]["bounds"]
    value = min(high, max(low, value))
    return float(PARAM_SPECS[name]["fmt"].format(value))


def build_nml_text(base_text: str, params: dict[str, float]) -> str:
    updated = base_text
    for name, value in params.items():
        updated = set_numeric_param(updated, name, value)
    return updated.rstrip() + "\n"


def run_glm() -> subprocess.CompletedProcess[str]:
    OUTPUT_NC.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT_NC.exists():
        OUTPUT_NC.unlink()
    cmd = [str(GLM_BIN)] if GLM_BIN.is_absolute() else [GLM_BIN.name]
    return subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=1800,
        check=False,
    )


def evaluate_candidate(
    base_text: str,
    obs_df: pd.DataFrame,
    params: dict[str, float],
    cache: dict[tuple[tuple[str, float], ...], EvalResult],
) -> EvalResult:
    key = tuple(sorted((name, float(value)) for name, value in params.items()))
    if key in cache:
        return cache[key]

    NML_PATH.write_text(build_nml_text(base_text, params), encoding="utf-8")
    result = run_glm()
    if result.returncode != 0 or not OUTPUT_NC.exists():
        evaluation = EvalResult(dict(params), math.inf, result.returncode, result.stdout, result.stderr)
        cache[key] = evaluation
        return evaluation

    sim_df = read_glm_output(OUTPUT_NC)
    rmse = calculate_rmse(sim_df, obs_df)
    evaluation = EvalResult(dict(params), rmse, result.returncode, result.stdout, result.stderr)
    cache[key] = evaluation
    return evaluation


def search_parameters(base_text: str, obs_df: pd.DataFrame, available_params: list[str]) -> EvalResult:
    initial = {name: read_numeric_param(base_text, name) for name in available_params}
    cache: dict[tuple[tuple[str, float], ...], EvalResult] = {}
    best = evaluate_candidate(base_text, obs_df, initial, cache)

    primary_params = [name for name in ("Kw", "wind_factor", "lw_factor") if name in available_params]
    primary_choices: list[list[float]] = []
    for name in primary_params:
        step = PARAM_SPECS[name]["coarse"]
        base_value = initial[name]
        choices = [
            clipped(name, base_value - step),
            clipped(name, base_value),
            clipped(name, base_value + step),
        ]
        primary_choices.append(sorted(set(choices)))

    if primary_params:
        def visit_primary(depth: int, current: dict[str, float]) -> None:
            nonlocal best
            if depth == len(primary_params):
                result = evaluate_candidate(base_text, obs_df, current, cache)
                if result.rmse < best.rmse:
                    best = result
                return
            name = primary_params[depth]
            for choice in primary_choices[depth]:
                next_params = dict(current)
                next_params[name] = choice
                visit_primary(depth + 1, next_params)

        visit_primary(0, dict(initial))
        if best.rmse < TARGET_RMSE:
            return best

    for name in ("coef_mix_hyp", "ch", "Kw", "wind_factor", "lw_factor"):
        if name not in available_params:
            continue
        for step_name in ("coarse", "fine"):
            step = PARAM_SPECS[name][step_name]
            for delta in (-step, step):
                candidate = dict(best.params)
                candidate[name] = clipped(name, candidate[name] + delta)
                result = evaluate_candidate(base_text, obs_df, candidate, cache)
                if result.rmse < best.rmse:
                    best = result
                    if best.rmse < TARGET_RMSE:
                        return best

    joint_offsets = {
        "Kw": (0.02, -0.02),
        "wind_factor": (0.04, -0.04),
        "lw_factor": (-0.02, 0.02),
        "coef_mix_hyp": (-0.04, 0.04),
        "ch": (-0.0001, 0.0001),
    }
    for direction in (0, 1):
        candidate = dict(best.params)
        changed = False
        for name in available_params:
            if name not in joint_offsets:
                continue
            candidate[name] = clipped(name, candidate[name] + joint_offsets[name][direction])
            changed = True
        if changed:
            result = evaluate_candidate(base_text, obs_df, candidate, cache)
            if result.rmse < best.rmse:
                best = result
                if best.rmse < TARGET_RMSE:
                    return best

    return best


def main() -> int:
    statuses = base_statuses()
    try:
        verify_bootstrap_gate(statuses)
    except Exception as exc:
        statuses["glm_config_status"] = "blocked_by_bootstrap_gate"
        statuses["simulation_status"] = "not_run"
        statuses["output_nc_status"] = "not_checked"
        statuses["rmse_status"] = "not_checked"
        write_completion(statuses)
        print(str(exc), file=sys.stderr)
        return 1

    try:
        base_text = NML_PATH.read_text(encoding="utf-8").rstrip() + "\n"
        obs_df = read_observations()
        available_params = [name for name in PARAM_ORDER if has_numeric_param(base_text, name)]
        if not available_params:
            raise RuntimeError("No supported GLM calibration parameters were found in /root/glm3.nml")

        best = search_parameters(base_text, obs_df, available_params)
        NML_PATH.write_text(build_nml_text(base_text, best.params), encoding="utf-8")
        final_run = run_glm()

        statuses["glm_config_status"] = "finalized:/root/glm3.nml"
        if final_run.returncode != 0:
            statuses["simulation_status"] = f"failed:exit_{final_run.returncode}"
            statuses["output_nc_status"] = "missing:/root/output/output.nc"
            statuses["rmse_status"] = "not_evaluated"
            write_completion(statuses)
            print(final_run.stderr or final_run.stdout, file=sys.stderr)
            return 1

        statuses["simulation_status"] = "passed:exit_0"
        if not OUTPUT_NC.exists():
            statuses["output_nc_status"] = "missing:/root/output/output.nc"
            statuses["rmse_status"] = "not_evaluated"
            write_completion(statuses)
            print("GLM finished without /root/output/output.nc", file=sys.stderr)
            return 1

        final_sim = read_glm_output(OUTPUT_NC)
        if not covers_target_window(final_sim):
            statuses["output_nc_status"] = "wrong_window:/root/output/output.nc"
        else:
            statuses["output_nc_status"] = "verified:/root/output/output.nc"

        final_rmse = calculate_rmse(final_sim, obs_df)
        if statuses["output_nc_status"].startswith("verified") and math.isfinite(final_rmse) and final_rmse < TARGET_RMSE:
            statuses["rmse_status"] = f"pass:{final_rmse:.4f}"
            write_completion(statuses)
            print(json.dumps({"best_params": best.params, "rmse": round(final_rmse, 4)}, indent=2))
            return 0

        if math.isfinite(final_rmse):
            statuses["rmse_status"] = f"fail:{final_rmse:.4f}"
        else:
            statuses["rmse_status"] = "fail:no_matches"
        write_completion(statuses)
        print(
            json.dumps(
                {
                    "best_params": best.params,
                    "rmse": None if not math.isfinite(final_rmse) else round(final_rmse, 4),
                    "output_nc_status": statuses["output_nc_status"],
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1
    except Exception as exc:
        if statuses["glm_config_status"] == "not_checked":
            statuses["glm_config_status"] = "failed"
        if statuses["simulation_status"] == "not_checked":
            statuses["simulation_status"] = "failed"
        if statuses["rmse_status"] == "not_checked":
            statuses["rmse_status"] = "failed"
        write_completion(statuses)
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
