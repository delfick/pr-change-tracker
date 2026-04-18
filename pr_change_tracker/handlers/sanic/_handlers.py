import datetime
import hmac
import json
from collections.abc import Callable, Iterator
from typing import Protocol

import attrs
import sanic

from pr_change_tracker.protocols import Logger

from .. import github


class _WithProcess(Protocol):
    async def process(self) -> None: ...


class IncomingProcessor(Protocol):
    def __call__(self, incoming: github.Incoming, /) -> Iterator[_WithProcess]: ...


class ExpectedSignatureDeterminer(Protocol):
    def __call__(self, body: bytes) -> str: ...


async def print_hook(
    request: sanic.Request,
    *,
    debug_github_webhook_secret: str,
    printer: Callable[[str], None],
) -> sanic.response.HTTPResponse:
    printer("!!!!!!!!! START RECEIVED HOOK")
    printer("")

    printer(f"- {datetime.datetime.now(datetime.UTC).isoformat()}")
    printer(f"- {debug_github_webhook_secret}")
    printer("")

    for name, value in sorted(request.headers.items()):
        printer(f":{name}: {value}")
    printer("")

    for line in json.dumps(request.json, indent="  ", sort_keys=True).split("\n"):
        printer(line)

    printer("")
    printer("!!!!!!!!! END RECEIVED HOOK")
    return sanic.empty(200)


@attrs.frozen
class GithubWebhook:
    _logger: Logger

    _process_incoming: IncomingProcessor
    _determine_expected_signature: ExpectedSignatureDeterminer

    async def handle(self, request: sanic.Request) -> sanic.response.HTTPResponse:
        logger = self._logger
        if "x-github-delivery" in request.headers:
            logger = logger.bind(github_delivery=request.headers["x-github-delivery"])

        if not request.headers["user-agent"].startswith("GitHub-Hookshot/"):
            # Github documentation say the user agent should always start with this specific string
            logger.error("User agent field was incorrect", found=request.headers["user-agent"])
            return sanic.empty(400)

        try:
            hub_signature_256 = request.headers["x-hub-signature-256"]
        except KeyError:
            logger.error("No x-hub-signature-256 header provided")
            return sanic.empty(400)
        else:
            if not hub_signature_256:
                logger.error("No x-hub-signature-256 header provided")
                return sanic.empty(400)

        expected_signature = self._determine_expected_signature(request.body)
        if not hmac.compare_digest(expected_signature, hub_signature_256):
            logger.error("Request from github web hook has invalid signature")
            return sanic.empty(403)

        try:
            body: dict[str, object] = request.json
        except (TypeError, ValueError):
            logger.exception("Failed to parse the webhook body as json")
            return sanic.empty(500)

        try:
            incoming = github.Incoming.from_http_request(
                headers=request.headers, body=body, logger=logger
            )
        except github.UnexpectedEmptyHeader:
            logger.error("Webhook has unexpected empty values")
            return sanic.empty(400)

        try:
            for event in self._process_incoming(incoming):
                await event.process()
        except github.GithubWebhookDropped as e:
            logger.info("Event dropped", reason=e.reason)
            return sanic.empty()
        except github.GithubWebhookError:
            logger.exception("Failed to process webhook")
            return sanic.empty(500)
        else:
            return sanic.empty()
