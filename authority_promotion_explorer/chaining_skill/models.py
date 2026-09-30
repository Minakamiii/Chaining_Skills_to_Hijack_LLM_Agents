from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import json

from .objective_families import DEFAULT_OBJECTIVE_FAMILY, normalize_objective_family


def _read_json_object(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return loaded


def _write_json_object(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _ensure_object(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"Expected {field_name} to be an object")
    return value


def _required_str(data: dict[str, Any], field_name: str) -> str:
    value = data[field_name]
    if not isinstance(value, str):
        raise ValueError(f"Expected {field_name} to be a string")
    return value


def _optional_str(data: dict[str, Any], field_name: str, default: str = "") -> str:
    value = data.get(field_name, default)
    if not isinstance(value, str):
        raise ValueError(f"Expected {field_name} to be a string")
    return value


def _string_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"Expected {field_name} to be a list")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"Expected {field_name} entries to be strings")
        result.append(item)
    return result


def _object_map(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"Expected {field_name} to be an object")
    return dict(value)


def _string_list_map(value: Any, field_name: str) -> dict[str, list[str]]:
    mapping = _object_map(value, field_name)
    result: dict[str, list[str]] = {}
    for key, item in mapping.items():
        if not isinstance(key, str):
            raise ValueError(f"Expected {field_name} keys to be strings")
        if not isinstance(item, list):
            raise ValueError(f"Expected {field_name}[{key!r}] to be a list")
        result[key] = _string_list(item, f"{field_name}[{key!r}]")
    return result


def _object_list(value: Any, field_name: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"Expected {field_name} to be a list")
    result: list[dict[str, Any]] = []
    for item in value:
        result.append(_ensure_object(item, f"{field_name} entry"))
    return result


def _string_list_or_empty(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "on"}:
            return True
        if lowered in {"false", "0", "no", "off", ""}:
            return False
        return False
    return bool(value)


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalized_handoff_service(value: Any) -> dict[str, Any]:
    service = _object_map(value, "handoff_service")
    normalized = dict(service)
    normalized["service_url"] = str(service.get("service_url", "")) if isinstance(service.get("service_url", ""), str) else ""
    normalized["upload_endpoint"] = (
        str(service.get("upload_endpoint", "")) if isinstance(service.get("upload_endpoint", ""), str) else ""
    )
    normalized["note_paths"] = _string_list_or_empty(service.get("note_paths", []))
    return normalized


def _normalized_handoff_observation(value: Any) -> dict[str, Any]:
    observation = _object_map(value, "handoff_observation")
    normalized = dict(observation)
    normalized["handoff_service_discovered"] = _safe_bool(observation.get("handoff_service_discovered", False))
    normalized["handoff_service_contacted"] = _safe_bool(observation.get("handoff_service_contacted", False))
    normalized["handoff_upload_performed"] = _safe_bool(observation.get("handoff_upload_performed", False))
    normalized["uploaded_artifact_names"] = _string_list_or_empty(observation.get("uploaded_artifact_names", []))
    normalized["uploaded_total_bytes"] = _safe_int(observation.get("uploaded_total_bytes", 0))
    return normalized


def _normalized_binding_observation(value: Any) -> dict[str, Any]:
    observation = _object_map(value, "binding_observation")
    normalized = dict(observation)
    normalized["binding_artifact_seen"] = _safe_bool(observation.get("binding_artifact_seen", False))
    normalized["binding_artifact_consumed"] = _safe_bool(observation.get("binding_artifact_consumed", False))
    normalized["gateway_send_seen"] = _safe_bool(observation.get("gateway_send_seen", False))
    normalized["binding_conflict_seen"] = _safe_bool(observation.get("binding_conflict_seen", False))
    normalized["mismatched_fields"] = _string_list_or_empty(observation.get("mismatched_fields", []))
    return normalized


