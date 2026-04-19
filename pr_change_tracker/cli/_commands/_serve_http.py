from __future__ import annotations

from typing import Protocol

import click

from pr_change_tracker import http_server, progress

from .. import _logging, _options


class _WithServeForever(Protocol):
    def serve_forever(self) -> None: ...


class HttpServerConstructor(Protocol):
    def __call__(
        self,
        *,
        postgres_url: str,
        github_webhook_secret: str,
        debug_github_webhook_secret: str | None,
        port: int,
        progress: progress.Progress,
    ) -> _WithServeForever: ...


def start_http_server(
    *,
    github_webhook_secret: str,
    debug_github_webhook_secret: str | None,
    postgres_url: str,
    port: int,
    dev_logging: bool,
    server_constructor: HttpServerConstructor,
) -> None:
    logger = _logging.setup_logging(dev_logging)
    server = server_constructor(
        postgres_url=postgres_url,
        github_webhook_secret=github_webhook_secret,
        debug_github_webhook_secret=debug_github_webhook_secret,
        port=port,
        progress=progress.Progress(logger=logger),
    )
    server.serve_forever()


@click.command
@_options.CLIOptions.github_webhook_secret_option
@_options.CLIOptions.provide_git_webhook_debug_endpoint_option
@_options.CLIOptions.postgres_url_option
@_options.CLIOptions.port_option
@_options.CLIOptions.dev_logging_option
def serve_http(
    *,
    github_webhook_secret: str,
    provide_git_webhook_debug_endpoint: bool,
    postgres_url: str,
    port: int,
    dev_logging: bool,
) -> None:
    return start_http_server(
        github_webhook_secret=github_webhook_secret,
        debug_github_webhook_secret=(
            "b7e854dc539ed48f9f03ad01ed59f199d29922bd1959d75368"
            if provide_git_webhook_debug_endpoint
            else None
        ),
        postgres_url=postgres_url,
        port=port,
        dev_logging=dev_logging,
        server_constructor=http_server.make_server,
    )
