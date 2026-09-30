from __future__ import annotations

import re


_COMPOSE_SERVICE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


def parse_compose_service_names(stdout: str | None) -> set[str]:
    """Return only valid service names from ``docker compose config --services``.

    Compose may send interpolation warnings to stdout. Harbor 0.3.0 accepted
    every non-empty output line as a service name, then attempted to start a
    container named after the warning. Service names have a restricted syntax,
    so filtering the command output retains valid Compose services while safely
    discarding diagnostics.
    """
    return {
        line.strip()
        for line in (stdout or "").splitlines()
        if _COMPOSE_SERVICE_NAME.fullmatch(line.strip())
    }


def install_harbor_compose_service_filter() -> None:
    """Install the Harbor 0.3.0 compatibility patch once for this CLI process."""
    from harbor.environments.docker.docker import DockerEnvironment

    if getattr(DockerEnvironment, "_agent_sec_lab_compose_filter_installed", False):
        return

    async def _compose_service_names(self: object, *args: str) -> set[str]:
        if args:
            raise ValueError("_compose_service_names no longer accepts runtime filters")
        result = await self._run_docker_compose_command(["config", "--services"])
        stdout = result.stdout or ""
        service_names = parse_compose_service_names(stdout)
        discarded = [line.strip() for line in stdout.splitlines() if line.strip() and line.strip() not in service_names]
        if discarded:
            self.logger.warning("Ignoring non-service Docker Compose output: %s", " | ".join(discarded))
        return service_names

    DockerEnvironment._compose_service_names = _compose_service_names
    DockerEnvironment._agent_sec_lab_compose_filter_installed = True
