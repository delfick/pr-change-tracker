import contextlib
from collections.abc import AsyncGenerator, AsyncIterator

import attrs

from pr_change_tracker import storage


@attrs.frozen
class _PullRequestUpdater(storage.CommonPullRequestUpdater):
    @contextlib.asynccontextmanager
    async def update(
        self,
    ) -> AsyncGenerator[tuple[storage.PullRequestDetails, storage.PullRequestStatusChangeDetails]]:
        if False:
            yield

        raise NotImplementedError()


@attrs.frozen
class MemoryStorage(storage.CommonStorage):
    _events: list[object] = attrs.field(factory=list)

    async def record_pull_request_status_change(
        self,
        *,
        pull_request: storage.PullRequestDetails,
        status_change: storage.PullRequestStatusChangeDetails,
    ) -> None:
        self._events.append(
            (
                "record_pull_request_status_change",
                pull_request,
                status_change,
            )
        )

    async def record_pull_request_review_change(
        self,
        *,
        pull_request: storage.PullRequestDetails,
        status_change: storage.PullRequestStatusChangeDetails,
        review_change: storage.PullRequestReviewChangeDetails,
    ) -> None:
        self._events.append(
            (
                "record_pull_request_review_change",
                pull_request,
                status_change,
                review_change,
            )
        )

    async def changed_pull_requests(self) -> AsyncIterator[_PullRequestUpdater]:
        if False:
            yield
        raise NotImplementedError()
