from __future__ import annotations

import abc
import collections
import contextlib
import datetime
from collections.abc import AsyncGenerator, AsyncIterator, Sequence

import attrs
import sqlalchemy.exc
from sqlalchemy import orm
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from . import _details, _enums, _pull_requests


class CommonPullRequestUpdater(abc.ABC):
    @abc.abstractmethod
    @contextlib.asynccontextmanager
    def update(
        self,
    ) -> AsyncGenerator[_details.PullRequestUpdateDetails]: ...


class CommonStorage(abc.ABC):
    @abc.abstractmethod
    async def record_pull_request_status_change(
        self,
        *,
        pull_request: _details.PullRequestDetails,
        status_change: _details.PullRequestStatusChangeDetails,
    ) -> None: ...

    @abc.abstractmethod
    async def record_pull_request_review_change(
        self,
        *,
        pull_request: _details.PullRequestDetails,
        status_change: _details.PullRequestStatusChangeDetails,
        review_change: _details.PullRequestReviewChangeDetails,
    ) -> None: ...

    @abc.abstractmethod
    def changed_pull_requests(self) -> AsyncIterator[CommonPullRequestUpdater]: ...


@attrs.frozen
class _PostgresPullRequestUpdater(CommonPullRequestUpdater):
    _engine: AsyncEngine

    _pr: _pull_requests.PullRequest
    _latest_updated_at: datetime.datetime

    _event_ids: Sequence[int]

    @contextlib.asynccontextmanager
    async def update(
        self,
    ) -> AsyncGenerator[_details.PullRequestUpdateDetails]:
        commit_pairs: list[_details.CommitPair] = []

        async with AsyncSession(self._engine) as session, session.begin():
            states = await session.scalars(
                sqlalchemy.select(_pull_requests.PullRequestState).where(
                    _pull_requests.PullRequestState.pr == self._pr
                )
            )
            for state in states:
                commit_pairs.append(
                    _details.CommitPair(
                        head_ref=state.head_ref,
                        head_sha=state.head_sha,
                        base_ref=state.base_ref,
                        base_sha=state.base_sha,
                    )
                )

            details = _details.PullRequestUpdateDetails(
                pr_number=self._pr.pr_number,
                repo_name=self._pr.repo_name,
                org=self._pr.org,
                branch_name=self._pr.branch_name,
                updated_at=self._latest_updated_at,
                commit_pairs=_details.CommitPairs.from_pairs(commit_pairs),
            )

            try:
                yield details
            finally:
                await session.execute(
                    sqlalchemy.delete(_pull_requests.PullRequestChangedEvent).where(
                        _pull_requests.PullRequestChangedEvent.id.in_(self._event_ids)
                    )
                )


