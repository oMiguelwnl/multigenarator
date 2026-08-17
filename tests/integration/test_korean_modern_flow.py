"""Offline Korean evidence through real orchestration, SQLite, and Kiwi."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import unicodedata

import pytest
from sqlalchemy import select

from multilang.db.models import (
    GenerationJob,
    LexicalCandidate,
    TextQualityRecordModel,
)
from multilang.domain.exporting import ExportCardIdentity, ExportCardRow
from multilang.domain.jobs import GenerationRequest, SupportedLanguage
from multilang.domain.korean import KoreanLexicalIdentity
import multilang.runtime as runtime_module
from multilang.runtime import build_runtime_service
from multilang.services import frequency_decks
from multilang.services.export_anki_package import build_multilang_note
from multilang.services.text_generation import (
    DefinitionGenerationResult,
    GeneratedSentence,
    GeneratedTranslation,
    SentenceGenerationResult,
    SentenceTranslationResult,
)
from multilang.settings import Settings


PRIVATE_HIGHLIGHT_TEXT = "눈은 매일 공부해요"


@dataclass(frozen=True, slots=True)
class _PersistedModeEvidence:
    source_type: str
    language: str
    identity_type: str


@dataclass(frozen=True, slots=True)
class _KoreanFlowEvidence:
    modes: tuple[_PersistedModeEvidence, ...]
    core_identity_count: int
    shared_fingerprint: bool
    positive_match_status: str
    negative_match_status: str
    review_statuses: tuple[str, ...]
    highlight_lemmas: tuple[str, ...]
    highlight_surfaces: tuple[str, ...]
    highlight_compound_signature: tuple[tuple[str, str], ...]
    private_record_retained: bool
    public_persistence_is_private: bool
    generic_fields: tuple[tuple[str, tuple[str, ...]], ...]
    generic_images_blank: bool
    generic_tags: tuple[tuple[str, tuple[str, ...]], ...]
    word_list_submitted_forms: tuple[str, ...]
    homograph_part_of_speech: str
    homograph_positive_match_status: str
    homograph_negative_match_status: str
    homograph_negative_validation_status: str


class _OfflineKoreanSentenceAdapter:
    """Deterministic provider-boundary fake; all internal services stay real."""

    def generate_definition(self, request: object) -> DefinitionGenerationResult:
        return DefinitionGenerationResult(
            definitions_html=f"verbo: estudar ({getattr(request, 'sense_id', 'fonte')})",
            provenance={"source": "offline-reviewed-fixture", "provider": "fixture"},
        )

    def generate_sentence(self, request: object) -> SentenceGenerationResult:
        lemma = str(getattr(request, "lemma"))
        sentences = {
            "공부하다": "저는 도서관에서 매일 한국어를 공부해요.",
            "눈": "제 눈은 밝은 빛에 아주 민감해요.",
            "배우": "저는 학교에서 매일 한국어를 배워요.",
        }
        return SentenceGenerationResult(
            sentence=sentences[lemma],
            intended_sense=str(getattr(request, "intended_sense", "reviewed fixture")),
            uncertainty_notes=[],
            provenance={"source": "offline-reviewed-fixture", "provider": "fixture"},
        )


class _OfflineKoreanTranslationAdapter:
    def translate_sentence(self, request: object) -> SentenceTranslationResult:
        return SentenceTranslationResult(
            translation="Tradução portuguesa sintética revisada para o teste.",
            provenance={"source": "offline-reviewed-fixture", "provider": "fixture"},
        )


class _ForbiddenAudioAdapter:
    def available_voice_ids(self) -> set[str] | None:
        raise AssertionError("Korean closure evidence must not query an audio provider")

    def synthesize(self, **kwargs: object) -> object:
        raise AssertionError("Korean closure evidence must not synthesize audio")


def _write_reviewed_lexicon(tmp_path: Path) -> Path:
    records = {
        "공부하다": ("verb", "fixture:study:1"),
        "눈": ("noun", "fixture:eye:1"),
        "배우": ("noun", "fixture:actor:1"),
    }
    index_path = tmp_path / "lexicon" / "ko" / "lexical-index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps(
            {
                lemma: {
                    "term": lemma,
                    "display_form": lemma,
                    "lemma": lemma,
                    "definitions": ["reviewed synthetic fixture only"],
                    "part_of_speech": part_of_speech,
                    "sense_id": sense_id,
                    "register": "standard",
                    "source": "reviewed-test-fixture",
                }
                for lemma, (part_of_speech, sense_id) in records.items()
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return index_path.parent.parent


def _write_word_list(tmp_path: Path) -> Path:
    path = tmp_path / "submitted-korean-words.txt"
    path.write_text(
        "\n".join((unicodedata.normalize("NFD", "공부해요"), "배우가")),
        encoding="utf-8",
    )
    return path


def _write_private_highlight(tmp_path: Path) -> Path:
    path = tmp_path / "Private Korean Reader.txt"
    path.write_text(
        "Synthetic Learner Reader\n"
        "- Your Highlight at Location 1\n"
        f"{PRIVATE_HIGHLIGHT_TEXT}\n"
        "==========",
        encoding="utf-8",
    )
    return path


def _temporary_korean_frequency_words(language: str):
    assert language == "ko"
    return iter(("공부해요",))


def _exercise_three_mode_flow(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> _KoreanFlowEvidence:
    """Return evidence only after all three production ingestion routes run."""

    monkeypatch.setattr(
        runtime_module,
        "LocalSentenceAdapter",
        _OfflineKoreanSentenceAdapter,
    )
    monkeypatch.setattr(
        runtime_module,
        "LocalTranslationAdapter",
        _OfflineKoreanTranslationAdapter,
    )
    monkeypatch.setattr(
        frequency_decks,
        "iter_wordlist",
        _temporary_korean_frequency_words,
    )
    service = build_runtime_service(
        Settings(
            _env_file=None,
            database_url=f"sqlite+pysqlite:///{tmp_path / 'korean-modern-flow.db'}",
            lexicon_data_dir=_write_reviewed_lexicon(tmp_path),
            audio_storage_dir=tmp_path / "audio",
            audio_provider="azure",
            text_generation_provider="local",
            translation_provider="local",
            tatoeba_enabled=False,
        ),
        audio_adapter=_ForbiddenAudioAdapter(),
    )
    private_highlight_path = _write_private_highlight(tmp_path)
    requests = (
        GenerationRequest(
            language=SupportedLanguage.KO,
            source_type="frequency",
            level=1,
            cards_per_level=1,
        ),
        GenerationRequest(
            language=SupportedLanguage.KO,
            source_type="word-list",
            input_file=_write_word_list(tmp_path),
        ),
        GenerationRequest(
            language=SupportedLanguage.KO,
            source_type="kindle-highlights",
            input_file=private_highlight_path,
        ),
    )
    session = service.lexical_repo.session
    engine = session.get_bind()
    try:
        job_ids = [service.execute(request).report.job_id for request in requests]
        session.commit()
        session.expire_all()

        evidence: list[_PersistedModeEvidence] = []
        identities: list[KoreanLexicalIdentity] = []
        jobs_by_source: dict[str, GenerationJob] = {}
        candidates_by_source: dict[str, list[object]] = {}
        for job_id in job_ids:
            job = session.scalar(
                select(GenerationJob).where(GenerationJob.id == job_id)
            )
            assert job is not None
            candidates = service.lexical_repo.list_candidates(job_id)
            jobs_by_source[job.source_type] = job
            candidates_by_source[job.source_type] = candidates
            study = next(item for item in candidates if item.lemma == "공부하다")
            identity = study.korean_identity
            assert isinstance(identity, KoreanLexicalIdentity)
            identities.append(identity)
            evidence.append(
                _PersistedModeEvidence(
                    source_type=job.source_type,
                    language=job.language,
                    identity_type=type(identity).__name__,
                )
            )

        core_identities = {
            (
                identity.canonical_nfc,
                identity.lemma,
                identity.part_of_speech,
                identity.sense_id,
                tuple(
                    (item.form, item.pos)
                    for item in identity.morpheme_signature
                ),
            )
            for identity in identities
        }
        matcher = service.generate_text_items_service.text_validation_service.korean_matcher
        assert matcher is service.grounding_service._korean_morphology
        positive_match = matcher.match_target(
            "저는 도서관에서 매일 한국어를 공부해요.",
            identities[0],
        )
        negative_match = matcher.match_target(
            "저는 도서관에서 매일 조용히 책을 읽어요.",
            identities[0],
        )

        word_list_candidates = candidates_by_source["word-list"]
        actor_candidate = next(
            candidate
            for candidate in word_list_candidates
            if candidate.lemma == "배우"
        )
        actor_identity = actor_candidate.korean_identity
        assert isinstance(actor_identity, KoreanLexicalIdentity)
        homograph_positive = matcher.match_target(
            "그 배우가 오늘 새 영화를 촬영해요.",
            actor_identity,
        )
        homograph_negative = matcher.match_target(
            "저는 학교에서 매일 한국어를 배워요.",
            actor_identity,
        )
        homograph_negative_validation = (
            service.generate_text_items_service.text_validation_service.validate(
                sentence=GeneratedSentence(
                    text="저는 학교에서 매일 한국어를 배워요.",
                    target_language="ko",
                    intended_sense="learn a language",
                    uncertainty_notes=[],
                    provenance={"source": "offline-reviewed-fixture"},
                ),
                translation=GeneratedTranslation(
                    text="Eu estudo coreano todos os dias na escola.",
                    target_language="pt",
                    provenance={"source": "offline-reviewed-fixture"},
                ),
                display_form=actor_candidate.display_form,
                lemma=actor_candidate.lemma,
                definitions_html=actor_candidate.definitions_html,
                korean_identity=actor_identity,
                require_translation=False,
            )
        )

        word_list_job_id = job_ids[1]
        service.generate_text(
            job_id=word_list_job_id,
            deck_language=SupportedLanguage.KO,
            synthesize_audio=False,
        )
        session.expire_all()
        review_statuses = tuple(
            session.scalars(
                select(TextQualityRecordModel.review_status)
                .where(TextQualityRecordModel.job_id == word_list_job_id)
                .order_by(TextQualityRecordModel.item_key.asc())
            )
        )

        highlight_candidates = candidates_by_source["kindle-highlights"]
        highlight_identities = tuple(
            candidate.korean_identity
            for candidate in highlight_candidates
            if isinstance(candidate.korean_identity, KoreanLexicalIdentity)
        )
        study_highlight_identity = next(
            identity
            for identity in highlight_identities
            if identity.lemma == "공부하다"
        )
        highlight_job = jobs_by_source["kindle-highlights"]
        private_records = service.highlight_import_repo.list_private_records(
            highlight_job.id
        )
        manifest = service.highlight_import_repo.get_manifest(highlight_job.id)
        public_rows = tuple(
            session.scalars(
                select(LexicalCandidate)
                .where(LexicalCandidate.job_id == highlight_job.id)
                .order_by(LexicalCandidate.item_key.asc())
            )
        )
        public_dump = json.dumps(
            {
                "manifest": manifest.model_dump(mode="json") if manifest else None,
                "rows": [
                    {
                        "item_key": row.item_key,
                        "normalized_source": row.normalized_source,
                        "submitted_form": row.submitted_form,
                        "display_form": row.display_form,
                        "lemma": row.lemma,
                        "lemma_key": row.lemma_key,
                        "provenance": row.provenance,
                        "korean_identity": row.korean_identity,
                    }
                    for row in public_rows
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        forbidden_public_values = (
            PRIVATE_HIGHLIGHT_TEXT,
            str(private_highlight_path),
            private_highlight_path.name,
            "normalized_text",
            "source_path",
            "highlight_context",
            "token_dump",
        )
        public_persistence_is_private = (
            manifest is not None
            and bool(public_rows)
            and all(len(row.normalized_source) == 64 for row in public_rows)
            and all(value not in public_dump for value in forbidden_public_values)
        )

        generic_fields: list[tuple[str, tuple[str, ...]]] = []
        generic_tags: list[tuple[str, tuple[str, ...]]] = []
        generic_images: list[str] = []
        for source_type in ("frequency", "word-list", "kindle-highlights"):
            job = jobs_by_source[source_type]
            persisted_study = session.scalar(
                select(LexicalCandidate).where(
                    LexicalCandidate.job_id == job.id,
                    LexicalCandidate.lemma == "공부하다",
                )
            )
            assert persisted_study is not None
            row = ExportCardRow(
                identity=ExportCardIdentity(
                    language=SupportedLanguage(job.language),
                    source_type=job.source_type,
                    job_id=job.id,
                    item_key=persisted_study.item_key,
                    lemma_key=persisted_study.lemma_key,
                    sort_index=1,
                ),
                word=persisted_study.lemma,
                front_of_card=persisted_study.display_form,
                ipa=persisted_study.ipa,
                definitions=persisted_study.definitions_html or "definição sintética",
                example_sentence="저는 도서관에서 매일 한국어를 공부해요.",
                translation="Eu estudo coreano todos os dias na biblioteca.",
                word_audio=f"[sound:{source_type}-word.mp3]",
                sentence_audio=f"[sound:{source_type}-sentence.mp3]",
            )
            mapping = row.ordered_field_mapping()
            note = build_multilang_note(row)
            generic_fields.append((source_type, tuple(mapping)))
            generic_images.append(str(mapping["Image"]))
            generic_tags.append((source_type, tuple(note.tags)))

        return _KoreanFlowEvidence(
            modes=tuple(evidence),
            core_identity_count=len(core_identities),
            shared_fingerprint=(
                len({identity.analyzer_fingerprint for identity in identities}) == 1
            ),
            positive_match_status=positive_match.status.value,
            negative_match_status=negative_match.status.value,
            review_statuses=review_statuses,
            highlight_lemmas=tuple(
                sorted(identity.lemma for identity in highlight_identities)
            ),
            highlight_surfaces=tuple(
                sorted(identity.canonical_nfc for identity in highlight_identities)
            ),
            highlight_compound_signature=tuple(
                (item.form, item.pos)
                for item in study_highlight_identity.morpheme_signature
            ),
            private_record_retained=(
                len(private_records) == 1
                and private_records[0].normalized_text == PRIVATE_HIGHLIGHT_TEXT
                and not hasattr(private_records[0], "source_path")
            ),
            public_persistence_is_private=public_persistence_is_private,
            generic_fields=tuple(generic_fields),
            generic_images_blank=all(image == "" for image in generic_images),
            generic_tags=tuple(generic_tags),
            word_list_submitted_forms=tuple(
                candidate.submitted_form for candidate in word_list_candidates
            ),
            homograph_part_of_speech=actor_identity.part_of_speech,
            homograph_positive_match_status=homograph_positive.status.value,
            homograph_negative_match_status=homograph_negative.status.value,
            homograph_negative_validation_status=(
                homograph_negative_validation.validation_status.value
            ),
        )
    finally:
        session.close()
        engine.dispose()


def test_three_korean_modes_persist_one_canonical_typed_identity_shape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = _exercise_three_mode_flow(tmp_path, monkeypatch).modes

    assert {item.source_type for item in evidence} == {
        "frequency",
        "word-list",
        "kindle-highlights",
    }
    assert {item.language for item in evidence} == {"ko"}
    assert {item.identity_type for item in evidence} == {"KoreanLexicalIdentity"}


def test_reloaded_identity_drives_strict_matching_and_persisted_review(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = _exercise_three_mode_flow(tmp_path, monkeypatch)

    assert evidence.core_identity_count == 1
    assert evidence.shared_fingerprint is True
    assert evidence.positive_match_status == "matched"
    assert evidence.negative_match_status == "mismatch"
    assert evidence.review_statuses == ("accepted", "review_required")


def test_nfd_inflection_and_pos_homograph_survive_real_reload_boundaries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = _exercise_three_mode_flow(tmp_path, monkeypatch)

    assert evidence.word_list_submitted_forms == (
        unicodedata.normalize("NFD", "공부해요"),
        "배우가",
    )
    assert evidence.homograph_part_of_speech == "NNG"
    assert evidence.homograph_positive_match_status == "matched"
    assert evidence.homograph_negative_match_status == "mismatch"
    assert evidence.homograph_negative_validation_status == "failed"


def test_private_highlight_and_generic_ko_artifacts_keep_existing_boundaries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = _exercise_three_mode_flow(tmp_path, monkeypatch)

    assert evidence.highlight_lemmas == ("공부하다", "눈")
    assert evidence.highlight_surfaces == ("공부해요", "눈은")
    assert evidence.highlight_compound_signature == (
        ("공부", "NNG"),
        ("하", "XSV"),
    )
    assert evidence.private_record_retained is True
    assert evidence.public_persistence_is_private is True
    assert dict(evidence.generic_fields) == {
        "frequency": (
            "SortIndex",
            "word",
            "IPA",
            "Definitions",
            "Example Sentence",
            "Translation",
            "word_audio",
            "sentence_audio",
            "Image",
        ),
        "word-list": (
            "SortIndex",
            "Word",
            "IPA",
            "Example Sentence",
            "sentence_audio",
            "Definition",
            "Image",
        ),
        "kindle-highlights": (
            "SortIndex",
            "Word",
            "IPA",
            "Example Sentence",
            "sentence_audio",
            "Definition",
            "Image",
        ),
    }
    assert evidence.generic_images_blank is True
    assert all(tags.count("ko") == 1 for _, tags in evidence.generic_tags)
    assert all("ko-KR" not in tags for _, tags in evidence.generic_tags)
