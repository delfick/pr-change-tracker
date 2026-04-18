import abc
import datetime

import attrs
import sqlalchemy.exc
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from . import _details, _enums, _pull_requests


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


@attrs.frozen
class PostgresStorage(CommonStorage):
    _engine: AsyncEngine

    async def _get_or_add_pull_request(
        self, *, session: AsyncSession, pr_number: int
    ) -> _pull_requests.PullRequest:
        try:
            pr = await session.get_one(_pull_requests.PullRequest, pr_number)
        except sqlalchemy.exc.NoResultFound:
            pr = _pull_requests.PullRequest(pr_number=pr_number)
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

    async def record_pull_request_status_change(
        self,
        *,
        pull_request: _details.PullRequestDetails,
        status_change: _details.PullRequestStatusChangeDetails,
    ) -> None:
        async with AsyncSession(self._engine) as session:
            async with session.begin():
                pr = await self._get_or_add_pull_request(
                    session=session, pr_number=pull_request.pr_number
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
                    session=session, pr_number=pull_request.pr_number
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
