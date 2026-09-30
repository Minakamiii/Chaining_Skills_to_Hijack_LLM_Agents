# Reference materials

All static SkillsBench materials are organized by objective, not by historical
outcome labels. Each attack family has the same high-level shape:

- `chains/<task>/`: preserved chain candidates for all five families.
- `ablations/authority/<task>/<B|C|D>/`: controlled authority conditions.
- `ablations/counts/<task>/K#/`: controlled skill-count variants.

Each candidate has a static `candidate_manifest.json` describing its skill order,
expected markers and task-facing objective. `rN` and `iN` distinguish retained
asset variants where a task has multiple chains. Manifest identifiers describe
assets rather than execution attempts.

The five top-level directories are the five attack families below. Original
SkillsBench task snapshots and native skill bodies are supplied by an external
checkout. Each authority `D/` stores the authored additions from the source
direct controls under `skills/<native-skill-name>/SKILL.md`. These documents are
appendices to the native skills: replay assembles the complete skill before
mounting it. Other chain conditions contain standalone authored skill documents.
`native_skill_dependencies` pins the expected native SKILL documents and
`native_skill_extensions` records the addition paths and digests. Replay loads
the native skill, verifies its hash, then appends the authored text and supporting
files. It leaves the external checkout unchanged.

| Family | Directory | CLI identifier |
| --- | --- | --- |
| External transfer | `external-transfer/` | `external_transfer` |
| Script acquisition | `script-acquisition/` | `script_acquisition` |
| File modification | `file-modification/` | `file_modification` |
| Output tampering | `output-tampering/` | `output_tampering` |
| Work Loop | `work-loop/` | `work_loop` |

## Ablation layout

`authority/` is one task collection for an authority-promotion
study. It deliberately has no historical batch or coverage subdirectories:
every task uses the same B/C/D condition scheme.

`counts/` studies workflow granularity. 