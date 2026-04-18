from __future__ import annotations

import abc
import datetime
from collections.abc import Iterator, Mapping
from typing import ClassVar, Self

import attrs
import jsonpath

from pr_change_tracker import storage
from pr_change_tracker.handlers import github as github_handlers

from . import _common


class UnknownState(Exception):
    pass


class PullRequestReviewEvent(abc.ABC):
    @abc.abstractmethod
    async def process(self) -> None: ...


class _Pointers:
    review_id: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer("/review/id")
    review_submitted_at: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer(
        "/review/submitted_at"
    )
    review_commit_id: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer("/review/commit_id")
    review_state: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer("/review/state")
    reviewer_id: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer("/review/user/id")
    reviewer_login: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer("/review/user/login")

    state: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer("/pull_request/state")
    is_draft: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer("/pull_request/draft")
    is_merged: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer("/pull_request/merged")


def _as_int(value: object) -> int:
    assert isinstance(value, int)
    return value


@attrs.frozen
class _Review:
    review_id: int

    commit_id: str
    submitted_at: datetime.datetime
    state: storage.ReviewState

    reviewer_id: int
    reviewer_login: str

    @classmethod
    def from_data(cls, data: Mapping[str, object]) -> Self | None:
        match state := _Pointers.review_state.resolve(data):
            case "changes_requested" | "approved" | "dismissed":
                return cls(
                    review_id=_as_int(_Pointers.review_id.resolve(data)),
                    commit_id=str(_Pointers.review_commit_id.resolve(data)),
                    submitted_at=datetime.datetime.fromisoformat(
                        str(_Pointers.review_submitted_at.resolve(data))
                    ),
                    state=storage.ReviewState(state),
                    reviewer_id=_as_int(_Pointers.reviewer_id.resolve(data)),
                    reviewer_login=str(_Pointers.reviewer_login.resolve(data)),
                )

            case _:
                return None


def _pull_request_status(data: Mapping[str, object]) -> storage.PullRequestStatus:
    state = str(_Pointers.state.resolve(data))
    is_draft = bool(_Pointers.is_draft.resolve(data))
    is_merged = bool(_Pointers.is_draft.resolve(data))
    match state:
        case "open":
            if is_draft:
                return storage.PullRequestStatus.DRAFT
            else:
                return storage.PullRequestStatus.READY_FOR_REVIEW
        case "closed":
            if is_merged:
                return storage.PullRequestStatus.MERGED
            else:
                return storage.PullRequestStatus.CLOSED
        case _:
            raise UnknownState


@attrs.frozen
class _ReviewChangedEvent(PullRequestReviewEvent):
    _storage: storage.CommonStorage

    pull_request: _common.PullRequest
    review: _Review
    head_and_base: _common.HeadAndBase
    sender: _common.Sender

    status: storage.PullRequestStatus

    async def process(self) -> None:
        await self._storage.record_pull_request_review_change(
            pull_request=storage.PullRequestDetails(
                pr_number=self.pull_request.pr_number,
                repo_name=self.pull_request.repo_name,
                org=self.pull_request.org,
                branch_name=self.pull_request.branch_name,
                updated_at=self.pull_request.updated_at,
            ),
            status_change=storage.PullRequestStatusChangeDetails(
                status=self.status,
                head_ref=self.head_and_base.head_ref,
                head_sha=self.head_and_base.head_sha,
                base_ref=self.head_and_base.base_ref,
                base_sha=self.head_and_base.base_sha,
                occurred_at=self.review.submitted_at,
                sender_id=self.sender.id,
                sender_login=self.sender.login,
            ),
            review_change=storage.PullRequestReviewChangeDetails(
                review_id=self.review.review_id,
                state=self.review.state,
                reviewer_id=self.review.reviewer_id,
                reviewer_login=self.review.reviewer_login,
            ),
        )


@attrs.frozen
class PullRequestReviewProcessor:
    _storage: storage.CommonStorage

    def process(self, incoming: github_handlers.Incoming) -> Iterator[PullRequestReviewEvent]:
        match incoming.action:
            case "dismissed" | "submitted":
                review = _Review.from_data(incoming.body)
                if review is not None:
                    yield _ReviewChangedEvent(
                        storage=self._storage,
                        review=review,
                        sender=_common.Sender.from_data(incoming.body),
                        pull_request=_common.PullRequest.from_data(incoming.body),
                        head_and_base=_common.HeadAndBase.from_data(incoming.body),
                        status=_pull_request_status(incoming.body),
                    )

            case "edited":
                # Don't care for edited
                pass

            case _:
                raise github_handlers.GithubWebhookDropped(reason="Unknown action")
