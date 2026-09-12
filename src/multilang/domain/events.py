"""Content-free domain facts shared by application services and the outbox."""

import json
from datetime import UTC, datetime
from hashlib import sha256
from typing import Literal

from pydantic import Field, computed_field

from multilang.domain.language_profiles import NativeContract

EventType = Literal[
    "LexicalIdentityCreated",
    "LexicalIdentityUpdated",
    "DatasetImported",
    "RankingCalculated",
    "AudioGenerated",
    "MigrationCompleted",
    "DatasetActivated",
    "ContentGenerated",
    "UserDataDeleted",
    "SurfaceFormUpdated",
    "EditionFrozen",
    "LearnerStateUpdated",
    "LearnerHistoryImported",
    "LearnerHistoryRevoked",
    "LearnerStateDeleted",
    "LearnerAliasesRegistered",
    "LanguageProfileRegistered",
]


def canonical_hash(value: object) -> str:
    """Hash canonical JSON; callers must serialize domain objects explicitly."""
    return sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


class DomainEvent(NativeContract):
    event_type: EventType
    entity_id: str = Field(min_length=1, max_length=255)
    revision: int = Field(ge=1)
    actor: str = Field(min_length=1, max_length=128, pattern=r"^[\w:@.\-]+$")
    reason: str = Field(min_length=1, max_length=128, pattern=r"^[\w:.\-]+$")
    before_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    after_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @computed_field
    @property
    def event_id(self) -> str:
        return canonical_hash(
            {
                key: value
                for key, value in self.model_dump(
                    mode="json", exclude={"event_id", "occurred_at"}
                ).items()
            }
        )


class LexicalIdentityCreated(DomainEvent):
    event_type: Literal["LexicalIdentityCreated"] = "LexicalIdentityCreated"


class LexicalIdentityUpdated(DomainEvent):
    event_type: Literal["LexicalIdentityUpdated"] = "LexicalIdentityUpdated"


class DatasetImported(DomainEvent):
    event_type: Literal["DatasetImported"] = "DatasetImported"


class RankingCalculated(DomainEvent):
    event_type: Literal["RankingCalculated"] = "RankingCalculated"


class AudioGenerated(DomainEvent):
    event_type: Literal["AudioGenerated"] = "AudioGenerated"


class MigrationCompleted(DomainEvent):
    event_type: Literal["MigrationCompleted"] = "MigrationCompleted"
