from __future__ import annotations

import datetime

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