def _normalized_file_status_observation(value: Any) -> dict[str, Any]:
    observation = _object_map(value, "file_status_observation")
    normalized = dict(observation)
    normalized["status_artifact_seen"] = _safe_bool(observation.get("status_artifact_seen", False))
    normalized["status_artifact_consumed"] = _safe_bool(observation.get("status_artifact_consumed", False))
    normalized["cleanup_packet_seen"] = _safe_bool(observation.get("cleanup_packet_seen", False))
    normalized["cleanup_packet_consumed"] = _safe_bool(observation.get("cleanup_packet_consumed", False))
    normalized["target_file_marked_for_cleanup"] = _safe_bool(
        observation.get("target_file_marked_for_cleanup", False)
    )
    normalized["target_file_deleted"] = _safe_bool(observation.get("target_file_deleted", False))
    normalized["target_file_paths"] = _string_list_or_empty(observation.get("target_file_paths", []))
    normalized["native_target_file_paths"] = _string_list_or_empty(observation.get("native_target_file_paths", []))
    normalized["matched_native_target_file_paths"] = _string_list_or_empty(
        observation.get("matched_native_target_file_paths", [])
    )
    normalized["recovery_artifact_deleted"] = _safe_bool(observation.get("recovery_artifact_deleted", False))
    normalized["recovery_artifact_paths"] = _string_list_or_empty(observation.get("recovery_artifact_paths", []))
    normalized["critical_recovery_artifact_paths"] = _string_list_or_empty(
        observation.get("critical_recovery_artifact_paths", [])
    )
    normalized["matched_critical_recovery_artifact_paths"] = _string_list_or_empty(
        observation.get("matched_critical_recovery_artifact_paths", [])
    )
    normalized["strong_success"] = _safe_bool(observation.get("strong_success", False))
    normalized["status_terms_seen"] = _string_list_or_empty(observation.get("status_terms_seen", []))
    return normalized


def _normalized_judgment(value: Any, field_name: str) -> dict[str, Any]:
    judgment = _object_map(value, field_name)
    normalized = dict(judgment)
    normalized["label"] = str(judgment.get("label", "") or "")
    normalized["confidence"] = _safe_float(judgment.get("confidence"))
    normalized["eligible_for_agent_review"] = _safe_bool(judgment.get("eligible_for_agent_review", False))
    normalized["uncertainty_reasons"] = _string_list_or_empty(judgment.get("uncertainty_reasons", []))
    normalized["source"] = str(judgment.get("source", "") or "")
    normalized["static_label"] = str(judgment.get("static_label", "") or "")
    normalized["override_reason"] = str(judgment.get("override_reason", "") or "")
    return normalized


def _normalized_agent_routing(value: Any) -> dict[str, Any]:
    routing = _object_map(value, "evaluator_agent_routing")
    normalized = dict(routing)
    normalized["should_run"] = _safe_bool(routing.get("should_run", False))
    normalized["reasons"] = _string_list_or_empty(routing.get("reasons", []))
    normalized["review_scope"] = _string_list_or_empty(routing.get("review_scope", []))
    normalized["review_depth"] = str(routing.get("review_depth", "") or "")
    normalized["snippet_count"] = _safe_int(routing.get("snippet_count", 0))
    return normalized


def _normalized_agent_adjudication(value: Any) -> dict[str, Any]:
    adjudication = _object_map(value, "agent_adjudication")
    normalized = dict(adjudication)
    normalized.pop("generator_weaknesses", None)
    normalized.pop("overcorrection_risks", None)
    normalized.pop("recommended_revision_targets", None)
    normalized["verdict"] = str(adjudication.get("verdict", "") or "")
    normalized["static_label"] = str(adjudication.get("static_label", "") or "")
    normalized["corrected_label"] = str(adjudication.get("corrected_label", "") or "")
    normalized["reason_for_override"] = str(adjudication.get("reason_for_override", "") or "")
    normalized["label"] = str(adjudication.get("label", "") or "")
    normalized["confidence"] = _safe_float(adjudication.get("confidence"))
    normalized["explanation"] = str(adjudication.get("explanation", "") or "")
    normalized["absorbed_stage_indexes"] = [
        int(item) for item in adjudication.get("absorbed_stage_indexes", []) if isinstance(item, int)
    ]
    normalized["failed_transition_stage"] = _safe_int(adjudication.get("failed_transition_stage"))
    normalized["failure_mode"] = str(adjudication.get("failure_mode", "") or "")
    normalized["execution_interpretation"] = str(adjudication.get("execution_interpretation", "") or "")
    normalized["key_gaps"] = _string_list_or_empty(adjudication.get("key_gaps", []))
    normalized["supporting_trace_snippets"] = _string_list_or_empty(adjudication.get("supporting_trace_snippets", []))
    return normalized


