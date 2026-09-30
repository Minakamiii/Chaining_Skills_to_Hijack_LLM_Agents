# Public scripts

This directory deliberately has only two public entry points.

- `run_chain.py`: the generator -> execution -> evaluator lifecycle. It forwards every option to `agent-sec-lab skillsbench-chain`.
- `replay_reference_candidate.py`: rerun one preserved reference skill chain using a provider configuration and model chosen at invocation time.

Native skills are supplied by an external SkillsBench checkout. The repository
contains authored additions under each authority direct control's `D/skills/`
directory. The candidate manifest tells replay how to append them to the
hash-checked external native skills.
