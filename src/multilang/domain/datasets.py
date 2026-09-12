"""Immutable dataset manifests; a rank belongs to an edition, never a card."""

from typing import Literal

from pydantic import Field, computed_field, model_validator

from multilang.domain.events import canonical_hash
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.language_profiles import NativeContract


class DatasetMember(NativeContract):
    identity_id: str = Field(min_length=1, max_length=128)
    rank: int = Field(ge=1, le=6000)
    identity_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


class DatasetManifest(NativeContract):
    language: SupportedLanguage
    kind: Literal["lexical", "ranking", "audio", "content"]
    namespace: Literal["core", "expansion", "custom", "highlight", "foundation"]
    version: str = Field(min_length=1, max_length=64)
    source_id: str = Field(min_length=1, max_length=128)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    policy_version: str = Field(min_length=1, max_length=64)
    redistribution_approved: bool = False
    approval_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    attribution: str = Field(default="", max_length=4000)
    owner_id: str = Field(default="", max_length=128)
    members: tuple[DatasetMember, ...] = Field(max_length=6000)
    metadata: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def coherent_inventory(self):
        if self.language == SupportedLanguage.LA and self.namespace in {"core", "expansion"}:
            raise ValueError("Latin remains in its isolated foundation inventory")
        if self.namespace in {"custom", "highlight"}:
            if not self.owner_id or self.redistribution_approved:
                raise ValueError("private datasets need owner and cannot be redistributed")
        elif self.owner_id:
            raise ValueError("shared datasets cannot have a private owner")
        if len({member.identity_id for member in self.members}) != len(self.members):
            raise ValueError("duplicate lexical identity")
        if len({member.rank for member in self.members}) != len(self.members):
            raise ValueError("duplicate rank")
        if self.redistribution_approved and (not self.approval_sha256 or not self.attribution):
            raise ValueError("redistribution requires source approval and attribution")
        if self.namespace == "expansion" and len(self.members) > 3000:
            raise ValueError("expansion cannot exceed 3000 additional identities")
        return self

    @computed_field
    @property
    def dataset_id(self) -> str:
        return canonical_hash(self.model_dump(mode="json", exclude={"dataset_id"}))

    def require_production(self) -> None:
        if self.namespace == "core" and (
            len(self.members) != 3000 or {item.rank for item in self.members} != set(range(1, 3001))
        ):
            raise ValueError("Core requires exactly 3000 identities ranked 1..3000")
        if self.namespace in {"core", "expansion"} and not self.redistribution_approved:
            raise ValueError("redistribution approval is required")
        if not self.approval_sha256:
            raise ValueError("production dataset requires reviewed approval evidence")
