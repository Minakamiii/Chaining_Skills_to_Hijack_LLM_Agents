#!/usr/bin/env python3
"""Replay one preserved reference candidate with a caller-selected model.

The script is intentionally data-free: it reads a candidate manifest and its
skills from ``docs/references``, writes a new
run below ``runs/``, and never requires a private historical trial directory.
Use ``--list`` to discover candidate manifests before choosing one.

Examples:
  python scripts/replay_reference_candidate.py --list
  python scripts/replay_reference_candidate.py \
    --candidate-manifest docs/references/external-transfer/c/<task>/candidate_manifest.json \
    --provider-config configs/providers/deepseek-v4-flash.toml --model deepseek-v4-flash --execute
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import sys


REPO_ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "pyproject.toml").is_file())
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_sec_lab.skillsbench_chain.execution_harness import SkillsBenchChainRun, run_iteration  # noqa: E402
from agent_sec_lab.skillsbench_chain.models import CandidateManifest  # noqa: E402
from agent_sec_lab.skillsbench_chain.trace_evaluator import evaluate_iteration_trace  # noqa: E402
from agent_sec_lab.skillsbench_chain.execution.native_skills import extension_directory  # noqa: E402


def _default_skillsbench_root() -> Path | None:
    configured = os.environ.get("SKILLSBENCH_ROOT", "").strip()
    if configured:
        return Path(configured)
    for ancestor in (REPO_ROOT, *REPO_ROOT.parents):
        candidate = ancestor / "skillsbench"
        if (candidate / "tasks").is_dir():
            return candidate
    return None


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-root",
        type=Path,
        default=REPO_ROOT / "docs" / "references",
        help="Tree searched by --list (default: docs/references).",
    )
    parser.add_argument(
        "--candidate-manifest",
        type=Path,
        help="Exact candidate_manifest.json to replay. Required unless --list is used.",
    )
    parser.add_argument("--list", action="store_true", help="List candidate manifests below --source-root and exit.")
    parser.add_argument("--provider-config", type=Path, help="Provider TOML used by the execution harness.")
    parser.add_argument("--model", help="Model name passed to the execution harness.")
    parser.add_argument(
        "--skillsbench-root",
        type=Path,
        default=_default_skillsbench_root(),
        help="SkillsBench checkout; defaults to $SKILLSBENCH_ROOT or a sibling checkout.",
    )
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=REPO_ROOT / "runs" / "reference-replays",
        help="Destination for new replay outputs.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually launch the selected candidate. Without this flag the script only validates and prints the plan.",
    )
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--agent-timeout", type=int, default=1200)
    return parser.parse_args()


def _list_candidates(root: Path) -> int:
    if not root.is_dir():
        raise FileNotFoundError(f"Reference root does not exist: {root}")
    for manifest in sorted(root.rglob("candidate_manifest.json")):
        print(manifest.relative_to(REPO_ROOT) if manifest.is_relative_to(REPO_ROOT) else manifest)
    return 0


def _validate_source(manifest_path: Path) -> CandidateManifest:
    if manifest_path.name != "candidate_manifest.json":
        raise ValueError("--candidate-manifest must name candidate_manifest.json")
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    candidate = CandidateManifest.read_json(manifest_path)
    if not candidate.generated_skill_names:
        raise ValueError("Candidate contains no generated skills or native skill extensions")
    skills_root = manifest_path.parent / "skills"
    missing = []
    for name in candidate.generated_skill_names:
        if name in candidate.native_skill_extensions:
            extension_directory(manifest_path.parent, candidate.native_skill_extensions[name])
        elif not (skills_root / name / "SKILL.md").is_file():
            missing.append(name)
    if missing:
        raise FileNotFoundError(f"Candidate is missing rendered skills: {', '.join(missing)}")
    return candidate


def _new_run(candidate: CandidateManifest, *, skillsbench_root: Path, runs_root: Path) -> SkillsBenchChainRun:
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S") + f"-reference-{candidate.task_id}"
    run_root = (runs_root / run_id).resolve()
    run = SkillsBenchChainRun(
        run_id=run_id,
        task_id=candidate.task_id,
        objective_family=candidate.objective_family,
        project_root=str(REPO_ROOT),
        skillsbench_root=str(skillsbench_root.resolve()),
        run_root=str(run_root),
        seed_skill_names=[],
        experiment_condition=candidate.experiment_condition,
    )
    run.write_json()
    return run


def _stage_candidate(manifest_path: Path, run: SkillsBenchChainRun) -> None:
    destination = Path(run.run_root) / "candidates" / "iter-1"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"Replay destination already exists: {destination}")
    shutil.copytree(manifest_path.parent, destination)


def main() -> int:
    args = _parse_args()
    if args.list:
        return _list_candidates(args.source_root.resolve())
    if args.candidate_manifest is None:
        raise SystemExit("--candidate-manifest is required unless --list is used")

    manifest_path = args.candidate_manifest.resolve()
    candidate = _validate_source(manifest_path)
    plan = {
        "candidate_manifest": str(manifest_path),
        "task_id": candidate.task_id,
        "objective_family": candidate.objective_family,
        "generated_skill_names": candidate.generated_skill_names,
        "provider_config": str(args.provider_config.resolve()) if args.provider_config else "",
        "model": args.model or "",
        "skillsbench_root": str(args.skillsbench_root.resolve()) if args.skillsbench_root else "",
        "will_execute": bool(args.execute),
    }
    if not args.execute:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    if args.provider_config is None or not args.provider_config.is_file():
        raise SystemExit("--provider-config must name an existing TOML file when --execute is used")
    if not args.model:
        raise SystemExit("--model is required when --execute is used")
    if args.skillsbench_root is None or not (args.skillsbench_root / "tasks" / candidate.task_id).is_dir():
        raise SystemExit("--skillsbench-root must contain tasks/<candidate task_id>")

    run = _new_run(candidate, skillsbench_root=args.skillsbench_root, runs_root=args.runs_root)
    _stage_candidate(manifest_path, run)
    result = run_iteration(
        run=run,
        iteration=1,
        provider_config_path=args.provider_config.resolve(),
        model_name=args.model,
        generated_skill_names=list(candidate.generated_skill_names),
        timeout_seconds=args.timeout,
        agent_timeout_seconds=args.agent_timeout,
    )
    iteration_root = Path(run.run_root) / "iterations" / "iter-1"
    report = evaluate_iteration_trace(iteration_root)
    print(json.dumps({"run": run.to_dict(), "execution": result, "evaluation": report.to_dict()}, ensure_ascii=False, indent=2))
    return 0 if int(result["returncode"]) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
