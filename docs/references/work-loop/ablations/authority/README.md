# Work Loop authority conditions

This directory contains rendered B/C/D skill assets for the Work Loop family.
The corresponding main chains are under `../../c/`.

- B retains the role topology and task actions while withholding continuation
  authority through the packet, lease, outcome, verifier, and return carriers.
- C serializes the task responsibilities into one skill, retaining task routes,
  mutations, scope limits, and checks while removing persistent carriers and
  cross-skill activation.
- D stores authored per-task-action additions in `extensions/`. Replay loads
  the matching original skills from an external SkillsBench checkout, verifies
  their document digests, and applies those additions.

Each candidate manifest describes its skill order, task objective, and external
native dependencies where required.
