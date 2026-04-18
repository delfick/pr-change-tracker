from __future__ import annotations

import abc
from collections.abc import Iterator

import attrs

from pr_change_tracker import storage
from pr_change_tracker.handlers import github as github_handlers


class PullRequestReviewEvent(abc.ABC):
    @abc.abstractmethod
    def process(self) -> None: ...


@attrs.frozen
class _DismissedEvent(PullRequestReviewEvent):
    def process(self) -> None:
        pass


@attrs.frozen
class _SubmittedEvent(PullRequestReviewEvent):
    def process(self) -> None:
        pass


@attrs.frozen
class PullRequestReviewProcessor:
    _storage: storage.CommonStorage

    def process(self, incoming: github_handlers.Incoming) -> Iterator[PullRequestReviewEvent]:
        match incoming.action:
            case "dismissed":
                yield _DismissedEvent()

            case "submitted":
                yield _SubmittedEvent()

            case "edited":
                # Don't care for edited
                pass

            case _:
                raise github_handlers.GithubWebhookDropped(reason="Unknown action")
