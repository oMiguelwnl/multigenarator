"""Content-free structured events, traces and metrics for application boundaries."""

import json
import logging
from contextlib import contextmanager
from time import monotonic

from opentelemetry import metrics, trace
from opentelemetry.trace import Status, StatusCode


class SafeJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        fields = {"level": record.levelname, "event": getattr(record, "event", "application.event")}
        # No formatted message, exception traceback, arbitrary extra data, or user content.
        for field in ("task_kind", "status", "duration_ms", "request_method", "api_version"):
            value = getattr(record, field, None)
            if isinstance(value, (str, int, float, bool)):
                fields[field] = value
        return json.dumps(fields, ensure_ascii=True)


def configure_logging() -> None:
    logger = logging.getLogger("multilang.native")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(SafeJsonFormatter())
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


@contextmanager
def operation(name: str, *, task_kind: str = "", enabled: bool = True):
    """Static operation/kind names only; do not pass request parameters."""
    if not enabled:
        yield
        return
    started = monotonic()
    status = "completed"
    tracer = trace.get_tracer("multilang.native")
    with tracer.start_as_current_span(
        name, record_exception=False, set_status_on_exception=False
    ) as span:
        span.set_attribute("task.kind", task_kind)
        try:
            yield
        except Exception:
            status = "failed"
            span.set_status(Status(StatusCode.ERROR))
            raise
        finally:
            duration_ms = (monotonic() - started) * 1000
            attributes = {"operation": name, "task.kind": task_kind, "status": status}
            meter = metrics.get_meter("multilang.native")
            meter.create_counter("multilang.operations").add(1, attributes)
            meter.create_histogram("multilang.operation.duration", unit="ms").record(
                duration_ms, attributes
            )
            logging.getLogger("multilang.native").info(
                "",
                extra={
                    "event": name,
                    "task_kind": task_kind,
                    "status": status,
                    "duration_ms": duration_ms,
                },
            )
