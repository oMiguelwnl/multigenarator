"""Synthetic package scale: semantic cardinality and actual deck destination checks."""

import sqlite3
import zipfile
from time import perf_counter

import pytest

from multilang.domain.anki_semantics import SemanticCard
from multilang.services.semantic_anki import (
    export_semantic_anki,
    summarize_cards,
    validate_semantic_cards,
)


@pytest.mark.parametrize("model,notes", [("A", 3000), ("B", 6000)])
def test_full_synthetic_core_with_all_forms_exports_without_truncation(
    tmp_path, model, notes, record_property
):
    cards = []
    for rank in range(1, 3001):
        head = SemanticCard(
            parent_lexical_identity_id=f"synthetic:{rank}",
            language="en",
            parent_lemma=f"lemma{rank}",
            sense_id="fixture",
            role="headword",
            display_text=f"lemma{rank}",
            context_cue=f"Synthetic meaning {rank}",
            inventory="core",
            rank=rank,
            deck_edition_id="synthetic-1",
        )
        form = SemanticCard.model_validate(
            head.model_dump()
            | {
                "role": "important_form",
                "display_text": f"form{rank}",
                "surface_form_id": f"surface:{rank}",
                "morphological_analysis_id": f"analysis:{rank}",
                "context_cue": f"Synthetic usage of form{rank}.",
                "prerequisite_card_id": head.card_id,
            }
        )
        cards.extend((head, form))
    validate_semantic_cards(cards, require_full_core=True)
    started = perf_counter()
    output = tmp_path / f"synthetic-{model}.apkg"
    result = export_semantic_anki(cards=cards, output_path=output, model=model, prototype=True)
    elapsed = perf_counter() - started
    record_property("export_seconds", round(elapsed, 3))
    record_property("apkg_bytes", output.stat().st_size)
    assert len(result.manifest) == 6000
    assert summarize_cards(cards)["core"] == {
        "identities": 3000,
        "headwords": 3000,
        "important_forms": 3000,
        "reverse": 0,
        "listening": 0,
        "cloze": 0,
        "total": 6000,
    }
    with zipfile.ZipFile(output) as archive:
        database = tmp_path / "collection.anki2"
        database.write_bytes(archive.read("collection.anki2"))
    with sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True) as connection:
        assert connection.execute("SELECT count(*) FROM notes").fetchone()[0] == notes
        assert sorted(
            row[0] for row in connection.execute("SELECT count(*) FROM cards GROUP BY did")
        ) == [2000, 2000, 2000]
    assert not result.client_acceptance_proven
