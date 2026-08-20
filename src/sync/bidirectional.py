from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from datetime import datetime, timezone

from src.checkpoint import CheckpointStore

from .reverse_contacts import ReverseContactSync
from .workflow import SyncWorkflow


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class BidirectionalSyncWorkflow:
    def __init__(
        self,
        forward: SyncWorkflow,
        reverse: ReverseContactSync,
        checkpoint: CheckpointStore,
        clock: Callable[[], str] = utc_now,
    ) -> None:
        self.forward = forward
        self.reverse = reverse
        self.checkpoint = checkpoint
        self.clock = clock

    def run(self, list_id: str) -> dict:
        forward_result = self.forward.run(list_id)
        until = self.clock()
        since = self.checkpoint.load()

        if not since:
            self.checkpoint.save(until)
            return {
                "forward": forward_result,
                "reverse": {"processed": 0, "statuses": {}, "checkpoint_initialized": True},
            }

        changed = self.reverse.read_changed(since, until)
        results = [self.reverse.sync(contact) for contact in changed]
        self.checkpoint.save(until)

        return {
            "forward": forward_result,
            "reverse": {
                "processed": len(changed),
                "statuses": dict(Counter(result["status"] for result in results)),
                "checkpoint_initialized": False,
            },
        }
