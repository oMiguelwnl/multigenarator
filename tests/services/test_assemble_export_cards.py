"""Tests for deterministic export-card assembly."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from importlib.util import find_spec
from types import SimpleNamespace

import pytest

from multilang.domain.audio import (
    AudioAssetKind,
    AudioAssetRecord,
    AudioFormat,
    AudioProvenance,
    AudioProvider,
    AudioReviewStatus,
    AudioSynthesisStatus,
    NormalizedTtsInput,
)
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.korean import KoreanAnalyzerFingerprint, KoreanLexicalIdentity, KoreanSignatureItem
from multilang.domain.lexicon import (
    DefinitionRecord,
    GroundingStatus,
    KoreanFrequencyLexicalEvidence,
    LexicalCardCandidate,
    LexicalProvenance,
)
from multilang.domain.text_quality import (
    ConfidenceLabel,
    KoreanAdaptiveIPlusOneEvidence,
    ReviewStatus,
    TextGenerationStatus,
    TextProvenance,
    TextQualityRecord,
    ValidationStatus,
)
from multilang.domain.exporting import (
    FREQUENCY_EXPORT_CARD_FIELD_NAMES,
    HIGHLIGHT_EXPORT_CARD_FIELD_NAMES,
    JAPANESE_EXPORT_CARD_FIELD_NAMES,
    LATIN_EXPORT_CARD_FIELD_NAMES,
    MANDARIN_EXPORT_CARD_FIELD_NAMES,
    MANUAL_EXPORT_CARD_FIELD_NAMES,
    ExportCardIdentity,
    ExportCardRow,
    export_field_names_for_rows,
)
from multilang.services.assemble_export_cards import AssembleExportCardsError, AssembleExportCardsService
from multilang.services.mandarin_orthography import MandarinOrthography, MandarinOrthographyError


_HASH_A = "a" * 64
_HASH_B = "b" * 64
_HASH_C = "c" * 64
_HASH_D = "d" * 64
_HASH_E = "e" * 64
_HASH_F = "f" * 64


def make_text_record(
    *,
    item_key: str,
    example_sentence: str = "I use run <fast> & often.",
    translation_text: str = "Eu corro <rápido> & sempre.",
) -> TextQualityRecord:
    return TextQualityRecord(
        job_id="job-1",
        item_key=item_key,
        lexical_candidate_id=f"lex-{item_key}",
        example_sentence=example_sentence,
        translation_text=translation_text,
        generation_status=TextGenerationStatus.GENERATED,
        validation_status=ValidationStatus.PASSED,
        review_status=ReviewStatus.ACCEPTED,
        repair_attempt_count=0,
        confidence_score=0.95,
        confidence_label=ConfidenceLabel.HIGH,
        validation_flags=[],
        review_reason=None,
        sentence_provenance=TextProvenance(source="generator", provider="local"),
        translation_provenance=TextProvenance(source="translator", provider="local"),
    )


def make_candidate(
    *,
    item_key: str,
    definitions_html: str = "verb: to run<ul><li>verb: to move & jump</li></ul>",
    ipa: str | None = None,
    spoken_form: str | None = None,
) -> LexicalCardCandidate:
    return LexicalCardCandidate(
        submitted_form=item_key,
        display_form=f"{item_key} <front>",
        lemma=item_key,
        lemma_key=f"en:{item_key}",
        frequency_rank=12,
        frequency_level=1,
        definitions_html=definitions_html,
        definition_language="en",
        ipa=ipa if ipa is not None else f"/{item_key}/",
        spoken_form=spoken_form if spoken_form is not None else item_key.upper(),
        translation_target_language="pt",
        grounding_status=GroundingStatus.GROUNDED,
        provenance=LexicalProvenance(
            source="manual",
            definition=DefinitionRecord(source="manual", value=definitions_html),
        ),
    )


def make_asset(*, item_key: str, asset_kind: AudioAssetKind, storage_path: str) -> AudioAssetRecord:
    display_text = item_key if asset_kind is AudioAssetKind.WORD else f"I use {item_key} every day."
    normalized = NormalizedTtsInput(
        display_text=display_text,
        tts_text=display_text,
        ssml_text=f"<speak version=\"1.0\">{display_text}</speak>",
    )
    return AudioAssetRecord(
        job_id="job-1",
        item_key=item_key,
        asset_kind=asset_kind,
        display_text=display_text,
        normalized_input=normalized,
        provenance=AudioProvenance(
            provider=AudioProvider.AZURE,
            voice_id="en-US-JennyNeural",
            locale="en-US",
            format=AudioFormat.AUDIO_24KHZ_48KBITRATE_MONO_MP3,
            text_hash=normalized.text_hash or "",
            ssml_hash=normalized.ssml_hash or "",
            storage_path=storage_path,
            byte_size=4096,
            duration_ms=800,
            status=AudioSynthesisStatus.SYNTHESIZED,
        ),
    )


def make_korean_asset(
    *,
    item_key: str,
    asset_kind: AudioAssetKind,
    display_text: str,
    storage_path: str,
    artifact_sha256: str,
    approved: bool = True,
) -> AudioAssetRecord:
    normalized = NormalizedTtsInput(
        display_text=display_text,
        tts_text=display_text,
        ssml_text=f"<speak version=\"1.0\">{display_text}</speak>",
        synthesis_request_sha256=_HASH_D,
    )
    review_status = AudioReviewStatus.APPROVED if approved else AudioReviewStatus.SYNTHESIZED_PENDING
    return AudioAssetRecord(
        job_id="job-1",
        item_key=item_key,
        asset_kind=asset_kind,
        display_text=display_text,
        normalized_input=normalized,
        provenance=AudioProvenance(
            provider=AudioProvider.AZURE,
            voice_id="ko-KR-SunHiNeural",
            locale="ko-KR",
            format=AudioFormat.AUDIO_24KHZ_48KBITRATE_MONO_MP3,
            text_hash=normalized.text_hash or "",
            ssml_hash=normalized.ssml_hash or "",
            storage_path=storage_path,
            byte_size=4096,
            duration_ms=900,
            status=AudioSynthesisStatus.SYNTHESIZED,
            fallback_used=False,
            provider_sdk_version="1.49.1",
            voice_profile_sha256=_HASH_A,
            catalog_receipt_sha256=_HASH_B,
            synthesis_request_sha256=_HASH_D,
            artifact_sha256=artifact_sha256,
            audio_review_status=review_status,
            audio_review_receipt_sha256=_HASH_E if approved else None,
            heard_review_receipt_sha256=_HASH_F if approved else None,
        ),
    )


def make_korean_fingerprint() -> KoreanAnalyzerFingerprint:
    return KoreanAnalyzerFingerprint(
        analyzer_name="kiwi",
        analyzer_package_version="0.23.2",
        model_package_version="0.23.0",
        model_type="cong",
        enabled_dialects="standard",
        num_workers=1,
        integrate_allomorph=True,
        top_n=2,
        split_complex=False,
        compatible_jamo=False,
        normalize_coda=False,
        z_coda=False,
        typos=None,
        oov_handling="chr",
        policy_version="kiwi-top2-consensus-v1",
    )


def make_korean_candidate(*, rank: int = 1001, level: int = 2, bundle_sha256: str = _HASH_A) -> LexicalCardCandidate:
    fingerprint = make_korean_fingerprint()
    identity = KoreanLexicalIdentity(
        submitted_form="학교",
        canonical_nfc="학교",
        lemma="학교",
        part_of_speech="NNG",
        sense_id="nikl:1001",
        register="standard",
        morpheme_signature=(KoreanSignatureItem(form="학교", pos="NNG"),),
        analyzer_fingerprint=fingerprint,
        status="resolved",
    )
    evidence = KoreanFrequencyLexicalEvidence(
        source_id="nikl-korean-learners-vocabulary",
        source_version="2003-06-04.revised-2019-05-30",
        source_rank=rank + 10,
        final_rank=rank,
        level=level,
        part_of_speech="NNG",
        sense_id="nikl:1001",
        grounding_confidence="reviewed-source-backed",
        license_decision="approved-local-use",
        curation_decision="accepted",
        bundle_sha256=bundle_sha256,
        source_sha256=_HASH_B,
        source_review_receipt_sha256=_HASH_C,
        source_review_aggregate_sha256=_HASH_D,
        analyzer_fingerprint=fingerprint,
    )
    return LexicalCardCandidate(
        submitted_form="학교",
        display_form="학교",
        lemma="학교",
        lemma_key=identity.lexical_key,
        frequency_rank=rank,
        frequency_level=level,
        definitions_html="substantivo: escola",
        definition_language="pt",
        ipa="/hak̚.k͈jo/",
        spoken_form="학교",
        translation_target_language="pt",
        grounding_status=GroundingStatus.GROUNDED,
        provenance=LexicalProvenance(source="korean-frequency-bundle"),
        korean_identity=identity,
        korean_frequency_evidence=evidence,
    )


def make_korean_text_record(
    *,
    item_key: str = "학교",
    text_review_receipt_sha256: str | None = _HASH_C,
    bundle_sha256: str = _HASH_A,
) -> TextQualityRecord:
    return make_text_record(
        item_key=item_key,
        example_sentence="학교에 가요.",
        translation_text="Eu vou para a escola.",
    ).model_copy(
        update={
            "adaptive_i_plus_one_evidence": KoreanAdaptiveIPlusOneEvidence(
                known_prefix_sha256=_HASH_A,
                known_concept_ids=("ko:foundation",),
                known_concept_count=1,
                frequency_bundle_content_sha256=bundle_sha256,
                candidate_sha256=_HASH_B,
                selected_ordinal=1,
                target_concept_id="ko:lexeme:school",
                observed_concept_ids=("ko:foundation", "ko:lexeme:school"),
                scorer_version="adaptive-i-plus-one-v1",
            ),
            "text_review_receipt_sha256": text_review_receipt_sha256,
        }
    )


@dataclass
class FakeTextRepository:
    accepted_records: list[TextQualityRecord]

    def list_accepted_records(self, job_id: str) -> list[TextQualityRecord]:
        return [record for record in self.accepted_records if record.job_id == job_id]


@dataclass
class FakeLexicalRepository:
    candidates: dict[str, LexicalCardCandidate]

    def get_candidate_for_item(self, job_id: str, item_key: str) -> LexicalCardCandidate | None:
        return self.candidates.get(item_key)


@dataclass
class FakeAudioRepository:
    assets: dict[tuple[str, str], AudioAssetRecord]

    def get_asset(self, job_id: str, item_key: str, asset_kind: AudioAssetKind) -> AudioAssetRecord | None:
        return self.assets.get((item_key, asset_kind.value))


@dataclass
class PreloadingAudioRepository(FakeAudioRepository):
    list_calls: int = 0
    get_calls: int = 0

    def list_assets_for_job(self, job_id: str) -> list[AudioAssetRecord]:
        self.list_calls += 1
        return list(self.assets.values())

    def get_asset(self, job_id: str, item_key: str, asset_kind: AudioAssetKind) -> AudioAssetRecord | None:
        self.get_calls += 1
        return super().get_asset(job_id, item_key, asset_kind)


@dataclass
class FakeExportRepository:
    saved_rows: list[object] = field(default_factory=list)

    def upsert_card_snapshot(self, record: object) -> object:
        self.saved_rows.append(record)
        return record


@dataclass
class BulkExportRepository(FakeExportRepository):
    bulk_calls: int = 0

    def upsert_card_snapshots(self, records: list[object]) -> list[object]:
        self.bulk_calls += 1
        self.saved_rows.extend(records)
        return list(records)


@dataclass
class FakeMandarinOrthographyService:
    value: MandarinOrthography | None = None
    error: MandarinOrthographyError | None = None
    calls: list[tuple[str, str]] = field(default_factory=list)

    def derive(self, *, word: str, sentence: str) -> MandarinOrthography:
        self.calls.append((word, sentence))
        if self.error is not None:
            raise self.error
        assert self.value is not None
        return self.value


def make_mandarin_candidate(*, item_key: str, source_type: str) -> object:
    payload = make_candidate(item_key=item_key, ipa=None).model_dump()
    payload.update(
        {
            "submitted_form": item_key,
            "display_form": item_key,
            "lemma": item_key,
            "lemma_key": f"zh:{item_key}",
            "ipa": None,
            "spoken_form": item_key,
            "frequency_rank": 1 if source_type == "frequency" else None,
            "frequency_level": 1 if source_type == "frequency" else None,
        }
    )
    if source_type == "frequency":
        return LexicalCardCandidate(**payload)
    return SimpleNamespace(**payload, source_type=source_type)


def build_service(
    *,
    accepted_records: list[TextQualityRecord],
    candidates: dict[str, LexicalCardCandidate],
    assets: dict[tuple[str, str], AudioAssetRecord],
    export_repository: FakeExportRepository | None = None,
    mandarin_orthography_service: FakeMandarinOrthographyService | None = None,
) -> tuple[AssembleExportCardsService, FakeExportRepository]:
    repository = export_repository or FakeExportRepository()
    service = AssembleExportCardsService(
        text_repository=FakeTextRepository(accepted_records=accepted_records),
        lexical_repository=FakeLexicalRepository(candidates=candidates),
        audio_repository=FakeAudioRepository(assets=assets),
        export_repository=repository,
        mandarin_orthography_service=mandarin_orthography_service,
    )
    return service, repository


@pytest.mark.parametrize("source_type", ["frequency", "word-list"])
def test_assemble_mandarin_derives_once_and_requires_both_audio_assets(source_type: str) -> None:
    orthography = FakeMandarinOrthographyService(
        value=MandarinOrthography(
            word_pinyin="zhōng <guó>",
            word_traditional="中國",
            sentence_pinyin="wǒ qù yín háng。",
            sentence_traditional="我去銀行。",
        )
    )
    service, repository = build_service(
        accepted_records=[make_text_record(item_key="中国", example_sentence="我去银行。", translation_text="I go to the bank.")],
        candidates={"中国": make_mandarin_candidate(item_key="中国", source_type=source_type)},
        assets={
            ("中国", AudioAssetKind.WORD.value): make_asset(
                item_key="中国", asset_kind=AudioAssetKind.WORD, storage_path="audio/word/zh-word.mp3"
            ),
            ("中国", AudioAssetKind.SENTENCE.value): make_asset(
                item_key="中国", asset_kind=AudioAssetKind.SENTENCE, storage_path="audio/sentence/zh-sentence.mp3"
            ),
        },
        mandarin_orthography_service=orthography,
    )

    result = service.execute(job_id="job-1", deck_language=SupportedLanguage.ZH)
    row = result.cards[0]

    assert orthography.calls == [("中国", "我去银行。")]
    assert tuple(row.ordered_field_mapping()) == MANDARIN_EXPORT_CARD_FIELD_NAMES
    assert row.mandarin_word_pinyin == "zhōng &lt;guó&gt;"
    assert row.mandarin_word_traditional == "中國"
    assert row.mandarin_sentence_pinyin == "wǒ qù yín háng。"
    assert row.mandarin_sentence_traditional == "我去銀行。"
    assert row.ipa is None
    assert row.word_audio == "[sound:zh-word.mp3]"
    assert row.sentence_audio == "[sound:zh-sentence.mp3]"
    assert repository.saved_rows == [row]


def test_assemble_mandarin_wraps_orthography_errors_with_item_context() -> None:
    orthography = FakeMandarinOrthographyService(error=MandarinOrthographyError("Traditional primary text"))
    service, _ = build_service(
        accepted_records=[make_text_record(item_key="中國", example_sentence="我去銀行。")],
        candidates={"中國": make_mandarin_candidate(item_key="中國", source_type="frequency")},
        assets={
            ("中國", AudioAssetKind.WORD.value): make_asset(
                item_key="中國", asset_kind=AudioAssetKind.WORD, storage_path="audio/word/zh-word.mp3"
            ),
            ("中國", AudioAssetKind.SENTENCE.value): make_asset(
                item_key="中國", asset_kind=AudioAssetKind.SENTENCE, storage_path="audio/sentence/zh-sentence.mp3"
            ),
        },
        mandarin_orthography_service=orthography,
    )

    with pytest.raises(AssembleExportCardsError, match="中國.*Traditional primary text"):
        service.execute(job_id="job-1", deck_language=SupportedLanguage.ZH)


def test_assemble_korean_frequency_rows_require_reviewed_manifest_text_audio_and_preserve_identity() -> None:
    candidate = make_korean_candidate(rank=1001, level=2)
    text_record = make_korean_text_record()
    service, repository = build_service(
        accepted_records=[text_record],
        candidates={"학교": candidate},
        assets={
            ("학교", AudioAssetKind.WORD.value): make_korean_asset(
                item_key="학교",
                asset_kind=AudioAssetKind.WORD,
                display_text="학교",
                storage_path="audio/ko-school-word.mp3",
                artifact_sha256=_HASH_E,
            ),
            ("학교", AudioAssetKind.SENTENCE.value): make_korean_asset(
                item_key="학교",
                asset_kind=AudioAssetKind.SENTENCE,
                display_text="학교에 가요.",
                storage_path="audio/ko-school-sentence.mp3",
                artifact_sha256=_HASH_F,
            ),
        },
    )

    row = service.execute(job_id="job-1", deck_language=SupportedLanguage.KO).cards[0]
    changed_internal = row.model_copy(
        update={
            "text_review_receipt_sha256": _HASH_D,
            "word_audio_artifact_sha256": _HASH_A,
            "sentence_audio_artifact_sha256": _HASH_B,
            "export_gate_receipt_sha256": _HASH_E,
        }
    )

    assert row.sort_index == 1001
    assert row.frequency_level == 2
    assert row.frequency_bundle_sha256 == _HASH_A
    assert row.text_review_receipt_sha256 == _HASH_C
    assert row.word_audio_artifact_sha256 == _HASH_E
    assert row.sentence_audio_artifact_sha256 == _HASH_F
    assert len(row.export_gate_receipt_sha256 or "") == 64
    assert tuple(row.ordered_field_mapping()) == FREQUENCY_EXPORT_CARD_FIELD_NAMES
    assert row.ordered_field_mapping()["Image"] == ""
    assert changed_internal.note_guid == row.note_guid
    assert repository.saved_rows == [row]


@pytest.mark.parametrize(
    ("text_record", "word_asset", "message"),
    [
        (
            make_korean_text_record(text_review_receipt_sha256=None),
            make_korean_asset(
                item_key="학교",
                asset_kind=AudioAssetKind.WORD,
                display_text="학교",
                storage_path="audio/ko-school-word.mp3",
                artifact_sha256=_HASH_E,
            ),
            "text review receipt",
        ),
        (
            make_korean_text_record(bundle_sha256=_HASH_B),
            make_korean_asset(
                item_key="학교",
                asset_kind=AudioAssetKind.WORD,
                display_text="학교",
                storage_path="audio/ko-school-word.mp3",
                artifact_sha256=_HASH_E,
            ),
            "frequency bundle",
        ),
        (
            make_korean_text_record(),
            make_korean_asset(
                item_key="학교",
                asset_kind=AudioAssetKind.WORD,
                display_text="학교",
                storage_path="audio/ko-school-word.mp3",
                artifact_sha256=_HASH_E,
                approved=False,
            ),
            "reviewed non-fallback word audio",
        ),
    ],
)
def test_assemble_korean_frequency_rejects_stale_or_unreviewed_final_evidence(
    text_record: TextQualityRecord,
    word_asset: AudioAssetRecord,
    message: str,
) -> None:
    service, repository = build_service(
        accepted_records=[text_record],
        candidates={"학교": make_korean_candidate(rank=1001, level=2)},
        assets={
            ("학교", AudioAssetKind.WORD.value): word_asset,
            ("학교", AudioAssetKind.SENTENCE.value): make_korean_asset(
                item_key="학교",
                asset_kind=AudioAssetKind.SENTENCE,
                display_text="학교에 가요.",
                storage_path="audio/ko-school-sentence.mp3",
                artifact_sha256=_HASH_F,
            ),
        },
    )

    with pytest.raises(AssembleExportCardsError, match=message):
        service.execute(job_id="job-1", deck_language=SupportedLanguage.KO)
    assert repository.saved_rows == []


def test_assemble_mandarin_rejects_invalid_pinyin_before_persisting_snapshot() -> None:
    service, repository = build_service(
        accepted_records=[make_text_record(item_key="㐂", example_sentence="我用㐂。", translation_text="I use the target.")],
        candidates={"㐂": make_mandarin_candidate(item_key="㐂", source_type="frequency")},
        assets={
            ("㐂", AudioAssetKind.WORD.value): make_asset(
                item_key="㐂", asset_kind=AudioAssetKind.WORD, storage_path="audio/word/zh-word.mp3"
            ),
            ("㐂", AudioAssetKind.SENTENCE.value): make_asset(
                item_key="㐂", asset_kind=AudioAssetKind.SENTENCE, storage_path="audio/sentence/zh-sentence.mp3"
            ),
        },
    )

    with pytest.raises(AssembleExportCardsError, match="㐂.*pinyin"):
        service.execute(job_id="job-1", deck_language=SupportedLanguage.ZH)
    assert repository.saved_rows == []


def test_assemble_export_cards_preloads_audio_and_persists_snapshots_in_batch() -> None:
    assets = {
        ("run", AudioAssetKind.WORD.value): make_asset(item_key="run", asset_kind=AudioAssetKind.WORD, storage_path="run-word.mp3"),
        ("run", AudioAssetKind.SENTENCE.value): make_asset(item_key="run", asset_kind=AudioAssetKind.SENTENCE, storage_path="run-sentence.mp3"),
        ("jump", AudioAssetKind.WORD.value): make_asset(item_key="jump", asset_kind=AudioAssetKind.WORD, storage_path="jump-word.mp3"),
        ("jump", AudioAssetKind.SENTENCE.value): make_asset(item_key="jump", asset_kind=AudioAssetKind.SENTENCE, storage_path="jump-sentence.mp3"),
    }
    audio_repository = PreloadingAudioRepository(assets=assets)
    export_repository = BulkExportRepository()
    service = AssembleExportCardsService(
        text_repository=FakeTextRepository(accepted_records=[make_text_record(item_key="run"), make_text_record(item_key="jump")]),
        lexical_repository=FakeLexicalRepository(candidates={"run": make_candidate(item_key="run"), "jump": make_candidate(item_key="jump")}),
        audio_repository=audio_repository,
        export_repository=export_repository,
    )

    result = service.execute(job_id="job-1", deck_language=SupportedLanguage.EN)

    assert len(result.cards) == 2
    assert audio_repository.list_calls == 1
    assert audio_repository.get_calls == 0
    assert export_repository.bulk_calls == 1
    assert len(export_repository.saved_rows) == 2


def test_assemble_export_cards_persists_exact_field_order_and_sound_tags() -> None:
    service, export_repository = build_service(
        accepted_records=[make_text_record(item_key="run")],
        candidates={"run": make_candidate(item_key="run")},
        assets={
            ("run", AudioAssetKind.WORD.value): make_asset(
                item_key="run", asset_kind=AudioAssetKind.WORD, storage_path="/tmp/audio/word/run-word.mp3"
            ),
            ("run", AudioAssetKind.SENTENCE.value): make_asset(
                item_key="run", asset_kind=AudioAssetKind.SENTENCE, storage_path="cache/audio/run-sentence.mp3"
            ),
        },
    )

    result = service.execute(job_id="job-1", deck_language=SupportedLanguage.EN)
    row = result.cards[0]

    assert tuple(row.ordered_field_mapping().keys()) == (
        "SortIndex",
        "word",
        "IPA",
        "Definitions",
        "Example Sentence",
        "Translation",
        "word_audio",
        "sentence_audio",
        "Image",
    )
    assert row.word_audio == "[sound:run-word.mp3]"
    assert row.sentence_audio == "[sound:run-sentence.mp3]"
    assert row.ipa == "/run/"
    assert export_repository.saved_rows[0].note_guid == row.note_guid


def test_assemble_export_cards_blocks_mismatched_word_audio_before_persisting() -> None:
    corrupted_word = make_asset(item_key="jump", asset_kind=AudioAssetKind.WORD, storage_path="jump-word.mp3").model_copy(
        update={"item_key": "run"}
    )
    service, export_repository = build_service(
        accepted_records=[make_text_record(item_key="run")],
        candidates={"run": make_candidate(item_key="run")},
        assets={
            ("run", AudioAssetKind.WORD.value): corrupted_word,
            ("run", AudioAssetKind.SENTENCE.value): make_asset(item_key="run", asset_kind=AudioAssetKind.SENTENCE, storage_path="run-sentence.mp3"),
        },
    )

    with pytest.raises(AssembleExportCardsError) as exc_info:
        service.execute(job_id="job-1", deck_language=SupportedLanguage.EN)

    message = str(exc_info.value)
    assert "word_audio" in message
    assert "Word" in message
    assert "run" in message
    assert export_repository.saved_rows == []


def test_assemble_export_cards_renders_ipa_without_spoken_form_suffix() -> None:
    service, _ = build_service(
        accepted_records=[make_text_record(item_key="casa")],
        candidates={"casa": make_candidate(item_key="casa", ipa="/ˈkaza/", spoken_form="KA-za")},
        assets={
            ("casa", AudioAssetKind.WORD.value): make_asset(item_key="casa", asset_kind=AudioAssetKind.WORD, storage_path="casa-word.mp3"),
            ("casa", AudioAssetKind.SENTENCE.value): make_asset(item_key="casa", asset_kind=AudioAssetKind.SENTENCE, storage_path="casa-sentence.mp3"),
        },
    )

    row = service.execute(job_id="job-1", deck_language=SupportedLanguage.EN).cards[0]

    assert row.ipa == "/ˈkaza/"


def test_assemble_export_cards_strips_redundant_parenthetical_word_hint_from_ipa() -> None:
    service, _ = build_service(
        accepted_records=[make_text_record(item_key="громко")],
        candidates={"громко": make_candidate(item_key="громко", ipa="[ˈɡromkə] (гро́мко)", spoken_form="гро́мко")},
        assets={
            ("громко", AudioAssetKind.WORD.value): make_asset(item_key="громко", asset_kind=AudioAssetKind.WORD, storage_path="gromko-word.mp3"),
            ("громко", AudioAssetKind.SENTENCE.value): make_asset(item_key="громко", asset_kind=AudioAssetKind.SENTENCE, storage_path="gromko-sentence.mp3"),
        },
    )

    row = service.execute(job_id="job-1", deck_language=SupportedLanguage.RU).cards[0]

    assert row.ipa == "[ˈɡromkə]"


def test_assemble_export_cards_builds_highlight_row_without_translation_field() -> None:
    highlight_payload = make_candidate(item_key="wash", ipa="/wɑʃ/", spoken_form="wash").model_dump()
    highlight_payload.update({"source_type": "kindle-highlights", "frequency_rank": None, "frequency_level": None})
    highlight_candidate = SimpleNamespace(**highlight_payload)
    service, _ = build_service(
        accepted_records=[
            make_text_record(
                item_key="wash",
                example_sentence="Readers wash every cup before the quiet chapter ends.",
                translation_text="Provider translation should not become learner-facing.",
            )
        ],
        candidates={"wash": highlight_candidate},
        assets={
            ("wash", AudioAssetKind.SENTENCE.value): make_asset(item_key="wash", asset_kind=AudioAssetKind.SENTENCE, storage_path="wash-sentence.mp3"),
        },
    )

    row = service.execute(job_id="job-1", deck_language=SupportedLanguage.EN).cards[0]
    mapping = row.ordered_field_mapping()

    assert tuple(mapping) == ("SortIndex", "Word", "IPA", "Example Sentence", "sentence_audio", "Definition", "Image")
    assert row.identity.source_type == "kindle-highlights"
    assert row.word == "wash"
    assert row.ipa == "/wɑʃ/"
    assert row.translation == ""
    assert "Translation" not in mapping
    assert mapping["Image"] == ""
    assert row.word_audio == ""
    assert mapping["sentence_audio"] == "[sound:wash-sentence.mp3]"


def test_japanese_export_row_requires_valid_romaji_and_preserves_non_japanese_contracts() -> None:
    assert JAPANESE_EXPORT_CARD_FIELD_NAMES == (
        "SortIndex",
        "Target Word",
        "Word Reading",
        "Word Romaji",
        "Definition",
        "Sentence",
        "Sentence Furigana",
        "Sentence Romaji",
        "Sentence Translation",
        "word_audio",
        "sentence_audio",
        "Image",
    )
    assert FREQUENCY_EXPORT_CARD_FIELD_NAMES == (
        "SortIndex", "word", "IPA", "Definitions", "Example Sentence", "Translation",
        "word_audio", "sentence_audio", "Image",
    )
    assert HIGHLIGHT_EXPORT_CARD_FIELD_NAMES == (
        "SortIndex", "Word", "IPA", "Example Sentence", "sentence_audio", "Definition", "Image",
    )
    assert MANUAL_EXPORT_CARD_FIELD_NAMES == HIGHLIGHT_EXPORT_CARD_FIELD_NAMES
    assert LATIN_EXPORT_CARD_FIELD_NAMES == (
        "SortIndex", "Word", "Definition", "Sentence", "Sentence Translation", "Grammar",
        "word_audio", "sentence_audio", "Image",
    )
    assert MANDARIN_EXPORT_CARD_FIELD_NAMES == (
        "SortIndex", "word", "Pinyin", "Traditional", "Definitions", "Example Sentence",
        "Sentence Pinyin", "Traditional Sentence", "Translation", "word_audio", "sentence_audio", "Image",
    )

    identity = ExportCardIdentity(
        language=SupportedLanguage.JA,
        source_type="frequency",
        job_id="job-ja",
        item_key="何",
        lemma_key="ja:何",
        sort_index=1,
    )
    payload = {
        "identity": identity,
        "word": "何",
        "front_of_card": "何",
        "ipa": None,
        "definitions": "pronoun: what",
        "example_sentence": "何しているの？",
        "translation": "What are you doing?",
        "word_audio": "[sound:nani.mp3]",
        "sentence_audio": "[sound:nani-sentence.mp3]",
        "word_reading": "何[なに]",
        "word_romaji": "Nani",
        "sentence_furigana": "何[なに]しているの？",
        "sentence_romaji": "Nan shite iru no?",
    }
    row = ExportCardRow(**payload)
    assert tuple(row.ordered_field_mapping()) == JAPANESE_EXPORT_CARD_FIELD_NAMES
    assert row.ordered_field_mapping()["Image"] == ""

    changed = ExportCardRow(**{**payload, "word_romaji": "Nani (changed)", "sentence_romaji": "Changed?"})
    assert changed.note_guid == row.note_guid

    for field_name in ("word_reading", "word_romaji", "sentence_furigana", "sentence_romaji"):
        with pytest.raises(ValueError, match="Japanese export rows require non-empty fields"):
            ExportCardRow(**{**payload, field_name: "   "})

    for invalid_values in (
        {"word_romaji": "?"},
        {"word_romaji": "学校"},
        {"sentence_romaji": "Nan shite iru no??"},
        {"sentence_romaji": "何 shite iru no?"},
    ):
        with pytest.raises(ValueError, match="romaji"):
            ExportCardRow(**{**payload, **invalid_values})


def test_assemble_export_cards_builds_japanese_row_without_ipa(monkeypatch: pytest.MonkeyPatch) -> None:
    romaji_calls: list[str] = []
    furigana_calls: list[str] = []

    def fake_romanize(source: str) -> str:
        romaji_calls.append(source)
        return {
            "学校": "Gakkou <word>",
            "学校に行く。": "Gakkou ni iku. & sentence",
        }[source]

    def fake_furigana(source: str) -> str:
        furigana_calls.append(source)
        return {
            "学校": "学校[がっこう]",
            "学校に行く。": "学校[がっこう]に行[い]く。",
        }[source]

    monkeypatch.setattr("multilang.services.assemble_export_cards.romanize_japanese", fake_romanize, raising=False)
    monkeypatch.setattr("multilang.services.assemble_export_cards.format_japanese_furigana", fake_furigana)
    candidate = make_candidate(item_key="学校", definitions_html="noun: school", ipa=None, spoken_form=None).model_copy(
        update={"display_form": "学校", "lemma_key": "ja:学校"}
    )
    service, _ = build_service(
        accepted_records=[
            make_text_record(
                item_key="学校",
                example_sentence="学校に行く。",
                translation_text="I go to school.",
            )
        ],
        candidates={"学校": candidate},
        assets={
            ("学校", AudioAssetKind.WORD.value): make_asset(item_key="学校", asset_kind=AudioAssetKind.WORD, storage_path="gakkou-word.mp3"),
            ("学校", AudioAssetKind.SENTENCE.value): make_asset(item_key="学校", asset_kind=AudioAssetKind.SENTENCE, storage_path="gakkou-sentence.mp3"),
        },
    )

    row = service.execute(job_id="job-1", deck_language=SupportedLanguage.JA).cards[0]
    field_names = export_field_names_for_rows([row])
    mapping = row.ordered_field_mapping(field_names=field_names)

    assert romaji_calls == ["学校", "学校に行く。"]
    assert furigana_calls == ["学校", "学校に行く。"]
    assert field_names == JAPANESE_EXPORT_CARD_FIELD_NAMES
    assert row.ipa is None
    assert mapping == {
        "SortIndex": 1,
        "Target Word": "学校",
        "Word Reading": "学校[がっこう]",
        "Word Romaji": "Gakkou &lt;word&gt;",
        "Definition": "noun: school",
        "Sentence": "学校に行く。",
        "Sentence Furigana": "学校[がっこう]に行[い]く。",
        "Sentence Romaji": "Gakkou ni iku. &amp; sentence",
        "Sentence Translation": "I go to school.",
        "word_audio": "[sound:gakkou-word.mp3]",
        "sentence_audio": "[sound:gakkou-sentence.mp3]",
        "Image": "",
    }


def test_assemble_japanese_romaji_fails_before_persisting(monkeypatch: pytest.MonkeyPatch) -> None:
    module_name = "multilang.services.japanese_romaji"
    assert find_spec(module_name) is not None, "Japanese romaji service is not implemented"
    error_type = import_module(module_name).JapaneseRomajiError
    calls: list[str] = []

    def failing_romanize(source: str) -> str:
        calls.append(source)
        if source == "学校に行く。":
            raise error_type("unresolved romaji placeholder")
        return "Gakkou"

    monkeypatch.setattr("multilang.services.assemble_export_cards.romanize_japanese", failing_romanize, raising=False)
    candidate = make_candidate(item_key="学校", definitions_html="noun: school", ipa=None, spoken_form=None).model_copy(
        update={"display_form": "学校", "lemma_key": "ja:学校"}
    )
    service, repository = build_service(
        accepted_records=[
            make_text_record(
                item_key="学校",
                example_sentence="学校に行く。",
                translation_text="I go to school.",
            )
        ],
        candidates={"学校": candidate},
        assets={
            ("学校", AudioAssetKind.WORD.value): make_asset(
                item_key="学校", asset_kind=AudioAssetKind.WORD, storage_path="gakkou-word.mp3"
            ),
            ("学校", AudioAssetKind.SENTENCE.value): make_asset(
                item_key="学校", asset_kind=AudioAssetKind.SENTENCE, storage_path="gakkou-sentence.mp3"
            ),
        },
    )

    with pytest.raises(AssembleExportCardsError, match="学校.*romaji"):
        service.execute(job_id="job-1", deck_language=SupportedLanguage.JA)

    assert calls == ["学校", "学校に行く。"]
    assert repository.saved_rows == []


def test_assemble_export_cards_rejects_non_english_definition_label() -> None:
    candidate = make_candidate(item_key="父親", definitions_html="名詞: father", ipa=None, spoken_form=None).model_copy(
        update={"display_form": "父親", "lemma_key": "ja:父親"}
    )
    service, _ = build_service(
        accepted_records=[
            make_text_record(
                item_key="父親",
                example_sentence="父親は今年50歳になる。",
                translation_text="My father turns 50 this year.",
            )
        ],
        candidates={"父親": candidate},
        assets={
            ("父親", AudioAssetKind.WORD.value): make_asset(item_key="父親", asset_kind=AudioAssetKind.WORD, storage_path="chichioya-word.mp3"),
            ("父親", AudioAssetKind.SENTENCE.value): make_asset(item_key="父親", asset_kind=AudioAssetKind.SENTENCE, storage_path="chichioya-sentence.mp3"),
        },
    )

    with pytest.raises(AssembleExportCardsError, match=r"must use '\[part of speech\]: \[meaning\]'"):
        service.execute(job_id="job-1", deck_language=SupportedLanguage.JA)


def test_assemble_export_cards_joins_definitions_on_one_line_and_preserves_image_blank() -> None:
    service, _ = build_service(
        accepted_records=[make_text_record(item_key="jump")],
        candidates={"jump": make_candidate(item_key="jump", definitions_html="noun: first sense<ul><li>noun: nested</li></ul>noun: second & third")},
        assets={
            ("jump", AudioAssetKind.WORD.value): make_asset(item_key="jump", asset_kind=AudioAssetKind.WORD, storage_path="jump-word.mp3"),
            ("jump", AudioAssetKind.SENTENCE.value): make_asset(item_key="jump", asset_kind=AudioAssetKind.SENTENCE, storage_path="jump-sentence.mp3"),
        },
    )

    row = service.execute(job_id="job-1", deck_language=SupportedLanguage.EN).cards[0]

    # Multiple senses stay on a single line (semicolon-joined, no <br> breaks);
    # the repeated "noun" label is shown only once.
    assert row.definitions == "noun: first sense; nested; second &amp; third"
    assert "<br>" not in row.definitions
    assert "<ul>" not in row.definitions
    assert "<li>" not in row.definitions
    assert row.image == ""


def test_assemble_export_cards_flattens_existing_br_separators_to_one_line() -> None:
    service, _ = build_service(
        accepted_records=[make_text_record(item_key="harbor")],
        candidates={"harbor": make_candidate(item_key="harbor", definitions_html="noun: first sense<br>noun: second & third")},
        assets={
            ("harbor", AudioAssetKind.WORD.value): make_asset(item_key="harbor", asset_kind=AudioAssetKind.WORD, storage_path="harbor-word.mp3"),
            ("harbor", AudioAssetKind.SENTENCE.value): make_asset(item_key="harbor", asset_kind=AudioAssetKind.SENTENCE, storage_path="harbor-sentence.mp3"),
        },
    )

    row = service.execute(job_id="job-1", deck_language=SupportedLanguage.EN).cards[0]

    # Incoming <br> senses are flattened to a single semicolon-joined line,
    # with the repeated "noun" label shown only once.
    assert row.definitions == "noun: first sense; second &amp; third"
    assert "<br>" not in row.definitions


def test_assemble_export_cards_keeps_distinct_labels_for_different_parts_of_speech() -> None:
    service, _ = build_service(
        accepted_records=[make_text_record(item_key="run")],
        candidates={"run": make_candidate(item_key="run", definitions_html="verb: to move quickly<br>noun: a short trip")},
        assets={
            ("run", AudioAssetKind.WORD.value): make_asset(item_key="run", asset_kind=AudioAssetKind.WORD, storage_path="run-word.mp3"),
            ("run", AudioAssetKind.SENTENCE.value): make_asset(item_key="run", asset_kind=AudioAssetKind.SENTENCE, storage_path="run-sentence.mp3"),
        },
    )

    row = service.execute(job_id="job-1", deck_language=SupportedLanguage.EN).cards[0]

    # A sense with a different part of speech keeps its own label.
    assert row.definitions == "verb: to move quickly; noun: a short trip"


def test_assemble_export_cards_accepts_portuguese_definition_labels() -> None:
    service, _ = build_service(
        accepted_records=[make_text_record(item_key="to")],
        candidates={"to": make_candidate(item_key="to", definitions_html="preposição: indica direção ou propósito")},
        assets={
            ("to", AudioAssetKind.WORD.value): make_asset(item_key="to", asset_kind=AudioAssetKind.WORD, storage_path="to-word.mp3"),
            ("to", AudioAssetKind.SENTENCE.value): make_asset(item_key="to", asset_kind=AudioAssetKind.SENTENCE, storage_path="to-sentence.mp3"),
        },
    )

    row = service.execute(job_id="job-1", deck_language=SupportedLanguage.EN).cards[0]

    assert row.definitions == "preposição: indica direção ou propósito"


def test_assemble_export_cards_escapes_text_and_keeps_guid_stable_when_text_changes() -> None:
    assets = {
        ("read", AudioAssetKind.WORD.value): make_asset(item_key="read", asset_kind=AudioAssetKind.WORD, storage_path="dir/read-word.mp3"),
        ("read", AudioAssetKind.SENTENCE.value): make_asset(item_key="read", asset_kind=AudioAssetKind.SENTENCE, storage_path="dir/read-sentence.mp3"),
    }
    service, _ = build_service(
        accepted_records=[make_text_record(item_key="read")],
        candidates={"read": make_candidate(item_key="read", definitions_html="verb: definition & example")},
        assets=assets,
    )
    changed_service, _ = build_service(
        accepted_records=[make_text_record(item_key="read", example_sentence="I read <later>.", translation_text='Eu leio "depois" & sempre.')],
        candidates={"read": make_candidate(item_key="read", definitions_html="verb: definition & example")},
        assets=assets,
    )

    original = service.execute(job_id="job-1", deck_language=SupportedLanguage.EN).cards[0]
    changed = changed_service.execute(job_id="job-1", deck_language=SupportedLanguage.EN).cards[0]

    assert original.example_sentence == "I use run &lt;fast&gt; &amp; often." or original.example_sentence == "I use read &lt;fast&gt; &amp; often."
    assert changed.example_sentence == "I read &lt;later&gt;."
    assert changed.translation == "Eu leio &quot;depois&quot; &amp; sempre."
    assert original.note_guid == changed.note_guid


@pytest.mark.parametrize(
    ("accepted_records", "candidates", "assets", "message"),
    [
        ([make_text_record(item_key="flagged")], {}, {
            ("flagged", AudioAssetKind.WORD.value): make_asset(item_key="flagged", asset_kind=AudioAssetKind.WORD, storage_path="flagged-word.mp3"),
            ("flagged", AudioAssetKind.SENTENCE.value): make_asset(item_key="flagged", asset_kind=AudioAssetKind.SENTENCE, storage_path="flagged-sentence.mp3"),
        }, "missing lexical candidate"),
        ([make_text_record(item_key="silent")], {"silent": make_candidate(item_key="silent")}, {
            ("silent", AudioAssetKind.WORD.value): make_asset(item_key="silent", asset_kind=AudioAssetKind.WORD, storage_path="silent-word.mp3"),
        }, "missing required sentence audio"),
        ([], {}, {}, "no accepted text records"),
    ],
)
def test_assemble_export_cards_fails_fast_on_missing_export_prerequisites(
    accepted_records: list[TextQualityRecord],
    candidates: dict[str, LexicalCardCandidate],
    assets: dict[tuple[str, str], AudioAssetRecord],
    message: str,
) -> None:
    service, _ = build_service(
        accepted_records=accepted_records,
        candidates=candidates,
        assets=assets,
    )

    with pytest.raises(AssembleExportCardsError, match=message):
        service.execute(job_id="job-1", deck_language=SupportedLanguage.EN)


def test_assemble_export_cards_rejects_untemplated_definitions() -> None:
    service, _ = build_service(
        accepted_records=[make_text_record(item_key="raw")],
        candidates={"raw": make_candidate(item_key="raw", definitions_html="raw meaning without grammar label")},
        assets={
            ("raw", AudioAssetKind.WORD.value): make_asset(
                item_key="raw", asset_kind=AudioAssetKind.WORD, storage_path="raw-word.mp3"
            ),
            ("raw", AudioAssetKind.SENTENCE.value): make_asset(
                item_key="raw", asset_kind=AudioAssetKind.SENTENCE, storage_path="raw-sentence.mp3"
            ),
        },
    )

    with pytest.raises(AssembleExportCardsError, match="must use"):
        service.execute(job_id="job-1", deck_language=SupportedLanguage.EN)


def test_assemble_export_cards_rejects_unresolved_morphology_only_definitions() -> None:
    service, _ = build_service(
        accepted_records=[make_text_record(item_key="case-form")],
        candidates={"case-form": make_candidate(item_key="case-form", definitions_html="adjective: masculine animate accusative singular")},
        assets={
            ("case-form", AudioAssetKind.WORD.value): make_asset(
                item_key="case-form", asset_kind=AudioAssetKind.WORD, storage_path="case-form-word.mp3"
            ),
            ("case-form", AudioAssetKind.SENTENCE.value): make_asset(
                item_key="case-form", asset_kind=AudioAssetKind.SENTENCE, storage_path="case-form-sentence.mp3"
            ),
        },
    )

    with pytest.raises(AssembleExportCardsError, match="learner-safe semantic definition"):
        service.execute(job_id="job-1", deck_language=SupportedLanguage.EN)


@pytest.mark.parametrize(
    ("candidate", "message"),
    [
        (make_candidate(item_key="missing-ipa").model_copy(update={"ipa": None}), "missing IPA"),
        (make_candidate(item_key="missing-spoken").model_copy(update={"ipa": ""}), "missing IPA"),
    ],
)
def test_assemble_export_cards_rejects_missing_pronunciation_data(
    candidate: LexicalCardCandidate,
    message: str,
) -> None:
    item_key = candidate.submitted_form
    service, _ = build_service(
        accepted_records=[make_text_record(item_key=item_key)],
        candidates={item_key: candidate},
        assets={
            (item_key, AudioAssetKind.WORD.value): make_asset(item_key=item_key, asset_kind=AudioAssetKind.WORD, storage_path=f"{item_key}-word.mp3"),
            (item_key, AudioAssetKind.SENTENCE.value): make_asset(item_key=item_key, asset_kind=AudioAssetKind.SENTENCE, storage_path=f"{item_key}-sentence.mp3"),
        },
    )

    with pytest.raises(AssembleExportCardsError, match=message):
        service.execute(job_id="job-1", deck_language=SupportedLanguage.EN)


def test_assemble_carries_structured_gramatica_into_export_row() -> None:
    record = make_text_record(item_key="vir")
    record = record.model_copy(
        update={
            "sentence_provenance": TextProvenance(
                source="latin-structured",
                provider="latin-structured",
                metadata={"gramatica": "vir: subst masc, 2a declinacao, Nominativus singularis, Suj."},
            )
        }
    )
    service, _ = build_service(
        accepted_records=[record],
        candidates={"vir": make_candidate(item_key="vir", definitions_html="substantivo: homem")},
        assets={
            ("vir", AudioAssetKind.WORD.value): make_asset(item_key="vir", asset_kind=AudioAssetKind.WORD, storage_path="vir-word.mp3"),
            ("vir", AudioAssetKind.SENTENCE.value): make_asset(item_key="vir", asset_kind=AudioAssetKind.SENTENCE, storage_path="vir-sentence.mp3"),
        },
    )

    result = service.execute(job_id="job-1", deck_language=SupportedLanguage.LA)
    row = result.cards[0]

    assert row.gramatica == "vir: subst masc, 2a declinacao, Nominativus singularis, Suj."
    # The dynamic Latin export path resolves field names by language (has_la).
    field_names = export_field_names_for_rows([row])
    mapping = row.ordered_field_mapping(field_names=field_names)
    assert mapping["Grammar"] == row.gramatica
    assert mapping["Grammar"] != mapping["Definition"]


def test_assemble_leaves_gramatica_blank_without_structured_metadata() -> None:
    service, _ = build_service(
        accepted_records=[make_text_record(item_key="run")],
        candidates={"run": make_candidate(item_key="run")},
        assets={
            ("run", AudioAssetKind.WORD.value): make_asset(item_key="run", asset_kind=AudioAssetKind.WORD, storage_path="run-word.mp3"),
            ("run", AudioAssetKind.SENTENCE.value): make_asset(item_key="run", asset_kind=AudioAssetKind.SENTENCE, storage_path="run-sentence.mp3"),
        },
    )

    result = service.execute(job_id="job-1", deck_language=SupportedLanguage.EN)

    assert result.cards[0].gramatica is None
