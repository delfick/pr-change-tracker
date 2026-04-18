import datetime

import attrs
import pytest
from pr_change_tracker_test_driver import fixtures as fixture_helpers
from pr_change_tracker_test_driver import storage as storage_helpers

from pr_change_tracker import storage
from pr_change_tracker.handlers import github as github_handlers
from pr_change_tracker.handlers.github._processors import _common, _pull_request_review


@attrs.frozen
class PerTestLogic:
    _hook_fixtures: fixture_helpers.HookFixtures

    storage: storage.CommonStorage

    pull_request: _common.PullRequest = attrs.field(
        default=_common.PullRequest(
            pr_number=0,
            branch_name="",
            repo_name="test-for-github-webhooks",
            org="delfick",
            updated_at=datetime.datetime.now(),
        )
    )

    class Senders:
        delfick = _common.Sender(id=109301, login="delfick")
        kcollasarundell = _common.Sender(id=393998, login="kcollasarundell")

    def assertFixture(self, fixture_name: str, event: object | None, *events: object) -> None:
        if event is None:
            assert len(events) == 0
            events = ()
        else:
            assert not any(event is None for event in events)
            events = (event, *events)

        incoming = self._hook_fixtures.incoming_from_fixture(fixture_name)
        processor = github_handlers.IncomingProcessor(storage=self.storage)
        assert list(processor.process(incoming)) == list(events)


@pytest.fixture
def test_logic(hook_fixtures: fixture_helpers.HookFixtures) -> PerTestLogic:
    return PerTestLogic(hook_fixtures=hook_fixtures, storage=storage_helpers.MemoryStorage())


class TestPullRequestReviewEvents:
    class TestDismissed:
        def test_dismissed_collab(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture(
                "dismissed-collab",
                _pull_request_review._ReviewChangedEvent(
                    storage=test_logic.storage,
                    review=_pull_request_review._Review(
                        review_id=2431185757,
                        submitted_at=datetime.datetime.fromisoformat("2024-11-13T00:14:56Z"),
                        commit_id="20be90fb76987ea58ad9c7698bf06658b45178d1",
                        state=storage.ReviewState.DISMISSED,
                        reviewer_id=393998,
                        reviewer_login="kcollasarundell",
                    ),
                    head_and_base=_common.HeadAndBase(
                        head_ref="test1",
                        head_sha="20be90fb76987ea58ad9c7698bf06658b45178d1",
                        base_ref="main",
                        base_sha="f2c691ea3431993ae49dcdd32b81a89c7859c4ec",
                    ),
                    sender=test_logic.Senders.kcollasarundell,
                    pull_request=attrs.evolve(
                        test_logic.pull_request,
                        pr_number=1,
                        branch_name="test1",
                        updated_at=datetime.datetime.fromisoformat("2024-11-13T00:23:02Z"),
                    ),
                    status=storage.PullRequestStatus.READY_FOR_REVIEW,
                ),
            )

        def test_dismissed_owner(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture(
                "dismissed-owner",
                _pull_request_review._ReviewChangedEvent(
                    storage=test_logic.storage,
                    review=_pull_request_review._Review(
                        review_id=2431217782,
                        submitted_at=datetime.datetime.fromisoformat("2024-11-13T00:28:41Z"),
                        commit_id="20be90fb76987ea58ad9c7698bf06658b45178d1",
                        state=storage.ReviewState.DISMISSED,
                        reviewer_id=393998,
                        reviewer_login="kcollasarundell",
                    ),
                    head_and_base=_common.HeadAndBase(
                        head_ref="test1",
                        head_sha="20be90fb76987ea58ad9c7698bf06658b45178d1",
                        base_ref="main",
                        base_sha="f2c691ea3431993ae49dcdd32b81a89c7859c4ec",
                    ),
                    sender=test_logic.Senders.delfick,
                    pull_request=attrs.evolve(
                        test_logic.pull_request,
                        pr_number=1,
                        branch_name="test1",
                        updated_at=datetime.datetime.fromisoformat("2024-11-13T00:28:56Z"),
                    ),
                    status=storage.PullRequestStatus.READY_FOR_REVIEW,
                ),
            )

    class TestSubmitted:
        def test_submitted_approve(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture(
                "submitted-approve",
                _pull_request_review._ReviewChangedEvent(
                    storage=test_logic.storage,
                    review=_pull_request_review._Review(
                        review_id=2431221502,
                        submitted_at=datetime.datetime.fromisoformat("2024-11-13T00:30:22Z"),
                        commit_id="20be90fb76987ea58ad9c7698bf06658b45178d1",
                        state=storage.ReviewState.APPROVED,
                        reviewer_id=393998,
                        reviewer_login="kcollasarundell",
                    ),
                    head_and_base=_common.HeadAndBase(
                        head_ref="test1",
                        head_sha="20be90fb76987ea58ad9c7698bf06658b45178d1",
                        base_ref="main",
                        base_sha="f2c691ea3431993ae49dcdd32b81a89c7859c4ec",
                    ),
                    sender=test_logic.Senders.kcollasarundell,
                    pull_request=attrs.evolve(
                        test_logic.pull_request,
                        pr_number=1,
                        branch_name="test1",
                        updated_at=datetime.datetime.fromisoformat("2024-11-13T00:30:22Z"),
                    ),
                    status=storage.PullRequestStatus.READY_FOR_REVIEW,
                ),
            )

        def test_submitted_changes_requested_collab(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture(
                "submitted-changes_requested-collab",
                _pull_request_review._ReviewChangedEvent(
                    storage=test_logic.storage,
                    review=_pull_request_review._Review(
                        review_id=2431185757,
                        submitted_at=datetime.datetime.fromisoformat("2024-11-13T00:14:56Z"),
                        commit_id="20be90fb76987ea58ad9c7698bf06658b45178d1",
                        state=storage.ReviewState.CHANGES_REQUESTED,
                        reviewer_id=393998,
                        reviewer_login="kcollasarundell",
                    ),
                    head_and_base=_common.HeadAndBase(
                        head_ref="test1",
                        head_sha="20be90fb76987ea58ad9c7698bf06658b45178d1",
                        base_ref="main",
                        base_sha="f2c691ea3431993ae49dcdd32b81a89c7859c4ec",
                    ),
                    sender=test_logic.Senders.kcollasarundell,
                    pull_request=attrs.evolve(
                        test_logic.pull_request,
                        pr_number=1,
                        branch_name="test1",
                        updated_at=datetime.datetime.fromisoformat("2024-11-13T00:14:56Z"),
                    ),
                    status=storage.PullRequestStatus.READY_FOR_REVIEW,
                ),
            )

        def test_submitted_commented_collab(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture("submitted-commented-collab", None)

        def test_submitted_commented_owner(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture("submitted-commented-owner", None)
