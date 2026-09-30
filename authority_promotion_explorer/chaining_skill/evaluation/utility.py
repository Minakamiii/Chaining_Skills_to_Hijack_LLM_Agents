"""Compute a task-neutral, equal-weight utility from retained CTRF reports.

This is intentionally a sidecar to SkillsBench's original verifier reward.
It never changes a task's verifier, reward.txt, or native baseline result.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable


SCHEMA_VERSION = 1
NATIVE_RESULT_FILENAME = "native_baseline_result.json"
DEFAULT_OUTPUT_NAME = "uniform_check_utility.json"
DEFAULT_SUMMARY_NAME = "uniform_check_utility_summary.json"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _numeric(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _trial_result_path(trial_root: Path) -> Path:
    return trial_root / "result.json"


def _raw_verifier_utility(trial_result: dict[str, Any]) -> float | None:
    verifier = trial_result.get("verifier_result")
    rewards = verifier.get("rewards") if isinstance(verifier, dict) else None
    return _numeric(rewards.get("reward")) if isinstance(rewards, dict) else None


def _trial_exception(trial_result: dict[str, Any]) -> dict[str, str] | None:
    exception = trial_result.get("exception_info")
    if not isinstance(exception, dict):
        return None
    return {
        "type": str(exception.get("exception_type", "") or ""),
        "message": str(exception.get("exception_message", "") or ""),
    }


def _ctrf_reports(verifier_root: Path) -> list[Path]:
    return sorted(path for path in verifier_root.glob("ctrf*.json") if path.is_file())


def _check_record(*, report_path: Path, test: dict[str, Any], index: int, count: int) -> dict[str, Any]:
    status = str(test.get("status", "unknown") or "unknown").casefold()
    name = str(test.get("name", "") or "")
    file_path = str(test.get("file_path", "") or "")
    weight = 1.0 / count
    passed = status == "passed"
    return {
        "id": f"{report_path.name}:{index}:{name or file_path or 'unnamed'}",
        "report": report_path.name,
        "name": name,
        "file_path": file_path,
        "status": status,
        "passed": passed,
        "weight": weight,
        "earned": weight if passed else 0.0,
    }


def analyze_trial(trial_root: Path) -> dict[str, Any]:
    """Return a uniform-check utility sidecar for one retained Harbor trial."""

    trial_root = trial_root.resolve()
    trial_result = _read_json(_trial_result_path(trial_root))
    verifier_root = trial_root / "verifier"
    report_errors: list[str] = []
    pending_checks: list[tuple[Path, dict[str, Any]]] = []
    for report_path in _ctrf_reports(verifier_root):
        report = _read_json(report_path)
        results = report.get("results")
        tests = results.get("tests") if isinstance(results, dict) else None
        if not isinstance(tests, list) or not tests:
            report_errors.append(f"no test entries in {report_path.name}")
            continue
        for test in tests:
            if isinstance(test, dict):
                pending_checks.append((report_path, test))
            else:
                report_errors.append(f"non-object test entry in {report_path.name}")

    exception = _trial_exception(trial_result)
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "analysis_kind": "skillsbench_uniform_check_utility",
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "trial_root": str(trial_root),
        "trial_result_path": str(_trial_result_path(trial_root)),
        "raw_verifier_utility": _raw_verifier_utility(trial_result),
        "trial_exception": exception,
        "report_paths": [str(path) for path in _ctrf_reports(verifier_root)],
        "report_errors": report_errors,
    }
    if not pending_checks:
        reason = "no_retained_itemized_ctrf_report"
        if exception is not None:
            reason = "trial_ended_before_itemized_verifier_report"
        payload.update(
            {
                "status": "unavailable",
                "reason": reason,
                "check_count": 0,
                "passed_check_count": 0,
                "failed_or_not_passed_check_count": 0,
                "uniform_check_utility": None,
                "checks": [],
            }
        )
        return payload

    count = len(pending_checks)
    checks = [
        _check_record(report_path=report_path, test=test, index=index, count=count)
        for index, (report_path, test) in enumerate(pending_checks, start=1)
    ]
    passed_count = sum(1 for check in checks if check["passed"])
    status_counts = dict(sorted(Counter(str(check["status"]) for check in checks).items()))
    payload.update(
        {
            "status": "scored",
            "reason": "",
            "check_count": count,
            "passed_check_count": passed_count,
            "failed_or_not_passed_check_count": count - passed_count,
            "uniform_check_utility": passed_count / count,
            "status_counts": status_counts,
            "checks": checks,
        }
    )
    return payload


def latest_trial_root(run_root: Path, *, iteration: int = 0) -> Path | None:
    trials_root = run_root / "iterations" / f"iter-{iteration}" / "trials"
    if not trials_root.is_dir():
        return None
    candidates = [path for path in trials_root.iterdir() if path.is_dir() and _trial_result_path(path).is_file()]
    return max(candidates, key=lambda path: _trial_result_path(path).stat().st_mtime_ns) if candidates else None


def analyze_native_baseline_run(run_root: Path, *, iteration: int = 0) -> dict[str, Any]:
    run_root = run_root.resolve()
    native_result = _read_json(run_root / NATIVE_RESULT_FILENAME)
    trial_root = latest_trial_root(run_root, iteration=iteration)
    if trial_root is None:
        analysis: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "analysis_kind": "skillsbench_uniform_check_utility",
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "trial_root": "",
            "trial_result_path": "",
            "raw_verifier_utility": _numeric(native_result.get("utility")),
            "trial_exception": None,
            "report_paths": [],
            "report_errors": [],
            "status": "unavailable",
            "reason": "no_retained_trial_result",
            "check_count": 0,
            "passed_check_count": 0,
            "failed_or_not_passed_check_count": 0,
            "uniform_check_utility": None,
            "checks": [],
        }
    else:
        analysis = analyze_trial(trial_root)
    analysis.update(
        {
            "run_root": str(run_root),
            "iteration": iteration,
            "task_id": str(native_result.get("task_id", "") or ""),
            "provider_label": str(native_result.get("provider_label", "") or ""),
            "model": str(native_result.get("model", "") or ""),
            "native_baseline_result_path": str(run_root / NATIVE_RESULT_FILENAME),
        }
    )
    return analysis


def discover_native_baseline_runs(runs_root: Path) -> list[Path]:
    runs_root = runs_root.resolve()
    if (runs_root / NATIVE_RESULT_FILENAME).is_file():
        return [runs_root]
    if not runs_root.is_dir():
        return []
    return sorted(path for path in runs_root.iterdir() if (path / NATIVE_RESULT_FILENAME).is_file())


def summarize(analyses: Iterable[dict[str, Any]], *, runs_root: Path, iteration: int) -> dict[str, Any]:
    records = list(analyses)
    scored = [
        float(item["uniform_check_utility"])
        for item in records
        if item.get("status") == "scored" and isinstance(item.get("uniform_check_utility"), (int, float))
    ]
    all_checks = sum(int(item.get("check_count", 0)) for item in records)
    all_passed = sum(int(item.get("passed_check_count", 0)) for item in records)
    return {
        "schema_version": SCHEMA_VERSION,
        "analysis_kind": "skillsbench_uniform_check_utility_summary",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runs_root": str(runs_root.resolve()),
        "iteration": iteration,
        "run_count": len(records),
        "scored_run_count": len(scored),
        "unavailable_run_count": len(records) - len(scored),
        "observed_check_count": all_checks,
        "passed_check_count": all_passed,
        "equal_weight_aggregate": (all_passed / all_checks) if all_checks else None,
        "mean_per_run_uniform_check_utility": mean(scored) if scored else None,
        "median_per_run_uniform_check_utility": median(scored) if scored else None,
        "runs": records,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
