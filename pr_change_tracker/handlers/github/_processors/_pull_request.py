from __future__ import annotations

import abc
import datetime
from collections.abc import Iterator
from typing import ClassVar

import attrs
import jsonpath

from pr_change_tracker import storage
from pr_change_tracker.handlers import github as github_handlers

from . import _common


class PullRequestEvent(abc.ABC):
    @abc.abstractmethod
    def process(self) -> None: ...


class _Pointers:
    merge_commit_sha: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer(
        "/pull_request/merge_commit_sha"
    )


@attrs.frozen
class _MergedEvent(PullRequestEvent):
    pull_request: _common.PullRequest
    timestamps: _common.Timestamps
    sender: _common.Sender

    merged_at: datetime.datetime
    merge_commit_sha: str

    def process(self) -> None:
        pass


@attrs.frozen
class _ClosedEvent(PullRequestEvent):
    pull_request: _common.PullRequest
    timestamps: _common.Timestamps
    sender: _common.Sender

    merge_commit_sha: str

    def process(self) -> None:
        pass


@attrs.frozen
class _ConvertedToDraftEvent(PullRequestEvent):
    pull_request: _common.PullRequest
    timestamps: _common.Timestamps
    sender: _common.Sender

    def process(self) -> None:
        pass


@attrs.frozen
class _EditedEvent(PullRequestEvent):
    pull_request: _common.PullRequest
    timestamps: _common.Timestamps
    sender: _common.Sender

    def process(self) -> None:
        pass


@attrs.frozen
class _OpenedEvent(PullRequestEvent):
    pull_request: _common.PullRequest
    timestamps: _common.Timestamps
    sender: _common.Sender

    def process(self) -> None:
        pass


@attrs.frozen
class _ReadyForReviewEvent(PullRequestEvent):
    pull_request: _common.PullRequest
    timestamps: _common.Timestamps
    sender: _common.Sender

    def process(self) -> None:
        pass


@attrs.frozen
class _ReopendEvent(PullRequestEvent):
    pull_request: _common.PullRequest
    timestamps: _common.Timestamps
    sender: _common.Sender

    def process(self) -> None:
        pass


@attrs.frozen
class _SynchronizeEvent(PullRequestEvent):
    pull_request: _common.PullRequest
    timestamps: _common.Timestamps
    sender: _common.Sender

    def process(self) -> None:
        pass


@attrs.frozen
class PullRequestProcessor:
    _storage: storage.CommonStorage

    def process(self, incoming: github_handlers.Incoming) -> Iterator[PullRequestEvent]:
        match incoming.action:
            case "closed":
                timestamps = _common.Timestamps.from_data(incoming.body)
                merge_commit_sha = str(_Pointers.merge_commit_sha.resolve(incoming.body))

                if timestamps.merged_at is None:
                    yield _ClosedEvent(
                        pull_request=_common.PullRequest.from_data(incoming.body),
                        timestamps=timestamps,
                        sender=_common.Sender.from_data(incoming.body),
                        merge_commit_sha=merge_commit_sha,
                    )
                else:
                    yield _MergedEvent(
                        pull_request=_common.PullRequest.from_data(incoming.body),
                        timestamps=timestamps,
                        sender=_common.Sender.from_data(incoming.body),
                        merged_at=timestamps.merged_at,
                        merge_commit_sha=merge_commit_sha,
                    )

            case "converted_to_draft":
                yield _ConvertedToDraftEvent(
                    pull_request=_common.PullRequest.from_data(incoming.body),
                    timestamps=_common.Timestamps.from_data(incoming.body),
                    sender=_common.Sender.from_data(incoming.body),
                )

            case "edited":
                yield _EditedEvent(
                    pull_request=_common.PullRequest.from_data(incoming.body),
                    timestamps=_common.Timestamps.from_data(incoming.body),
                    sender=_common.Sender.from_data(incoming.body),
                )

            case "opened":
                yield _OpenedEvent(
                    pull_request=_common.PullRequest.from_data(incoming.body),
                    timestamps=_common.Timestamps.from_data(incoming.body),
                    sender=_common.Sender.from_data(incoming.body),
                )

            case "ready_for_review":
                yield _ReadyForReviewEvent(
                    pull_request=_common.PullRequest.from_data(incoming.body),
                    timestamps=_common.Timestamps.from_data(incoming.body),
                    sender=_common.Sender.from_data(incoming.body),
                )

            case "reopened":
                yield _ReopendEvent(
                    pull_request=_common.PullRequest.from_data(incoming.body),
                    timestamps=_common.Timestamps.from_data(incoming.body),
                    sender=_common.Sender.from_data(incoming.body),
                )

            case "synchronize":
                yield _SynchronizeEvent(
                    pull_request=_common.PullRequest.from_data(incoming.body),
                    timestamps=_common.Timestamps.from_data(incoming.body),
                    sender=_common.Sender.from_data(incoming.body),
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
