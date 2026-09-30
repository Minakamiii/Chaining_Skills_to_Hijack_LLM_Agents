from __future__ import annotations

from pathlib import Path
import hashlib
import json
import os
import shlex
import uuid

from harbor.agents.installed.base import with_prompt_template
from harbor.agents.installed.codex import Codex
from harbor.models.agent.context import AgentContext
from harbor.models.trial.paths import EnvironmentPaths

from agent_sec_lab.config import load_model_config
from agent_sec_lab.skillsbench_chain.defense_modes import DEFENSE_MODE_ENFORCE, DEFENSE_MODE_SHADOW
from agent_sec_lab.skillsbench_chain.execution.harbor_bridge import (
    build_codex_config_overrides,
    bridge_process_env,
    build_direct_provider_overrides,
    build_execution_instruction,
    model_uses_glm52_skill_discovery_preflight,
    provider_uses_direct_responses,
    render_bridge_script,
)
from agent_sec_lab.skillsbench_chain.execution.loop_guard import (
    DEFAULT_MAX_IDENTICAL_CALLS,
    DEFAULT_MAX_POLL_WAIT_RECOVERIES,
    LONG_WAIT_RESUME_PROMPT,
)


def _coerce_bool(value: bool | str) -> bool:
    if isinstance(value, bool):
        return value
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _tool_loop_guard_name(model: str) -> str:
    """Disable repeated-tool-call termination for every provider."""
    del model
    return ""


def _render_tool_loop_guard_command(
    *,
    guard_script: Path,
    sessions_dir: Path,
    target_pid_file: Path,
    diagnostic_path: Path,
    recovery_prefix: Path,
    codex_log_path: Path,
    guard_name: str,
    initial_command: str,
    resume_command: str,
) -> str:
    """Run Codex under a loop guard and resume an empty poll session once prompted."""
    return " ".join(
        [
            "set -euo pipefail;",
            "recovery_attempt=0;",
            "while :; do",
            f"rm -f {shlex.quote(target_pid_file.as_posix())} {shlex.quote(diagnostic_path.as_posix())};",
            "guard_resume_option='';",
            'if [ "$recovery_attempt" -gt 0 ]; then guard_resume_option="--skip-existing-events"; fi;',
            f"python3 {shlex.quote(guard_script.as_posix())}",
            f"--sessions-dir {shlex.quote(sessions_dir.as_posix())}",
            f"--target-pid-file {shlex.quote(target_pid_file.as_posix())}",
            f"--diagnostic-path {shlex.quote(diagnostic_path.as_posix())}",
            f"--max-repeats {DEFAULT_MAX_IDENTICAL_CALLS}",
            f"--guard-name {shlex.quote(guard_name)} $guard_resume_option &",
            "guard_pid=$!;",
            'cleanup_guard() { kill "$guard_pid" 2>/dev/null || true; wait "$guard_pid" 2>/dev/null || true; };',
            "trap cleanup_guard EXIT INT TERM;",
            'if [ "$recovery_attempt" -eq 0 ]; then',
            f"( exec {initial_command} ) > {shlex.quote(codex_log_path.as_posix())} 2>&1 < /dev/null &",
            "else",
            f"( exec {resume_command} ) >> {shlex.quote(codex_log_path.as_posix())} 2>&1 < /dev/null &",
            "fi;",
            "codex_pid=$!;",
            f'printf "%s\n" "$codex_pid" > {shlex.quote(target_pid_file.as_posix())};',
            'set +e; wait "$codex_pid"; codex_status=$?; set -e;',
            'wait "$guard_pid" 2>/dev/null || true;',
            f"if [ -f {shlex.quote(diagnostic_path.as_posix())} ] &&",
            f"grep -q '\"recovery_requested\": true' {shlex.quote(diagnostic_path.as_posix())} &&",
            f'[ "$recovery_attempt" -lt {DEFAULT_MAX_POLL_WAIT_RECOVERIES} ]; then',
            f'cp {shlex.quote(diagnostic_path.as_posix())} {shlex.quote(recovery_prefix.as_posix())}-"$((recovery_attempt + 1))".json;',
            "recovery_attempt=$((recovery_attempt + 1));",
            "continue;",
            "fi;",
            f"if [ -f {shlex.quote(diagnostic_path.as_posix())} ]; then cat {shlex.quote(diagnostic_path.as_posix())} >&2; exit 75; fi;",
            'exit "$codex_status";',
            "done",
        ]
    )


