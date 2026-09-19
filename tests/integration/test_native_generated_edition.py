"""Synthetic provider/evidence exercise of the actual generated-data workflow."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from support.audio import SILENT_MP3
from test_native_application import import_payload, qualified_profile

from multilang.db.base import Base
from multilang.db.native_models import AudioVersionRecord, ContentVersionRecord
from multilang.domain.audio_version import PronunciationSignature
from multilang.domain.content import ContentRequest, ContentVersion, TargetMatchEvidence
from multilang.domain.editions import CardVersionBinding, DeckEdition
from multilang.native_runtime import NativeFacade
from multilang.repositories.native_repository import NativeRepository, model_payload
from multilang.services.audio_synthesis import AudioSynthesisResponse, AudioSynthesisService
from multilang.services.native_audio import NativeAudioService
from multilang.services.native_content import NativeContentService
from multilang.services.native_evidence import SignedEvidence
from multilang.services.native_review import ReviewApproval
from multilang.services.semantic_anki import project_cards
from multilang.settings import Settings


@pytest.mark.parametrize("source_path", ["dictionary", "qualification"])
def test_generate_review_pin_and_export_preserve_canonical_versions(tmp_path, source_path):
    settings = Settings(
        _env_file=None,
        roadmap_4_enabled=True,
        audio_storage_dir=tmp_path / "audio",
        export_output_dir=tmp_path / "exports",
        native_evidence_dir=tmp_path / "evidence",
        native_evidence_signing_key="synthetic-test-key-not-production-123456",
    )
    settings.native_evidence_dir.mkdir()

    class AudioAdapter:
        provider = "azure"

        def synthesize(self, **kwargs):
            path = kwargs["output_path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(SILENT_MP3)
            return AudioSynthesisResponse(
                storage_path=path, byte_size=path.stat().st_size, duration_ms=200
            )

    def match(request, sentence):
        return TargetMatchEvidence(
            lexical_identity_id=request.lexical_identity_id,
            sense_id=request.sense_id,
            target_concept_id=request.target_concept_id,
            matched=True,
            observed_concept_ids=(request.target_concept_id,),
            analyzer_version="1",
            evidence_sha256="b" * 64,
        )

    content = NativeContentService(
        generator=lambda request: {
            "definition": "Move on foot.",
            "example_sentence": f"I {request.display_text}.",
            "translation": "Eu me movimento a pé.",
        },
        matcher=match,
        provider="synthetic",
        model_version="1",
    )
    audio = NativeAudioService(
        synthesis_service=AudioSynthesisService(adapter=AudioAdapter(), settings=settings),
        storage_dir=settings.audio_storage_dir,
        provider_model_version="fixture-1",
    )
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            repo = NativeRepository(session)
            repo.put_profile(
                qualified_profile().model_copy(update={"provider_locales": {"azure": "en-US"}})
            )
            facade = NativeFacade(session, settings, content_service=content, audio_service=audio)
            if source_path == "qualification":
                from qualification_fixture import import_qualification_fixture

                imported = import_qualification_fixture(facade, tmp_path, settings)
            else:
                imported = facade.import_dataset(import_payload(), "linguist")
            dataset_id = imported["dataset_id"]
            identities = repo.dataset_identities(dataset_id)
            cards = project_cards(
                identities=identities,
                approved_forms=(),
                ranks={
                    identity.lexical_identity_id: i + 1 for i, identity in enumerate(identities)
                },
                deck_edition_id=dataset_id,
            )

            def approve(kind, version_id):
                approval = ReviewApproval(
                    kind=kind,
                    version_id=version_id,
                    receipt_sha256="a" * 64,
                    license_receipt_sha256="c" * 64 if kind == "audio" else None,
                )
                signed = approval.model_dump(mode="json", exclude={"receipt_sha256"}) | {
                    "reviewer": "independent-fixture-reviewer"
                }
                receipt = SignedEvidence.sign(
                    signed,
                    key=settings.native_evidence_signing_key.get_secret_value().encode(),
                    signer="independent-fixture-reviewer",
                    purpose=f"{kind}-review",
                    expires_at=datetime.now(UTC) + timedelta(hours=1),
                )
                (settings.native_evidence_dir / f"{receipt.receipt_id}.json").write_text(
                    receipt.model_dump_json()
                )
                return facade.approve_review(
                    approval.model_dump(mode="json") | {"receipt_sha256": receipt.receipt_id},
                    "independent-fixture-reviewer",
                )["version_id"]

            bindings = []
            for card in cards:
                grounding = repo.get_identity(card.parent_lexical_identity_id)
                request = ContentRequest(
                    lexical_identity_id=card.parent_lexical_identity_id,
                    card_id=card.card_id,
                    language="en",
                    language_profile_version="1",
                    lemma=card.parent_lemma,
                    display_text=card.display_text,
                    sense_id=card.sense_id,
                    context_cue=card.context_cue,
                    namespace="core",
                    deck_edition_id=dataset_id,
                    grounding_sha256=grounding["content_sha256"],
                    target_concept_id=card.card_id,
                    explanation_language="pt",
                )
                pending = facade.generate_content(request.model_dump(mode="json"), "generator")[
                    "content_version_id"
                ]
                approved = approve("content", pending)
                assert (
                    session.get(ContentVersionRecord, pending).payload["review_status"] == "pending"
                )
                assert approved != pending
                audio_ids = []
                for kind, text in (
                    ("word", card.display_text),
                    ("sentence", f"I {card.display_text}."),
                ):
                    signature = PronunciationSignature(
                        language="en",
                        language_profile_version="1",
                        display_text=text,
                        normalized_text=text,
                        contextual_reading=text,
                        context=card.context_cue,
                        sense_id=card.sense_id,
                        locale="en-US",
                        voice_id="en-US-AriaNeural",
                        ssml=f'<speak xml:lang="en-US"><voice name="en-US-AriaNeural">{escape(text)}</voice></speak>',
                        pronunciation_policy_version="1",
                        provider="azure",
                        provider_model_version="fixture-1",
                        audio_format="audio-24khz-48kbitrate-mono-mp3",
                        asset_kind=kind,
                    )
                    generated = facade.generate_audio(
                        {
                            "identity_id": card.parent_lexical_identity_id,
                            "signature": signature.model_dump(mode="json"),
                        },
                        "generator",
                    )["audio_version_id"]
                    audio_ids.append(approve("audio", generated))
                    assert (
                        session.get(AudioVersionRecord, generated).payload["review_status"]
                        == "pending"
                    )
                bindings.append(
                    CardVersionBinding(
                        card_id=card.card_id,
                        content_version_id=approved,
                        word_audio_version_id=audio_ids[0],
                        sentence_audio_version_id=audio_ids[1],
                    )
                )
            session.commit()
            edition = DeckEdition(
                edition_id=dataset_id,
                dataset_id=dataset_id,
                bindings=tuple(bindings),
                approval_receipt_sha256="d" * 64,
            )
            pinned = repo.edition_cards(edition, production=False)
            assert [card.content.version_id for card in pinned] == [
                item.content_version_id for item in bindings
            ]
            changed_grounding = ContentVersion.model_validate(
                pinned[0].content.model_dump(mode="json")
                | {
                    "request": pinned[0].content.request.model_dump(mode="json")
                    | {"grounding_sha256": "f" * 64}
                }
            )
            repo.save_content(
                version_id=changed_grounding.version_id,
                identity_id=cards[0].parent_lexical_identity_id,
                namespace="core",
                owner_id="",
                edition_id=dataset_id,
                payload=model_payload(changed_grounding),
                search_text="fixture",
                actor="fixture",
            )
            wrong_binding = bindings[0].model_copy(
                update={"content_version_id": changed_grounding.version_id}
            )
            wrong_edition = edition.model_copy(update={"bindings": (wrong_binding, *bindings[1:])})
            with pytest.raises(ValueError, match="grounding"):
                repo.edition_cards(wrong_edition, production=False)
            # The adversarial approved row is isolated from the remaining
            # prototype export, which rejects ambiguous automatic selection.
            session.delete(session.get(ContentVersionRecord, changed_grounding.version_id))
            session.flush()
            exported = facade.export_anki(
                {"dataset_id": dataset_id, "model": "B", "prototype": True}, "operator"
            )
            assert exported["card_count"] == 2 and exported["prototype"]
            assert (
                Path(settings.export_output_dir) / "native" / f"{exported['export_id']}.apkg"
            ).is_file()
            with pytest.raises(ValueError, match="3000"):
                facade.export_anki(
                    {"dataset_id": dataset_id, "model": "B", "edition_id": dataset_id}, "operator"
                )
            # A corrupt media file invalidates the pinned edition; it is never
            # replaced with another voice/content version from the database.
            Path(pinned[0].word_audio.storage_path).write_bytes(b"corrupt")
            with pytest.raises(ValueError, match="integrity"):
                repo.edition_cards(edition, production=False)
    finally:
        engine.dispose()
