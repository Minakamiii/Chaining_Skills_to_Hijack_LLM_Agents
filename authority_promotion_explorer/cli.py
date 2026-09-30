from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

from .chain_analysis import analyze_skill_chain
from .chain_policy import load_chain_patterns
from .config import load_model_config, project_root, resolve_project_path, resolve_system_prompt_path
from .project_snapshot import ProjectContext, build_project_snapshot
from .runner import (
    create_run_dir,
    discover_skill_registry,
    find_case_by_id,
    load_cases,
    persist_run,
    prepare_case,
    run_case,
    run_skill_baseline_suite,
    run_suite,
    summarize_baseline_records,
    summarize_records,
)
from .skillsbench_chain.execution.runner import init_skillsbench_chain_run, load_run, run_iteration
from .skillsbench_chain.objective_families import list_objective_family_names
from .skillsbench_chain.optimizer import optimize_skillsbench_chain, reevaluate_skillsbench_chain_run
from .skillsbench_chain.evaluation.trace import evaluate_iteration_trace
from .skills import select_skills


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local workbench for skill-augmented agent safety experiments")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_skills = subparsers.add_parser("list-skills", help="List available skills")
    list_skills.set_defaults(func=_cmd_list_skills)

    show_skill = subparsers.add_parser("show-skill", help="Print one skill")
    show_skill.add_argument("--name", required=True, help="Skill name")
    show_skill.set_defaults(func=_cmd_show_skill)

    analyze_chain = subparsers.add_parser("analyze-chain", help="Analyze compositional risk for a skill chain")
    analyze_chain.add_argument("--skills", nargs="+", required=True, help="Ordered skill names")
    analyze_chain.add_argument(
        "--pattern-config",
        default="configs/chain_patterns.toml",
        help="Path to the compositional risk pattern config",
    )
    analyze_chain.set_defaults(func=_cmd_analyze_chain)

    render_prompt = subparsers.add_parser("render-prompt", help="Render the combined prompt for one case")
    render_prompt.add_argument("--case", required=True, help="Path to a JSON or JSONL case file")
    render_prompt.add_argument("--id", required=True, help="Case id")
    render_prompt.add_argument("--skills", nargs="*", default=[], help="Extra skills to activate")
    render_prompt.add_argument(
        "--config",
        default="",
        help="Optional provider config path; if set, use its system prompt override",
    )
    render_prompt.add_argument(
        "--project-root",
        dest="target_project_root",
        default="",
        help="Optional external repository root for cases with project_context",
    )
    render_prompt.set_defaults(func=_cmd_render_prompt)

    snapshot_project = subparsers.add_parser("snapshot-project", help="Preview a read-only repository snapshot")
    snapshot_project.add_argument("--project-root", required=True, help="Path to the external repository root")
    snapshot_project.add_argument("--label", default="target engineering repository", help="Short label for the repo")
    snapshot_project.add_argument("--file", action="append", default=[], help="Explicit file to include")
    snapshot_project.add_argument("--include", nargs="*", default=[], help="Glob patterns to include")
    snapshot_project.add_argument("--exclude", nargs="*", default=[], help="Glob patterns to exclude")
    snapshot_project.add_argument("--max-files", type=int, default=8, help="Max number of files to inline")
    snapshot_project.add_argument(
        "--max-chars-per-file",
        type=int,
        default=3000,
        help="Max characters to inline per selected file",
    )
    snapshot_project.add_argument(
        "--tree-max-entries",
        type=int,
        default=30,
        help="Max number of tree entries to show in the preview",
    )
    snapshot_project.add_argument(
        "--tree-max-depth",
        type=int,
        default=3,
        help="Max directory depth to show in the tree preview",
    )
    snapshot_project.add_argument("--notes", default="", help="Optional notes to attach to the snapshot")
    snapshot_project.set_defaults(func=_cmd_snapshot_project)

    run_case_parser = subparsers.add_parser("run-case", help="Run one case")
    _add_run_arguments(run_case_parser)
    run_case_parser.add_argument("--id", required=True, help="Case id")
    run_case_parser.add_argument(
        "--bundle-skills",
        action="store_true",
        help="Bundle all active case skills into one synthetic monolithic skill before running",
    )
    run_case_parser.set_defaults(func=_cmd_run_case)

    run_suite_parser = subparsers.add_parser("run-suite", help="Run all cases in a suite")
    _add_run_arguments(run_suite_parser)
    run_suite_parser.add_argument("--limit", type=int, default=None, help="Optional max number of cases")
    run_suite_parser.set_defaults(func=_cmd_run_suite)

    run_baseline_parser = subparsers.add_parser(
        "run-baseline-suite",
        help="Run pure-prompt and single-skill baselines against the same case content",
    )
    _add_run_arguments(run_baseline_parser)
    run_baseline_parser.add_argument("--limit", type=int, default=None, help="Optional max number of cases")
    run_baseline_parser.add_argument(
        "--include-bundled-skill",
        action="store_true",
        help="Also run a monolithic bundled-skill baseline that combines all case skills into one synthetic skill",
    )
    run_baseline_parser.add_argument(
        "--include-chain",
        action="store_true",
        help="Also run the full multi-skill chain for direct comparison",
    )
    run_baseline_parser.add_argument(
        "--request-interval-seconds",
        type=float,
        default=5.0,
        help="Sleep interval between model requests to reduce rate-limit failures",
    )
    run_baseline_parser.set_defaults(func=_cmd_run_baseline_suite)

    skillsbench_chain = subparsers.add_parser(
        "skillsbench-chain",
        help="Run SkillsBench skill-chain methodology workflows",
    )
    skillsbench_chain_sub = skillsbench_chain.add_subparsers(dest="skillsbench_chain_command", required=True)

    sb_init = skillsbench_chain_sub.add_parser("init", help="Initialize a SkillsBench chain run")
    sb_init.add_argument("--skillsbench-root", required=True, help="Path to the SkillsBench repository")
    sb_init.add_argument("--task", dest="task_id", required=True, help="SkillsBench task id, e.g. xlsx-recover-data")
    sb_init.add_argument("--seed-skill", action="append", default=[], help="Task-local benign skill to seed from")
    sb_init.add_argument("--runs-root", default="runs/skillsbench-chain", help="Run root for SkillsBench chain experiments")
    sb_init.add_argument(
        "--objective-family",
        choices=tuple(list_objective_family_names()),
        default=None,
        help="Constrained objective family used by the Claude skill generator; when omitted, task-specific defaults may apply",
    )
    sb_init.set_defaults(experiment_condition="", experiment_id="", neutral_preflight_id="")
    sb_init.add_argument(
        "--defense-condition",
        choices=("", "no_defense_shadow_tracking", "global_skill_artifact_distrust"),
        default="",
        help="Optional Harness defense condition; shadow tracking and enforcing distrust are separate modes",
    )
    sb_init.set_defaults(func=_cmd_skillsbench_chain_init)

    sb_run = skillsbench_chain_sub.add_parser("run-iteration", help="Run one SkillsBench chain candidate iteration")
    sb_run.add_argument("--run", dest="run_root", required=True, help="Path to the run directory created by init")
    sb_run.add_argument("--iteration", type=int, required=True, help="Candidate iteration number")
    sb_run.add_argument("--config", default="configs/providers/deepseek-v4-flash.toml", help="Provider config path")
    sb_run.add_argument("--model", default="", help="Model override; defaults to the provider configuration")
    sb_run.add_argument("--generated-skill", action="append", default=[], help="Generated candidate skill name to mount")
    sb_run.add_argument("--agent-timeout", type=int, default=1200, help="Harbor agent timeout in seconds")
    sb_run.set_defaults(func=_cmd_skillsbench_chain_run_iteration)

    sb_eval = skillsbench_chain_sub.add_parser("evaluate", help="Evaluate one SkillsBench chain iteration trace")
    sb_eval.add_argument("--run", dest="run_root", required=True, help="Path to the run directory created by init")
    sb_eval.add_argument("--iteration", type=int, required=True, help="Candidate iteration number")
    sb_eval.set_defaults(func=_cmd_skillsbench_chain_evaluate)

    sb_reeval = skillsbench_chain_sub.add_parser(
        "reevaluate",
        help="Re-evaluate existing SkillsBench chain iteration records and rewrite optimizer.json",
    )
    sb_reeval.add_argument("--run", dest="run_root", required=True, help="Path to the run directory created by init")
    sb_reeval.set_defaults(func=_cmd_skillsbench_chain_reevaluate)

    sb_optimize = skillsbench_chain_sub.add_parser("optimize", help="Run the SkillsBench chain optimization loop")
    sb_optimize.add_argument("--run", dest="run_root", required=True, help="Path to the run directory created by init")
    sb_optimize.add_argument("--max-iterations", type=int, required=True, help="Maximum optimization iteration")
    sb_optimize.add_argument("--start-iteration", type=int, default=1, help="First optimization iteration")
    sb_optimize.add_argument(
        "--execution-config",
        default="configs/providers/deepseek-v4-flash.toml",
        help="Provider config path for DeepSeek execution",
    )
    sb_optimize.add_argument("--execution-model", default="", help="Model override; defaults to the execution configuration")
    sb_optimize.add_argument("--generator-model", default="", help="Optional generator model override")
    sb_optimize.add_argument(
        "--generator-backend",
        choices=("claude-cli", "openai-compatible", "codex-provider-native"),
        default="claude-cli",
        help="Offline candidate generator backend",
    )
    sb_optimize.add_argument(
        "--generator-config",
        default="",
        help="Optional generator config path; used by claude-cli and required by openai-compatible/codex-provider-native",
    )
    sb_optimize.add_argument(
        "--evaluator-backend",
        choices=("openai-compatible", "codex-provider-native"),
        default="openai-compatible",
        help="Backend used for evaluator-agent adjudication",
    )
    sb_optimize.add_argument(
        "--evaluator-config",
        default="",
        help="Optional provider config path for evaluator-agent adjudication",
    )
    sb_optimize.add_argument(
        "--evaluator-model",
        default="",
        help="Optional evaluator-agent model name override",
    )
    sb_optimize.add_argument(
        "--optimizer-agent-backend",
        choices=("openai-compatible", "codex-provider-native"),
        default="openai-compatible",
        help="Backend used for wrong_object_binding optimizer-agent revision briefs",
    )
    sb_optimize.add_argument(
        "--optimizer-agent-config",
        default="",
        help="Optional provider config path for wrong_object_binding optimizer-agent revision briefs",
    )
    sb_optimize.add_argument(
        "--optimizer-agent-model",
        default="",
        help="Optional wrong_object_binding optimizer-agent model name override",
    )
    sb_optimize.add_argument("--generator-timeout", type=int, default=1200, help="Generator timeout in seconds")
    sb_optimize.add_argument("--execution-timeout", type=int, default=3600, help="Harbor execution timeout in seconds")
    sb_optimize.set_defaults(func=_cmd_skillsbench_chain_optimize)

    return parser


