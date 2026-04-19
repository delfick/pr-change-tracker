import functools
import logging
import os
from collections.abc import Callable
from typing import Protocol

import click
import structlog

from . import events, http_server, protocols


class EnvSecret(click.ParamType):
    name = "env_secret"

    def convert(
        self, value: object, param: click.Parameter | None, ctx: click.Context | None
    ) -> str:
        if not isinstance(value, str):
            self.fail("Expect env value to be a str", param, ctx)
        if value.startswith("env:"):
            env_name = value[4:]
            from_env = os.environ.get(env_name)
            if from_env is None:
                raise self.fail(f"No value found for environment variable ${env_name}", param, ctx)
            value = from_env
        return value


def setup_logging(dev_logging: bool) -> protocols.Logger:
    timestamper = structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S")
    shared_processors: list[structlog.typing.Processor] = [
        # structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        # structlog.processors.StackInfoRenderer(),
        timestamper,
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    log = structlog.get_logger().bind()
    assert isinstance(log, structlog.stdlib.BoundLogger)

    # And make stdlib logging use structlog
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            *(
                (structlog.dev.ConsoleRenderer(),)
                if dev_logging
                else (structlog.processors.JSONRenderer(),)
            ),
        ],
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.propagate = False
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    return log


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
        logger: protocols.Logger,
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
    logger = setup_logging(dev_logging)
    server = server_constructor(
        postgres_url=postgres_url,
        github_webhook_secret=github_webhook_secret,
        debug_github_webhook_secret=debug_github_webhook_secret,
        port=port,
        logger=logger,
    )
    server.serve_forever()


class EventProcessorConstructor(Protocol):
    def __call__(self, *, logger: protocols.Logger, postgres_url: str) -> _WithServeForever: ...


def start_event_processor(
    *,
    postgres_url: str,
    dev_logging: bool,
    processor_constructor: EventProcessorConstructor,
) -> None:
    logger = setup_logging(dev_logging)
    processor = processor_constructor(
        logger=logger,
        postgres_url=postgres_url,
    )
    processor.serve_forever()


postgres_url_option = click.option(
    "--postgres-url",
    help="The url for the postgres database",
    default="env:PR_CHANGE_TRACKER_ALEMBIC_DB_URL",
    type=EnvSecret(),
)
dev_logging_option = click.option(
    "--dev-logging",
    is_flag=True,
    help="Print out the logs as human readable",
)


def http_server_args[**P_Args, T_Ret](func: Callable[P_Args, T_Ret]) -> Callable[P_Args, T_Ret]:
    @click.option(
        "--github-webhook-secret",
        help="The value of the secret for the github webhooks or 'env:NAME_OF_ENV_VAR'",
        default="env:PR_CHANGE_TRACKER_GITHUB_WEBHOOK_SECRET",
        type=EnvSecret(),
    )
    @click.option(
        "--provide-git-webhook-debug-endpoint",
        help="Used to enable an endpoint to print out full incoming http requests from the github webhook for test fixtures",
        is_flag=True,
    )
    @postgres_url_option
    @click.option(
        "--port",
        help="The port to expose the app from. Defaults to $PR_CHANGE_TRACKER_SERVER_PORT or 3000",
        default=os.environ.get("PR_CHANGE_TRACKER_SERVER_PORT", 3000),
        type=int,
    )
    @dev_logging_option
    @functools.wraps(func)
    def wrapped(*args: P_Args.args, **kwargs: P_Args.kwargs) -> T_Ret:
        return func(*args, **kwargs)

    return wrapped


@click.command
@http_server_args
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
        server_constructor=http_server.Server,
    )


@click.command
@postgres_url_option
@dev_logging_option
def event_processor(*, postgres_url: str, dev_logging: bool) -> None:
    return start_event_processor(
        postgres_url=postgres_url,
        dev_logging=dev_logging,
        processor_constructor=events.make_postgres_event_processor,
    )


@click.group(help="Interact with pr change tracker")
def main() -> None:
    pass


main.add_command(serve_http)
main.add_command(event_processor)
