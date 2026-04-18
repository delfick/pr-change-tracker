import datetime

import attrs
import pytest
from pr_change_tracker_test_driver import comparators
from pr_change_tracker_test_driver import fixtures as fixture_helpers
from pr_change_tracker_test_driver import storage as storage_helpers

from pr_change_tracker import storage
from pr_change_tracker.handlers import github as github_handlers
from pr_change_tracker.handlers.github._processors import _common, _pull_request


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
        )
    )

    class Senders:
        delfick = _common.Sender(id=109301, login="delfick")

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


class TestPullRequestEvents:
    class TestClosedAction:
        def test_closed_merged(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture(
                "closed-merged",
                _pull_request._MergedEvent(
                    storage=test_logic.storage,
                    timestamps=comparators.IsInstance.using(_common.Timestamps),
                    sender=test_logic.Senders.delfick,
                    head_and_base=_common.HeadAndBase(
                        head_ref="test1",
                        head_sha="20be90fb76987ea58ad9c7698bf06658b45178d1",
                        base_ref="main",
                        base_sha="f2c691ea3431993ae49dcdd32b81a89c7859c4ec",
                    ),
                    pull_request=attrs.evolve(
                        test_logic.pull_request, pr_number=1, branch_name="test1"
                    ),
                    merge_commit_sha="c41709e060bc496d3cd7df1d5ee339d0b223527b",
                    merged_at=datetime.datetime.fromisoformat("2024-11-13T00:31:15Z"),
                ),
            )

        def test_closed_nomerge(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture(
                "closed-nomerge",
                _pull_request._ClosedEvent(
                    storage=test_logic.storage,
                    timestamps=comparators.IsInstance.using(_common.Timestamps),
                    sender=test_logic.Senders.delfick,
                    head_and_base=_common.HeadAndBase(
                        head_ref="revert-1-test1",
                        head_sha="40c48fc469d5c5adc498cc1fac3f6430dd927701",
                        base_ref="main",
                        base_sha="c41709e060bc496d3cd7df1d5ee339d0b223527b",
                    ),
                    pull_request=attrs.evolve(
                        test_logic.pull_request, pr_number=2, branch_name="revert-1-test1"
                    ),
                    merge_commit_sha="e902a1300f7ae670a97a466c2d6ff851c4751450",
                ),
            )

    class TestConvertedToDraftAction:
        def test_converted_to_draft(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture(
                "converted_to_draft",
                _pull_request._ConvertedToDraftEvent(
                    storage=test_logic.storage,
                    timestamps=comparators.IsInstance.using(_common.Timestamps),
                    sender=test_logic.Senders.delfick,
                    head_and_base=_common.HeadAndBase(
                        head_ref="test1",
                        head_sha="20be90fb76987ea58ad9c7698bf06658b45178d1",
                        base_ref="main",
                        base_sha="f2c691ea3431993ae49dcdd32b81a89c7859c4ec",
                    ),
                    pull_request=attrs.evolve(
                        test_logic.pull_request, pr_number=1, branch_name="test1"
                    ),
                ),
            )

    class TestEditedAction:
        def test_edited_base(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture(
                "edited-base",
                _pull_request._BaseChangedEvent(
                    storage=test_logic.storage,
                    timestamps=comparators.IsInstance.using(_common.Timestamps),
                    sender=test_logic.Senders.delfick,
                    head_and_base=_common.HeadAndBase(
                        head_ref="change-file",
                        head_sha="02ebe652bf359cadb5f96375ce9b21637cdbc1eb",
                        base_ref="change-file-prior",
                        base_sha="ce3858babcbf3c57458164e468ac0e9de9016e9d",
                    ),
                    pull_request=attrs.evolve(
                        test_logic.pull_request, pr_number=4, branch_name="change-file"
                    ),
                ),
            )

        def test_edited_body(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture("edited-body", None)

        def test_edited_title(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture("edited-title", None)

    class TestOpened:
        def test_opened(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture(
                "opened",
                _pull_request._OpenedEvent(
                    storage=test_logic.storage,
                    timestamps=comparators.IsInstance.using(_common.Timestamps),
                    sender=test_logic.Senders.delfick,
                    head_and_base=_common.HeadAndBase(
                        head_ref="test1",
                        head_sha="20be90fb76987ea58ad9c7698bf06658b45178d1",
                        base_ref="main",
                        base_sha="f2c691ea3431993ae49dcdd32b81a89c7859c4ec",
                    ),
                    pull_request=attrs.evolve(
                        test_logic.pull_request, pr_number=1, branch_name="test1"
                    ),
                ),
            )

        def test_opened_revert(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture(
                "opened-revert",
                _pull_request._OpenedEvent(
                    storage=test_logic.storage,
                    timestamps=comparators.IsInstance.using(_common.Timestamps),
                    sender=test_logic.Senders.delfick,
                    head_and_base=_common.HeadAndBase(
                        head_ref="revert-1-test1",
                        head_sha="40c48fc469d5c5adc498cc1fac3f6430dd927701",
                        base_ref="main",
                        base_sha="c41709e060bc496d3cd7df1d5ee339d0b223527b",
                    ),
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
                    storage=test_logic.storage,
                    timestamps=comparators.IsInstance.using(_common.Timestamps),
                    sender=test_logic.Senders.delfick,
                    head_and_base=_common.HeadAndBase(
                        head_ref="test1",
                        head_sha="20be90fb76987ea58ad9c7698bf06658b45178d1",
                        base_ref="main",
                        base_sha="f2c691ea3431993ae49dcdd32b81a89c7859c4ec",
                    ),
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
                    storage=test_logic.storage,
                    timestamps=comparators.IsInstance.using(_common.Timestamps),
                    sender=test_logic.Senders.delfick,
                    head_and_base=_common.HeadAndBase(
                        head_ref="revert-1-test1",
                        head_sha="40c48fc469d5c5adc498cc1fac3f6430dd927701",
                        base_ref="main",
                        base_sha="c41709e060bc496d3cd7df1d5ee339d0b223527b",
                    ),
                    pull_request=attrs.evolve(
                        test_logic.pull_request, pr_number=2, branch_name="revert-1-test1"
                    ),
                ),
            )

    class TestSynchronizeAction:
        def test_synchronize(self, test_logic: PerTestLogic) -> None:
            test_logic.assertFixture(
                "synchronize",
                _pull_request._SynchronizeEvent(
                    storage=test_logic.storage,
                    timestamps=comparators.IsInstance.using(_common.Timestamps),
                    sender=test_logic.Senders.delfick,
                    head_and_base=_common.HeadAndBase(
                        head_ref="change-file",
                        head_sha="02ebe652bf359cadb5f96375ce9b21637cdbc1eb",
                        base_ref="main",
                        base_sha="c41709e060bc496d3cd7df1d5ee339d0b223527b",
                    ),
                    pull_request=attrs.evolve(
                        test_logic.pull_request, pr_number=4, branch_name="change-file"
                    ),
                ),
            )
