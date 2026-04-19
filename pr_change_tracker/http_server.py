from __future__ import annotations

import abc
import asyncio
import functools
import logging
import signal
from types import SimpleNamespace

import attrs
import sanic
from hypercorn.asyncio import serve as hypercorn_serve
from hypercorn.config import Config

from . import progress, storage
from .handlers import github as github_handlers
from .handlers import sanic as sanic_handlers


@attrs.frozen
class ServerBase[T_SanicConfig: sanic.Config, T_SanicNamespace]:
    storage: storage.CommonStorage
    github_webhook_secret: str
    debug_github_webhook_secret: str | None
    port: int
    _progress: progress.Progress

    def serve_forever(self) -> None:
        config = self.make_hypercorn_config()
        config = self.configure_hypercorn_config(config)

        app = self.make_sanic_app()

        app = self.configure_sanic(app=app)

        asyncio.run(self.serve_app(app=app, config=config))

    @abc.abstractmethod
    def make_sanic_app(self) -> sanic.Sanic[T_SanicConfig, T_SanicNamespace]: ...

    def make_hypercorn_config(self) -> Config:
        return Config()

    def configure_hypercorn_config(self, config: Config) -> Config:
        config.accesslog = logging.getLogger("hypercorn.access")
        config.errorlog = logging.getLogger("hypercorn.access")
        config.bind = [f"127.0.0.1:{self.port}"]
        return config

    def configure_sanic(
        self, *, app: sanic.Sanic[T_SanicConfig, T_SanicNamespace]
    ) -> sanic.Sanic[T_SanicConfig, T_SanicNamespace]:
        github_handler = sanic_handlers.GithubWebhook(
            progress=self._progress,
            process_incoming=github_handlers.IncomingProcessor(storage=self.storage).process,
            determine_expected_signature=functools.partial(
                github_handlers.determine_expected_signature, self.github_webhook_secret
            ),
        )

        @app.post("/github/webhook", name="github_webhook")
        async def github_webhook(request: sanic.Request) -> sanic.response.HTTPResponse:
            return await github_handler.handle(request)

        debug_github_webhook_secret = self.debug_github_webhook_secret
        if debug_github_webhook_secret:

            @app.post("/debug/print_hook", name="debug_print_hook")
            async def github_webhook(request: sanic.Request) -> sanic.response.HTTPResponse:
                return await sanic_handlers.print_hook(
                    request,
                    printer=print,
                    debug_github_webhook_secret=debug_github_webhook_secret,
                )

        return app

    async def serve_app(
        self,
        *,
        app: sanic.Sanic[T_SanicConfig, T_SanicNamespace],
        config: Config,
    ) -> None:
        shutdown_event = asyncio.Event()

        def on_sigterm() -> None:
            shutdown_event.set()

        asyncio.get_running_loop().add_signal_handler(signal.SIGINT, on_sigterm)
        asyncio.get_running_loop().add_signal_handler(signal.SIGTERM, on_sigterm)

        await hypercorn_serve(app, config, shutdown_trigger=shutdown_event.wait)


@attrs.frozen
class Server(ServerBase[sanic.Config, SimpleNamespace]):
    def make_sanic_app(self) -> sanic.Sanic[sanic.Config, SimpleNamespace]:
        app = sanic.Sanic(
            "pr_change_tracker", env_prefix="PR_CHANGE_TRACKER", configure_logging=False
        )
        app.config.MOTD = False
        return app


def make_server(
    *,
    postgres_url: str,
    github_webhook_secret: str,
    debug_github_webhook_secret: str | None,
    port: int,
    progress: progress.Progress,
) -> Server:
    return Server(
        progress=progress,
        port=port,
        github_webhook_secret=github_webhook_secret,
        debug_github_webhook_secret=debug_github_webhook_secret,
        storage=storage.PostgresStorage(
            engine=storage.make_engine(postgres_url=postgres_url),
        ),
    )
