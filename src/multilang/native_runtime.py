"""Native application composition using Multilang's existing domain/service layers."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from multilang.db.native_models import (
    AudioVersionRecord,
    ContentVersionRecord,
    LanguageProfileRecord,
    LexicalIdentityRecord,
    SurfaceFormRecord,
)
from multilang.domain.anki_semantics import SemanticCard, TopologyDecision
from multilang.domain.audio_version import AudioVersion, PronunciationSignature
from multilang.domain.content import ContentRequest, ContentVersion
from multilang.domain.datasets import DatasetManifest, DatasetMember
from multilang.domain.events import RankingCalculated, canonical_hash
from multilang.domain.language_profiles import LanguageProfile
from multilang.domain.learning import AdaptivePolicy, HistoryAlias
from multilang.domain.lexical_identity import ImportantFormPolicy, LexicalIdentity
from multilang.domain.ranking import CorpusManifest, CorpusObservation, RankingPolicy
from multilang.repositories.native_repository import NativeRepository, model_payload
from multilang.services.language_profiles import LanguageProfileRegistry
from multilang.services.legacy_identity_adapter import (
    LegacyAliasCandidate,
    LegacyAliasPreview,
    LegacyIdentityAdapter,
)
from multilang.services.lexical_pipeline import (
    LexicalPipeline,
    SourceEvidenceAnalyzer,
    SourceLexeme,
    StaticLexicalSource,
)
from multilang.services.native_cache import VersionedCache
from multilang.services.native_imports import CSVImporter, DictionaryImporter, ImportSource
from multilang.services.plugins import PluginRegistry
from multilang.services.ranking import RankingEngine
from multilang.services.vocabulary_review import (
    CompiledVocabularyBundle,
    persist_compiled_vocabulary,
    verify_compiled_vocabulary,
)
from multilang.settings import Settings

NATIVE_PLUGINS = PluginRegistry()
NATIVE_PLUGINS.register(
    kind="analyzer", name="source-evidence", version="1", plugin=SourceEvidenceAnalyzer()
)
NATIVE_PLUGINS.register(
    kind="importer", name="dictionary", version="1", plugin=DictionaryImporter()
)
NATIVE_PLUGINS.register(kind="importer", name="csv", version="1", plugin=CSVImporter())


class ClosedRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class DatasetImportRequest(ClosedRequest):
    format: Literal["dictionary", "csv"]
    source: ImportSource
    data: str = Field(min_length=1, max_length=8_000_000)
    version: str = Field(min_length=1, max_length=64)
    namespace: Literal["core", "expansion"] = "core"


class ReviewedVocabularyImportRequest(ClosedRequest):
    format: Literal["reviewed-vocabulary"]
    profile_version: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=64)
    namespace: Literal["core", "expansion"] = "core"
    bundle: CompiledVocabularyBundle


class RankingUpdateRequest(ClosedRequest):
    language: str
    profile_version: str
    version: str
    corpora: tuple[CorpusManifest, ...] = Field(min_length=1, max_length=100)
    observations: tuple[CorpusObservation, ...] = Field(max_length=100000)
    policy: RankingPolicy


class AudioGenerationRequest(ClosedRequest):
    signature: PronunciationSignature
    identity_id: str = Field(min_length=1, max_length=128)
    namespace: Literal["core", "custom", "highlight"] = "core"


class AnkiExportRequest(ClosedRequest):
    dataset_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    model: Literal["A", "B"]
    prototype: bool = False
    important_form_policy: ImportantFormPolicy | None = None
    optional_roles: tuple[Literal["reverse", "listening", "cloze"], ...] = ()
    topology: TopologyDecision | None = None
    edition_id: str | None = Field(default=None, min_length=1, max_length=128)


class HistoryImportRequest(ClosedRequest):
    path: Path
    expected_revision: int = Field(ge=0)
    alias_guids: tuple[str, ...] | None = Field(default=None, max_length=100000)


class HistoryAliasRequest(ClosedRequest):
    aliases: tuple[HistoryAlias, ...] = Field(min_length=1, max_length=100000)
    receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class LearnerUpdateRequest(ClosedRequest):
    action: Literal["known", "reading", "expansion", "override", "reset", "revoke", "delete"]
    expected_revision: int = Field(ge=0)
    card_ids: tuple[str, ...] = Field(default=(), max_length=200000)
    enabled: bool = False
    card_id: str | None = Field(default=None, min_length=1, max_length=255)
    priority: int | None = Field(default=None, ge=-10000, le=10000)
    import_id: str | None = Field(default=None, min_length=1, max_length=128)


class AdaptiveQueueRequest(ClosedRequest):
    dataset_ids: tuple[str, ...] = Field(min_length=1, max_length=100)
    important_form_policy: ImportantFormPolicy | None = None
    policy: AdaptivePolicy = Field(default_factory=AdaptivePolicy)


class LegacyAliasesRequest(ClosedRequest):
    candidates: tuple[LegacyAliasCandidate, ...] = Field(min_length=1, max_length=10000)


class LegacyAliasesApplyRequest(ClosedRequest):
    preview: LegacyAliasPreview
    confirmation_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class NativeFacade:
    """Request/worker-scoped facade. The caller owns the supplied Session."""

    def __init__(
        self,
        session: Session,
        settings: Settings,
        *,
        plugins: PluginRegistry = NATIVE_PLUGINS,
        content_service=None,
        audio_service=None,
        topology_verifier=None,
    ):
        self.session, self.settings = session, settings
        self.repository = NativeRepository(session)
        self.plugins, self.content_service, self.audio_service = (
            plugins,
            content_service,
            audio_service,
        )
        self.topology_verifier = topology_verifier
        self.cache = VersionedCache()

    def _enabled(self) -> None:
        if not self.settings.roadmap_4_enabled:
            raise ValueError("ROADMAP_4_ENABLED is required")

    def _profile(self, language: str, version: str) -> LanguageProfile:
        row = self.session.get(LanguageProfileRecord, f"{language}:{version}")
        if row is None:
            return LanguageProfileRegistry().get(language)
        cached = self.cache.get("language", row.content_sha256, row.id)
        if cached is None:
            cached = row.payload
            self.cache.put("language", row.content_sha256, row.id, cached)
        return LanguageProfile.model_validate(cached)

    def search(
        self,
        query: str,
        language: str | None = None,
        limit: int = 50,
        owner_id: str | None = None,
        min_rank: int | None = None,
        max_rank: int | None = None,
    ) -> list[dict]:
        self._enabled()
        return self.repository.search(
            query,
            language=language,
            limit=limit,
            owner_id=owner_id,
            min_rank=min_rank,
            max_rank=max_rank,
        )

    def list_datasets(self) -> list[dict]:
        self._enabled()
        return self.repository.list_datasets()

    def import_dataset(self, payload: dict, actor: str) -> dict:
        self._enabled()
        if payload.get("format") == "reviewed-vocabulary":
            return self.import_reviewed_vocabulary(payload, actor)
        request = DatasetImportRequest.model_validate(payload)
        source = request.source
        profile = self._profile(source.language.value, source.profile_version)
        profile.require(
            request.namespace, policy_groups=("identity", "normalization", "morphology", "sources")
        )
        if (
            profile.version != source.profile_version
            or profile.normalization_version != source.normalizer_version
        ):
            raise ValueError("import source/profile normalization version mismatch")
        importer = self.plugins.get("importer", request.format, "1")
        identities = importer.parse(request.data.encode("utf-8"), source)
        records = [
            SourceLexeme(
                record_id=str(index),
                language=identity.language,
                surface=identity.normalized_lemma,
                lemma=identity.normalized_lemma,
                part_of_speech=identity.part_of_speech,
                sense_id=identity.sense_id,
                source_id=source.source_id,
                source_version=source.version,
                source_sha256=source.sha256,
                confidence=1,
            )
            for index, identity in enumerate(identities)
        ]
        analyzer = self.plugins.get("analyzer", profile.analyzer_id, profile.analyzer_version)
        result = LexicalPipeline().run(
            profile=profile,
            source=StaticLexicalSource(records),
            analyzer=analyzer,
            capability=request.namespace,
        )
        if result.quarantine:
            raise ValueError(
                "source contains unresolved lexical analysis; entire import quarantined"
            )
        # Preserve source order for staging. Corpus ranking creates a separate
        # edition and is mandatory for production; this ordering is not RANK-01.
        manifest = DatasetManifest(
            language=source.language,
            kind="lexical",
            namespace=request.namespace,
            version=request.version,
            source_id=source.source_id,
            source_sha256=source.sha256,
            policy_version=profile.version,
            attribution=source.attribution,
            redistribution_approved=source.redistribution_approved,
            approval_sha256=source.approval_sha256,
            members=tuple(
                DatasetMember(identity_id=identity.lexical_identity_id, rank=index + 1)
                for index, identity in enumerate(identities)
            ),
            metadata={
                "pipeline_sha256": result.manifest_sha256,
                "ordering": "source-order-staging",
            },
        )
        if self.repository.get_dataset(manifest.dataset_id) is not None:
            return {
                "dataset_id": manifest.dataset_id,
                "identity_count": len(result.identities),
                "form_count": len(result.forms),
                "production_eligible": False,
            }
        for identity in result.identities:
            previous = self.repository.get_identity(identity.lexical_identity_id)
            self.repository.put_identity(
                identity,
                actor=actor,
                reason="source_import",
                expected_revision=previous["revision"] if previous else None,
            )
        for form in result.forms:
            previous = self.session.get(SurfaceFormRecord, form.surface_form_id)
            self.repository.put_form(
                form,
                identity_id=form.lexical_identity_id,
                analysis_id=form.analysis.morphological_analysis_id,
                text=form.text,
                actor=actor,
                expected_revision=previous.revision if previous else None,
            )
        self.repository.save_dataset(manifest, actor=actor, reason="source_import")
        return {
            "dataset_id": manifest.dataset_id,
            "identity_count": len(result.identities),
            "form_count": len(result.forms),
            "production_eligible": False,
        }

    def import_reviewed_vocabulary(self, payload: dict, actor: str) -> dict:
        """Persist verified identities and observed forms without the legacy CSV projection."""
        self._enabled()
        request = ReviewedVocabularyImportRequest.model_validate(payload)
        profile = self._profile(request.bundle.language.value, request.profile_version)
        profile.require(
            request.namespace,
            policy_groups=("identity", "normalization", "morphology", "sense", "sources"),
        )
        if profile.version != request.profile_version:
            raise ValueError("reviewed import profile version mismatch")
        bundle = verify_compiled_vocabulary(
            request.bundle, profile=profile, verifier=_evidence_store(self.settings)
        )
        if not bundle.identities:
            raise ValueError("reviewed import has no accepted lexical identities")
        artifact = persist_compiled_vocabulary(
            bundle, self.settings.native_evidence_dir / "artifacts"
        )
        manifest = DatasetManifest(
            language=bundle.language,
            kind="lexical",
            namespace=request.namespace,
            version=request.version,
            source_id=bundle.review.source_id,
            source_sha256=bundle.preparation_manifest["dictionary_sha256"],
            policy_version=profile.version,
            attribution=f"Reviewed source {bundle.review.source_id}, version {bundle.review.source_version}",
            members=tuple(
                DatasetMember(identity_id=identity.lexical_identity_id, rank=index + 1)
                for index, identity in enumerate(bundle.identities)
            ),
            metadata={
                "ordering": "identity-order-staging",
                "bundle_sha256": bundle.bundle_sha256,
                "review_bundle_artifact_sha256": artifact,
                "preparation_sha256": bundle.review.preparation_sha256,
                "decisions_sha256": bundle.decisions_sha256,
                "important_form_count": str(len(bundle.important_forms)),
                "form_count": str(len(bundle.forms)),
                "source_evidence_sha256": canonical_hash(
                    [item.model_dump(mode="json") for item in bundle.source_evidence]
                ),
                "important_form_policy_sha256": canonical_hash(
                    bundle.review.important_form_policy.model_dump(mode="json")
                    if bundle.review.important_form_policy
                    else None
                ),
            },
        )
        result = {
            "dataset_id": manifest.dataset_id,
            "identity_count": len(bundle.identities),
            "form_count": len(bundle.forms),
            "important_form_count": len(bundle.important_forms),
            "quarantined_count": len(bundle.quarantine),
            "production_eligible": False,
        }
        if self.repository.get_dataset(manifest.dataset_id) is not None:
            return result
        for identity in bundle.identities:
            previous = self.repository.get_identity(identity.lexical_identity_id)
            self.repository.put_identity(
                identity,
                actor=actor,
                reason="reviewed_vocabulary_import",
                expected_revision=previous["revision"] if previous else None,
            )
        for form in bundle.forms:
            previous = self.session.get(SurfaceFormRecord, form.surface_form_id)
            self.repository.put_form(
                form,
                identity_id=form.lexical_identity_id,
                analysis_id=form.analysis.morphological_analysis_id,
                text=form.text,
                actor=actor,
                expected_revision=previous.revision if previous else None,
            )
        self.repository.save_dataset(
            manifest,
            actor=actor,
            reason="reviewed_vocabulary_import",
            form_ids=tuple(form.surface_form_id for form in bundle.forms),
        )
        return result

    def import_contextual_bindings(self, payload: dict, actor: str) -> dict:
        from multilang.services.contextual_bindings import (
            ContextualBindingSet,
            ReviewedBindingStore,
        )

        self._enabled()
        request = ContextualBindingSet.model_validate(payload)
        private = request.namespace != "core"
        if private and request.namespace != f"user:{actor}":
            raise ValueError("contextual bindings belong to another owner")
        profile = self._profile(request.language, request.profile_version)
        profile.require("custom" if private else "core", policy_groups=("sense", "matching"))
        if profile.version != request.profile_version:
            raise ValueError("contextual binding profile version mismatch")
        for binding in request.bindings:
            identity, _ = self._identity(binding.lexical_identity_id)
            if identity.language.value != request.language or identity.sense_id != binding.sense_id:
                raise ValueError("contextual binding differs from canonical lexical identity")
            if binding.morphological_analysis_id:
                forms = self.session.scalars(
                    select(SurfaceFormRecord).where(
                        SurfaceFormRecord.identity_id == identity.lexical_identity_id,
                        SurfaceFormRecord.analysis_id == binding.morphological_analysis_id,
                    )
                ).first()
                if forms is None:
                    raise ValueError("contextual binding refers to an unknown observed form")
        return ReviewedBindingStore(
            self.settings.native_contextual_bindings_dir,
            verifier=_evidence_store(self.settings).verify,
        ).put(request)

    def calculate_ranking(self, payload: dict, actor: str) -> dict:
        self._enabled()
        request = RankingUpdateRequest.model_validate(payload)
        profile = self._profile(request.language, request.profile_version)
        profile.require("core", policy_groups=("RANK-01", "sources"))
        if (
            request.policy.analyzer_version != profile.analyzer_version
            or request.policy.normalizer_version != profile.normalization_version
            or request.policy.tokenizer_version != profile.tokenizer_version
            or request.policy.tagset_version != profile.tagset_version
        ):
            raise ValueError("ranking policy differs from qualified profile versions")
        if any(
            corpus.language != profile.language or corpus.source_id not in profile.source_ids
            for corpus in request.corpora
        ):
            raise ValueError("ranking corpus is not authorized by profile")
        if any(corpus.privacy_class != "public" for corpus in request.corpora):
            raise ValueError("private corpora cannot alter shared Core ranking")
        result = RankingEngine().calculate(
            corpora=request.corpora, observations=request.observations, policy=request.policy
        )
        manifest = DatasetManifest(
            language=profile.language,
            kind="ranking",
            namespace="core",
            version=request.version,
            source_id="corpus-aggregation",
            source_sha256=result.manifest_sha256,
            policy_version=request.policy.version,
            members=tuple(
                DatasetMember(identity_id=entry.lexical_identity_id, rank=entry.rank)
                for entry in result.entries
            ),
            metadata={
                "ranking_manifest_sha256": result.manifest_sha256,
                "profile_version": profile.version,
                "ranking_result": result.model_dump_json(),
            },
        )
        self.repository.save_dataset(manifest, actor=actor, reason="ranking_update")
        self.repository.record_event(
            RankingCalculated(
                entity_id=manifest.dataset_id,
                revision=1,
                actor=actor,
                reason="corpus_aggregation",
                after_sha256=result.manifest_sha256,
            )
        )
        return {
            "dataset_id": manifest.dataset_id,
            "ranking_sha256": result.manifest_sha256,
            "identity_count": len(result.entries),
            "quarantined_count": len(result.quarantine),
        }

    def _identity(self, identity_id: str) -> tuple[LexicalIdentity, str]:
        row = self.session.get(LexicalIdentityRecord, identity_id)
        if row is None:
            raise ValueError("unknown lexical identity")
        return LexicalIdentity.model_validate(row.payload), row.content_sha256

    def _content_context(self, payload: dict, actor: str):
        self._enabled()
        request = ContentRequest.model_validate(payload)
        identity, digest = self._identity(request.lexical_identity_id)
        profile = self._profile(request.language, request.language_profile_version)
        private = request.namespace != "core"
        if private and request.namespace != f"user:{actor}":
            raise ValueError("private content belongs to another owner")
        profile.require(
            "custom" if private else "core", policy_groups=("matching", "AISEC-01", "CONTENT-01")
        )
        if (
            request.lemma != identity.normalized_lemma
            or request.sense_id != identity.sense_id
            or request.language != identity.language.value
            or request.grounding_sha256 != digest
            or request.explanation_language != profile.explanation_language
        ):
            raise ValueError("content request does not match canonical lexical grounding/profile")
        return request, profile

    def _content_service(self, profile):
        service = self.content_service
        if service is None:
            # A qualified target matcher is registered by trusted application
            # configuration; absence blocks before any provider request.
            matcher = self.plugins.get(
                "analyzer", f"{profile.analyzer_id}-target", profile.analyzer_version
            )
            if not self.settings.native_provider_calls_enabled:
                raise ValueError("native provider calls require configured budget and enablement")
            from multilang.runtime import _build_translation_adapter
            from multilang.services.native_content import (
                NativeContentService,
                NativeProviderContentAdapter,
            )

            service = NativeContentService(
                generator=NativeProviderContentAdapter(
                    settings=self.settings,
                    translation_adapter=_build_translation_adapter(self.settings),
                ),
                matcher=matcher,
                provider=self.settings.text_generation_provider,
                model_version=self.settings.text_generation_model,
            )
        return service

    def generate_content(self, payload: dict, actor: str) -> dict:
        request, profile = self._content_context(payload, actor)
        service = self._content_service(profile)
        version = service.generate(request)
        return self._save_content(version, actor)

    def draft_content(self, payload: dict, actor: str) -> dict:
        from multilang.services.content_drafts import ContentDraftStore

        request, profile = self._content_context(payload, actor)
        draft = self._content_service(profile).prepare(request)
        ContentDraftStore(self.settings.native_content_drafts_dir).put(draft)
        return draft.model_dump(mode="json")

    def complete_content_draft(self, payload: dict, actor: str) -> dict:
        from multilang.domain.content import ContentDraft
        from multilang.services.content_drafts import ContentDraftStore
        from multilang.services.native_content import NativeContentService

        self._enabled()
        draft = ContentDraft.model_validate(payload)
        request, profile = self._content_context(draft.request.model_dump(mode="json"), actor)
        original = ContentDraftStore(self.settings.native_content_drafts_dir).load(
            draft.draft_sha256, namespace=request.namespace
        )
        if original != draft:
            raise ValueError("reviewed draft differs from original provider output")
        matcher = self.plugins.get(
            "analyzer", f"{profile.analyzer_id}-target", profile.analyzer_version
        )
        service = NativeContentService(
            generator=None,
            matcher=matcher,
            provider=draft.provider,
            model_version=draft.model_version,
        )
        return self._save_content(service.complete(draft), actor)

    def _save_content(self, version: ContentVersion, actor: str) -> dict:
        request = version.request
        private = request.namespace != "core"
        self.repository.save_content(
            version_id=version.version_id,
            identity_id=request.lexical_identity_id,
            namespace="custom" if private else "core",
            owner_id=actor if private else "",
            edition_id=request.deck_edition_id,
            payload=model_payload(version),
            search_text=" ".join((version.content.definition, version.content.explanation)),
            actor=actor,
        )
        return {
            "content_version_id": version.version_id,
            "review_status": version.review_status,
            "lexical_identity_id": request.lexical_identity_id,
        }

    def generate_audio(self, payload: dict, actor: str) -> dict:
        self._enabled()
        request = AudioGenerationRequest.model_validate(payload)
        identity, _ = self._identity(request.identity_id)
        signature = request.signature
        profile = self._profile(signature.language, signature.language_profile_version)
        private = request.namespace != "core"
        profile.require("custom" if private else "core", policy_groups=("AUDIO-02",))
        if signature.language != identity.language.value or signature.sense_id != identity.sense_id:
            raise ValueError("audio language/sense differs from lexical identity")
        if profile.provider_locales.get(signature.provider.value) != signature.locale:
            raise ValueError("audio locale is not registered in language profile")
        namespace = f"user:{actor}" if private else "core"
        service = self.audio_service
        if service is None:
            if not self.settings.native_provider_calls_enabled:
                raise ValueError("native provider calls require configured budget and enablement")
            from multilang.runtime import _build_single_audio_adapter
            from multilang.services.audio_synthesis import AudioSynthesisService
            from multilang.services.native_audio import NativeAudioService

            service = NativeAudioService(
                synthesis_service=AudioSynthesisService(
                    adapter=_build_single_audio_adapter(
                        self.settings, self.settings.audio_provider
                    ),
                    settings=self.settings,
                ),
                storage_dir=self.settings.audio_storage_dir,
                provider_model_version=self.settings.native_audio_model_version,
            )
        candidates = self.repository.find_audio(
            signature.signature_sha256, owner_id=actor if private else ""
        )
        cached = AudioVersion.model_validate(candidates[0]) if candidates else None
        version = service.generate(
            signature,
            job_id="native",
            item_key=identity.lexical_identity_id,
            namespace=namespace,
            cached_version=cached,
        )
        self.repository.save_audio(
            version_id=version.version_id,
            signature_sha256=signature.signature_sha256,
            namespace=request.namespace,
            owner_id=actor if private else "",
            payload=model_payload(version),
            actor=actor,
        )
        return {
            "audio_version_id": version.version_id,
            "artifact_sha256": version.artifact_sha256,
            "review_status": version.review_status,
        }

    def export_anki(self, payload: dict, actor: str) -> dict:
        self._enabled()
        request = AnkiExportRequest.model_validate(payload)
        dataset = self.repository.get_dataset(request.dataset_id)
        if dataset is None:
            raise ValueError("unknown shared dataset")
        manifest = DatasetManifest.model_validate(
            {key: value for key, value in dataset.items() if key != "dataset_id"}
        )
        if not request.prototype:
            manifest.require_production()
            if manifest.kind != "ranking":
                raise ValueError("production export requires a reviewed corpus ranking")
            if not request.edition_id:
                raise ValueError("production export requires a frozen canonical edition")
            edition = self.repository.get_edition(request.edition_id)
            if edition.dataset_id != request.dataset_id:
                raise ValueError("edition does not belong to the requested dataset")
            if (
                request.important_form_policy is not None
                and request.important_form_policy != edition.important_form_policy
                or request.optional_roles
                and request.optional_roles != edition.optional_roles
            ):
                raise ValueError("export cannot override frozen edition forms or optional roles")
            profile = self._profile(
                manifest.language.value,
                manifest.metadata.get("profile_version", manifest.policy_version),
            )
            profile.require(
                "core",
                policy_groups=(
                    "ANKI-01",
                    "RANK-01",
                    "FORM-04",
                    "DISPLAY-01",
                    "AUDIO-02",
                    "AISEC-01",
                    "CONTENT-01",
                    "EVAL-01",
                ),
            )
            cards = self.repository.edition_cards(edition)
            from multilang.services.semantic_anki import export_semantic_anki

            output_id = canonical_hash([edition.bundle_sha256, request.model])
            output = Path(self.settings.export_output_dir) / "native" / f"{output_id}.apkg"
            result = export_semantic_anki(
                cards=cards,
                output_path=output,
                model=request.model,
                decision=request.topology,
                evidence_verifier=self.topology_verifier,
            )
            return {
                "export_id": output_id,
                "artifact_sha256": result.artifact_sha256,
                "prototype": False,
                "card_count": len(result.manifest),
                "edition_sha256": edition.bundle_sha256,
            }
        identities = self.repository.dataset_identities(request.dataset_id)
        forms = self.repository.dataset_forms(request.dataset_id)
        approved_forms = (
            request.important_form_policy.select(forms) if request.important_form_policy else ()
        )
        from multilang.services.semantic_anki import export_semantic_anki, project_cards

        cards = project_cards(
            identities=identities,
            approved_forms=approved_forms,
            ranks={member.identity_id: member.rank for member in manifest.members},
            deck_edition_id=manifest.dataset_id,
            inventory=manifest.namespace,
            optional_roles=request.optional_roles,
        )
        versions = [
            ContentVersion.model_validate(row.payload)
            for row in self.session.scalars(
                select(ContentVersionRecord).where(
                    ContentVersionRecord.edition_id == manifest.dataset_id,
                    ContentVersionRecord.owner_id == "",
                )
            )
        ]
        by_card = {}
        for version in versions:
            if version.review_status == "approved":
                if version.request.card_id in by_card:
                    raise ValueError("edition has ambiguous approved content versions")
                by_card[version.request.card_id] = version
        # Attach only versions selected by this edition; no fallback across users.
        enriched = []
        audio_versions = (
            [
                AudioVersion.model_validate(row.payload)
                for row in self.session.scalars(
                    select(AudioVersionRecord).where(AudioVersionRecord.owner_id == "")
                )
            ]
            if by_card
            else []
        )
        audio_index = {}
        for version in audio_versions:
            if version.review_status != "approved":
                continue
            signature = version.signature
            key = (
                signature.language,
                signature.sense_id,
                signature.asset_kind.value,
                signature.display_text,
            )
            audio_index.setdefault(key, []).append(version)
        for card in cards:
            content = by_card.get(card.card_id)
            word, sentence = [], []
            audio = audio_index.get(
                (card.language.value, card.sense_id, "word", card.display_text), []
            )
            if content:
                audio = audio + audio_index.get(
                    (
                        card.language.value,
                        card.sense_id,
                        "sentence",
                        content.content.example_sentence,
                    ),
                    [],
                )
            for version in audio:
                signature = version.signature
                if signature.language != card.language.value or signature.sense_id != card.sense_id:
                    continue
                if (
                    signature.asset_kind.value == "word"
                    and signature.display_text == card.display_text
                    and signature.morphological_analysis_id == card.morphological_analysis_id
                ):
                    word.append(version)
                elif (
                    content
                    and signature.asset_kind.value == "sentence"
                    and signature.display_text == content.content.example_sentence
                ):
                    sentence.append(version)
            if len(word) > 1 or len(sentence) > 1:
                raise ValueError("edition audio requires explicit unambiguous version selection")
            enriched.append(
                SemanticCard.model_validate(
                    card.model_dump(mode="json")
                    | {
                        "content": content,
                        "word_audio": word[0] if word else None,
                        "sentence_audio": sentence[0] if sentence else None,
                    }
                )
            )
        output_id = canonical_hash(
            [
                manifest.dataset_id,
                request.model,
                request.prototype,
                [card.model_dump(mode="json") for card in enriched],
            ]
        )
        output = Path(self.settings.export_output_dir) / "native" / f"{output_id}.apkg"
        result = export_semantic_anki(
            cards=enriched,
            output_path=output,
            model=request.model,
            prototype=request.prototype,
            decision=request.topology,
            evidence_verifier=self.topology_verifier,
        )
        return {
            "export_id": output_id,
            "artifact_sha256": result.artifact_sha256,
            "prototype": result.prototype,
            "card_count": len(result.manifest),
        }

    def freeze_edition(self, payload: dict, actor: str) -> dict:
        self._enabled()
        from multilang.domain.editions import DeckEdition

        edition = DeckEdition.model_validate(payload)
        store = _evidence_store(self.settings)
        self.repository.freeze_edition(
            edition,
            actor=actor,
            verifier=lambda value: store.verify(
                value.approval_receipt_sha256,
                value.model_dump(mode="json", exclude={"approval_receipt_sha256"}),
                purpose="deck-edition",
            ),
        )
        return {"edition_id": edition.edition_id, "bundle_sha256": edition.bundle_sha256}

    def approve_review(self, payload: dict, actor: str) -> dict:
        self._enabled()
        from multilang.services.native_review import NativeReviewService

        return NativeReviewService(self.session, _evidence_store(self.settings)).approve(
            payload, actor=actor
        )

    def _learning(self):
        from multilang.services.native_learning import NativeLearningService

        return NativeLearningService(self.repository, evidence_store=_evidence_store(self.settings))

    def import_history(self, payload: dict, actor: str) -> dict:
        """Local operator CLI only; HTTP clients cannot supply server paths."""
        self._enabled()
        request = HistoryImportRequest.model_validate(payload)
        service = self._learning()
        result = service.import_history(
            owner_id=actor,
            path=request.path,
            expected_revision=request.expected_revision,
            alias_guids=request.alias_guids,
        )
        return {
            "import_id": result.import_id,
            "mapped_count": len(result.states),
            "quarantined_count": result.quarantined_count,
            "raw_copy_retained": False,
            "revision": service.get_state(owner_id=actor).revision,
        }

    def register_history_aliases(self, payload: dict, actor: str) -> dict:
        self._enabled()
        request = HistoryAliasRequest.model_validate(payload)
        count = self._learning().register_aliases(
            aliases=request.aliases, receipt_sha256=request.receipt_sha256, actor=actor
        )
        return {"registered_aliases": count}

    def _legacy_alias_adapter(self):
        store = _evidence_store(self.settings)
        return LegacyIdentityAdapter(
            self.session,
            evidence_verifier=lambda candidate: store.verify(
                candidate.evidence_sha256,
                candidate.model_dump(mode="json", exclude={"evidence_sha256"}),
                purpose="legacy-identity-alias",
            ),
        )

    def preview_legacy_aliases(self, payload: dict, actor: str) -> dict:
        self._enabled()
        request = LegacyAliasesRequest.model_validate(payload)
        preview = self._legacy_alias_adapter().preview(request.candidates)
        return {
            "preview": model_payload(preview),
            "confirmation_sha256": preview.confirmation_sha256,
        }

    def apply_legacy_aliases(self, payload: dict, actor: str) -> dict:
        self._enabled()
        request = LegacyAliasesApplyRequest.model_validate(payload)
        return self._legacy_alias_adapter().apply(
            request.preview, confirmation_sha256=request.confirmation_sha256, actor=actor
        )

    def update_learner_state(self, payload: dict, actor: str) -> dict:
        self._enabled()
        request = LearnerUpdateRequest.model_validate(payload)
        service = self._learning()
        common = {"owner_id": actor, "expected_revision": request.expected_revision}
        if request.action in {"known", "reading"}:
            operation = service.set_known if request.action == "known" else service.set_reading
            state = operation(card_ids=request.card_ids, **common)
        elif request.action == "expansion":
            state = service.set_expansion(enabled=request.enabled, **common)
        elif request.action == "override":
            if request.card_id is None:
                raise ValueError("priority override requires card_id")
            state = service.override(card_id=request.card_id, priority=request.priority, **common)
        elif request.action == "reset":
            state = service.reset(**common)
        elif request.action == "revoke":
            if request.import_id is None:
                raise ValueError("history revocation requires import_id")
            state = service.revoke_history(import_id=request.import_id, **common)
        else:
            service.delete(**common)
            return {"learner_state_deleted": True}
        return {
            "revision": state.revision,
            "history_count": len(state.history),
            "known_card_count": len(state.known_card_ids),
        }

    def adaptive_queue(self, payload: dict, actor: str) -> dict:
        self._enabled()
        from multilang.services.semantic_anki import project_cards

        request = AdaptiveQueueRequest.model_validate(payload)
        cards = []
        for dataset_id in request.dataset_ids:
            data = self.repository.get_dataset(dataset_id)
            owner_id = ""
            if data is None:
                data = self.repository.get_dataset(dataset_id, owner_id=actor)
                owner_id = actor
            if data is None:
                raise ValueError("unknown accessible dataset")
            manifest = DatasetManifest.model_validate(data)
            forms = self.repository.dataset_forms(dataset_id, owner_id=owner_id)
            selected = (
                request.important_form_policy.select(forms) if request.important_form_policy else ()
            )
            cards.extend(
                project_cards(
                    identities=self.repository.dataset_identities(dataset_id, owner_id=owner_id),
                    approved_forms=selected,
                    ranks={m.identity_id: m.rank for m in manifest.members},
                    deck_edition_id=dataset_id,
                    inventory=manifest.namespace,
                    namespace=f"user:{actor}" if owner_id else "core",
                )
            )
            if len(cards) > request.policy.max_cards:
                raise ValueError("adaptive preparation workload exceeds configured limit")
        return (
            self._learning()
            .queue(owner_id=actor, cards=cards, policy=request.policy)
            .model_dump(mode="json")
        )


def _evidence_store(settings: Settings):
    from multilang.services.native_evidence import EvidenceStore

    signing_key = getattr(settings, "native_evidence_signing_key", None)
    return EvidenceStore(
        getattr(settings, "native_evidence_dir", Path(".multilang/evidence")),
        key=signing_key.get_secret_value().encode() if signing_key else None,
    )


def build_native_facade(session: Session, settings: Settings) -> NativeFacade:
    from multilang.services.contextual_bindings import (
        ReviewedBindingStore,
        StoredContextualTargetMatcher,
    )
    from multilang.services.contextual_morphology import LocalContextualMorphologyService

    store = _evidence_store(settings)
    plugins = PluginRegistry()
    for kind, name, version in NATIVE_PLUGINS.inventory():
        plugins.register(
            kind=kind, name=name, version=version, plugin=NATIVE_PLUGINS.get(kind, name, version)
        )
    plugins.register(
        kind="analyzer",
        name="contextual-morphology-target",
        version="1",
        plugin=StoredContextualTargetMatcher(
            analyzer=LocalContextualMorphologyService(
                model_root=settings.native_language_models_dir,
                **(
                    {"model_profiles": settings.native_language_model_profiles}
                    if settings.native_language_model_profiles
                    else {}
                ),
            ),
            store=ReviewedBindingStore(
                settings.native_contextual_bindings_dir, verifier=store.verify
            ),
        ),
    )
    return NativeFacade(session, settings, plugins=plugins, topology_verifier=store.verify_topology)