@attrs.frozen
class PostgresStorage(CommonStorage):
    _engine: AsyncEngine

    async def _get_or_add_pull_request(
        self,
        *,
        session: AsyncSession,
        pr_number: int,
        repo_name: str,
        org: str,
        branch_name: str,
    ) -> _pull_requests.PullRequest:
        try:
            pr = await session.get_one(_pull_requests.PullRequest, pr_number)
        except sqlalchemy.exc.NoResultFound:
            pr = _pull_requests.PullRequest(
                pr_number=pr_number, repo_name=repo_name, org=org, branch_name=branch_name
            )
            session.add(pr)

        return pr

    def _add_status_change(
        self,
        *,
        session: AsyncSession,
        pr: _pull_requests.PullRequest,
        updated_at: datetime.datetime,
        head_sha: str,
        head_ref: str,
        base_sha: str,
        base_ref: str,
        status: _enums.PullRequestStatus,
        sender_id: int,
        sender_login: str,
    ) -> _pull_requests.PullRequestState:
        state = _pull_requests.PullRequestState(
            pr=pr,
            pr_updated_at=updated_at,
            head_sha=head_sha,
            head_ref=head_ref,
            base_sha=base_sha,
            base_ref=base_ref,
            status=status,
            sender_id=sender_id,
            sender_login=sender_login,
        )
        session.add(state)
        return state

    def _add_pull_request_changed_event(
        self,
        *,
        session: AsyncSession,
        pr: _pull_requests.PullRequest,
        pr_updated_at: datetime.datetime,
    ) -> None:
        session.add(_pull_requests.PullRequestChangedEvent(pr=pr, pr_updated_at=pr_updated_at))

    async def record_pull_request_status_change(
        self,
        *,
        pull_request: _details.PullRequestDetails,
        status_change: _details.PullRequestStatusChangeDetails,
    ) -> None:
        async with AsyncSession(self._engine) as session:
            async with session.begin():
                pr = await self._get_or_add_pull_request(
                    session=session,
                    pr_number=pull_request.pr_number,
                    repo_name=pull_request.repo_name,
                    org=pull_request.org,
                    branch_name=pull_request.branch_name,
                )
                self._add_status_change(
                    session=session,
                    pr=pr,
                    updated_at=pull_request.updated_at,
                    head_sha=status_change.head_sha,
                    head_ref=status_change.head_ref,
                    base_sha=status_change.base_sha,
                    base_ref=status_change.base_ref,
                    status=status_change.status,
                    sender_id=status_change.sender_id,
                    sender_login=status_change.sender_login,
                )
                self._add_pull_request_changed_event(
                    session=session, pr=pr, pr_updated_at=pull_request.updated_at
                )

    async def record_pull_request_review_change(
        self,
        *,
        pull_request: _details.PullRequestDetails,
        status_change: _details.PullRequestStatusChangeDetails,
        review_change: _details.PullRequestReviewChangeDetails,
    ) -> None:
        async with AsyncSession(self._engine) as session:
            async with session.begin():
                pr = await self._get_or_add_pull_request(
                    session=session,
                    pr_number=pull_request.pr_number,
                    repo_name=pull_request.repo_name,
                    org=pull_request.org,
                    branch_name=pull_request.branch_name,
                )
                pr_state = self._add_status_change(
                    session=session,
                    pr=pr,
                    updated_at=pull_request.updated_at,
                    head_sha=status_change.head_sha,
                    head_ref=status_change.head_ref,
                    base_sha=status_change.base_sha,
                    base_ref=status_change.base_ref,
                    status=status_change.status,
                    sender_id=status_change.sender_id,
                    sender_login=status_change.sender_login,
                )

                session.add(
                    _pull_requests.PullRequestReviewChange(
                        pr_state=pr_state,
                        review_id=review_change.review_id,
                        state=review_change.state,
                        reviewer_id=review_change.reviewer_id,
                        reviewer_login=review_change.reviewer_login,
                    )
                )
                self._add_pull_request_changed_event(
                    session=session, pr=pr, pr_updated_at=pull_request.updated_at
                )

    async def changed_pull_requests(self) -> AsyncIterator[_PostgresPullRequestUpdater]:
        async with AsyncSession(self._engine) as session:
            async with session.begin():
                events = (
                    await session.scalars(
                        sqlalchemy.select(_pull_requests.PullRequestChangedEvent).options(
                            orm.joinedload(_pull_requests.PullRequestChangedEvent.pr)
                        ),
                    )
                ).all()

                if not any(events):
                    return

                by_number: dict[int, _pull_requests.PullRequest] = {}
                by_pr: dict[int, list[int]] = collections.defaultdict(list)
                latest_updated_at = max(event.pr_updated_at for event in events)
                for event in events:
                    pr = event.pr
                    orm.make_transient(pr)
                    by_pr[pr.pr_number].append(event.id)
                    by_number[pr.pr_number] = pr

            for pr_number, event_ids in by_pr.items():
                yield _PostgresPullRequestUpdater(
                    engine=self._engine,
                    pr=by_number[pr_number],
                    latest_updated_at=latest_updated_at,
                    event_ids=event_ids,
                )
