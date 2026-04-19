from __future__ import annotations

import datetime

import sqlalchemy
from sqlalchemy import orm

from . import _enums, _metadata


@orm.mapped_as_dataclass(_metadata.registry)
class PullRequest:
    __tablename__ = "pull_request"

    pr_number: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    repo_name: orm.Mapped[str] = orm.mapped_column()
    org: orm.Mapped[str] = orm.mapped_column()
    branch_name: orm.Mapped[str] = orm.mapped_column()


@orm.mapped_as_dataclass(_metadata.registry)
class PullRequestChangedEvent:
    __tablename__ = "pull_request_changed_event"

    id: orm.Mapped[_metadata.BigInt] = orm.mapped_column(init=False, primary_key=True)

    pr_updated_at: orm.Mapped[datetime.datetime] = orm.mapped_column()

    pr_number: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.ForeignKey(PullRequest.pr_number), init=False
    )
    pr: orm.Mapped[PullRequest] = orm.relationship()


@orm.mapped_as_dataclass(_metadata.registry)
class PullRequestState:
    __tablename__ = "pull_request_state"

    id: orm.Mapped[int] = orm.mapped_column(init=False, primary_key=True)

    pr_number: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.ForeignKey(PullRequest.pr_number), init=False
    )
    pr: orm.Mapped[PullRequest] = orm.relationship()
    status: orm.Mapped[_enums.PullRequestStatus] = orm.mapped_column()

    pr_updated_at: orm.Mapped[datetime.datetime] = orm.mapped_column(index=True)

    head_sha: orm.Mapped[str] = orm.mapped_column()
    head_ref: orm.Mapped[str] = orm.mapped_column()
    base_sha: orm.Mapped[str] = orm.mapped_column()
    base_ref: orm.Mapped[str] = orm.mapped_column()

    sender_id: orm.Mapped[int] = orm.mapped_column()
    sender_login: orm.Mapped[str] = orm.mapped_column()


@orm.mapped_as_dataclass(_metadata.registry)
class PullRequestReviewChange:
    __tablename__ = "pull_request_review_change"

    pr_state_id: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.ForeignKey(PullRequestState.id), init=False, primary_key=True
    )
    pr_state: orm.Mapped[PullRequestState] = orm.relationship()

    state: orm.Mapped[_enums.ReviewState] = orm.mapped_column()

    review_id: orm.Mapped[int] = orm.mapped_column()
    reviewer_id: orm.Mapped[int] = orm.mapped_column()
    reviewer_login: orm.Mapped[str] = orm.mapped_column()
