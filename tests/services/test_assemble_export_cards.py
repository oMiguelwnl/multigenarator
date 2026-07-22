"""Tests for deterministic export-card assembly."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace

import pytest

from multilang.domain.audio import AudioAssetKind, AudioAssetRecord, AudioFormat, AudioProvenance, AudioProvider, AudioSynthesisStatus, NormalizedTtsInput
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexicon import DefinitionRecord, GroundingStatus, LexicalCardCandidate, LexicalProvenance
from multilang.domain.text_quality import ConfidenceLabel, ReviewStatus, TextGenerationStatus, TextProvenance, TextQualityRecord, ValidationStatus
from multilang.domain.exporting import JAPANESE_EXPORT_CARD_FIELD_NAMES, MANDARIN_EXPORT_CARD_FIELD_NAMES, export_field_names_for_rows
from multilang.services.assemble_export_cards import AssembleExportCardsError, AssembleExportCardsService
from multilang.services.mandarin_orthography import MandarinOrthography, MandarinOrthographyError


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


def test_assemble_export_cards_builds_japanese_row_without_ipa() -> None:
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

    assert field_names == JAPANESE_EXPORT_CARD_FIELD_NAMES
    assert row.ipa is None
    assert mapping == {
        "SortIndex": 1,
        "Target Word": "学校",
        "Word Reading": "学校[がっこう]",
        "Definition": "noun: school",
        "Sentence": "学校に行く。",
        "Sentence Furigana": "学校[がっこう]に行[い]く。",
        "Sentence Translation": "I go to school.",
        "word_audio": "[sound:gakkou-word.mp3]",
        "sentence_audio": "[sound:gakkou-sentence.mp3]",
        "Image": "",
    }


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
