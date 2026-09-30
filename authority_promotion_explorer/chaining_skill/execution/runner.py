from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence
import json
import os
import re
import shutil
import subprocess
import sys

from ..generation.prompts import write_generator_prompt_pack
from .handoff import (
    EXTERNAL_SCRIPT_FETCH_LISTENER_PORT,
    external_script_fetch_service_url,
    external_script_fetch_visible_aliases,
    objective_family_supports_external_script_fetch_runtime,
    objective_family_supports_network_handoff,
    task_handoff_service_url,
    task_visible_handoff_aliases,
)
from ..models import CandidateManifest
from ..defense_modes import DEFENSE_MODE_ENFORCE, DEFENSE_MODE_SHADOW
from .failures import cleanup_timed_out_compose_containers
from ..objective_families import DEFAULT_OBJECTIVE_FAMILY
from ..generation.assets import prompt_asset_path
from .overlay import build_task_overlay


_AGENT_IMPORT_PATH = "agent_sec_lab.skillsbench_chain.execution.harbor_agent:DeepSeekCodex"
_STRICT_SKILL_ADOPTION_MODELS = frozenset(
    {
        "grok-4.5",
        "claude-sonnet-5",
        "deepseek-v3.2",
        "deepseek-v4-flash",
        "gemini-3.5-flash",
        "kimi-k2.6",
    }
)
_MAX_AGENT_LOG_TAIL_CHARS = 8000
_BASELINE_ITERATION = 0
_HARBOR_CLI_MODULE = "agent_sec_lab.skillsbench_chain.execution.harbor_cli"


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-") or "run"


def _execution_prompt_template_path(model_name: str) -> Path:
    """Require the strict skill-adoption protocol for supported replay models."""
    if model_name.strip().casefold() in _STRICT_SKILL_ADOPTION_MODELS:
        return prompt_asset_path("execution_skill_adoption")
    return prompt_asset_path("execution_safety")


@dataclass(slots=True)
class SkillsBenchChainRun:
    run_id: str
    task_id: str
    project_root: str
    skillsbench_root: str
    run_root: str
    seed_skill_names: list[str]
    objective_family: str = DEFAULT_OBJECTIVE_FAMILY
    experiment_condition: str = ""
    experiment_id: str = ""
    neutral_preflight_id: str = ""
    defense_condition: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write_json(self) -> None:
        path = Path(self.run_root) / "run.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    @classmethod
    def read_json(cls, path: Path) -> "SkillsBenchChainRun":
        loaded = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            run_id=str(loaded["run_id"]),
            task_id=str(loaded["task_id"]),
            objective_family=str(loaded.get("objective_family", DEFAULT_OBJECTIVE_FAMILY)),
            experiment_condition=str(loaded.get("experiment_condition", "") or ""),
            experiment_id=str(loaded.get("experiment_id", "") or ""),
            neutral_preflight_id=str(loaded.get("neutral_preflight_id", "") or ""),
            defense_condition=str(loaded.get("defense_condition", "") or ""),
            project_root=str(loaded["project_root"]),
            skillsbench_root=str(loaded["skillsbench_root"]),
            run_root=str(loaded["run_root"]),
            seed_skill_names=[str(item) for item in loaded.get("seed_skill_names", [])],
        )


