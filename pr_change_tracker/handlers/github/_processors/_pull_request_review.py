from __future__ import annotations

import abc
import datetime
from collections.abc import Iterator, Mapping
from typing import ClassVar, Literal, Self

import attrs
import jsonpath

from pr_change_tracker import storage
from pr_change_tracker.handlers import github as github_handlers

from . import _common


class PullRequestReviewEvent(abc.ABC):
    @abc.abstractmethod
    def process(self) -> None: ...


class _Pointers:
    review_id: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer("/review/id")
    review_submitted_at: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer(
        "/review/submitted_at"
    )
    review_commit_id: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer("/review/commit_id")
    review_state: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer("/review/state")


def _as_int(value: object) -> int:
    assert isinstance(value, int)
    return value


@attrs.frozen
class _Review:
    review_id: int
    submitted_at: datetime.datetime
    commit_id: str
    state: Literal["changes_requested", "approved"]

    @classmethod
    def from_data(cls, data: Mapping[str, object]) -> Self | None:
        match state := _Pointers.review_state.resolve(data):
            case "changes_requested" | "approved":
                return cls(
                    review_id=_as_int(_Pointers.review_id.resolve(data)),
                    submitted_at=datetime.datetime.fromisoformat(
                        str(_Pointers.review_submitted_at.resolve(data))
                    ),
                    commit_id=str(_Pointers.review_commit_id.resolve(data)),
                    state=state,
                )

            case _:
                return None


@attrs.frozen
class _DismissedEvent(PullRequestReviewEvent):
    _storage: storage.CommonStorage

    pull_request: _common.PullRequest
    timestamps: _common.Timestamps
    sender: _common.Sender

    def process(self) -> None:
        pass


@attrs.frozen
class _SubmittedEvent(PullRequestReviewEvent):
    _storage: storage.CommonStorage

    pull_request: _common.PullRequest
    review: _Review
    timestamps: _common.Timestamps
    sender: _common.Sender

    def process(self) -> None:
        pass


@attrs.frozen
class PullRequestReviewProcessor:
    _storage: storage.CommonStorage

    def process(self, incoming: github_handlers.Incoming) -> Iterator[PullRequestReviewEvent]:
        match incoming.action:
            case "dismissed":
                yield _DismissedEvent(
                    storage=self._storage,
                    pull_request=_common.PullRequest.from_data(incoming.body),
                    timestamps=_common.Timestamps.from_data(incoming.body),
                    sender=_common.Sender.from_data(incoming.body),
                )

            case "submitted":
                review = _Review.from_data(incoming.body)
                if review is not None:
                    yield _SubmittedEvent(
                        storage=self._storage,
                        review=review,
                        pull_request=_common.PullRequest.from_data(incoming.body),
                        timestamps=_common.Timestamps.from_data(incoming.body),
                        sender=_common.Sender.from_data(incoming.body),
                    )

            case "edited":
                # Don't care for edited
                pass

            case _:
                raise github_handlers.GithubWebhookDropped(reason="Unknown action")
