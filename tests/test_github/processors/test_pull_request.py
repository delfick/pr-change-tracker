import attrs
import pytest
from pr_change_tracker_test_driver import fixtures as fixture_helpers
from pr_change_tracker_test_driver import storage as storage_helpers

from pr_change_tracker import storage
from pr_change_tracker.handlers import github as github_handlers
from pr_change_tracker.handlers.github._processors import _pull_request


@attrs.frozen
class PerTestLogic:
    _storage: storage.CommonStorage
    _hook_fixtures: fixture_helpers.HookFixtures

    def assertFixture(self, fixture_name: str, *events: object) -> None:
        incoming = self._hook_fixtures.incoming_from_fixture(fixture_name)
        processor = github_handlers.IncomingProcessor(storage=self._storage)
        assert list(processor.process(incoming)) == list(events)


@pytest.fixture
def test_logic(hook_fixtures: fixture_helpers.HookFixtures) -> PerTestLogic:
    return PerTestLogic(hook_fixtures=hook_fixtures, storage=storage_helpers.MemoryStorage())


class TestPullRequestEvents:
    class TestClosedAction:
        def test_closed_merged(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture("closed-merged", _pull_request._ClosedEvent())

        def test_closed_nomerge(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture("closed-nomerge", _pull_request._ClosedEvent())

    class TestConvertedToDraftAction:
        def test_converted_to_draft(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture("converted_to_draft", _pull_request._ConvertedToDraftEvent())

    class TestEditedAction:
        pass

    class TestOpened:
        def test_opened(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture("opened", _pull_request._OpenedEvent())

        def test_opened_revert(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture("opened-revert", _pull_request._OpenedEvent())

    class TestReadyForReviewAction:
        def test_ready_for_review(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture("ready_for_review", _pull_request._ReadyForReviewEvent())

    class TestReopenedAction:
        def test_reopend(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture("reopened", _pull_request._ReopendEvent())

    class TestSynchronizeAction:
        pass
