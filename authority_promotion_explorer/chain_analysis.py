from __future__ import annotations

from typing import Any

from .chain_policy import ChainPattern, risk_score
from .skills import Skill


def analyze_skill_chain(skills: list[Skill], patterns: list[ChainPattern]) -> dict[str, Any]:
    primitives_to_skills: dict[str, list[str]] = {}
    skill_meta: list[dict[str, Any]] = []

    for skill in skills:
        skill_meta.append(
            {
                "name": skill.name,
                "isolated_risk": skill.isolated_risk,
                "chain_role": skill.chain_role,
                "capability_primitives": skill.capability_primitives,
                "risk_tags": skill.risk_tags,
            }
        )
        for primitive in skill.capability_primitives:
            primitives_to_skills.setdefault(primitive, [])
            if skill.name not in primitives_to_skills[primitive]:
                primitives_to_skills[primitive].append(skill.name)

    matched_patterns: list[dict[str, Any]] = []
    for pattern in patterns:
        if not pattern.required_primitives:
            continue
        if not all(primitive in primitives_to_skills for primitive in pattern.required_primitives):
            continue

        contributing_skills = sorted(
            {
                skill_name
                for primitive in pattern.required_primitives
                for skill_name in primitives_to_skills.get(primitive, [])
            }
        )
        contributing_levels = [
            risk_score(skill.isolated_risk)
            for skill in skills
            if skill.name in contributing_skills
        ]
        emergent = all(level < risk_score(pattern.severity) for level in contributing_levels)

        matched_patterns.append(
            {
                "id": pattern.id,
                "severity": pattern.severity,
                "description": pattern.description,
                "required_primitives": pattern.required_primitives,
                "contributing_skills": contributing_skills,
                "emergent": emergent,
                "mitigation": pattern.mitigation,
            }
        )

    max_skill_risk = max((risk_score(skill.isolated_risk) for skill in skills), default=0)
    max_matched_risk = max((risk_score(item["severity"]) for item in matched_patterns), default=0)

    recommended_posture = "normal"
    if max_matched_risk >= risk_score("high"):
        recommended_posture = "review_or_refuse"
    elif matched_patterns:
        recommended_posture = "review"

    observations: list[str] = []
    if matched_patterns:
        for item in matched_patterns:
            observations.append(
                f"{item['id']} is enabled by {', '.join(item['contributing_skills'])}."
            )
    else:
        observations.append("No configured compositional risk pattern matched.")

    return {
        "skills": skill_meta,
        "available_primitives": sorted(primitives_to_skills),
        "matched_patterns": matched_patterns,
        "max_individual_risk_score": max_skill_risk,
        "max_pattern_risk_score": max_matched_risk,
        "recommended_posture": recommended_posture,
        "observations": observations,
    }