class DeepSeekCodex(Codex):
    """Harbor custom agent that runs Codex against either a direct Responses provider or a local bridge."""

    @staticmethod
    def name() -> str:
        return "deepseek-codex"

    def __init__(
        self,
        logs_dir: Path,
        model_name: str | None = None,
        provider_config_path: str = "configs/providers/deepseek-v4-flash.toml",
        bridge_port: int = 8765,
        global_skill_artifact_distrust: bool | str = False,
        global_skill_artifact_distrust_mode: str = "",
        global_skill_artifact_distrust_skill_names_json: str | list[str] = "[]",
        *args,
        **kwargs,
    ) -> None:
        super().__init__(logs_dir=logs_dir, model_name=model_name, *args, **kwargs)
        self._provider_config_path = provider_config_path
        self._bridge_port = int(bridge_port)
        requested_mode = str(global_skill_artifact_distrust_mode or "").strip().casefold()
        if not requested_mode and _coerce_bool(global_skill_artifact_distrust):
            requested_mode = DEFENSE_MODE_ENFORCE
        mode_aliases = {
            "shadow": DEFENSE_MODE_SHADOW,
            "no_defense_shadow_tracking": DEFENSE_MODE_SHADOW,
            "enforce": DEFENSE_MODE_ENFORCE,
            "global_skill_artifact_distrust": DEFENSE_MODE_ENFORCE,
            "": "",
        }
        if requested_mode not in mode_aliases:
            raise ValueError(f"unknown global skill-artifact distrust mode: {global_skill_artifact_distrust_mode!r}")
        self._global_skill_artifact_distrust_mode = mode_aliases[requested_mode]
        self._global_skill_artifact_distrust = self._global_skill_artifact_distrust_mode == DEFENSE_MODE_ENFORCE
        raw_skill_names = global_skill_artifact_distrust_skill_names_json
        if isinstance(raw_skill_names, str):
            loaded_skill_names = json.loads(raw_skill_names or "[]")
        elif isinstance(raw_skill_names, list):
            loaded_skill_names = raw_skill_names
        else:
            raise ValueError(
                "global_skill_artifact_distrust_skill_names_json must be a JSON string array or string array"
            )
        if not isinstance(loaded_skill_names, list) or not all(
            isinstance(item, str) and item.strip() for item in loaded_skill_names
        ):
            raise ValueError(
                "global_skill_artifact_distrust_skill_names_json must be a JSON string array or string array"
            )
        self._global_skill_artifact_distrust_skill_names = tuple(
            dict.fromkeys(item.strip() for item in loaded_skill_names)
        )

    async def install(self, environment) -> None:
        """Guarantee the bridge and Codex toolchain before agent execution.

        A task image can have neither Python nor a writable global npm prefix.
        Install missing prerequisites as root once, then verify the exact Codex
        binary that the non-root agent will invoke. The bridge uses Python's
        standard-library HTTP client, so ``curl`` is not a prerequisite. This
        preserves the read-only pinned-binary fast path and never bootstraps
        nvm from GitHub.
        """
        version_spec = f"@{self._version}" if self._version else "@0.147.0"
        await self.exec_as_root(
            environment,
            command=(
                "set -euo pipefail; "
                "if command -v python3 >/dev/null 2>&1 && { command -v codex >/dev/null 2>&1 || command -v npm >/dev/null 2>&1; }; then exit 0; fi; "
                "if command -v apt-get >/dev/null 2>&1; then apt-get update && apt-get install -y python3 nodejs npm; exit 0; fi; "
                "if command -v apk >/dev/null 2>&1; then apk add --no-cache python3 nodejs npm; exit 0; fi; "
                "if command -v dnf >/dev/null 2>&1; then dnf -y install python3 nodejs npm; exit 0; fi; "
                "if command -v yum >/dev/null 2>&1; then yum install -y python3 nodejs npm; exit 0; fi; "
                "echo 'python3 and Codex/npm are required but no supported package manager exists' >&2; exit 1"
            ),
            env={"DEBIAN_FRONTEND": "noninteractive"},
        )
        install_script = (
            "set -euo pipefail\n"
            "command -v python3 >/dev/null 2>&1 || { echo 'python3 is required for the provider bridge' >&2; exit 1; }\n"
            "if command -v codex >/dev/null 2>&1; then codex --version; exit 0; fi\n"
            "command -v npm >/dev/null 2>&1 || { echo 'npm is required to install Codex' >&2; exit 1; }\n"
            f"npm install -g @openai/codex{version_spec}\n"
            "codex --version\n"
        )
        await self.exec_as_root(environment, command=f"bash -lc {shlex.quote(install_script)}")
        await self.exec_as_root(
            environment,
            command=(
                "for bin in node codex; do "
                'BIN_PATH="$(command -v \"$bin\" 2>/dev/null || true)"; '
                'if [ -n "$BIN_PATH" ] && [ "$BIN_PATH" != "/usr/local/bin/$bin" ]; then '
                'ln -sf "$BIN_PATH" "/usr/local/bin/$bin"; fi; '
                "done"
            ),
        )

    @with_prompt_template
    async def run(self, instruction: str, environment, context: AgentContext) -> None:
        provider_config = load_model_config(Path(self._provider_config_path))
        if provider_config.reasoning_effort is not None:
            self._resolved_flags["reasoning_effort"] = provider_config.reasoning_effort
        if provider_config.reasoning_summary is not None:
            self._resolved_flags["reasoning_summary"] = provider_config.reasoning_summary
        provider_key = self._get_env(provider_config.api_key_env) or os.environ.get(provider_config.api_key_env, "")
        if not provider_key:
            raise RuntimeError(f"Environment variable {provider_config.api_key_env} is empty")

        model = self.model_name or provider_config.model
        env = {
            "CODEX_HOME": EnvironmentPaths.agent_dir.as_posix(),
            provider_config.api_key_env: provider_key,
        }
        provider_env = bridge_process_env(env, bypass_proxy=provider_config.bypass_proxy)
        bridge_dir = EnvironmentPaths.agent_dir / "skillsbench-chain-bridge"
        using_bridge = not provider_uses_direct_responses(provider_config)
        if using_bridge:
            bridge_token = "bridge-" + uuid.uuid4().hex
            bridge_script = bridge_dir / "bridge.py"
            bridge_log = bridge_dir / "bridge.log"
            escaped_script = shlex.quote(render_bridge_script())
            await self.exec_as_agent(
                environment,
                command=f"mkdir -p {bridge_dir.as_posix()} && printf %s {escaped_script} > {bridge_script.as_posix()}",
            )

            bridge_env = dict(provider_env)
            bridge_env["CODEX_PROVIDER_BRIDGE_API_KEY"] = bridge_token
            bridge_extra_body = shlex.quote(json.dumps(provider_config.extra_body, separators=(",", ":")))
            bridge_extra_headers = shlex.quote(json.dumps(provider_config.extra_headers, separators=(",", ":")))
            bridge_usage_log = bridge_dir / "usage.jsonl"
            await self.exec_as_agent(
                environment,
                command=(
                    f"python3 {bridge_script.as_posix()} "
                    f"--host 127.0.0.1 --port {self._bridge_port} "
                    f"--model {shlex.quote(provider_config.model)} "
                    f"--provider-base-url {shlex.quote(provider_config.base_url)} "
                    f"--provider-api-key-env {shlex.quote(provider_config.api_key_env)} "
                    f"--bridge-api-key-env CODEX_PROVIDER_BRIDGE_API_KEY "
                    f"--timeout-seconds {provider_config.timeout_seconds} "
                    f"--temperature {provider_config.temperature} "
                    f"--context-max-input-chars {provider_config.context_max_input_chars} "
                    f"--context-tool-output-max-chars {provider_config.context_tool_output_max_chars} "
                    f"--extra-body-json {bridge_extra_body} "
                    f"--extra-headers-json {bridge_extra_headers} "
                    f"--usage-log {shlex.quote(bridge_usage_log.as_posix())} "
                    f"> {bridge_log.as_posix()} 2>&1 & echo $! > {(bridge_dir / 'bridge.pid').as_posix()}"
                ),
                env=bridge_env,
            )
            await self.exec_as_agent(
                environment,
                command=(
                    "python3 - <<'PY'\n"
                    "import time, urllib.request\n"
                    f"url='http://127.0.0.1:{self._bridge_port}/health'\n"
                    "for _ in range(50):\n"
                    "    try:\n"
                    "        print(urllib.request.urlopen(url, timeout=1).read().decode())\n"
                    "        raise SystemExit(0)\n"
                    "    except Exception:\n"
                    "        time.sleep(0.1)\n"
                    "raise SystemExit('bridge health check failed')\n"
                    "PY"
                ),
            )
            codex_flags = build_codex_config_overrides(
                provider_name="skillsbench-chain-bridge",
                display_name="SkillsBench Chain Bridge",
                base_url=f"http://127.0.0.1:{self._bridge_port}/v1",
                env_key="CODEX_PROVIDER_BRIDGE_API_KEY",
            )
            provider_env["CODEX_PROVIDER_BRIDGE_API_KEY"] = bridge_token
        else:
            codex_flags = build_direct_provider_overrides(provider_config)

        # Web search is unavailable in the execution sandbox, and some models
        # (e.g. claude-sonnet-5) burn their first turn calling it, which fails
        # with "temporarily unavailable" and ends the run with zero work done.
        # Disable the tool entirely (WebSearchMode::Disabled).
        codex_flags += " -c web_search=disabled"

        taint_registry_path = ""
        skill_lease_command = ""
        if self._global_skill_artifact_distrust_mode:
            from agent_sec_lab.skillsbench_chain.global_artifact_distrust import (
                DEFAULT_EXCLUDE_PREFIXES,
                DEFAULT_WORKSPACE_ROOTS,
                DEFENSE_AGENT_REGISTRY_PATH,
                DEFENSE_SKILL_LEASE_SOCKET_PATH,
                SKILL_LEASE_COMMAND_PATH,
                render_skill_lease_helper,
                render_supervisor_script,
            )
            taint_registry_path = (
                DEFENSE_AGENT_REGISTRY_PATH.as_posix()
                if self._global_skill_artifact_distrust
                else ""
            )
            skill_lease_command = SKILL_LEASE_COMMAND_PATH.as_posix()
        rendered_instruction = build_execution_instruction(
            instruction,
            include_skill_discovery_preflight=model_uses_glm52_skill_discovery_preflight(model),
            global_skill_artifact_distrust=self._global_skill_artifact_distrust,
            taint_registry_path=taint_registry_path,
            skill_lease_command=skill_lease_command,
        )
        escaped_instruction = shlex.quote(rendered_instruction)
        cli_flags = self.build_cli_flags()
        cli_flags_arg = (cli_flags + " ") if cli_flags else ""
        codex_command = (
            "codex exec "
            "--dangerously-bypass-approvals-and-sandbox "
            "--skip-git-repo-check "
            f"--model {shlex.quote(model)} "
            "--json "
            "--enable unified_exec "
            f"{codex_flags} "
            f"{cli_flags_arg}"
            "-- "
            f"{escaped_instruction}"
        )
        resume_command = (
            "codex exec resume --last "
            "--dangerously-bypass-approvals-and-sandbox "
            "--skip-git-repo-check "
            f"--model {shlex.quote(model)} "
            "--json "
            "--enable unified_exec "
            f"{codex_flags} "
            f"{cli_flags_arg}"
            "-- "
            f"{shlex.quote(LONG_WAIT_RESUME_PROMPT)}"
        )
        if self._global_skill_artifact_distrust_mode:
            defense_dir = EnvironmentPaths.agent_dir / "global-skill-artifact-distrust"
            supervisor_script = defense_dir / "supervisor.py"
            registry_path = defense_dir / "taint-registry.json"
            codex_log_path = EnvironmentPaths.agent_dir / "codex.txt"
            escaped_supervisor = shlex.quote(render_supervisor_script())
            escaped_lease_helper = shlex.quote(render_skill_lease_helper(DEFENSE_SKILL_LEASE_SOCKET_PATH))
            await self.exec_as_root(
                environment,
                command=(
                    f"mkdir -p {shlex.quote(DEFENSE_AGENT_REGISTRY_PATH.parent.as_posix())} "
                    f"&& chmod 0777 {shlex.quote(DEFENSE_AGENT_REGISTRY_PATH.parent.as_posix())} "
                    f"&& printf %s {escaped_lease_helper} > {shlex.quote(SKILL_LEASE_COMMAND_PATH.as_posix())} "
                    f"&& chmod 0555 {shlex.quote(SKILL_LEASE_COMMAND_PATH.as_posix())}"
                ),
            )
            await self.exec_as_agent(
                environment,
                command=(
                    f"mkdir -p {shlex.quote(defense_dir.as_posix())} "
                    f"&& printf %s {escaped_supervisor} > {shlex.quote(supervisor_script.as_posix())}"
                ),
            )
            supervisor_args = [
                "python3",
                supervisor_script.as_posix(),
                "--registry-path",
                registry_path.as_posix(),
                "--projection-path",
                DEFENSE_AGENT_REGISTRY_PATH.as_posix(),
                "--log-path",
                codex_log_path.as_posix(),
                "--original-user-request-sha256",
                hashlib.sha256(instruction.encode("utf-8")).hexdigest(),
                "--require-skill-lease",
                "--skill-lease-socket",
                DEFENSE_SKILL_LEASE_SOCKET_PATH.as_posix(),
            ]
            for workspace_root in DEFAULT_WORKSPACE_ROOTS:
                supervisor_args.extend(["--workspace-root", workspace_root.as_posix()])
            for exclude_prefix in DEFAULT_EXCLUDE_PREFIXES:
                supervisor_args.extend(["--exclude-prefix", exclude_prefix.as_posix()])
            for skill_name in self._global_skill_artifact_distrust_skill_names:
                supervisor_args.extend(["--skill-name", skill_name])
            supervised_command = f"{shlex.join(supervisor_args)} -- {codex_command}"
            resume_supervised_command = f"{shlex.join(supervisor_args)} -- {resume_command}"
        else:
            supervised_command = codex_command
            resume_supervised_command = resume_command
        loop_guard_name = _tool_loop_guard_name(model)
        if loop_guard_name:
            source_guard = Path(__file__).resolve().with_name("loop_guard.py")
            guard_script = EnvironmentPaths.agent_dir / f"{loop_guard_name}_tool_loop_guard.py"
            target_pid_file = EnvironmentPaths.agent_dir / f"{loop_guard_name}-codex.pid"
            diagnostic_path = EnvironmentPaths.agent_dir / f"{loop_guard_name}-tool-loop-guard.json"
            recovery_prefix = EnvironmentPaths.agent_dir / f"{loop_guard_name}-tool-loop-recovery"
            codex_log_path = EnvironmentPaths.agent_dir / "codex.txt"
            escaped_guard = shlex.quote(source_guard.read_text(encoding="utf-8"))
            await self.exec_as_agent(
                environment,
                command=(
                    f"printf %s {escaped_guard} > {shlex.quote(guard_script.as_posix())} "
                    f"&& chmod 0700 {shlex.quote(guard_script.as_posix())}"
                ),
            )
            guarded_command = _render_tool_loop_guard_command(
                guard_script=guard_script,
                sessions_dir=EnvironmentPaths.agent_dir / "sessions",
                target_pid_file=target_pid_file,
                diagnostic_path=diagnostic_path,
                recovery_prefix=recovery_prefix,
                codex_log_path=codex_log_path,
                guard_name=loop_guard_name,
                initial_command=supervised_command,
                resume_command=resume_supervised_command,
            )
        else:
            guarded_command = (
                supervised_command
                if self._global_skill_artifact_distrust_mode
                else f"{supervised_command} 2>&1 </dev/null | tee {(EnvironmentPaths.agent_dir / 'codex.txt').as_posix()}"
            )
        try:
            await self.exec_as_agent(
                environment,
                command=(
                    "if [ -s ~/.nvm/nvm.sh ]; then . ~/.nvm/nvm.sh; fi; "
                    f"{guarded_command}"
                ),
                env=provider_env,
            )
        finally:
            if using_bridge:
                await environment.exec(
                    command=(
                        f"test -f {(bridge_dir / 'bridge.pid').as_posix()} "
                        f"&& kill $(cat {(bridge_dir / 'bridge.pid').as_posix()}) || true"
                    )
                )
