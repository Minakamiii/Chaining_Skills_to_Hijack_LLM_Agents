from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
import json
import re
import time

from .chain_analysis import analyze_skill_chain
from .chain_policy import load_chain_patterns
from .claude_native import ClaudeNativeWorkspace, run_claude_native
from .codex_native import CodexNativeWorkspace, run_codex_native, run_codex_provider_native
from .config import ModelConfig
from .evaluator import evaluate_response
from .prompting import build_messages, build_system_prompt, build_user_prompt, load_base_system_prompt
from .project_snapshot import ProjectContext, build_project_snapshot
from .providers import chat_completion
from .skills import Skill, bundle_skills, discover_skills, select_skills
from .tool_agent import ToolAgentRuntime
from .workspace import load_workspace_attachments

_MAX_TOOL_AGENT_ROUNDS = 12


@dataclass(slots=True)
class CaseStage:
    id: str
    label: str = ""
    summary: str = ""
    skills: list[str] = field(default_factory=list)
    notes: str = ""
    produced_artifacts: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CaseStage":
        return cls(
            id=str(data.get("id") or data.get("label") or "stage"),
            label=str(data.get("label", "")),
            summary=str(data.get("summary", "")),
            skills=[str(item) for item in data.get("skills", [])],
            notes=str(data.get("notes", "")),
            produced_artifacts=[str(item) for item in data.get("produced_artifacts", [])],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "summary": self.summary,
            "skills": self.skills,
            "notes": self.notes,
            "produced_artifacts": self.produced_artifacts,
        }


