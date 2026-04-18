from __future__ import annotations

import abc
from collections.abc import Iterator

import attrs

from pr_change_tracker import storage
from pr_change_tracker.handlers import github as github_handlers

from . import _common


class PullRequestEvent(abc.ABC):
    @abc.abstractmethod
    def process(self) -> None: ...


@attrs.frozen
class _ClosedEvent(PullRequestEvent):
    pull_request: _common.PullRequest

    def process(self) -> None:
        pass


@attrs.frozen
class _ConvertedToDraftEvent(PullRequestEvent):
    pull_request: _common.PullRequest

    def process(self) -> None:
        pass


@attrs.frozen
class _EditedEvent(PullRequestEvent):
    pull_request: _common.PullRequest

    def process(self) -> None:
        pass


@attrs.frozen
class _OpenedEvent(PullRequestEvent):
    pull_request: _common.PullRequest

    def process(self) -> None:
        pass


@attrs.frozen
class _ReadyForReviewEvent(PullRequestEvent):
    pull_request: _common.PullRequest

    def process(self) -> None:
        pass


@attrs.frozen
class _ReopendEvent(PullRequestEvent):
    pull_request: _common.PullRequest

    def process(self) -> None:
        pass


@attrs.frozen
class _SynchronizeEvent(PullRequestEvent):
    pull_request: _common.PullRequest

    def process(self) -> None:
        pass


@attrs.frozen
class PullRequestProcessor:
    _storage: storage.CommonStorage

    def process(self, incoming: github_handlers.Incoming) -> Iterator[PullRequestEvent]:
        match incoming.action:
            case "closed":
                yield _ClosedEvent(
                    pull_request=_common.PullRequest.from_data(incoming.body),
                )

            case "converted_to_draft":
                yield _ConvertedToDraftEvent(
                    pull_request=_common.PullRequest.from_data(incoming.body),
                )

            case "edited":
                yield _EditedEvent(
                    pull_request=_common.PullRequest.from_data(incoming.body),
                )

            case "opened":
                yield _OpenedEvent(
                    pull_request=_common.PullRequest.from_data(incoming.body),
                )

            case "ready_for_review":
                yield _ReadyForReviewEvent(
                    pull_request=_common.PullRequest.from_data(incoming.body),
                )

            case "reopened":
                yield _ReopendEvent(
                    pull_request=_common.PullRequest.from_data(incoming.body),
                )

            case "synchronize":
                yield _SynchronizeEvent(
                    pull_request=_common.PullRequest.from_data(incoming.body),
                )

            # We don't care about these actions
            case "assigned":
                pass
            case "auto_merge_disabled":
                pass
            case "auto_merge_enabled":
                pass
            case "demilestoned":
                pass
            case "dequeued":
                pass
            case "enqueued":
                pass
            case "labeled":
                pass
            case "locked":
                pass
            case "milestoned":
                pass
            case "review_request_removed":
                pass
            case "review_requested":
                pass
            case "unassigned":
                pass
            case "unlabeled":
                pass
            case "unlocked":
                pass
            case _:
                raise github_handlers.GithubWebhookDropped(reason="Unknown action")