def init_skillsbench_chain_run(
    *,
    project_root: Path,
    skillsbench_root: Path,
    runs_root: Path,
    task_id: str,
    seed_skill_names: list[str],
    diagnostic_history: list[str],
    objective_family: str | None = None,
    experiment_condition: str = "",
    experiment_id: str = "",
    neutral_preflight_id: str = "",
    defense_condition: str = "",
) -> SkillsBenchChainRun:
    if experiment_condition.strip():
        raise ValueError("Ablation generation is not included in this release")
    normalized_experiment_condition = ""
    normalized_defense_condition = defense_condition.strip().casefold()
    defense_aliases = {"": "", "shadow": DEFENSE_MODE_SHADOW, "no_defense_shadow_tracking": DEFENSE_MODE_SHADOW, "enforce": DEFENSE_MODE_ENFORCE, "global_skill_artifact_distrust": DEFENSE_MODE_ENFORCE}
    if normalized_defense_condition not in defense_aliases:
        raise ValueError("unknown defense condition; expected empty, no_defense_shadow_tracking, or global_skill_artifact_distrust")
    normalized_defense_condition = defense_aliases[normalized_defense_condition]
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + _safe_name(task_id)
    run_root = runs_root / run_id
    source_task = skillsbench_root / "tasks" / task_id
    run = SkillsBenchChainRun(
        run_id=run_id,
        task_id=task_id,
        objective_family="",
        project_root=str(project_root.resolve()),
        skillsbench_root=str(skillsbench_root.resolve()),
        run_root=str(run_root.resolve()),
        seed_skill_names=list(seed_skill_names),
        experiment_condition=normalized_experiment_condition,
        experiment_id=experiment_id,
        neutral_preflight_id=neutral_preflight_id,
        defense_condition=normalized_defense_condition,
    )
    write_generator_prompt_pack(
        run_root=run_root,
        run_id=run_id,
        iteration=1,
        task_id=task_id,
        source_task_path=source_task,
        seed_skill_names=seed_skill_names,
        diagnostic_history=diagnostic_history,
        objective_family=objective_family,
        experiment_condition=normalized_experiment_condition,
        experiment_id=experiment_id,
        neutral_preflight_id=neutral_preflight_id,
    )
    manifest = CandidateManifest.read_json(run_root / "candidates" / "iter-1" / "candidate_manifest.json")
    run.objective_family = manifest.objective_family
    run.experiment_condition = manifest.experiment_condition
    run.write_json()
    return run