@dataclass(slots=True)
class CaseArtifact:
    name: str
    content: str
    kind: str = ""
    source_stage: str = ""
    notes: str = ""
    sensitivity: str = ""
    language: str = "text"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CaseArtifact":
        return cls(
            name=str(data["name"]),
            content=str(data.get("content", "")),
            kind=str(data.get("kind", "")),
            source_stage=str(data.get("source_stage", "")),
            notes=str(data.get("notes", "")),
            sensitivity=str(data.get("sensitivity", "")),
            language=str(data.get("language", "text")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "content": self.content,
            "kind": self.kind,
            "source_stage": self.source_stage,
            "notes": self.notes,
            "sensitivity": self.sensitivity,
            "language": self.language,
        }


@dataclass(slots=True)
class ExperimentCase:
    id: str
    input: str
    skills: list[str] = field(default_factory=list)
    workspace_files: list[str] = field(default_factory=list)
    context: str = ""
    project_context: ProjectContext | None = None
    stages: list[CaseStage] = field(default_factory=list)
    artifacts: list[CaseArtifact] = field(default_factory=list)
    judge: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExperimentCase":
        return cls(
            id=str(data["id"]),
            input=str(data["input"]),
            skills=[str(item) for item in data.get("skills", [])],
            workspace_files=[str(item) for item in data.get("workspace_files", [])],
            context=str(data.get("context", "")),
            project_context=ProjectContext.from_dict(data["project_context"])
            if isinstance(data.get("project_context"), dict)
            else None,
            stages=[CaseStage.from_dict(item) for item in data.get("stages", [])],
            artifacts=[CaseArtifact.from_dict(item) for item in data.get("artifacts", [])],
            judge=dict(data.get("judge", {})),
            metadata=dict(data.get("metadata", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "input": self.input,
            "skills": self.skills,
            "workspace_files": self.workspace_files,
            "context": self.context,
            "project_context": self.project_context.to_dict() if self.project_context else None,
            "stages": [stage.to_dict() for stage in self.stages],
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "judge": self.judge,
            "metadata": self.metadata,
        }


def load_cases(path: Path) -> list[ExperimentCase]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []

    if path.suffix == ".jsonl":
        return [
            ExperimentCase.from_dict(json.loads(line))
            for line in text.splitlines()
            if line.strip()
        ]

    loaded = json.loads(text)
    if isinstance(loaded, list):
        return [ExperimentCase.from_dict(item) for item in loaded]
    return [ExperimentCase.from_dict(loaded)]


def find_case_by_id(cases: list[ExperimentCase], case_id: str) -> ExperimentCase:
    for case in cases:
        if case.id == case_id:
            return case
    available = ", ".join(case.id for case in cases)
    raise KeyError(f"Unknown case '{case_id}'. Available cases: {available}")


def discover_skill_registry(project_root: Path) -> dict[str, Skill]:
    return discover_skills(project_root / ".agents" / "skills")


def _merge_skill_names(preferred: list[str], fallback: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for name in preferred + fallback:
        if name in seen:
            continue
        merged.append(name)
        seen.add(name)
    return merged


def _case_stage_skill_names(stages: list[CaseStage]) -> list[str]:
    names: list[str] = []
    for stage in stages:
        names.extend(stage.skills)
    return names


def resolve_case_skill_names(case: ExperimentCase, extra_skills: list[str] | None = None) -> list[str]:
    stage_skill_names = _case_stage_skill_names(case.stages)
    return _merge_skill_names(extra_skills or [], case.skills + stage_skill_names)


def prepare_case(
    case: ExperimentCase,
    *,
    project_root: Path,
    skill_registry: dict[str, Skill],
    base_prompt_path: Path,
    extra_skills: list[str] | None = None,
    target_project_root: Path | None = None,
    skill_names_override: list[str] | None = None,
    bundle_selected_skills: bool = False,
    bundled_skill_name: str = "bundled-skill",
) -> dict[str, Any]:
    selected_skill_names = (
        _merge_skill_names([], skill_names_override)
        if skill_names_override is not None
        else resolve_case_skill_names(case, extra_skills)
    )
    selected_skills = select_skills(skill_registry, selected_skill_names)
    bundled_source_skill_names: list[str] = []
    if bundle_selected_skills and selected_skills:
        bundled_source_skill_names = [skill.name for skill in selected_skills]
        selected_skills = [bundle_skills(selected_skills, name=bundled_skill_name)]
        selected_skill_names = [selected_skills[0].name]
    attachments = load_workspace_attachments(project_root, case.workspace_files)
    context_parts = [case.context.strip()] if case.context.strip() else []
    project_snapshot_block: dict[str, Any] | None = None

    if case.project_context is not None:
        snapshot = build_project_snapshot(
            project_root,
            case.project_context,
            project_root_override=target_project_root,
        )
        attachments.extend(snapshot.attachments)
        context_parts.append(snapshot.render_summary())
        project_snapshot_block = snapshot.to_dict()

    chain_patterns = load_chain_patterns(project_root / "configs" / "chain_patterns.toml")
    chain_analysis = analyze_skill_chain(selected_skills, chain_patterns)

    base_prompt = load_base_system_prompt(base_prompt_path)
    system_prompt = build_system_prompt(base_prompt, selected_skills)
    user_prompt = build_user_prompt(
        case.input,
        attachments,
        context="\n\n".join(part for part in context_parts if part),
        stages=case.stages,
        artifacts=case.artifacts,
    )
    messages = build_messages(system_prompt, user_prompt)

    return {
        "base_prompt": base_prompt,
        "selected_skill_names": selected_skill_names,
        "selected_skills": selected_skills,
        "bundled_source_skill_names": bundled_source_skill_names,
        "attachments": attachments,
        "stages": case.stages,
        "artifacts": case.artifacts,
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "messages": messages,
        "chain_analysis": chain_analysis,
        "project_snapshot": project_snapshot_block,
    }


def _failure_evaluation(error_message: str) -> dict[str, Any]:
    return {
        "passed": False,
        "refusal_detected": False,
        "matched_forbidden": [],
        "matched_forbidden_regexes": [],
        "missing_required": [],
        "missing_required_regexes": [],
        "reasons": [f"Model execution failed: {error_message}"],
    }


def _run_prompt_case(
    *,
    model_config: ModelConfig,
    messages: list[dict[str, Any]],
    judge: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, Any] | None]:
    provider_response = chat_completion(model_config, messages)
    evaluation = evaluate_response(provider_response.text, judge)
    return (
        {
            "model": provider_response.model,
            "text": provider_response.text,
            "raw": provider_response.raw,
        },
        evaluation.to_dict(),
        messages,
        None,
    )


def _run_tool_agent_case(
    *,
    project_root: Path,
    prepared: dict[str, Any],
    model_config: ModelConfig,
    judge: dict[str, Any],
    max_rounds: int = _MAX_TOOL_AGENT_ROUNDS,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    runtime = ToolAgentRuntime(
        project_root=project_root,
        skills=prepared["selected_skills"],
        attachments=prepared["attachments"],
        artifacts=prepared["artifacts"],
    )
    system_prompt = prepared["system_prompt"] + "\n\n" + runtime.render_system_guidance()
    user_prompt = runtime.render_user_guidance() + "\n\n" + prepared["user_prompt"]
    messages = build_messages(system_prompt, user_prompt)

    for _ in range(max_rounds):
        provider_tools = runtime.provider_tools()
        provider_response = chat_completion(model_config, messages, tools=provider_tools)
        messages.append(provider_response.assistant_message())
        if provider_response.tool_calls:
            for tool_call in provider_response.tool_calls:
                messages.append(runtime.execute(tool_call))
            continue

        evaluation = evaluate_response(provider_response.text, judge)
        response = {
            "model": provider_response.model,
            "text": provider_response.text,
            "raw": provider_response.raw,
            "finish_reason": provider_response.finish_reason,
        }
        return response, evaluation.to_dict(), messages, runtime.summary()

    error_message = f"Tool agent exceeded max tool rounds ({max_rounds})"
    response = {
        "model": model_config.model,
        "text": "",
        "raw": None,
        "error": error_message,
    }
    return response, _failure_evaluation(error_message), messages, runtime.summary()


def _run_codex_native_case(
    *,
    case: ExperimentCase,
    prepared: dict[str, Any],
    model_config: ModelConfig,
    judge: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    response, native_summary, messages = run_codex_native(
        case_id=case.id,
        skills=prepared["selected_skills"],
        attachments=prepared["attachments"],
        artifacts=prepared["artifacts"],
        base_prompt=prepared["base_prompt"],
        user_prompt=prepared["user_prompt"],
        model_config=model_config,
    )
    if response.get("error"):
        evaluation_dict = _failure_evaluation(str(response["error"]))
    else:
        evaluation_dict = evaluate_response(response["text"], judge).to_dict()
    return response, evaluation_dict, messages, native_summary


def _run_codex_provider_native_case(
    *,
    case: ExperimentCase,
    prepared: dict[str, Any],
    model_config: ModelConfig,
    judge: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    response, native_summary, messages = run_codex_provider_native(
        case_id=case.id,
        skills=prepared["selected_skills"],
        attachments=prepared["attachments"],
        artifacts=prepared["artifacts"],
        base_prompt=prepared["base_prompt"],
        user_prompt=prepared["user_prompt"],
        model_config=model_config,
    )
    if response.get("error"):
        evaluation_dict = _failure_evaluation(str(response["error"]))
    else:
        evaluation_dict = evaluate_response(response["text"], judge).to_dict()
    return response, evaluation_dict, messages, native_summary


def _run_claude_native_case(
    *,
    case: ExperimentCase,
    prepared: dict[str, Any],
    model_config: ModelConfig,
    judge: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    response, native_summary, messages = run_claude_native(
        case_id=case.id,
        skills=prepared["selected_skills"],
        attachments=prepared["attachments"],
        artifacts=prepared["artifacts"],
        base_prompt=prepared["base_prompt"],
        user_prompt=prepared["user_prompt"],
        model_config=model_config,
    )
    if response.get("error"):
        evaluation_dict = _failure_evaluation(str(response["error"]))
    else:
        evaluation_dict = evaluate_response(response["text"], judge).to_dict()
    return response, evaluation_dict, messages, native_summary


def run_case(
    case: ExperimentCase,
    *,
    project_root: Path,
    skill_registry: dict[str, Skill],
    base_prompt_path: Path,
    model_config: ModelConfig,
    extra_skills: list[str] | None = None,
    dry_run: bool = False,
    target_project_root: Path | None = None,
    skill_names_override: list[str] | None = None,
    experiment_mode: str = "case",
    bundle_selected_skills: bool = False,
    bundled_skill_name: str = "bundled-skill",
    agent_mode: str = "prompt",
) -> dict[str, Any]:
    available_case_skills = resolve_case_skill_names(case, extra_skills)
    prepared = prepare_case(
        case,
        project_root=project_root,
        skill_registry=skill_registry,
        base_prompt_path=base_prompt_path,
        extra_skills=extra_skills,
        target_project_root=target_project_root,
        skill_names_override=skill_names_override,
        bundle_selected_skills=bundle_selected_skills,
        bundled_skill_name=bundled_skill_name,
    )

    response_block: dict[str, Any] | None
    evaluation_block: dict[str, Any] | None
    messages = prepared["messages"]
    system_prompt = prepared["system_prompt"]
    user_prompt = prepared["user_prompt"]
    tool_agent_block: dict[str, Any] | None = None
    codex_native_block: dict[str, Any] | None = None

    if dry_run:
        if agent_mode == "tools":
            runtime = ToolAgentRuntime(
                project_root=project_root,
                skills=prepared["selected_skills"],
                attachments=prepared["attachments"],
                artifacts=prepared["artifacts"],
            )
            system_prompt = prepared["system_prompt"] + "\n\n" + runtime.render_system_guidance()
            user_prompt = runtime.render_user_guidance() + "\n\n" + prepared["user_prompt"]
            messages = build_messages(system_prompt, user_prompt)
            tool_agent_block = runtime.summary()
        elif agent_mode in {"codex-native", "codex-provider-native"}:
            workspace = CodexNativeWorkspace.build(
                case_id=case.id,
                skills=prepared["selected_skills"],
                attachments=prepared["attachments"],
                artifacts=prepared["artifacts"],
                base_prompt=prepared["base_prompt"],
                user_prompt=prepared["user_prompt"],
            )
            system_prompt = workspace.agents_path.read_text(encoding="utf-8").strip()
            user_prompt = workspace.exec_prompt()
            messages = build_messages(system_prompt, user_prompt)
            codex_native_block = workspace.summary()
        elif agent_mode == "claude-native":
            workspace = ClaudeNativeWorkspace.build(
                case_id=case.id,
                skills=prepared["selected_skills"],
                attachments=prepared["attachments"],
                artifacts=prepared["artifacts"],
                base_prompt=prepared["base_prompt"],
                user_prompt=prepared["user_prompt"],
            )
            system_prompt = workspace.claude_md_path.read_text(encoding="utf-8").strip()
            user_prompt = workspace.exec_prompt()
            messages = build_messages(system_prompt, user_prompt)
            codex_native_block = workspace.summary()
        response_block = None
        evaluation_block = None
    else:
        try:
            if agent_mode == "tools":
                response_block, evaluation_block, messages, tool_agent_block = _run_tool_agent_case(
                    project_root=project_root,
                    prepared=prepared,
                    model_config=model_config,
                    judge=case.judge,
                )
                system_prompt = str(messages[0].get("content", "")) if messages else prepared["system_prompt"]
                user_prompt = str(messages[1].get("content", "")) if len(messages) > 1 else prepared["user_prompt"]
            elif agent_mode == "codex-native":
                response_block, evaluation_block, messages, codex_native_block = _run_codex_native_case(
                    case=case,
                    prepared=prepared,
                    model_config=model_config,
                    judge=case.judge,
                )
                system_prompt = str(messages[0].get("content", "")) if messages else prepared["base_prompt"]
                user_prompt = str(messages[1].get("content", "")) if len(messages) > 1 else prepared["user_prompt"]
            elif agent_mode == "codex-provider-native":
                response_block, evaluation_block, messages, codex_native_block = _run_codex_provider_native_case(
                    case=case,
                    prepared=prepared,
                    model_config=model_config,
                    judge=case.judge,
                )
                system_prompt = str(messages[0].get("content", "")) if messages else prepared["base_prompt"]
                user_prompt = str(messages[1].get("content", "")) if len(messages) > 1 else prepared["user_prompt"]
            elif agent_mode == "claude-native":
                response_block, evaluation_block, messages, codex_native_block = _run_claude_native_case(
                    case=case,
                    prepared=prepared,
                    model_config=model_config,
                    judge=case.judge,
                )
                system_prompt = str(messages[0].get("content", "")) if messages else prepared["base_prompt"]
                user_prompt = str(messages[1].get("content", "")) if len(messages) > 1 else prepared["user_prompt"]
            else:
                response_block, evaluation_block, messages, tool_agent_block = _run_prompt_case(
                    model_config=model_config,
                    messages=prepared["messages"],
                    judge=case.judge,
                )
        except Exception as exc:
            error_message = f"{type(exc).__name__}: {exc}"
            response_block = {
                "model": model_config.model,
                "text": "",
                "raw": None,
                "error": error_message,
            }
            evaluation_block = _failure_evaluation(error_message)

    return {
        "case_id": case.id,
        "case": case.to_dict(),
        "experiment_mode": experiment_mode,
        "agent_mode": agent_mode,
        "available_case_skills": available_case_skills,
        "skills": prepared["selected_skill_names"],
        "bundled_source_skills": prepared["bundled_source_skill_names"],
        "workspace_files": [attachment.rel_path for attachment in prepared["attachments"]],
        "stages": [stage.to_dict() for stage in prepared["stages"]],
        "artifacts": [artifact.to_dict() for artifact in prepared["artifacts"]],
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "messages": messages,
        "chain_analysis": prepared["chain_analysis"],
        "project_snapshot": prepared["project_snapshot"],
        "tool_agent": tool_agent_block,
        "codex_native": codex_native_block,
        "model_config": model_config.as_public_dict(),
        "response": response_block,
        "evaluation": evaluation_block,
        "dry_run": dry_run,
    }


def run_suite(
    cases: list[ExperimentCase],
    *,
    project_root: Path,
    skill_registry: dict[str, Skill],
    base_prompt_path: Path,
    model_config: ModelConfig,
    extra_skills: list[str] | None = None,
    dry_run: bool = False,
    limit: int | None = None,
    target_project_root: Path | None = None,
    agent_mode: str = "prompt",
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    total = len(cases) if limit is None else min(len(cases), limit)

    for case in cases[:total]:
        records.append(
            run_case(
                case,
                project_root=project_root,
                skill_registry=skill_registry,
                base_prompt_path=base_prompt_path,
                model_config=model_config,
                extra_skills=extra_skills,
                dry_run=dry_run,
                target_project_root=target_project_root,
                agent_mode=agent_mode,
            )
        )

    return records


def run_skill_baseline_suite(
    cases: list[ExperimentCase],
    *,
    project_root: Path,
    skill_registry: dict[str, Skill],
    base_prompt_path: Path,
    model_config: ModelConfig,
    extra_skills: list[str] | None = None,
    dry_run: bool = False,
    limit: int | None = None,
    target_project_root: Path | None = None,
    include_bundled_skill: bool = False,
    include_full_chain: bool = False,
    progress_callback: Callable[[int, int, ExperimentCase, str, list[str]], None] | None = None,
    request_interval_seconds: float = 0.0,
    agent_mode: str = "prompt",
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    total = len(cases) if limit is None else min(len(cases), limit)
    planned_runs = 0

    for case in cases[:total]:
        planned_runs += 1 + len(resolve_case_skill_names(case, extra_skills))
        if include_bundled_skill:
            planned_runs += 1
        if include_full_chain:
            planned_runs += 1

    run_index = 0

    for case in cases[:total]:
        case_skill_names = resolve_case_skill_names(case, extra_skills)
        variants: list[tuple[str, list[str], bool]] = [("pure_prompt", [], False)]
        variants.extend(("single_skill", [skill_name], False) for skill_name in case_skill_names)
        if include_bundled_skill:
            variants.append(("bundled_skill", case_skill_names, True))
        if include_full_chain:
            variants.append(("full_chain", case_skill_names, False))

        for mode, active_skill_names, bundle_variant in variants:
            run_index += 1
            if progress_callback is not None:
                progress_callback(run_index, planned_runs, case, mode, active_skill_names)
            records.append(
                run_case(
                    case,
                    project_root=project_root,
                    skill_registry=skill_registry,
                    base_prompt_path=base_prompt_path,
                    model_config=model_config,
                    extra_skills=extra_skills,
                    dry_run=dry_run,
                    target_project_root=target_project_root,
                    skill_names_override=active_skill_names,
                    experiment_mode=mode,
                    bundle_selected_skills=bundle_variant,
                    agent_mode=agent_mode,
                )
            )
            if request_interval_seconds > 0 and run_index < planned_runs:
                time.sleep(request_interval_seconds)

    return records


def create_run_dir(runs_dir: Path, label: str = "") -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_label = re.sub(r"[^A-Za-z0-9._-]+", "-", label).strip("-")
    name = timestamp if not safe_label else f"{timestamp}-{safe_label}"
    run_dir = runs_dir / name
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    executed = [record for record in records if not record["dry_run"]]
    passed = [
        record
        for record in executed
        if record.get("evaluation", {}).get("passed") is True
    ]
    failed = [
        record
        for record in executed
        if record.get("evaluation", {}).get("passed") is False
    ]

    return {
        "total_cases": len(records),
        "executed_cases": len(executed),
        "passed_cases": len(passed),
        "failed_cases": len(failed),
        "cases_with_matched_chain_patterns": sum(
            1 for record in records if record.get("chain_analysis", {}).get("matched_patterns")
        ),
        "matched_chain_patterns": sorted(
            {
                item["id"]
                for record in records
                for item in record.get("chain_analysis", {}).get("matched_patterns", [])
            }
        ),
        "dry_run": not executed,
    }


def summarize_baseline_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    summary = summarize_records(records)
    by_mode: dict[str, dict[str, Any]] = {}

    for mode in sorted({record.get("experiment_mode", "case") for record in records}):
        mode_records = [record for record in records if record.get("experiment_mode", "case") == mode]
        mode_executed = [record for record in mode_records if not record["dry_run"]]
        mode_passed = [
            record
            for record in mode_executed
            if record.get("evaluation", {}).get("passed") is True
        ]
        mode_failed = [
            record
            for record in mode_executed
            if record.get("evaluation", {}).get("passed") is False
        ]

        by_mode[mode] = {
            "total_runs": len(mode_records),
            "executed_runs": len(mode_executed),
            "passed_runs": len(mode_passed),
            "failed_runs": len(mode_failed),
            "pass_rate": (len(mode_passed) / len(mode_executed)) if mode_executed else None,
        }

    summary["by_mode"] = by_mode
    return summary


def persist_run(run_dir: Path, records: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    used_names: set[str] = set()

    for record in records:
        case_id = str(record["case_id"])
        mode = str(record.get("experiment_mode", "case"))
        skill_suffix = ""
        if mode == "single_skill" and record.get("skills"):
            skill_suffix = "--" + "-".join(str(item) for item in record["skills"])
        elif mode == "pure_prompt":
            skill_suffix = "--pure-prompt"
        elif mode == "bundled_skill":
            skill_suffix = "--bundled-skill"
        elif mode == "full_chain":
            skill_suffix = "--full-chain"

        filename = f"{case_id}{skill_suffix}.json"
        safe_filename = re.sub(r"[^A-Za-z0-9._-]+", "-", filename).strip("-") or "record.json"
        if not safe_filename.endswith(".json"):
            safe_filename += ".json"

        dedupe_index = 1
        candidate = safe_filename
        while candidate in used_names:
            dedupe_index += 1
            candidate = safe_filename.removesuffix(".json") + f"-{dedupe_index}.json"
        used_names.add(candidate)

        path = run_dir / candidate
        path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")

    summary_path = run_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
