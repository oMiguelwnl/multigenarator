import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.domain.editions import CardVersionBinding, DeckEdition
from multilang.repositories.native_repository import NativeRepository


def test_edition_bindings_are_immutable_and_duplicates_fail_closed():
    binding = CardVersionBinding(
        card_id="card:1",
        content_version_id="content:1",
        word_audio_version_id="audio:word",
        sentence_audio_version_id="audio:sentence",
    )
    edition = DeckEdition(
        edition_id="edition:1",
        dataset_id="a" * 64,
        bindings=(binding,),
        important_form_policy=None,
        approval_receipt_sha256="b" * 64,
    )
    assert (
        edition.model_dump_json()
        == DeckEdition.model_validate_json(edition.model_dump_json()).model_dump_json()
    )
    with pytest.raises(ValueError, match="duplicate"):
        DeckEdition(
            edition_id="edition:1",
            dataset_id="a" * 64,
            bindings=(binding, binding),
            approval_receipt_sha256="b" * 64,
        )


def test_missing_production_evidence_cannot_freeze_edition():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            repo = NativeRepository(session)
            edition = DeckEdition(
                edition_id="edition:1",
                dataset_id="a" * 64,
                bindings=(),
                approval_receipt_sha256="b" * 64,
            )
            with pytest.raises(ValueError, match="dataset"):
                repo.freeze_edition(edition, actor="linguist", verifier=lambda _: True)
    finally:
        engine.dispose()