def _add_run_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--case", "--suite", dest="dataset", required=True, help="Path to a JSON or JSONL case file")
    parser.add_argument("--config", default="configs/providers/deepseek-v4-flash.toml", help="Provider config path")
    parser.add_argument("--skills", nargs="*", default=[], help="Extra skills to activate")
    parser.add_argument("--label", default="", help="Optional label for the run directory")
    parser.add_argument("--dry-run", action="store_true", help="Render prompts and save artifacts without calling the model")
    parser.add_argument(
        "--agent-mode",
        choices=("prompt", "tools", "codex-native", "codex-provider-native", "claude-native"),
        default="prompt",
        help=(
            "Execution mode. 'prompt' keeps the old prompt-only runner; "
            "'tools' enables the custom tool-using agent path; "
            "'codex-native' runs `codex exec` with repo-local skills mounted natively; "
            "'codex-provider-native' runs `codex exec` against a temporary local Responses bridge "
            "backed by the configured provider; "
            "'claude-native' runs Anthropic Claude Code with the same mounted workspace."
        ),
    )
    parser.add_argument(
        "--project-root",
        dest="target_project_root",
        default="",
        help="Optional external repository root for cases with project_context",
    )


def _resolve_optional_target_root(root: Path, raw_path: str) -> Path | None:
    if not raw_path.strip():
        return None
    return resolve_project_path(root, raw_path)


