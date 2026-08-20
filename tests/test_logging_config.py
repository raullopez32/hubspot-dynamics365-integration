import json
import logging

from src.logging_config import JsonFormatter


def test_json_formatter_outputs_cloud_logging_fields():
    record = logging.LogRecord(
        name="sync",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Synchronization completed",
        args=(),
        exc_info=None,
    )

    payload = json.loads(JsonFormatter().format(record))

    assert payload["severity"] == "INFO"
    assert payload["logger"] == "sync"
    assert payload["message"] == "Synchronization completed"
    assert "timestamp" in payload
