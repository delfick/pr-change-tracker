from __future__ import annotations

import datetime
from collections.abc import Mapping, Sequence
from typing import Self

import attrs

from . import _enums


@attrs.frozen
class PullRequestDetails:
    pr_number: int
    repo_name: str
    org: str
    branch_name: str
    updated_at: datetime.datetime


@attrs.frozen
class CommitPair:
    head_ref: str
    head_sha: str
    base_ref: str
    base_sha: str


@attrs.frozen
class CommitPairs:
    head_sha_to_base_sha: Mapping[str, str]
    head_sha_to_ref: Mapping[str, str]
    base_sha_to_ref: Mapping[str, str]

    @classmethod
    def from_pairs(cls, pairs: Sequence[CommitPair]) -> Self:
        head_sha_to_base_sha: dict[str, str] = {}
        head_sha_to_ref: dict[str, str] = {}
        base_sha_to_ref: dict[str, str] = {}

        for pair in pairs:
            head_sha_to_base_sha[pair.head_sha] = pair.base_sha
            head_sha_to_ref[pair.head_sha] = pair.head_ref
            base_sha_to_ref[pair.base_sha] = pair.base_ref

        return cls(
            head_sha_to_base_sha=head_sha_to_ref,
            head_sha_to_ref=head_sha_to_ref,
            base_sha_to_ref=base_sha_to_ref,
        )


@attrs.frozen
class PullRequestUpdateDetails(PullRequestDetails):
    commit_pairs: CommitPairs


@attrs.frozen
class PullRequestStatusChangeDetails:
    status: _enums.PullRequestStatus

    occurred_at: datetime.datetime

    head_ref: str
    head_sha: str
    base_ref: str
    base_sha: str

    sender_id: int
    sender_login: str


@attrs.frozen
class PullRequestReviewChangeDetails:
    review_id: int
    state: _enums.ReviewState

    reviewer_id: int
    reviewer_login: str
