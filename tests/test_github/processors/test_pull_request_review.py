import attrs
import pytest
from pr_change_tracker_test_driver import fixtures as fixture_helpers
from pr_change_tracker_test_driver import storage as storage_helpers

from pr_change_tracker import storage
from pr_change_tracker.handlers import github as github_handlers
from pr_change_tracker.handlers.github._processors import _common, _pull_request_review


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


class TestPullRequestReviewEvents:
    class TestDismissed:
        def test_dismissed_collab(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture(
                "dismissed-collab",
                _pull_request_review._DismissedEvent(
                    pull_request=attrs.evolve(
                        test_logic.pull_request, pr_number=1, branch_name="test1"
                    ),
                ),
            )

        def test_dismissed_owner(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture(
                "dismissed-owner",
                _pull_request_review._DismissedEvent(
                    pull_request=attrs.evolve(
                        test_logic.pull_request, pr_number=1, branch_name="test1"
                    ),
                ),
            )

    class TestSubmitted:
        def test_submitted_approve(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture(
                "submitted-approve",
                _pull_request_review._SubmittedEvent(
                    pull_request=attrs.evolve(
                        test_logic.pull_request, pr_number=1, branch_name="test1"
                    ),
                ),
            )

        def test_submitted_changes_requested_collab(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture(
                "submitted-changes_requested-collab",
                _pull_request_review._SubmittedEvent(
                    pull_request=attrs.evolve(
                        test_logic.pull_request, pr_number=1, branch_name="test1"
                    ),
                ),
            )

        def test_submitted_commented_collab(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture(
                "submitted-commented-collab",
                _pull_request_review._SubmittedEvent(
                    pull_request=attrs.evolve(
                        test_logic.pull_request, pr_number=1, branch_name="test1"
                    ),
                ),
            )

        def test_submitted_commented_owner(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture(
                "submitted-commented-owner",
                _pull_request_review._SubmittedEvent(
                    pull_request=attrs.evolve(
                        test_logic.pull_request, pr_number=1, branch_name="test1"
                    ),
                ),
            )
