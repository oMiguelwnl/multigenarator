"""Hash-bound migration input independent of database/provider implementations."""

from typing import Literal

from pydantic import Field

from multilang.domain.events import canonical_hash
from multilang.domain.language_profiles import NativeContract


class MigrationPreview(NativeContract):
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    target_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    backup_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_locator_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    target_revision: Literal["20260912_20"] = "20260912_20"
    policy: Literal["additive-preserve-legacy"] = "additive-preserve-legacy"
    topology_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    rehearsal_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    unresolved_count: int = Field(default=0, ge=0)

    @property
    def confirmation_sha256(self) -> str:
        return canonical_hash(self.model_dump(mode="json"))


MigrationContract = MigrationPreview
