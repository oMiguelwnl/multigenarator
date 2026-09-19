"""Cached snapshots must not bypass current Korean review and audio gates."""

from types import SimpleNamespace

import pytest

from multilang.domain.exporting import ExportArtifactFormat
from multilang.runtime import RuntimeGenerateService


@pytest.mark.parametrize("source", ["frequency", "word-list", "kindle-highlights"])
def test_korean_export_rechecks_current_evidence_even_with_cached_snapshots(tmp_path, monkeypatch, source):
    monkeypatch.setattr("multilang.runtime.assert_anki_id_registry_clean", lambda **_: None)
    calls = []

    def require_current(**kwargs):
        calls.append(kwargs)
        raise ValueError("current Korean review required")

    runtime = SimpleNamespace(
        job_service=SimpleNamespace(repository=SimpleNamespace(
            get_job=lambda _: SimpleNamespace(language="ko", source_type=source))),
        export_repository=SimpleNamespace(list_card_snapshots=lambda _: [object()]),
        assemble_export_cards_service=SimpleNamespace(execute=require_current),
    )

    with pytest.raises(ValueError, match="current Korean review required"):
        RuntimeGenerateService.export_job(runtime, job_id="personal", export_format=ExportArtifactFormat.APKG,
            output_dir=tmp_path)
    assert len(calls) == 1
    assert list(tmp_path.iterdir()) == []


def test_korean_tabular_media_copy_is_exact_and_does_not_overwrite_different_media(tmp_path):
    from multilang.services.korean_tabular_media import copy_korean_tabular_media

    source = tmp_path / "sentence.mp3"
    source.write_bytes(b"exact reviewed bytes")
    output = tmp_path / "export"
    media = {"[sound:sentence.mp3]": source}
    copy_korean_tabular_media(media, output)
    copy_korean_tabular_media(media, output)
    target = output / "collection.media" / source.name
    assert target.read_bytes() == source.read_bytes()
    target.write_bytes(b"previous different export")
    with pytest.raises(ValueError, match="conflicts"):
        copy_korean_tabular_media(media, output)
    assert target.read_bytes() == b"previous different export"


