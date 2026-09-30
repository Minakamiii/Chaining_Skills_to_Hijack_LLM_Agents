from __future__ import annotations

from .compose import install_harbor_compose_service_filter


def main() -> None:
    install_harbor_compose_service_filter()
    from harbor.cli.main import app

    app()


if __name__ == "__main__":
    main()
