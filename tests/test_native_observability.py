import importlib.util
import json
import logging


def test_structured_logs_allowlist_fields_and_omit_payload():
    assert importlib.util.find_spec("multilang.observability") is not None, (
        "native telemetry missing"
    )
    from multilang.observability import SafeJsonFormatter

    record = logging.LogRecord("native", logging.INFO, "secret/path", 1, "private prompt", (), None)
    record.event = "task.completed"
    record.task_kind = "ranking"
    record.payload = {"token": "private"}
    parsed = json.loads(SafeJsonFormatter().format(record))
    assert parsed["event"] == "task.completed"
    assert "private" not in json.dumps(parsed)
    assert "secret" not in json.dumps(parsed)
