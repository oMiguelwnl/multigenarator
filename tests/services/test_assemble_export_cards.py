"""Tests for deterministic export-card assembly."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace

import pytest

from multilang.domain.audio import AudioAssetKind, AudioAssetRecord, AudioFormat, AudioProvenance, AudioProvider, AudioSynthesisStatus, NormalizedTtsInput
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexicon import DefinitionRecord, GroundingStatus, LexicalCardCandidate, LexicalProvenance
from multilang.domain.text_quality import ConfidenceLabel, ReviewStatus, TextGenerationStatus, TextProvenance, TextQualityRecord, ValidationStatus
from multilang.services.assemble_export_cards import AssembleExportCardsError, AssembleExportCardsService


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


def build_service(
    *,
    accepted_records: list[TextQualityRecord],
    candidates: dict[str, LexicalCardCandidate],
    assets: dict[tuple[str, str], AudioAssetRecord],
    export_repository: FakeExportRepository | None = None,
) -> tuple[AssembleExportCardsService, FakeExportRepository]:
    repository = export_repository or FakeExportRepository()
    service = AssembleExportCardsService(
        text_repository=FakeTextRepository(accepted_records=accepted_records),
        lexical_repository=FakeLexicalRepository(candidates=candidates),
        audio_repository=FakeAudioRepository(assets=assets),
        export_repository=repository,
    )
    return service, repository


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


def test_assemble_export_cards_joins_definitions_with_br_and_preserves_image_blank() -> None:
    service, _ = build_service(
        accepted_records=[make_text_record(item_key="jump")],
        candidates={"jump": make_candidate(item_key="jump", definitions_html="noun: first sense<ul><li>noun: nested</li></ul>noun: second & third")},
        assets={
            ("jump", AudioAssetKind.WORD.value): make_asset(item_key="jump", asset_kind=AudioAssetKind.WORD, storage_path="jump-word.mp3"),
            ("jump", AudioAssetKind.SENTENCE.value): make_asset(item_key="jump", asset_kind=AudioAssetKind.SENTENCE, storage_path="jump-sentence.mp3"),
        },
    )

    row = service.execute(job_id="job-1", deck_language=SupportedLanguage.EN).cards[0]

    assert row.definitions == "noun: first sense<br>noun: nested<br>noun: second &amp; third"
    assert "<ul>" not in row.definitions
    assert "<li>" not in row.definitions
    assert row.image == ""


def test_assemble_export_cards_normalizes_existing_br_separators() -> None:
    service, _ = build_service(
        accepted_records=[make_text_record(item_key="harbor")],
        candidates={"harbor": make_candidate(item_key="harbor", definitions_html="noun: first sense<br>noun: second & third")},
        assets={
            ("harbor", AudioAssetKind.WORD.value): make_asset(item_key="harbor", asset_kind=AudioAssetKind.WORD, storage_path="harbor-word.mp3"),
            ("harbor", AudioAssetKind.SENTENCE.value): make_asset(item_key="harbor", asset_kind=AudioAssetKind.SENTENCE, storage_path="harbor-sentence.mp3"),
        },
    )

    row = service.execute(job_id="job-1", deck_language=SupportedLanguage.EN).cards[0]

    assert row.definitions == "noun: first sense<br>noun: second &amp; third"


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
