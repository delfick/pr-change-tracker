from __future__ import annotations

import abc
import datetime
from collections.abc import Iterator, Mapping
from typing import ClassVar, Literal

import attrs
import jsonpath

from pr_change_tracker import storage
from pr_change_tracker.handlers import github as github_handlers

from . import _common


class InvalidClosedActionDetails(Exception):
    pass


class PullRequestEvent(abc.ABC):
    @abc.abstractmethod
    async def process(self) -> None: ...


class _Pointers:
    changed_base_ref: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer(
        "/changes/base/ref/from"
    )
    changed_base_sha: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer(
        "/changes/base/sha/from"
    )

    is_draft: ClassVar[jsonpath.JSONPointer] = jsonpath.JSONPointer("/pull_request/draft")


def _get_open_status(
    data: Mapping[str, object],
) -> Literal[storage.PullRequestStatus.DRAFT, storage.PullRequestStatus.READY_FOR_REVIEW]:
    is_draft = bool(_Pointers.is_draft.resolve(data))
    if is_draft:
        return storage.PullRequestStatus.DRAFT
    else:
        return storage.PullRequestStatus.READY_FOR_REVIEW


@attrs.frozen
class _StatusChangeEvent(PullRequestEvent):
    _storage: storage.CommonStorage

    pull_request: _common.PullRequest
    sender: _common.Sender
    head_and_base: _common.HeadAndBase

    occurred_at: datetime.datetime

    status: storage.PullRequestStatus

    async def process(self) -> None:
        await self._storage.record_pull_request_status_change(
            pull_request=storage.PullRequestDetails(
                pr_number=self.pull_request.pr_number,
                repo_name=self.pull_request.repo_name,
                org=self.pull_request.org,
                branch_name=self.pull_request.branch_name,
                updated_at=self.pull_request.updated_at,
            ),
            status_change=storage.PullRequestStatusChangeDetails(
                status=self.status,
                occurred_at=self.occurred_at,
                head_ref=self.head_and_base.head_ref,
                head_sha=self.head_and_base.head_sha,
                base_ref=self.head_and_base.base_ref,
                base_sha=self.head_and_base.base_sha,
                sender_id=self.sender.id,
                sender_login=self.sender.login,
            ),
        )


@attrs.frozen
class PullRequestProcessor:
    _storage: storage.CommonStorage

    def process(self, incoming: github_handlers.Incoming) -> Iterator[PullRequestEvent]:
        match incoming.action:
            case "closed":
                timestamps = _common.Timestamps.from_data(incoming.body)

                match (timestamps.closed_at, timestamps.merged_at):
                    case (datetime.datetime(), None):
                        yield _StatusChangeEvent(
                            storage=self._storage,
                            pull_request=_common.PullRequest.from_data(incoming.body),
                            sender=_common.Sender.from_data(incoming.body),
                            head_and_base=_common.HeadAndBase.from_data(incoming.body),
                            occurred_at=timestamps.closed_at,
                            status=storage.PullRequestStatus.CLOSED,
                        )
                    case (datetime.datetime(), datetime.datetime()):
                        yield _StatusChangeEvent(
                            storage=self._storage,
                            pull_request=_common.PullRequest.from_data(incoming.body),
                            sender=_common.Sender.from_data(incoming.body),
                            head_and_base=_common.HeadAndBase.from_data(incoming.body),
                            occurred_at=timestamps.merged_at,
                            status=storage.PullRequestStatus.MERGED,
                        )
                    case _:
                        raise InvalidClosedActionDetails

            case "converted_to_draft":
                pull_request = _common.PullRequest.from_data(incoming.body)
                yield _StatusChangeEvent(
                    storage=self._storage,
                    pull_request=pull_request,
                    sender=_common.Sender.from_data(incoming.body),
                    head_and_base=_common.HeadAndBase.from_data(incoming.body),
                    occurred_at=pull_request.updated_at,
                    status=storage.PullRequestStatus.DRAFT,
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
                    pull_request = _common.PullRequest.from_data(incoming.body)

                    yield _StatusChangeEvent(
                        storage=self._storage,
                        pull_request=pull_request,
                        sender=_common.Sender.from_data(incoming.body),
                        head_and_base=head_and_base,
                        occurred_at=pull_request.updated_at,
                        status=_get_open_status(incoming.body),
                    )

            case "opened":
                timestamps = _common.Timestamps.from_data(incoming.body)

                yield _StatusChangeEvent(
                    storage=self._storage,
                    pull_request=_common.PullRequest.from_data(incoming.body),
                    sender=_common.Sender.from_data(incoming.body),
                    head_and_base=_common.HeadAndBase.from_data(incoming.body),
                    occurred_at=timestamps.created_at,
                    status=_get_open_status(incoming.body),
                )

            case "ready_for_review":
                pull_request = _common.PullRequest.from_data(incoming.body)
                yield _StatusChangeEvent(
                    storage=self._storage,
                    pull_request=pull_request,
                    sender=_common.Sender.from_data(incoming.body),
                    head_and_base=_common.HeadAndBase.from_data(incoming.body),
                    occurred_at=pull_request.updated_at,
                    status=storage.PullRequestStatus.READY_FOR_REVIEW,
                )

            case "reopened":
                pull_request = _common.PullRequest.from_data(incoming.body)

                yield _StatusChangeEvent(
                    storage=self._storage,
                    pull_request=pull_request,
                    sender=_common.Sender.from_data(incoming.body),
                    head_and_base=_common.HeadAndBase.from_data(incoming.body),
                    occurred_at=pull_request.updated_at,
                    status=_get_open_status(incoming.body),
                )

            case "synchronize":
                pull_request = _common.PullRequest.from_data(incoming.body)
                yield _StatusChangeEvent(
                    storage=self._storage,
                    pull_request=pull_request,
                    sender=_common.Sender.from_data(incoming.body),
                    head_and_base=_common.HeadAndBase.from_data(incoming.body),
                    occurred_at=pull_request.updated_at,
                    status=_get_open_status(incoming.body),
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
