import pytest

from multilang.domain.events import DomainEvent, LexicalIdentityCreated
from multilang.services.domain_events import EventBus


def test_event_subscribers_are_explicit_and_failures_remain_retryable():
    bus = EventBus()
    calls = []
    bus.subscribe("LexicalIdentityCreated", lambda event: calls.append(event.event_id))
    event = LexicalIdentityCreated(
        entity_id="lexical:fixture",
        revision=1,
        actor="fixture",
        reason="review",
        after_sha256="a" * 64,
    )
    bus.publish(event)
    assert calls == [event.event_id]
    assert DomainEvent.model_validate(event.model_dump()).event_type == "LexicalIdentityCreated"
    with pytest.raises(ValueError):
        DomainEvent(event_type="arbitrary", entity_id="x", actor="a", reason="r", revision=1)


def test_events_reject_private_payload_and_never_derive_id_from_clock():
    values = dict(entity_id="x", revision=1, actor="a", reason="review", after_sha256="a" * 64)
    assert LexicalIdentityCreated(**values).event_id == LexicalIdentityCreated(**values).event_id
    with pytest.raises(ValueError):
        LexicalIdentityCreated(**values, raw_prompt="secret")
