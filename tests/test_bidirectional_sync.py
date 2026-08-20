from unittest import mock

import pytest

from src.sync.bidirectional import BidirectionalSyncWorkflow


def test_first_run_initializes_checkpoint_without_replay():
    forward = mock.Mock()
    forward.run.return_value = {"processed": 2}
    reverse = mock.Mock()
    checkpoint = mock.Mock()
    checkpoint.load.return_value = None
    workflow = BidirectionalSyncWorkflow(
        forward=forward,
        reverse=reverse,
        checkpoint=checkpoint,
        clock=lambda: "2026-08-20T13:00:00Z",
    )

    result = workflow.run("123")

    assert result["reverse"] == {
        "processed": 0,
        "statuses": {},
        "checkpoint_initialized": True,
    }
    checkpoint.save.assert_called_once_with("2026-08-20T13:00:00Z")
    reverse.read_changed.assert_not_called()


def test_reverse_sync_advances_checkpoint_after_success():
    forward = mock.Mock()
    forward.run.return_value = {"processed": 1}
    reverse = mock.Mock()
    reverse.read_changed.return_value = [mock.Mock(), mock.Mock()]
    reverse.sync.side_effect = [
        {"status": "updated"},
        {"status": "unchanged"},
    ]
    checkpoint = mock.Mock()
    checkpoint.load.return_value = "2026-08-20T11:00:00Z"
    workflow = BidirectionalSyncWorkflow(
        forward=forward,
        reverse=reverse,
        checkpoint=checkpoint,
        clock=lambda: "2026-08-20T13:00:00Z",
    )

    result = workflow.run("123")

    reverse.read_changed.assert_called_once_with(
        "2026-08-20T11:00:00Z",
        "2026-08-20T13:00:00Z",
    )
    assert result["reverse"]["statuses"] == {"updated": 1, "unchanged": 1}
    checkpoint.save.assert_called_once_with("2026-08-20T13:00:00Z")


def test_reverse_failure_does_not_advance_checkpoint():
    forward = mock.Mock()
    forward.run.return_value = {"processed": 1}
    reverse = mock.Mock()
    reverse.read_changed.return_value = [mock.Mock()]
    reverse.sync.side_effect = RuntimeError("HubSpot failed")
    checkpoint = mock.Mock()
    checkpoint.load.return_value = "2026-08-20T11:00:00Z"
    workflow = BidirectionalSyncWorkflow(
        forward=forward,
        reverse=reverse,
        checkpoint=checkpoint,
        clock=lambda: "2026-08-20T13:00:00Z",
    )

    with pytest.raises(RuntimeError):
        workflow.run("123")

    checkpoint.save.assert_not_called()
