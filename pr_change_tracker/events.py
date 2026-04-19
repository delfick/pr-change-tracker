from __future__ import annotations

import asyncio
import contextlib
import datetime
import functools
import signal
from collections.abc import Callable

import attrs

from pr_change_tracker import progress, storage

from .api import github as github_api


def _on_done(res: asyncio.Future[None]) -> None:
    if res.cancelled():
        return

    res.exception()


def make_postgres_event_processor(
    *,
    progress: progress.Progress,
    postgres_url: str,
    github_api_token: str,
    github_api_requester: str,
) -> EventProcessor:
    return EventProcessor(
        progress=progress,
        storage=storage.PostgresStorage(
            engine=storage.make_engine(postgres_url=postgres_url),
        ),
        manage_github_api=functools.partial(
            github_api.GithubAPI.create,
            token=github_api_token,
            requester=github_api_requester,
        ),
    )


@attrs.frozen
class EventProcessor:
    _progress: progress.Progress

    _storage: storage.CommonStorage
    _manage_github_api: Callable[
        [], contextlib.AbstractAsyncContextManager[github_api.CommonGithubAPI]
    ]

    _max_concurrent_pr_updates: int = attrs.field(default=4)

    def serve_forever(self) -> None:

        async def _run() -> None:
            async with self._manage_github_api() as gh:
                await self._serve(gh)

        asyncio.run(_run())

    async def _serve(self, gh: github_api.CommonGithubAPI) -> None:
        shutdown_event = asyncio.Event()
        do_next_process_event = asyncio.Event()
        do_next_process_event.set()

        def on_sigterm() -> None:
            shutdown_event.set()
            do_next_process_event.set()

        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, on_sigterm)
        loop.add_signal_handler(signal.SIGTERM, on_sigterm)

        last_checked: datetime.datetime | None = None
        while True:
            await do_next_process_event.wait()
            do_next_process_event.clear()

            if shutdown_event.is_set():
                break

            try:
                await self._tick(gh)
            except:
                self._progress.logger.exception("Failed to run the tick")

            next_tick = datetime.timedelta(minutes=1)
            now = datetime.datetime.now()
            if last_checked is not None:
                diff = now - last_checked
                if diff < next_tick:
                    next_tick = next_tick - diff
                else:
                    next_tick = datetime.timedelta(seconds=1)

            loop.call_later(next_tick.total_seconds(), do_next_process_event.set)
            last_checked = now

    async def _tick(self, gh: github_api.CommonGithubAPI) -> None:
        success = 0
        errored = 0

        limit = asyncio.Semaphore(self._max_concurrent_pr_updates)

        async def _run_update(pr: storage.CommonPullRequestUpdater) -> None:
            nonlocal success
            nonlocal errored

            async with limit:
                async with pr.update() as (details, latest_status):
                    try:
                        await self._update_pr(gh=gh, details=details, latest_status=latest_status)
                        success += 1
                    except:
                        errored += 1
                        raise

        loop = asyncio.get_running_loop()
        tasks: list[asyncio.Task[None]] = []
        async for pr in self._storage.changed_pull_requests():
            task = loop.create_task(_run_update(pr))
            task.add_done_callback(_on_done)
            tasks.append(task)

        await asyncio.gather(*tasks)
        self._progress.logger.info(
            "Updated pull requests", total=success + errored, errored=errored
        )

    async def _update_pr(
        self,
        *,
        gh: github_api.CommonGithubAPI,
        details: storage.PullRequestDetails,
        latest_status: storage.PullRequestStatusChangeDetails,
    ) -> None:
        # current_details = await gh.for_pull_request(
        #     repo_name=details.repo_name, org=details.org, pr_number=details.pr_number
        # ).current_state()
        pass
