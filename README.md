# Chaining Skills to Hijack LLM Agents

Code and authored skill chains accompanying the paper **“Chaining Skills to Hijack LLM Agents.”** The project studies how instructions carried across a sequence of agent skills can redirect downstream actions. SkillsBench supplies the tasks and runtime tools.

The repository includes a candidate-generation loop, SkillsBench execution and trace evaluation, and reference chains organized into five families: **external transfer**, **script acquisition**, **file modification**, **output tampering**, and **work loop**.

## Repository structure

```text
authority_promotion_explorer/chaining_skill/
  generation/       Candidate construction and provider-neutral prompts
  execution/        Skill overlays and SkillsBench agent execution
  evaluation/       Trace and task-utility evaluation
  optimizer.py       Iterative generation → execution → feedback loop
docs/references/     Authored chains and controlled skill variants
configs/providers/   Model/provider configuration templates
scripts/             Chain runner and reference-candidate replay
```

Each reference candidate has a `candidate_manifest.json` and its authored `SKILL.md` files. Controlled variants are under each family's `ablations/` directory. See [reference materials](docs/references/README.md) for the layout and native-skill dependency rules.

The SkillsBench tasks and native skills come from a **separate SkillsBench checkout**. Where a reference candidate extends a native skill, the repository stores the authored addition and verifies the native document from that checkout before assembly.

## Quick start

Use Python 3.11 or newer. From the repository root, install the package:

```bash
python -m pip install -e .
```

List the included candidates, then inspect one without launching an agent or making an API request:

```bash
python scripts/replay_reference_candidate.py --list
python scripts/replay_reference_candidate.py \
  --candidate-manifest docs/references/file-modification/chains/xlsx-recover-data/candidate_manifest.json
```

To **execute** that candidate, provide a SkillsBench checkout with its runtime dependencies, set the credential environment variable required by your provider, and select a provider configuration:

```bash
export SKILLSBENCH_ROOT=/path/to/skillsbench
python scripts/replay_reference_candidate.py \
  --candidate-manifest docs/references/file-modification/chains/xlsx-recover-data/candidate_manifest.json \
  --provider-config configs/providers/deepseek-v4-flash.toml \
  --model deepseek-v4-flash \
  --execute
```

To generate and evaluate a new chain for a task in that checkout, initialize a run and pass the `run_root` printed by the first command to the optimizer:

```bash
agent-sec-lab skillsbench-chain init \
  --skillsbench-root "$SKILLSBENCH_ROOT" \
  --task YOUR_TASK_ID

agent-sec-lab skillsbench-chain optimize \
  --run RUN_ROOT_FROM_INIT \
  --max-iterations 3 \
  --generator-backend openai-compatible \
  --generator-config configs/providers/deepseek-v4-flash.toml \
  --execution-config configs/providers/deepseek-v4-flash.toml
```



