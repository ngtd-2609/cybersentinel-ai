import json
import logging

from cybersentinel_ai.observability.logging import JsonFormatter


def test_json_log_formatter_keeps_operational_context():
    record = logging.LogRecord(
        name="cybersentinel.http",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="request_completed",
        args=(),
        exc_info=None,
    )
    record.request_id = "request-123"
    record.method = "GET"
    record.path = "/events/{event_id}"
    record.status = 200
    record.duration_ms = 12.5

    payload = json.loads(JsonFormatter().format(record))

    assert payload["message"] == "request_completed"
    assert payload["request_id"] == "request-123"
    assert payload["path"] == "/events/{event_id}"
    assert payload["duration_ms"] == 12.5
