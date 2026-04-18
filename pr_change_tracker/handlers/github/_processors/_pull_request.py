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

    changed_base_ref: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer(
        "/changes/base/ref/from"
    )
    changed_base_sha: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer(
        "/changes/base/sha/from"
    )


@attrs.frozen
class _MergedEvent(PullRequestEvent):
    _storage: storage.CommonStorage

    pull_request: _common.PullRequest
    timestamps: _common.Timestamps
    sender: _common.Sender
    head_and_base: _common.HeadAndBase

    merged_at: datetime.datetime
    merge_commit_sha: str

    def process(self) -> None:
        pass


@attrs.frozen
class _ClosedEvent(PullRequestEvent):
    _storage: storage.CommonStorage

    pull_request: _common.PullRequest
    timestamps: _common.Timestamps
    sender: _common.Sender
    head_and_base: _common.HeadAndBase

    merge_commit_sha: str

    def process(self) -> None:
        pass


@attrs.frozen
class _ConvertedToDraftEvent(PullRequestEvent):
    _storage: storage.CommonStorage

    pull_request: _common.PullRequest
    timestamps: _common.Timestamps
    sender: _common.Sender
    head_and_base: _common.HeadAndBase

    def process(self) -> None:
        pass


@attrs.frozen
class _BaseChangedEvent(PullRequestEvent):
    _storage: storage.CommonStorage

    pull_request: _common.PullRequest
    timestamps: _common.Timestamps
    sender: _common.Sender
    head_and_base: _common.HeadAndBase

    def process(self) -> None:
        pass


@attrs.frozen
class _OpenedEvent(PullRequestEvent):
    _storage: storage.CommonStorage

    pull_request: _common.PullRequest
    timestamps: _common.Timestamps
    sender: _common.Sender
    head_and_base: _common.HeadAndBase

    def process(self) -> None:
        pass


@attrs.frozen
class _ReadyForReviewEvent(PullRequestEvent):
    _storage: storage.CommonStorage

    pull_request: _common.PullRequest
    timestamps: _common.Timestamps
    sender: _common.Sender
    head_and_base: _common.HeadAndBase

    def process(self) -> None:
        pass


@attrs.frozen
class _ReopendEvent(PullRequestEvent):
    _storage: storage.CommonStorage

    pull_request: _common.PullRequest
    timestamps: _common.Timestamps
    sender: _common.Sender
    head_and_base: _common.HeadAndBase

    def process(self) -> None:
        pass


@attrs.frozen
class _SynchronizeEvent(PullRequestEvent):
    _storage: storage.CommonStorage

    pull_request: _common.PullRequest
    timestamps: _common.Timestamps
    sender: _common.Sender
    head_and_base: _common.HeadAndBase

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
                        storage=self._storage,
                        pull_request=_common.PullRequest.from_data(incoming.body),
                        timestamps=timestamps,
                        sender=_common.Sender.from_data(incoming.body),
                        head_and_base=_common.HeadAndBase.from_data(incoming.body),
                        merge_commit_sha=merge_commit_sha,
                    )
                else:
                    yield _MergedEvent(
                        storage=self._storage,
                        pull_request=_common.PullRequest.from_data(incoming.body),
                        timestamps=timestamps,
                        sender=_common.Sender.from_data(incoming.body),
                        head_and_base=_common.HeadAndBase.from_data(incoming.body),
                        merged_at=timestamps.merged_at,
                        merge_commit_sha=merge_commit_sha,
                    )

            case "converted_to_draft":
                yield _ConvertedToDraftEvent(
                    storage=self._storage,
                    pull_request=_common.PullRequest.from_data(incoming.body),
                    timestamps=_common.Timestamps.from_data(incoming.body),
                    sender=_common.Sender.from_data(incoming.body),
                    head_and_base=_common.HeadAndBase.from_data(incoming.body),
                )

            case "edited":
                changed_base_ref = _Pointers.changed_base_ref.resolve(incoming.body, default=None)
                changed_base_sha = _Pointers.changed_base_sha.resolve(incoming.body, default=None)
                head_and_base = _common.HeadAndBase.from_data(incoming.body)

                if (
                    changed_base_ref is not None
                    and changed_base_sha is not None
                    and (changed_base_ref, changed_base_sha)
                    != (
                        head_and_base.base_ref,
                        head_and_base.base_sha,
                    )
                ):
                    yield _BaseChangedEvent(
                        storage=self._storage,
                        pull_request=_common.PullRequest.from_data(incoming.body),
                        timestamps=_common.Timestamps.from_data(incoming.body),
                        sender=_common.Sender.from_data(incoming.body),
                        head_and_base=head_and_base,
                    )

            case "opened":
                yield _OpenedEvent(
                    storage=self._storage,
                    pull_request=_common.PullRequest.from_data(incoming.body),
                    timestamps=_common.Timestamps.from_data(incoming.body),
                    sender=_common.Sender.from_data(incoming.body),
                    head_and_base=_common.HeadAndBase.from_data(incoming.body),
                )

            case "ready_for_review":
                yield _ReadyForReviewEvent(
                    storage=self._storage,
                    pull_request=_common.PullRequest.from_data(incoming.body),
                    timestamps=_common.Timestamps.from_data(incoming.body),
                    sender=_common.Sender.from_data(incoming.body),
                    head_and_base=_common.HeadAndBase.from_data(incoming.body),
                )

            case "reopened":
                yield _ReopendEvent(
                    storage=self._storage,
                    pull_request=_common.PullRequest.from_data(incoming.body),
                    timestamps=_common.Timestamps.from_data(incoming.body),
                    sender=_common.Sender.from_data(incoming.body),
                    head_and_base=_common.HeadAndBase.from_data(incoming.body),
                )

            case "synchronize":
                yield _SynchronizeEvent(
                    storage=self._storage,
                    pull_request=_common.PullRequest.from_data(incoming.body),
                    timestamps=_common.Timestamps.from_data(incoming.body),
                    sender=_common.Sender.from_data(incoming.body),
                    head_and_base=_common.HeadAndBase.from_data(incoming.body),
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
