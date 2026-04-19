from __future__ import annotations

import asyncio
import datetime
import signal

import attrs
import sqlalchemy
import sqlalchemy.engine.url
from sqlalchemy.ext.asyncio import create_async_engine

from pr_change_tracker import protocols, storage


def make_postgres_event_processor(
    *, logger: protocols.Logger, postgres_url: str
) -> EventProcessor:
    url = sqlalchemy.engine.url.make_url(postgres_url)
    url = url.set(drivername="postgresql+psycopg")
    return EventProcessor(
        logger=logger, storage=storage.PostgresStorage(engine=create_async_engine(url))
    )


@attrs.frozen
class EventProcessor:
    _logger: protocols.Logger

    _storage: storage.CommonStorage

    def serve_forever(self) -> None:
        asyncio.run(self._serve())

    async def _serve(self) -> None:
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
                await self._tick()
            except:
                self._logger.exception("Failed to run the tick")

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

    async def _tick(self) -> None:
        success = 0
        errored = 0
        async for pr in self._storage.changed_pull_requests():
            async with pr.update() as (details, latest_status):
                try:
                    await self._update_pr(details=details, latest_status=latest_status)
                    success += 1
                except:
                    errored += 1
                    raise

        self._logger.info("Updated pull requests", total=success + errored, errored=errored)

    async def _update_pr(
        self,
        *,
        details: storage.PullRequestDetails,
        latest_status: storage.PullRequestStatusChangeDetails,
    ) -> None:
        pass
