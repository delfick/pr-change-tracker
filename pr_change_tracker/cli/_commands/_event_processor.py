from __future__ import annotations

from typing import Protocol

import click

from pr_change_tracker import events, progress

from .. import _logging, _options


class _WithServeForever(Protocol):
    def serve_forever(self) -> None: ...


class EventProcessorConstructor(Protocol):
    def __call__(
        self,
        *,
        progress: progress.Progress,
        postgres_url: str,
        github_api_token: str,
        github_api_requester: str,
    ) -> _WithServeForever: ...


def start_event_processor(
    *,
    postgres_url: str,
    github_api_token: str,
    github_api_requester: str,
    dev_logging: bool,
    processor_constructor: EventProcessorConstructor,
) -> None:
    logger = _logging.setup_logging(dev_logging)
    processor = processor_constructor(
        progress=progress.Progress(logger=logger),
        github_api_token=github_api_token,
        github_api_requester=github_api_requester,
        postgres_url=postgres_url,
    )
    processor.serve_forever()


@click.command
@_options.CLIOptions.postgres_url_option
@_options.CLIOptions.dev_logging_option
@_options.CLIOptions.github_api_token_option
@_options.CLIOptions.github_api_requester_option
def event_processor(
    *, postgres_url: str, dev_logging: bool, github_api_token: str, github_api_requester: str
) -> None:
    return start_event_processor(
        postgres_url=postgres_url,
        dev_logging=dev_logging,
        github_api_token=github_api_token,
        github_api_requester=github_api_requester,
        processor_constructor=events.make_postgres_event_processor,
    )