def test_korean_tabular_media_copy_refuses_destination_symlink(tmp_path):
    from multilang.services.korean_tabular_media import copy_korean_tabular_media

    source = tmp_path / "sentence.mp3"
    source.write_bytes(b"exact reviewed bytes")
    output = tmp_path / "export"
    output.mkdir()
    outside = tmp_path / "other"
    outside.mkdir()
    (output / "collection.media").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="unsafe"):
        copy_korean_tabular_media({"[sound:sentence.mp3]": source}, output)
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize("source", ["word-list", "kindle-highlights"])
@pytest.mark.parametrize("format", [ExportArtifactFormat.APKG, ExportArtifactFormat.CSV, ExportArtifactFormat.TSV])
def test_reviewed_personal_cards_export_with_media_and_recheck_changed_text(tmp_path, monkeypatch, source, format):
    from hashlib import sha256

    from sqlalchemy import delete, select
    from test_assemble_export_cards import make_korean_asset
    from test_korean_personal_text_review import _evidence, _setup

    from multilang.db.models import LexicalCandidate, TextQualityRecordModel
    from multilang.domain.audio import AudioAssetKind, AudioReviewStatus
    from multilang.domain.text_quality import ConfidenceLabel, ValidationStatus
    from multilang.repositories.audio_repository import AudioRepository
    from multilang.repositories.export_repository import ExportRepository
    from multilang.repositories.lexical_repository import LexicalRepository
    from multilang.repositories.provider_call_log_repository import ProviderCallLogRepository
    from multilang.services.assemble_export_cards import AssembleExportCardsService
    from multilang.services.korean_personal_text_review import (
        apply_personal_text_evidence,
        prepare_personal_text_evidence,
    )
    from multilang.services.text_validation import TextValidationResult

    learning, job_id, engine = _setup(tmp_path)
    session = learning.session
    try:
        # Keep one fixture item, and bind its actual source before review.
        session.execute(delete(TextQualityRecordModel).where(TextQualityRecordModel.item_key == "row-2"))
        session.execute(delete(LexicalCandidate).where(LexicalCandidate.item_key == "row-2"))
        job = learning.jobs.get_job(job_id)
        job.total_items, job.source_type = 1, source
        candidate = session.scalar(select(LexicalCandidate).where(LexicalCandidate.item_key == "row-1"))
        candidate.source_type = source
        candidate.ipa, candidate.spoken_form = "[tɕip̚]", "집"
        session.commit()
        learning.review_edit(job_id=job_id, item_id="row-1", field="definition", value="substantivo: casa",
            actor_id="fixture-editor", request_id="definition-export-format", expected_pointer_version=1)
        learning.review_validate(job_id=job_id, item_id="row-1", validator=SimpleNamespace(
            validate=lambda **_: TextValidationResult(validation_status=ValidationStatus.PASSED,
                validation_flags=[], confidence_score=1, confidence_label=ConfidenceLabel.HIGH)))
        evidence = _evidence(prepare_personal_text_evidence(learning, job_id=job_id, item_id="row-1"))
        apply_personal_text_evidence(learning, job_id=job_id, item_id="row-1", evidence=evidence,
            actor_id="fixture-review-import", request_id="apply-export-review")
        audio = AudioRepository(session)
        text = learning.texts.get_text_record(job_id, "row-1")
        for kind, spoken in ((AudioAssetKind.WORD, candidate.lemma), (AudioAssetKind.SENTENCE, text.example_sentence)):
            path = tmp_path / f"{kind.value}.mp3"
            data = (bytes.fromhex("fff364c0") + bytes(140)) * 3
            path.write_bytes(data)
            asset = make_korean_asset(item_key="row-1", asset_kind=kind, display_text=spoken,
                storage_path=str(path), artifact_sha256=sha256(b"artifact:" + data).hexdigest())
            audio.upsert_audio_asset(asset.model_copy(update={"job_id": job_id,
                "provenance": asset.provenance.model_copy(update={"byte_size": len(data), "duration_ms": 72})}))
        runtime = RuntimeGenerateService.__new__(RuntimeGenerateService)
        runtime.job_service = SimpleNamespace(repository=learning.jobs)
        runtime.text_repository, runtime.audio_repository = learning.texts, audio
        runtime.export_repository = ExportRepository(session)
        runtime.provider_call_log_repository = ProviderCallLogRepository(session)
        runtime.assemble_export_cards_service = AssembleExportCardsService(text_repository=learning.texts,
            lexical_repository=LexicalRepository(session), audio_repository=audio,
            export_repository=runtime.export_repository)

        processed = learning.process(job_id=job_id, source="custom" if source == "word-list" else "highlight", mode="start")
        assert processed["accepted"] == 1 and processed["complete"], processed
        assert learning.status(job_id)["status"] == "complete"
        result = runtime.export_job(job_id=job_id, export_format=format, output_dir=tmp_path / "export")

        assert result.card_count == 1 and result.output_path.is_file()
        if format in {ExportArtifactFormat.CSV, ExportArtifactFormat.TSV}:
            assert (result.output_path.parent / "collection.media" / "sentence.mp3").read_bytes() == data
        approved = audio.get_asset(job_id, "row-1", AudioAssetKind.SENTENCE)
        assemble = runtime.assemble_export_cards_service.execute

        def reject_after_assembly(**kwargs):
            result = assemble(**kwargs)
            audio.upsert_audio_asset(approved.model_copy(update={"provenance": approved.provenance.model_copy(
                update={"audio_review_status": AudioReviewStatus.REJECTED})}))
            return result

        with monkeypatch.context() as context:
            context.setattr(runtime.assemble_export_cards_service, "execute", reject_after_assembly)
            with pytest.raises(ValueError, match="Korean personal export media review drift"):
                runtime.export_job(job_id=job_id, export_format=format, output_dir=tmp_path / "audio-blocked")
        assert not (tmp_path / "audio-blocked").exists()
        audio.upsert_audio_asset(approved)
        candidate.definitions_html = "Texto novo ainda sem revisão."
        session.commit()
        with pytest.raises(ValueError, match="Korean personal export requires current"):
            runtime.export_job(job_id=job_id, export_format=format, output_dir=tmp_path / "blocked")
        assert not (tmp_path / "blocked").exists()
    finally:
        session.close()
        engine.dispose()
