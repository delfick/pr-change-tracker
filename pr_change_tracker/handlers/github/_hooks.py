from __future__ import annotations

import hashlib
import hmac
from collections.abc import Iterator
from typing import Protocol

import attrs

from ... import storage
from . import _errors, _event, _processors


def determine_expected_signature(secret: str, body: bytes) -> str:
    hash_object = hmac.new(secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256)
    return f"sha256={hash_object.hexdigest()}"


class _WithProcess(Protocol):
    async def process(self) -> None: ...


@attrs.frozen
class IncomingProcessor:
    _storage: storage.CommonStorage

    _pull_request_processor: _processors.PullRequestProcessor = attrs.field(
        default=attrs.Factory(
            lambda self: _processors.PullRequestProcessor(storage=self._storage), takes_self=True
        )
    )
    _pull_request_review_processor: _processors.PullRequestReviewProcessor = attrs.field(
        default=attrs.Factory(
            lambda self: _processors.PullRequestReviewProcessor(storage=self._storage),
            takes_self=True,
        )
    )

    def process(self, incoming: _event.Incoming, /) -> Iterator[_WithProcess]:
        match incoming.event:
            case "pull_request":
                yield from self._pull_request_processor.process(incoming)

            case "pull_request_review":
                yield from self._pull_request_review_processor.process(incoming)

            case _:
                raise _errors.GithubWebhookDropped(reason="Unrecognised webhook event")