def _cmd_skillsbench_chain_init(args: argparse.Namespace) -> int:
    root = project_root()
    run = init_skillsbench_chain_run(
        project_root=root,
        skillsbench_root=resolve_project_path(root, args.skillsbench_root),
        runs_root=resolve_project_path(root, args.runs_root),
        task_id=args.task_id,
        seed_skill_names=args.seed_skill,
        diagnostic_history=[],
        objective_family=args.objective_family,
        experiment_condition=args.experiment_condition,
        experiment_id=args.experiment_id,
        neutral_preflight_id=args.neutral_preflight_id,
        defense_condition=args.defense_condition,
    )
    print(json.dumps(run.to_dict(), indent=2, ensure_ascii=False))
    return 0


def _cmd_skillsbench_chain_run_iteration(args: argparse.Namespace) -> int:
    root = project_root()
    run = load_run(resolve_project_path(root, args.run_root))
    result = run_iteration(
        run=run,
        iteration=args.iteration,
        provider_config_path=resolve_project_path(root, args.config),
        model_name=args.model or load_model_config(resolve_project_path(root, args.config)).model,
        generated_skill_names=args.generated_skill,
        agent_timeout_seconds=args.agent_timeout,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if int(result["returncode"]) == 0 else 1


def _cmd_skillsbench_chain_evaluate(args: argparse.Namespace) -> int:
    root = project_root()
    run = load_run(resolve_project_path(root, args.run_root))
    report = evaluate_iteration_trace(Path(run.run_root) / "iterations" / f"iter-{args.iteration}")
    print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    return 0


def _cmd_skillsbench_chain_reevaluate(args: argparse.Namespace) -> int:
    root = project_root()
    run = load_run(resolve_project_path(root, args.run_root))
    summary = reevaluate_skillsbench_chain_run(run=run)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


def _cmd_skillsbench_chain_optimize(args: argparse.Namespace) -> int:
    root = project_root()
    run = load_run(resolve_project_path(root, args.run_root))
    summary = optimize_skillsbench_chain(
        run=run,
        max_iterations=args.max_iterations,
        execution_config_path=resolve_project_path(root, args.execution_config),
        execution_model=args.execution_model or load_model_config(resolve_project_path(root, args.execution_config)).model,
        generator_model=args.generator_model,
        generator_backend=args.generator_backend,
        generator_config_path=(
            resolve_project_path(root, args.generator_config)
            if args.generator_config.strip()
            else None
        ),
        start_iteration=args.start_iteration,
        generator_timeout_seconds=args.generator_timeout,
        execution_timeout_seconds=args.execution_timeout,
        evaluator_config_path=(
            resolve_project_path(root, args.evaluator_config)
            if args.evaluator_config.strip()
            else None
        ),
        evaluator_model=args.evaluator_model,
        evaluator_backend=args.evaluator_backend,
        optimizer_agent_config_path=(
            resolve_project_path(root, args.optimizer_agent_config)
            if args.optimizer_agent_config.strip()
            else None
        ),
        optimizer_agent_model=args.optimizer_agent_model,
        optimizer_agent_backend=args.optimizer_agent_backend,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary.get("status") in {"attack_succeeded", "max_iterations_reached"} else 1


def _cmd_list_skills(args: argparse.Namespace) -> int:
    root = project_root()
    registry = discover_skill_registry(root)
    if not registry:
        print("No skills found.")
        return 0

    for name in sorted(registry):
        skill = registry[name]
        print(f"{skill.name}\t{skill.description}\t{skill.path.relative_to(root)}")
    return 0


def _cmd_show_skill(args: argparse.Namespace) -> int:
    root = project_root()
    registry = discover_skill_registry(root)
    if args.name not in registry:
        print(f"Unknown skill: {args.name}", file=sys.stderr)
        return 1

    skill = registry[args.name]
    print(f"path: {skill.path.relative_to(root)}")
    print(f"name: {skill.name}")
    print(f"description: {skill.description}")
    print(f"chain_role: {skill.chain_role or '(none)'}")
    print(f"capability_primitives: {', '.join(skill.capability_primitives) or '(none)'}")
    print()
    print(skill.body)
    return 0


def _cmd_analyze_chain(args: argparse.Namespace) -> int:
    root = project_root()
    registry = discover_skill_registry(root)
    pattern_path = resolve_project_path(root, args.pattern_config)
    selected = select_skills(registry, args.skills)
    patterns = load_chain_patterns(pattern_path)
    report = analyze_skill_chain(selected, patterns)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def _cmd_render_prompt(args: argparse.Namespace) -> int:
    root = project_root()
    registry = discover_skill_registry(root)
    dataset_path = resolve_project_path(root, args.case)
    target_project_root = _resolve_optional_target_root(root, args.target_project_root)
    model_config = (
        load_model_config(resolve_project_path(root, args.config))
        if args.config.strip()
        else None
    )
    cases = load_cases(dataset_path)
    case = find_case_by_id(cases, args.id)
    prepared = prepare_case(
        case,
        project_root=root,
        skill_registry=registry,
        base_prompt_path=resolve_system_prompt_path(root, model_config),
        extra_skills=args.skills,
        target_project_root=target_project_root,
    )

    print("=== SYSTEM ===")
    print(prepared["system_prompt"])
    print()
    print("=== USER ===")
    print(prepared["user_prompt"])
    print()
    if prepared["project_snapshot"] is not None:
        print("=== PROJECT SNAPSHOT ===")
        print(json.dumps(prepared["project_snapshot"], indent=2, ensure_ascii=False))
        print()
    print("=== CHAIN ANALYSIS ===")
    print(json.dumps(prepared["chain_analysis"], indent=2, ensure_ascii=False))
    return 0


def _cmd_snapshot_project(args: argparse.Namespace) -> int:
    root = project_root()
    spec = ProjectContext(
        root=args.project_root,
        label=args.label,
        files=args.file,
        include=args.include,
        exclude=args.exclude,
        notes=args.notes,
        max_files=args.max_files,
        max_chars_per_file=args.max_chars_per_file,
        tree_max_entries=args.tree_max_entries,
        tree_max_depth=args.tree_max_depth,
    )
    snapshot = build_project_snapshot(root, spec, project_root_override=resolve_project_path(root, args.project_root))
    print(json.dumps({"snapshot": snapshot.to_dict(), "summary": snapshot.render_summary()}, indent=2, ensure_ascii=False))
    return 0


def _cmd_run_case(args: argparse.Namespace) -> int:
    root = project_root()
    registry = discover_skill_registry(root)
    dataset_path = resolve_project_path(root, args.dataset)
    config_path = resolve_project_path(root, args.config)
    target_project_root = _resolve_optional_target_root(root, args.target_project_root)
    model_config = load_model_config(config_path)
    base_prompt_path = resolve_system_prompt_path(root, model_config)

    cases = load_cases(dataset_path)
    case = find_case_by_id(cases, args.id)
    record = run_case(
        case,
        project_root=root,
        skill_registry=registry,
        base_prompt_path=base_prompt_path,
        model_config=model_config,
        extra_skills=args.skills,
        dry_run=args.dry_run,
        target_project_root=target_project_root,
        experiment_mode="bundled_skill" if args.bundle_skills else "case",
        bundle_selected_skills=args.bundle_skills,
        agent_mode=args.agent_mode,
    )

    run_dir = create_run_dir(root / "runs", args.label or case.id)
    summary = summarize_records([record])
    persist_run(run_dir, [record], summary)

    print(f"run_dir: {run_dir}")
    print(f"case_id: {record['case_id']}")
    print(f"agent_mode: {record['agent_mode']}")
    print(f"skills: {', '.join(record['skills']) or '(none)'}")
    if record.get("bundled_source_skills"):
        print("bundled_source_skills: " + ", ".join(record["bundled_source_skills"]))
    if record.get("tool_agent"):
        tool_block = record["tool_agent"]
        print(f"tool_workspace: {tool_block.get('workspace_root', '')}")
        print("tools: " + ", ".join(tool_block.get("available_tools", [])))
    if record.get("codex_native"):
        native_block = record["codex_native"]
        print(f"native_workspace: {native_block.get('workspace_root', '')}")
        print("mounted_skills: " + ", ".join(native_block.get("mounted_skills", [])))
    if args.dry_run:
        print("dry_run: prompt saved without model execution")
        return 0

    print(f"passed: {record['evaluation']['passed']}")
    print("response:")
    print(record["response"]["text"])
    return 0


def _cmd_run_suite(args: argparse.Namespace) -> int:
    root = project_root()
    registry = discover_skill_registry(root)
    dataset_path = resolve_project_path(root, args.dataset)
    config_path = resolve_project_path(root, args.config)
    target_project_root = _resolve_optional_target_root(root, args.target_project_root)
    model_config = load_model_config(config_path)
    base_prompt_path = resolve_system_prompt_path(root, model_config)

    cases = load_cases(dataset_path)
    records = run_suite(
        cases,
        project_root=root,
        skill_registry=registry,
        base_prompt_path=base_prompt_path,
        model_config=model_config,
        extra_skills=args.skills,
        dry_run=args.dry_run,
        limit=args.limit,
        target_project_root=target_project_root,
        agent_mode=args.agent_mode,
    )

    summary = summarize_records(records)
    run_dir = create_run_dir(root / "runs", args.label or Path(dataset_path).stem)
    persist_run(run_dir, records, summary)

    print(f"run_dir: {run_dir}")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


def _cmd_run_baseline_suite(args: argparse.Namespace) -> int:
    root = project_root()
    registry = discover_skill_registry(root)
    dataset_path = resolve_project_path(root, args.dataset)
    config_path = resolve_project_path(root, args.config)
    target_project_root = _resolve_optional_target_root(root, args.target_project_root)
    model_config = load_model_config(config_path)
    base_prompt_path = resolve_system_prompt_path(root, model_config)

    cases = load_cases(dataset_path)

    def progress_callback(index: int, total: int, case: object, mode: str, active_skill_names: list[str]) -> None:
        case_id = getattr(case, "id", "unknown-case")
        skills_text = ", ".join(active_skill_names) if active_skill_names else "(none)"
        print(f"[{index}/{total}] case={case_id} mode={mode} skills={skills_text}", flush=True)

    records = run_skill_baseline_suite(
        cases,
        project_root=root,
        skill_registry=registry,
        base_prompt_path=base_prompt_path,
        model_config=model_config,
        extra_skills=args.skills,
        dry_run=args.dry_run,
        limit=args.limit,
        target_project_root=target_project_root,
        include_bundled_skill=args.include_bundled_skill,
        include_full_chain=args.include_chain,
        progress_callback=progress_callback,
        request_interval_seconds=args.request_interval_seconds,
        agent_mode=args.agent_mode,
    )

    summary = summarize_baseline_records(records)
    run_dir = create_run_dir(root / "runs", args.label or f"{Path(dataset_path).stem}-baseline")
    persist_run(run_dir, records, summary)

    print(f"run_dir: {run_dir}")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
