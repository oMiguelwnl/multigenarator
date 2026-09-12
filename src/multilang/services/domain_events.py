"""Explicit in-process event subscribers and a durable, at-least-once outbox."""

from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from multilang.db.native_models import DomainEventRecord
from multilang.domain.events import DomainEvent


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[DomainEvent], None]]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable[[DomainEvent], None]) -> None:
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)

    def publish(self, event: DomainEvent) -> None:
        # Exceptions intentionally propagate; an outbox delivery is not acknowledged.
        for handler in self._subscribers[event.event_type]:
            handler(event)

    def dispatch_pending(self, session: Session, *, limit: int = 100) -> int:
        if not 1 <= limit <= 1000:
            raise ValueError("event batch limit must be 1..1000")
        rows = session.scalars(
            select(DomainEventRecord)
            .where(DomainEventRecord.delivered_at.is_(None))
            .order_by(DomainEventRecord.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        count = 0
        for row in rows:
            row.attempts += 1
            event = DomainEvent.model_validate(
                {key: value for key, value in row.payload.items() if key != "event_id"}
            )
            self.publish(event)
            row.delivered_at = datetime.now(UTC)
            count += 1
        session.flush()
        return count
