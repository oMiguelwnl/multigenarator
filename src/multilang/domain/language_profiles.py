"""Versioned, fail-closed language capability contracts for native generation."""

from __future__ import annotations

from copy import deepcopy
from enum import Enum
from typing import Annotated, Any, Literal, Protocol, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from multilang.domain.jobs import SupportedLanguage

Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Identifier = Annotated[
    str, Field(min_length=1, max_length=128, pattern=r"^\S(?:.*\S)?$")
]


class _FrozenDict(dict):
    """JSON-compatible mapping whose public mutation methods are disabled."""

    def _immutable(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("native contract mappings are immutable")

    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = (
        __ior__
    ) = _immutable

    def __deepcopy__(self, memo: dict[int, Any]) -> _FrozenDict:
        return _FrozenDict(
            {deepcopy(key, memo): deepcopy(value, memo) for key, value in self.items()}
        )


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return _FrozenDict({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


class NativeContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    @model_validator(mode="wrap")
    @classmethod
    def verify_serialized_computed_fields(cls, value: Any, handler: Any) -> Any:
        """JSON round-trips may include IDs, but supplied IDs cannot override facts."""
        supplied = {}
        if isinstance(value, dict):
            supplied = {
                key: value[key] for key in cls.model_computed_fields if key in value
            }
            value = {key: item for key, item in value.items() if key not in supplied}
        result = handler(value)
        for key in cls.model_fields:
            object.__setattr__(result, key, _freeze(getattr(result, key)))
        serialized = (
            result.model_dump(mode="json", include=set(supplied)) if supplied else {}
        )
        for key, expected in supplied.items():
            if getattr(result, key) != expected and serialized.get(key) != expected:
                raise ValueError(f"computed contract field drift: {key}")
        return result

    def model_copy(
        self, *, update: dict[str, Any] | None = None, deep: bool = False
    ) -> Self:
        if update:
            return type(self).model_validate(
                {**self.model_dump(round_trip=True), **update}
            )
        return super().model_copy(deep=deep)


class CapabilityState(str, Enum):
    DISABLED = "disabled"
    EVIDENCE_PENDING = "evidence_pending"
    ENABLED = "enabled"


class CapabilityEvidence(NativeContract):
    state: CapabilityState = CapabilityState.DISABLED
    version: Identifier = "1"
    evidence_sha256: Sha256 | None = None
    reason: str = Field(
        default="Independent qualification evidence required", max_length=500
    )

    @model_validator(mode="after")
    def enabled_requires_evidence(self) -> Self:
        if self.state is CapabilityState.ENABLED and self.evidence_sha256 is None:
            raise ValueError("enabled capability requires evidence_sha256")
        return self


POLICY_GROUPS = (
    "identity",
    "normalization",
    "segmentation",
    "morphology",
    "sense",
    "matching",
    "sources",
    "privacy",
    "quality",
    "ANKI-01",
    "RANK-01",
    "FORM-04",
    "DISPLAY-01",
    "AUDIO-02",
    "AISEC-01",
    "CONTENT-01",
    "EVAL-01",
)
CAPABILITIES = ("core", "expansion", "custom", "highlights", "history", "adaptive")


class LanguageProfile(NativeContract):
    language: SupportedLanguage
    name: Identifier
    version: Identifier = "1"
    family: Literal["modern", "classical"] = "modern"
    explanation_language: Literal["en", "pt"]
    normalization_version: Identifier = "nfc-preserve-1"
    scripts: tuple[Identifier, ...] = ()
    variant: Identifier | None = None
    mixed_text_policy: Literal["quarantine", "explicit-source"] = "quarantine"
    tokenizer_id: Identifier | None = None
    tokenizer_version: Identifier | None = None
    analyzer_id: Identifier | None = None
    analyzer_version: Identifier | None = None
    tagset: Identifier | None = None
    tagset_version: Identifier | None = None
    provider_locales: dict[str, str] = Field(default_factory=dict)
    source_ids: tuple[Identifier, ...] = ()
    capabilities: dict[str, CapabilityEvidence] = Field(default_factory=dict)
    policies: dict[str, CapabilityEvidence] = Field(default_factory=dict)

    @model_validator(mode="after")
    def linguistic_policy_is_consistent(self) -> Self:
        expected = (
            "pt"
            if self.language in {SupportedLanguage.EN, SupportedLanguage.LA}
            else "en"
        )
        if self.explanation_language != expected:
            raise ValueError(
                "explanation language must follow the native language policy"
            )
        if (self.language is SupportedLanguage.LA) != (self.family == "classical"):
            raise ValueError("Latin must remain isolated from modern language profiles")
        if self.family == "classical" and any(
            item.state is CapabilityState.ENABLED for item in self.capabilities.values()
        ):
            raise ValueError("Latin cannot inherit modern capabilities")
        if len(self.source_ids) != len(set(self.source_ids)):
            raise ValueError("duplicate authorized source IDs")
        if any(key not in CAPABILITIES for key in self.capabilities):
            raise ValueError("unknown language capability")
        return self

    def require(self, capability: str, *, policy_groups: tuple[str, ...] = ()) -> None:
        """Authorize an operation only when every requested authority is present."""
        item = self.capabilities.get(capability)
        if (
            item is None
            or item.state is not CapabilityState.ENABLED
            or not item.evidence_sha256
        ):
            raise ValueError(
                f"{self.language.value}: capability {capability} not enabled; qualification required"
            )
        for name in policy_groups:
            policy = self.policies.get(name)
            if (
                policy is None
                or policy.state is not CapabilityState.ENABLED
                or not policy.evidence_sha256
            ):
                raise ValueError(
                    f"{self.language.value}: policy {name} not enabled; qualification required"
                )


class LanguageProfileContract(Protocol):
    def get(self, language: str | SupportedLanguage) -> LanguageProfile: ...

    def all(self) -> tuple[LanguageProfile, ...]: ...
