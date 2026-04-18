import attrs
import pytest
from pr_change_tracker_test_driver import fixtures as fixture_helpers
from pr_change_tracker_test_driver import storage as storage_helpers

from pr_change_tracker import storage
from pr_change_tracker.handlers import github as github_handlers
from pr_change_tracker.handlers.github._processors import _common, _pull_request


@attrs.frozen
class PerTestLogic:
    _storage: storage.CommonStorage
    _hook_fixtures: fixture_helpers.HookFixtures

    pull_request: _common.PullRequest = attrs.field(
        default=_common.PullRequest(
            pr_number=0,
            branch_name="",
            repo_name="test-for-github-webhooks",
            org="delfick",
        )
    )

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
            test_logic.assertFixture(
                "closed-merged",
                _pull_request._ClosedEvent(
                    pull_request=attrs.evolve(
                        test_logic.pull_request, pr_number=1, branch_name="test1"
                    ),
                ),
            )

        def test_closed_nomerge(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture(
                "closed-nomerge",
                _pull_request._ClosedEvent(
                    pull_request=attrs.evolve(
                        test_logic.pull_request, pr_number=2, branch_name="revert-1-test1"
                    ),
                ),
            )

    class TestConvertedToDraftAction:
        def test_converted_to_draft(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture(
                "converted_to_draft",
                _pull_request._ConvertedToDraftEvent(
                    pull_request=attrs.evolve(
                        test_logic.pull_request, pr_number=1, branch_name="test1"
                    ),
                ),
            )

    class TestEditedAction:
        pass

    class TestOpened:
        def test_opened(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture(
                "opened",
                _pull_request._OpenedEvent(
                    pull_request=attrs.evolve(
                        test_logic.pull_request, pr_number=1, branch_name="test1"
                    ),
                ),
            )

        def test_opened_revert(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture(
                "opened-revert",
                _pull_request._OpenedEvent(
                    pull_request=attrs.evolve(
                        test_logic.pull_request, pr_number=2, branch_name="revert-1-test1"
                    ),
                ),
            )

    class TestReadyForReviewAction:
        def test_ready_for_review(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture(
                "ready_for_review",
                _pull_request._ReadyForReviewEvent(
                    pull_request=attrs.evolve(
                        test_logic.pull_request, pr_number=1, branch_name="test1"
                    ),
                ),
            )

    class TestReopenedAction:
        def test_reopend(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture(
                "reopened",
                _pull_request._ReopendEvent(
                    pull_request=attrs.evolve(
                        test_logic.pull_request, pr_number=2, branch_name="revert-1-test1"
                    ),
                ),
            )

    class TestSynchronizeAction:
        pass
