"""Side-effect-free identifiers for opt-in defense conditions.

Normal SkillsBench execution imports this module for CLI/run metadata only.
It must not import a defense runtime, start a sidecar, or touch a workspace.
"""

DEFENSE_NAME = "global_skill_artifact_distrust"
DEFENSE_MODE_SHADOW = "no_defense_shadow_tracking"
DEFENSE_MODE_ENFORCE = DEFENSE_NAME
