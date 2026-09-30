# Chaining Skills to Hijack LLM Agents

Official implementation and experimental artifacts for:

> **Chaining Skills to Hijack LLM Agents**  

This repository contains the code, authored skill chains, evaluation pipeline,
and controlled variants used in our study of compositional security risks in
LLM-agent skill ecosystems.

We study how individually plausible skills can become harmful when composed
through intermediate artifacts and handoffs. In particular, we examine how
instructions and state introduced by upstream skills can influence downstream
tool use without requiring a single obviously malicious skill.

Our experiments cover six model families, five attack families, controlled
ablations, and a runtime defense evaluated on SkillsBench.

## Key findings

Our evaluation shows that compositional skill chains can substantially alter
agent behavior even when individual skills appear task-relevant in isolation.

Across 690 attack instances, the evaluated chains succeed in 512 cases
(74.2%). On GPT-5.4, the full compositional attack reaches an 84.3% attack
success rate, compared with 17.4% for a monolithic baseline.

Authorization ablations substantially reduce attack success, indicating that
apparent authorization carried through intermediate artifacts is an important
part of the attack mechanism.

For recurrent work-loop attacks, the generated workflows can also substantially
increase execution cost by repeatedly creating additional task-related work.

## Attack families

| Family | Objective |
|---|---|
| External Transfer | Cause selected task material to be sent to an external destination |
| Script Acquisition | Retrieve and execute a task-associated external malicious helper |
| File Modification | Cause unauthorized modification or deletion of task files |
| Output Tampering | Cause generated output to conflict with the task's authorized source or target |
| Work Loop | Repeatedly create additional task-related work through chained handoffs |

## Repository structure

```text
authority_promotion_explorer/
└── chaining_skill/
    ├── generation/       Candidate construction and provider-neutral prompts
    ├── execution/        Skill overlays and SkillsBench agent execution
    ├── evaluation/       Trace parsing, success checks, and utility evaluation
    └── optimizer.py      Generation → execution → feedback optimization loop

configs/
└── providers/            Model and provider configuration templates

docs/
└── references/
    ├── external-transfer/
    ├── script-acquisition/
    ├── file-modification/
    ├── output-tampering/
    └── work-loop/

scripts/
├── replay_reference_candidate.py
└── run_chain.py
```

Each reference candidate contains a candidate_manifest.json together with the
authored SKILL.md components needed to reconstruct the chain.

Controlled experimental variants are stored under the corresponding
ablations/ directory.

## Quick start

Use Python 3.11 or newer. From the repository root, install the package:

```bash
python -m pip install -e .
```

The repository supports three common workflows:

### 1. Inspect a reference chain

```bash
python scripts/replay_reference_candidate.py --list
```
### 2. Replay an authored reference candidate

```bash
python scripts/replay_reference_candidate.py \
  --candidate-manifest docs/references/file-modification/chains/xlsx-recover-data/candidate_manifest.json \
  --provider-config configs/providers/deepseek-v4-flash.toml \
  --model deepseek-v4-flash \
  --execute
```
### 3. Generate and optimize a new candidate

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
Exact model availability and provider configuration may differ from the
environment used for the paper.

# SkillsBench dependency

This repository does not vendor the full SkillsBench benchmark.

To execute reference candidates, clone SkillsBench separately and set:

```bash
export SKILLSBENCH_ROOT=/path/to/skillsbench
```

The replay pipeline uses this checkout to obtain:
- benchmark tasks;
- native skills;
- runtime tools;
- task fixtures and evaluation dependencies.
When a reference chain extends a native SkillsBench skill, the repository stores
only the authored extension and checks the corresponding native skill before
assembly.

## Models

The paper evaluates the attack across multiple model families, including:

- GPT-5.4
- DeepSeek
- Claude Sonnet
- Gemini 3.5 Flash
- Grok 4.5
- Kimi K2.6

Provider configuration templates are stored under `configs/providers/`.

Model names, API endpoints, and availability may change over time, so the
configuration files should be treated as templates rather than permanent API
specifications.

## Evaluation

The evaluation pipeline separates:

- attack success;
- task utility;
- endpoint or tool-call evidence;
- token usage;
- execution traces.

Attack success is determined from observable execution evidence rather than
from the model's textual claims alone.

Trace-based evaluation utilities are implemented in:

```text
authority_promotion_explorer/chaining_skill/evaluation/
```
## Run artifacts

Each experiment run records the artifacts required for later inspection,
including generated candidates, execution traces, evaluator outputs, and
iteration-level feedback.

A typical optimization run follows:

```text
candidate generation
        ↓
skill-chain assembly
        ↓
SkillsBench execution
        ↓
trace collection
        ↓
success / utility evaluation
        ↓
feedback
        ↓
next candidate
```

This makes the generation and evaluation process auditable independently of the
final aggregate metrics.

## Responsible use

This repository is intended for research on LLM-agent security, evaluation, and
defense. The reference chains are designed for controlled benchmark
environments. Users should avoid applying the techniques to systems or data for
which they do not have authorization.

## License

The code in this repository is released under the MIT License. See
[LICENSE](LICENSE) for details.

SkillsBench and third-party model APIs are governed by their respective
licenses and terms.

