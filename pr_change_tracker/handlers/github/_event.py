from collections.abc import Mapping
from typing import Self, TypedDict

import attrs

from pr_change_tracker.protocols import Logger

from . import _errors


class _RawHeaders(TypedDict):
    delivery: str
    event: str
    hook_id: str
    hook_installation_target_id: str
    hook_installation_target_type: str


@attrs.frozen
class Incoming:
    # The json in the body of the request
    body: Mapping[str, object]

    # Logger instance already bound with relevant information
    logger: Logger

    # Name of the event that triggered the delivery.
    event: str

    # Unique identifier of the webhook.
    hook_id: str

    # A globally unique identifier (GUID) to identify the event.
    delivery: str

    # Unique identifier of the resource where the webhook was created.
    hook_installation_target_id: str

    # Type of resource where the webhook was created.
    hook_installation_target_type: str

    @classmethod
    def from_http_request(
        cls, headers: Mapping[str, str], body: Mapping[str, object], logger: Logger
    ) -> Self:

        def _get_header(name: str) -> str:
            value = headers.get(name)
            if not value:
                raise _errors.UnexpectedEmptyHeader(name=name)
            return value

        return cls(
            body=body,
            logger=logger,
            delivery=_get_header("x-github-delivery"),
            event=_get_header("x-github-event"),
            hook_id=_get_header("x-github-hook-id"),
            hook_installation_target_id=_get_header("x-github-hook-installation-target-id"),
            hook_installation_target_type=_get_header("x-github-hook-installation-target-type"),
        )

    @property
    def action(self) -> str | None:
        if not isinstance(action := self.body.get("action"), str):
            return None
        else:
            return action