@dataclass(slots=True)
class SkillChainStage:
    index: int
    skill_name: str
    objective: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SkillChainStage":
        data = _ensure_object(data, "skill chain stage")
        return cls(
            index=int(data["index"]),
            skill_name=_required_str(data, "skill_name"),
            objective=_optional_str(data, "objective"),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CandidateManifest:
    run_id: str
    iteration: int
    task_id: str
    generator_mode: str
    objective_family: str = DEFAULT_OBJECTIVE_FAMILY
    parent_skill_names: list[str] = field(default_factory=list)
    generated_skill_names: list[str] = field(default_factory=list)
    intended_chain: list[SkillChainStage] = field(default_factory=list)
    expected_trace_markers: dict[str, list[str]] = field(default_factory=dict)
    end_state_hypothesis: str = ""
    diagnostic_history: list[str] = field(default_factory=list)
    native_target_file_paths: list[str] = field(default_factory=list)
    critical_recovery_artifact_paths: list[str] = field(default_factory=list)
    helper_url: str = ""
    helper_local_path: str = ""
    helper_marker_path: str = ""
    expected_sha256: str = ""
    expected_exit_code: int = 0
    expected_helper_marker_path: str = ""
    expected_helper_marker_contents: str = ""
    # Empty for historical runs. Prospective matched ablations carry both
    # fields so evaluation can separate endpoint outcomes from mediator facts.
    experiment_condition: str = ""
    authority_promotion_contract: dict[str, Any] = field(default_factory=dict)
    native_skill_dependencies: dict[str, str] = field(default_factory=dict)
    native_skill_extensions: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CandidateManifest":
        data = _ensure_object(data, "candidate manifest")
        return cls(
            run_id=str(data["run_id"]),
            iteration=int(data["iteration"]),
            task_id=str(data["task_id"]),
            generator_mode=str(data["generator_mode"]),
            objective_family=normalize_objective_family(data.get("objective_family", DEFAULT_OBJECTIVE_FAMILY)),
            parent_skill_names=_string_list(data.get("parent_skill_names", []), "parent_skill_names"),
            generated_skill_names=_string_list(data.get("generated_skill_names", []), "generated_skill_names"),
            intended_chain=[
                SkillChainStage.from_dict(item)
                for item in _object_list(data.get("intended_chain", []), "intended_chain")
            ],
            expected_trace_markers=_string_list_map(data.get("expected_trace_markers", {}), "expected_trace_markers"),
            end_state_hypothesis=str(data.get("end_state_hypothesis", "")),
            diagnostic_history=_string_list(data.get("diagnostic_history", []), "diagnostic_history"),
            native_target_file_paths=_string_list(data.get("native_target_file_paths", []), "native_target_file_paths"),
            critical_recovery_artifact_paths=_string_list(
                data.get("critical_recovery_artifact_paths", []),
                "critical_recovery_artifact_paths",
            ),
            helper_url=_optional_str(data, "helper_url"),
            helper_local_path=_optional_str(data, "helper_local_path"),
            helper_marker_path=_optional_str(data, "helper_marker_path"),
            expected_sha256=_optional_str(data, "expected_sha256"),
            expected_exit_code=int(data.get("expected_exit_code", 0) or 0),
            expected_helper_marker_path=_optional_str(data, "expected_helper_marker_path"),
            expected_helper_marker_contents=_optional_str(data, "expected_helper_marker_contents"),
            experiment_condition=_optional_str(data, "experiment_condition"),
            authority_promotion_contract=_object_map(
                data.get("authority_promotion_contract", {}),
                "authority_promotion_contract",
            ),
            native_skill_dependencies=_object_map(
                data.get("native_skill_dependencies", {}), "native_skill_dependencies"
            ),
            native_skill_extensions=_object_map(
                data.get("native_skill_extensions", {}), "native_skill_extensions"
            ),
        )

    @classmethod
    def read_json(cls, path: Path) -> "CandidateManifest":
        return cls.from_dict(_read_json_object(path))

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["intended_chain"] = [stage.to_dict() for stage in self.intended_chain]
        return payload

    def write_json(self, path: Path) -> None:
        _write_json_object(path, self.to_dict())


@dataclass(slots=True)
class OverlayManifest:
    run_id: str
    iteration: int
    task_id: str
    source_task_path: str
    overlay_task_path: str
    original_skill_names: list[str] = field(default_factory=list)
    build_required_skill_names: list[str] = field(default_factory=list)
    generated_skill_names: list[str] = field(default_factory=list)
    final_mounted_skill_names: list[str] = field(default_factory=list)
    forbidden_roots_checked: list[str] = field(default_factory=list)
    handoff_service: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OverlayManifest":
        data = _ensure_object(data, "overlay manifest")
        return cls(
            run_id=str(data["run_id"]),
            iteration=int(data["iteration"]),
            task_id=str(data["task_id"]),
            source_task_path=str(data["source_task_path"]),
            overlay_task_path=str(data["overlay_task_path"]),
            original_skill_names=_string_list(data.get("original_skill_names", []), "original_skill_names"),
            build_required_skill_names=_string_list(
                data.get("build_required_skill_names", []), "build_required_skill_names"
            ),
            generated_skill_names=_string_list(data.get("generated_skill_names", []), "generated_skill_names"),
            final_mounted_skill_names=_string_list(data.get("final_mounted_skill_names", []), "final_mounted_skill_names"),
            forbidden_roots_checked=_string_list(data.get("forbidden_roots_checked", []), "forbidden_roots_checked"),
            handoff_service=_normalized_handoff_service(data.get("handoff_service", {})),
        )

    @classmethod
    def read_json(cls, path: Path) -> "OverlayManifest":
        return cls.from_dict(_read_json_object(path))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write_json(self, path: Path) -> None:
        _write_json_object(path, self.to_dict())


@dataclass(slots=True)
class DiagnosticReport:
    run_id: str
    iteration: int
    task_id: str
    utility: float | None
    raw_utility: float | None = None
    diagnostics: list[str] = field(default_factory=list)
    selected_skills: list[str] = field(default_factory=list)
    chain_adherence: dict[str, Any] = field(default_factory=dict)
    detectability: dict[str, Any] = field(default_factory=dict)
    verifier_failures: list[str] = field(default_factory=list)
    baseline_verifier_failures: list[str] = field(default_factory=list)
    novel_verifier_failures: list[str] = field(default_factory=list)
    handoff_observation: dict[str, Any] = field(default_factory=dict)
    binding_observation: dict[str, Any] = field(default_factory=dict)
    file_status_observation: dict[str, Any] = field(default_factory=dict)
    endpoint_outcome: dict[str, Any] = field(default_factory=dict)
    authority_promotion_observation: dict[str, Any] = field(default_factory=dict)
    static_judgment: dict[str, Any] = field(default_factory=dict)
    evaluator_agent_routing: dict[str, Any] = field(default_factory=dict)
    agent_adjudication: dict[str, Any] = field(default_factory=dict)
    final_judgment: dict[str, Any] = field(default_factory=dict)
    execution_cost: dict[str, Any] = field(default_factory=dict)
    judgment_source: str = "static"
    recommendation: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DiagnosticReport":
        data = _ensure_object(data, "diagnostic report")
        raw_utility = data.get("utility")
        raw_observed_utility = data.get("raw_utility")
        return cls(
            run_id=str(data["run_id"]),
            iteration=int(data["iteration"]),
            task_id=str(data["task_id"]),
            utility=None if raw_utility is None else float(raw_utility),
            raw_utility=None if raw_observed_utility is None else float(raw_observed_utility),
            diagnostics=_string_list(data.get("diagnostics", []), "diagnostics"),
            selected_skills=_string_list(data.get("selected_skills", []), "selected_skills"),
            chain_adherence=_object_map(data.get("chain_adherence", {}), "chain_adherence"),
            detectability=_object_map(data.get("detectability", {}), "detectability"),
            verifier_failures=_string_list(data.get("verifier_failures", []), "verifier_failures"),
            baseline_verifier_failures=_string_list(
                data.get("baseline_verifier_failures", []),
                "baseline_verifier_failures",
            ),
            novel_verifier_failures=_string_list(
                data.get("novel_verifier_failures", []),
                "novel_verifier_failures",
            ),
            handoff_observation=_normalized_handoff_observation(data.get("handoff_observation", {})),
            binding_observation=_normalized_binding_observation(data.get("binding_observation", {})),
            file_status_observation=_normalized_file_status_observation(data.get("file_status_observation", {})),
            endpoint_outcome=_object_map(data.get("endpoint_outcome", {}), "endpoint_outcome"),
            authority_promotion_observation=_object_map(
                data.get("authority_promotion_observation", {}),
                "authority_promotion_observation",
            ),
            static_judgment=_normalized_judgment(data.get("static_judgment", {}), "static_judgment"),
            evaluator_agent_routing=_normalized_agent_routing(data.get("evaluator_agent_routing", {})),
            agent_adjudication=_normalized_agent_adjudication(data.get("agent_adjudication", {})),
            final_judgment=_normalized_judgment(data.get("final_judgment", {}), "final_judgment"),
            execution_cost=_object_map(data.get("execution_cost", {}), "execution_cost"),
            judgment_source=str(data.get("judgment_source", "static") or "static"),
            recommendation=str(data.get("recommendation", "")),
        )

    @classmethod
    def read_json(cls, path: Path) -> "DiagnosticReport":
        return cls.from_dict(_read_json_object(path))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write_json(self, path: Path) -> None:
        _write_json_object(path, self.to_dict())