def build_harbor_trial_command(
    *,
    skillsbench_root: Path,
    overlay_task_path: Path,
    trials_dir: Path,
    provider_config_path: Path,
    model_name: str,
    agent_timeout_seconds: int | None = 1200,
    defense_condition: str = "",
    defense_skill_names: Sequence[str] = (),
) -> list[str]:
    python_bin = skillsbench_root / ".venv" / "bin" / "python"
    executable = str(python_bin) if python_bin.exists() else sys.executable
    prompt_template_path = _execution_prompt_template_path(model_name)
    command = [
        executable,
        "-m",
        _HARBOR_CLI_MODULE,
        "trial",
        "start",
        "-p",
        str(overlay_task_path),
        "--trials-dir",
        str(trials_dir.resolve()),
        "--agent-import-path",
        _AGENT_IMPORT_PATH,
        "-m",
        model_name,
        "--agent-kwarg",
        f"provider_config_path={provider_config_path}",
        "--agent-kwarg",
        f"prompt_template_path={prompt_template_path}",
    ]
    if agent_timeout_seconds is not None:
        command.extend(["--agent-timeout", str(agent_timeout_seconds)])
    normalized_defense = defense_condition.strip().casefold()
    if normalized_defense in {DEFENSE_MODE_SHADOW, DEFENSE_MODE_ENFORCE}:
        command.extend(["--agent-kwarg", f"global_skill_artifact_distrust_mode={normalized_defense}"])
        names = list(dict.fromkeys(name.strip() for name in defense_skill_names if name.strip()))
        command.extend(["--agent-kwarg", f"global_skill_artifact_distrust_skill_names_json={json.dumps(names, separators=(chr(44), chr(58)))}"])
    elif normalized_defense:
        raise ValueError(f"unknown defense condition: {defense_condition!r}")
    return command


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    loaded = json.loads(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def _latest_trial_result_payload(trials_dir: Path) -> tuple[Path | None, dict[str, Any]]:
    if not trials_dir.exists():
        return None, {}

    result_paths = [path / "result.json" for path in trials_dir.iterdir() if path.is_dir() and (path / "result.json").exists()]
    if not result_paths:
        return None, {}

    latest = max(result_paths, key=lambda path: path.stat().st_mtime_ns)
    return latest, _read_json(latest)


def _read_text_tail(path: Path, *, max_chars: int = _MAX_AGENT_LOG_TAIL_CHARS) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def _cleanup_timed_out_overlay_containers(overlay_task_path: Path) -> dict[str, Any]:
    """Backward-compatible facade; recovery policy lives in execution.failures."""
    return cleanup_timed_out_compose_containers(overlay_task_path, runner=subprocess.run)


def run_iteration(
    *,
    run: SkillsBenchChainRun,
    iteration: int,
    provider_config_path: Path,
    model_name: str,
    generated_skill_names: list[str],
    timeout_seconds: int = 3600,
    agent_timeout_seconds: int | None = 1200,
) -> dict[str, Any]:
    run_root = Path(run.run_root)
    iteration_root = run_root / "iterations" / f"iter-{iteration}"
    iteration_root.mkdir(parents=True, exist_ok=True)
    candidate_path = run_root / "candidates" / f"iter-{iteration}" / "candidate_manifest.json"
    candidate = CandidateManifest.read_json(candidate_path)
    generated_names = generated_skill_names if generated_skill_names else candidate.generated_skill_names
    handoff_capture_dir = iteration_root / "handoff_capture"
    uses_handoff_loopback = objective_family_supports_network_handoff(candidate.objective_family)
    uses_external_script_fetch_runtime = objective_family_supports_external_script_fetch_runtime(
        candidate.objective_family
    )
    if uses_handoff_loopback or uses_external_script_fetch_runtime:
        handoff_capture_dir.mkdir(parents=True, exist_ok=True)
    trials_dir = iteration_root / "trials"
    mounted_seed_skill_names = list(run.seed_skill_names) if iteration == _BASELINE_ITERATION else []
    if uses_external_script_fetch_runtime:
        handoff_service_url = external_script_fetch_service_url(run.task_id)
        handoff_service_aliases = external_script_fetch_visible_aliases(run.task_id)
        # Optional experiment knob: append extra public-style hostnames that resolve
        # to the same internal listener (compose network aliases / extra_hosts), so
        # the URL the model sees can look like an external endpoint while the
        # traffic stays on the private network. Comma-separated, default empty.
        extra_aliases = os.environ.get("SKILLSBENCH_EXTRA_ESF_ALIASES", "")
        if extra_aliases:
            handoff_service_aliases = list(handoff_service_aliases) + [
                a.strip() for a in extra_aliases.split(",") if a.strip()
            ]
        handoff_runtime_kind = "script_acquisition"
        handoff_listener_port = EXTERNAL_SCRIPT_FETCH_LISTENER_PORT
    elif uses_handoff_loopback:
        handoff_service_url = task_handoff_service_url(run.task_id)
        handoff_service_aliases = task_visible_handoff_aliases(run.task_id)
        handoff_runtime_kind = "handoff_loopback"
        handoff_listener_port = None
    else:
        handoff_service_url = None
        handoff_service_aliases = None
        handoff_runtime_kind = "handoff_loopback"
        handoff_listener_port = None
    overlay_manifest = build_task_overlay(
        run_id=run.run_id,
        iteration=iteration,
        task_id=run.task_id,
        source_task_path=Path(run.skillsbench_root) / "tasks" / run.task_id,
        overlay_root=run_root / "overlays" / f"iter-{iteration}",
        seed_skill_names=mounted_seed_skill_names,
        candidate_skills_root=run_root / "candidates" / f"iter-{iteration}" / "skills",
        generated_skill_names=generated_names,
        forbidden_skill_roots=[Path(run.project_root) / ".agents" / "skills"],
        native_skill_dependencies=candidate.native_skill_dependencies,
        native_skill_extensions=candidate.native_skill_extensions,
        handoff_service_url=handoff_service_url,
        handoff_service_aliases=handoff_service_aliases,
        handoff_runtime_kind=handoff_runtime_kind,
        handoff_listener_port=handoff_listener_port,
        handoff_capture_dir=handoff_capture_dir if handoff_service_url else None,
        attach_handoff_note=os.environ.get("SKILLSBENCH_SUPPRESS_HANDOFF_NOTE", "").strip().lower()
        not in {"1", "true", "yes", "on"},
    )
    shutil.copy2(candidate_path, iteration_root / "candidate_manifest.json")
    shutil.copy2(Path(overlay_manifest.overlay_task_path) / "overlay_manifest.json", iteration_root / "overlay_manifest.json")

    defense_condition = run.defense_condition or os.environ.get("SKILLSBENCH_DEFENSE_CONDITION", "")
    # The policy must know every installed package, including a task-native
    # skill retained solely because the Dockerfile needs it at build time.
    # Restricting this to generated/seed names made valid lease requests for
    # native packages look like attempts to name an uninstalled Skill.
    final_mounted_skill_names = getattr(overlay_manifest, "final_mounted_skill_names", None)
    defense_skill_names = list(dict.fromkeys(final_mounted_skill_names or [*mounted_seed_skill_names, *generated_names]))
    command = build_harbor_trial_command(
        skillsbench_root=Path(run.skillsbench_root),
        overlay_task_path=Path(overlay_manifest.overlay_task_path),
        trials_dir=trials_dir,
        provider_config_path=provider_config_path,
        model_name=model_name,
        agent_timeout_seconds=agent_timeout_seconds,
        defense_condition=defense_condition,
        defense_skill_names=defense_skill_names,
    )
    env = os.environ.copy()
    project_path = run.project_root
    env["PYTHONPATH"] = project_path + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    try:
        completed = subprocess.run(
            command,
            cwd=Path(run.skillsbench_root),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        timeout_cleanup = _cleanup_timed_out_overlay_containers(Path(overlay_manifest.overlay_task_path))
        (iteration_root / "timeout-container-cleanup.json").write_text(
            json.dumps(
                {
                    "event": "outer_harbor_timeout",
                    "recorded_at": datetime.now().isoformat(),
                    "timeout_seconds": timeout_seconds,
                    "container_cleanup": timeout_cleanup,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        raise
    trial_result_path, trial_result = _latest_trial_result_payload(trials_dir)
    trial_exception_info = trial_result.get("exception_info")
    agent_log_tail = ""
    if trial_result_path is not None:
        agent_log_tail = _read_text_tail(trial_result_path.parent / "agent" / "codex.txt")
    effective_returncode = completed.returncode
    effective_stderr = completed.stderr
    if completed.returncode == 0 and isinstance(trial_exception_info, dict):
        effective_returncode = 1
        effective_stderr = str(trial_exception_info.get("exception_message", "")).strip() or effective_stderr
    result = {
        "run_id": run.run_id,
        "iteration": iteration,
        "task_id": run.task_id,
        "defense_condition": defense_condition,
        "defense_skill_names": defense_skill_names,
        "command": command,
        "harbor_returncode": completed.returncode,
        "returncode": effective_returncode,
        "stdout": completed.stdout,
        "stderr": effective_stderr,
        "overlay_manifest_path": str(Path(overlay_manifest.overlay_task_path) / "overlay_manifest.json"),
        "trial_result_path": str(trial_result_path) if trial_result_path is not None else "",
        "trial_exception_info": trial_exception_info if isinstance(trial_exception_info, dict) else None,
        "agent_log_tail": agent_log_tail,
        "trial_phase": {
            "environment_setup": bool(trial_result.get("environment_setup")),
            "agent_setup": bool(trial_result.get("agent_setup")),
            "agent_execution": bool(trial_result.get("agent_execution")),
            "verifier": bool(trial_result.get("verifier")),
        },
    }
    (iteration_root / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def load_run(run_root: Path) -> SkillsBenchChainRun:
    return SkillsBenchChainRun.read_json(run_root / "run.json")
