#!/usr/bin/env python3
"""Run the public SkillsBench generator -> execution -> evaluator workflow.

This is a small, stable convenience entry point over the package CLI. It does
not contain provider- or experiment-specific logic; all workflow options remain
available through ``agent-sec-lab skillsbench-chain --help``.

Examples:
  python scripts/run_chain.py init --skillsbench-root ../skillsbench --task xlsx-recover-data
  python scripts/run_chain.py optimize --run runs/skillsbench-chain/<run-id> --max-iterations 3
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


REPO_ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "pyproject.toml").is_file())


def main() -> int:
    command = [sys.executable, "-m", "agent_sec_lab.cli", "skillsbench-chain", *sys.argv[1:]]
    return subprocess.run(command, cwd=REPO_ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
