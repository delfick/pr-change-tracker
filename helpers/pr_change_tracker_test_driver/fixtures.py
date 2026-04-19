from __future__ import annotations

import datetime
import json
import pathlib
from collections.abc import Callable, Mapping
from typing import Self

import attrs
import pytest

from pr_change_tracker import progress
from pr_change_tracker.handlers import github as github_handlers


@attrs.frozen
class _FixtureData:
    date: datetime.datetime
    webhook_secret: str

    headers: Mapping[str, str]
    body: Mapping[str, object]

    @classmethod
    def from_path(cls, path: pathlib.Path) -> Self:
        lines = path.read_text().splitlines()

        assert lines[0].startswith("- ")
        date = datetime.datetime.fromisoformat(lines.pop(0)[2:])

        assert lines[0].startswith("- ")
        webhook_secret = lines.pop(0)[2:]

        headers: dict[str, str] = {}
        while lines and (lines[0] == "" or lines[0].startswith(":")):
            line = lines.pop(0)
            if line == "":
                continue
            name, value = line[1:].split(":", 1)
            headers[name.strip()] = value.strip()

        body = json.loads("\n".join(lines).strip())

        return cls(date=date, webhook_secret=webhook_secret, body=body, headers=headers)


@attrs.frozen
class HookFixtures:
    _progress: progress.Progress
    _fixture_folder: pathlib.Path

    @classmethod
    def as_fixture(
        cls, fixture_folder: pathlib.Path
    ) -> Callable[[progress.Progress], HookFixtures]:
        @pytest.fixture
        def hook_fixtures(progress: progress.Progress) -> HookFixtures:
            return cls(progress=progress, fixture_folder=fixture_folder)

        return hook_fixtures

    def incoming_from_fixture(self, name: str) -> github_handlers.Incoming:
        data = _FixtureData.from_path(pathlib.Path(self._fixture_folder, name))

        return github_handlers.Incoming.from_http_request(
            headers=data.headers, body=data.body, progress=self._progress
        )
