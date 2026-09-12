"""Sources -> normalization -> qualified analysis -> ranking -> validated dataset.

Adapters provide evidence; this orchestration never guesses a POS or sense and
never promotes a language merely because its code is registered.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from typing import Literal, Protocol, Self

from pydantic import Field, computed_field, model_validator

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.language_profiles import (
    Identifier,
    LanguageProfile,
    NativeContract,
    Sha256,
)
from multilang.domain.lexical_identity import (
    LexicalIdentity,
    MorphologicalAnalysis,
    SurfaceForm,
    UnitDecimal,
    canonical_sha256,
    normalize_identity_text,
)
from multilang.domain.ranking import (
    CorpusManifest,
    CorpusObservation,
    RankingPolicy,
    RankingResult,
    validate_core_ranking,
)
from multilang.services.ranking import RankingEngine


class SourceLexeme(NativeContract):
    record_id: Identifier
    language: SupportedLanguage
    surface: str = Field(min_length=1, max_length=512)
    lemma: str = Field(min_length=1, max_length=512)
    part_of_speech: Identifier | None = None
    sense_id: Identifier | None = None
    source_id: Identifier
    source_version: Identifier
    source_sha256: Sha256
    confidence: UnitDecimal
    features: dict[str, Identifier] = Field(default_factory=dict)
    attestation: int = Field(default=0, ge=0)
    context: str | None = Field(default=None, max_length=2000)
    evidence_values: dict[str, UnitDecimal] = Field(default_factory=dict)


class ResolvedLexicalAnalysis(NativeContract):
    normalized_lemma: str = Field(min_length=1, max_length=512)
    part_of_speech: Identifier
    sense_id: Identifier
    confidence: UnitDecimal
    features: dict[str, Identifier] = Field(default_factory=dict)
    evidence_sha256: Sha256


class LexicalSourceAdapter(Protocol):
    def read(self) -> Iterable[SourceLexeme]: ...


class LexicalAnalyzerAdapter(Protocol):
    analyzer_id: str
    analyzer_version: str

    def analyze(
        self, *, record: SourceLexeme, profile: LanguageProfile
    ) -> tuple[ResolvedLexicalAnalysis, ...]: ...


class StaticLexicalSource:
    """Adapter for previously validated dictionary/corpus/import records."""

    def __init__(self, records: Iterable[SourceLexeme]) -> None:
        self._records = records

    def read(self) -> Iterable[SourceLexeme]:
        return iter(self._records)


class SourceEvidenceAnalyzer:
    """Project explicit source-tagged lemmas; no inference or generic fallback.

    This adapter still requires independent qualification in each LanguageProfile.
    It is useful for curated dictionary imports with existing lemma/POS/sense data.
    """

    analyzer_id = "source-evidence"
    analyzer_version = "1"

    def analyze(
        self, *, record: SourceLexeme, profile: LanguageProfile
    ) -> tuple[ResolvedLexicalAnalysis, ...]:
        if record.part_of_speech is None or record.sense_id is None:
            return ()
        return (
            ResolvedLexicalAnalysis(
                normalized_lemma=normalize_identity_text(record.lemma),
                part_of_speech=record.part_of_speech,
                sense_id=record.sense_id,
                confidence=record.confidence,
                features=record.features,
                evidence_sha256=record.source_sha256,
            ),
        )


class PipelineQuarantine(NativeContract):
    record_id: Identifier
    source_sha256: Sha256
    reason: Literal[
        "unresolved_analysis",
        "ambiguous_analysis",
        "low_confidence",
        "invalid_analysis",
        "analyzer_unavailable",
    ]


class IdentitySourceEvidence(NativeContract):
    lexical_identity_id: Identifier
    record_id: Identifier
    source_id: Identifier
    source_version: Identifier
    source_sha256: Sha256


class ProductionApproval(NativeContract):
    source_license_sha256: Sha256
    linguistic_review_sha256: Sha256
    independent_review_sha256: Sha256
    evaluation_baseline_sha256: Sha256
    anki_decision_sha256: Sha256
    workload_manifest_sha256: Sha256


class PipelineResult(NativeContract):
    language: SupportedLanguage
    profile_version: Identifier
    identities: tuple[LexicalIdentity, ...]
    forms: tuple[SurfaceForm, ...]
    evidence: tuple[IdentitySourceEvidence, ...]
    quarantine: tuple[PipelineQuarantine, ...]
    input_record_count: int = Field(ge=0)
    accepted_record_count: int = Field(ge=0)
    input_sha256: Sha256
    ranking: RankingResult | None = None
    approval: ProductionApproval | None = None

    @model_validator(mode="after")
    def reconcile_dataset(self) -> Self:
        if self.accepted_record_count + len(self.quarantine) != self.input_record_count:
            raise ValueError("pipeline accepted/quarantined accounting drift")
        ids = {item.lexical_identity_id for item in self.identities}
        if len(ids) != len(self.identities):
            raise ValueError("duplicate production identity")
        if any(item.language != self.language for item in self.identities):
            raise ValueError("dataset language drift")
        if any(form.lexical_identity_id not in ids for form in self.forms):
            raise ValueError("orphan surface form")
        if self.ranking and any(
            entry.lexical_identity_id not in ids for entry in self.ranking.entries
        ):
            raise ValueError("ranking references identities outside this dataset")
        if self.approval:
            if self.quarantine or not self.ranking:
                raise ValueError(
                    "production approval requires fully resolved ranked dataset"
                )
            validate_core_ranking(self.ranking)
            if ids != {entry.lexical_identity_id for entry in self.ranking.entries}:
                raise ValueError(
                    "production Core membership must exactly match canonical ranking"
                )
            if any(
                c.privacy_class != "public" or not c.redistribution_approved
                for c in self.ranking.corpora
            ):
                raise ValueError(
                    "production dataset requires approved public redistribution"
                )
        return self

    @computed_field
    @property
    def production_eligible(self) -> bool:
        return self.approval is not None

    @computed_field
    @property
    def manifest_sha256(self) -> str:
        return canonical_sha256(
            self.model_dump(mode="json", exclude_computed_fields=True)
        )


class LexicalPipeline:
    def __init__(
        self, *, max_records: int = 100_000, minimum_confidence: Decimal = Decimal(1)
    ) -> None:
        if (
            max_records < 1
            or not minimum_confidence.is_finite()
            or not 0 <= minimum_confidence <= 1
        ):
            raise ValueError("invalid lexical pipeline limits")
        self.max_records = max_records
        self.minimum_confidence = minimum_confidence

    def run(
        self,
        *,
        profile: LanguageProfile,
        source: LexicalSourceAdapter,
        analyzer: LexicalAnalyzerAdapter,
        capability: str = "core",
        corpora: Iterable[CorpusManifest] = (),
        observations: Iterable[CorpusObservation] = (),
        ranking_policy: RankingPolicy | None = None,
        approval: ProductionApproval | None = None,
    ) -> PipelineResult:
        profile.require(
            capability,
            policy_groups=(
                "identity",
                "normalization",
                "morphology",
                "sense",
                "sources",
            ),
        )
        if profile.family != "modern":
            raise ValueError("modern lexical pipeline cannot process isolated Latin")
        if profile.normalization_version != "nfc-preserve-1":
            raise ValueError(
                "normalization adapter is not implemented for the declared profile version"
            )
        if ranking_policy is not None and (
            ranking_policy.normalizer_version != profile.normalization_version
            or ranking_policy.analyzer_version != profile.analyzer_version
            or ranking_policy.tagset_version != profile.tagset_version
        ):
            raise ValueError(
                "ranking normalizer/analyzer version drift from the LanguageProfile"
            )
        if (profile.analyzer_id, profile.analyzer_version) != (
            analyzer.analyzer_id,
            analyzer.analyzer_version,
        ):
            raise ValueError(
                "analyzer does not match the qualified LanguageProfile version"
            )
        if not profile.tagset or not profile.tagset_version:
            raise ValueError(
                "qualified analyzer tagset and tagset version are required"
            )
        records = []
        record_ids = set()
        for record in source.read():
            if len(records) >= self.max_records:
                raise ValueError("lexical pipeline record limit exceeded")
            validated = SourceLexeme.model_validate(
                record.model_dump(mode="json")
                if isinstance(record, SourceLexeme)
                else record
            )
            if (
                validated.language != profile.language
                or validated.source_id not in profile.source_ids
            ):
                raise ValueError(
                    "source is not authorized by the requested LanguageProfile"
                )
            record_key = (validated.source_id, validated.record_id)
            if record_key in record_ids:
                raise ValueError("duplicate source record ID")
            record_ids.add(record_key)
            records.append(validated)
        records.sort(key=lambda item: (item.source_id, item.record_id))
        identities: dict[str, LexicalIdentity] = {}
        forms: dict[str, SurfaceForm] = {}
        evidence = []
        quarantine = []
        accepted = 0
        for record in records:
            try:
                analyses = tuple(analyzer.analyze(record=record, profile=profile))
            except Exception:  # noqa: BLE001 - unavailable analyzer must quarantine without disclosing source text.
                quarantine.append(self._quarantine(record, "analyzer_unavailable"))
                continue
            if len(analyses) != 1:
                quarantine.append(
                    self._quarantine(
                        record,
                        "ambiguous_analysis" if analyses else "unresolved_analysis",
                    )
                )
                continue
            try:
                analysis = ResolvedLexicalAnalysis.model_validate(
                    analyses[0].model_dump(mode="json")
                )
                if analysis.confidence < self.minimum_confidence:
                    quarantine.append(self._quarantine(record, "low_confidence"))
                    continue
                identity = LexicalIdentity(
                    language=profile.language,
                    normalized_lemma=analysis.normalized_lemma,
                    part_of_speech=analysis.part_of_speech,
                    sense_id=analysis.sense_id,
                    profile_version=profile.version,
                    normalizer_version=profile.normalization_version,
                    analyzer_version=analyzer.analyzer_version,
                    source_id=record.source_id,
                    source_version=record.source_version,
                    source_sha256=record.source_sha256,
                )
                morphology = MorphologicalAnalysis(
                    lexical_identity_id=identity.lexical_identity_id,
                    analyzer_id=analyzer.analyzer_id,
                    analyzer_version=analyzer.analyzer_version,
                    features=analysis.features,
                    confidence=analysis.confidence,
                    evidence_sha256=analysis.evidence_sha256,
                )
                form = SurfaceForm(
                    lexical_identity_id=identity.lexical_identity_id,
                    text=record.surface,
                    analysis=morphology,
                    source_id=record.source_id,
                    source_sha256=record.source_sha256,
                    attestation=record.attestation,
                    context=record.context,
                    evidence_values=record.evidence_values,
                )
            except (ValueError, AttributeError):
                quarantine.append(self._quarantine(record, "invalid_analysis"))
                continue
            identities.setdefault(identity.lexical_identity_id, identity)
            existing_form = forms.get(form.surface_form_id)
            if existing_form is not None and existing_form != form:
                raise ValueError(
                    "conflicting surface evidence requires explicit source reconciliation"
                )
            forms[form.surface_form_id] = form
            evidence.append(
                IdentitySourceEvidence(
                    lexical_identity_id=identity.lexical_identity_id,
                    record_id=record.record_id,
                    source_id=record.source_id,
                    source_version=record.source_version,
                    source_sha256=record.source_sha256,
                )
            )
            accepted += 1
        ranking = None
        if ranking_policy is not None:
            profile.require(capability, policy_groups=("RANK-01",))
            ranking = RankingEngine().calculate(
                corpora=corpora, observations=observations, policy=ranking_policy
            )
        elif tuple(corpora) or tuple(observations):
            raise ValueError("ranking inputs require a versioned RankingPolicy")
        return PipelineResult(
            language=profile.language,
            profile_version=profile.version,
            identities=tuple(identities[key] for key in sorted(identities)),
            forms=tuple(forms[key] for key in sorted(forms)),
            evidence=tuple(evidence),
            quarantine=tuple(quarantine),
            input_record_count=len(records),
            accepted_record_count=accepted,
            input_sha256=canonical_sha256(
                [row.model_dump(mode="json") for row in records]
            ),
            ranking=ranking,
            approval=approval,
        )

    @staticmethod
    def _quarantine(record: SourceLexeme, reason: str) -> PipelineQuarantine:
        return PipelineQuarantine(
            record_id=record.record_id,
            source_sha256=record.source_sha256,
            reason=reason,
        )
