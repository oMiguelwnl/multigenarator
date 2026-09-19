"""Local card previews expose draft content without becoming export artifacts."""

from html.parser import HTMLParser

import pytest

from multilang.domain.exporting import export_field_names_for_language_and_source
from multilang.domain.jobs import SupportedLanguage
from multilang.services.qualification_machine import MachineCitation, MachineLexicalDecision
from multilang.services.qualification_machine_draft import MachineLexicalMapping


def mapping(
    *, item="lexical-1", candidate="candidate-1", lemma="casa", sense="house", gloss="dwelling"
):
    return MachineLexicalMapping(
        item_id=item,
        candidate_id=candidate,
        candidate_sha256="a" * 64,
        source_record_sha256="b" * 64,
        original_lemma=lemma,
        original_pos="NOUN",
        source_correction_proposed=False,
        decision=MachineLexicalDecision(
            item_id=item,
            item_sha256="c" * 64,
            decision="accepted",
            reason="The supplied lexical evidence supports this proposal.",
            citations=(
                MachineCitation(
                    source_index=0, source_sha256="d" * 64, start=0, end=5, quote="house"
                ),
            ),
            proposed_lemma=lemma,
            proposed_pos="NOUN",
            proposed_sense_id=sense,
            proposed_gloss=gloss,
        ),
    )


def test_preview_only_fills_preliminary_lemma_and_gloss_in_nine_existing_fields():
    from multilang.services.qualification_machine_preview import build_machine_card_preview

    source = mapping()
    preview = build_machine_card_preview((source,), language="pt")
    assert preview.origin == "machine"
    assert preview.production_eligible is False and preview.exportable is False
    assert preview.language_binding == "caller_declared"
    card = preview.cards[0]
    assert tuple(card.fields) == (
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
    assert card.fields["word"] == "casa"
    assert card.fields["Definitions"] == "dwelling"
    assert all(
        value == "" for key, value in card.fields.items() if key not in {"word", "Definitions"}
    )
    assert card.metadata.mappings == (source,)
    assert card.metadata.sense_id == "house"
    assert card.metadata.field_status["Definitions"] == "preliminary_lexical_gloss"
    assert card.metadata.field_status["IPA"] == "pending"
    assert card.metadata.field_status["Image"] == "intentionally_empty"
    assert "validated_definition" in card.metadata.pending_requirements
    assert "native_identity_and_profile_binding" in card.metadata.pending_requirements


@pytest.mark.parametrize("count", [-1, True, "<script>", 10001])
def test_preview_render_rejects_invalid_conflict_counts(count):
    from multilang.services.qualification_machine_preview import (
        build_machine_card_preview,
        render_machine_card_preview,
    )

    preview = build_machine_card_preview((), language="pt")
    with pytest.raises(ValueError, match="conflict count"):
        render_machine_card_preview(preview, conflicting_mapping_count=count)


@pytest.mark.parametrize("language", list(SupportedLanguage))
def test_preview_preserves_existing_language_specific_schema(language):
    from multilang.services.qualification_machine_preview import build_machine_card_preview

    card = build_machine_card_preview((mapping(),), language=language).cards[0]
    expected = export_field_names_for_language_and_source(
        language=language, source_type="frequency"
    )
    assert tuple(card.fields) == expected
    assert sorted(value for value in card.fields.values() if value) == ["casa", "dwelling"]
    assert card.fields["Image"] == ""


@pytest.mark.parametrize("limit", [0, -1, 101, True, "10", 1.5])
def test_preview_rejects_invalid_limits(limit):
    from multilang.services.qualification_machine_preview import build_machine_card_preview

    with pytest.raises(ValueError, match="limit"):
        build_machine_card_preview((mapping(),), language="pt", limit=limit)


def test_preview_limits_display_deterministically_without_losing_counts():
    from multilang.services.qualification_machine_preview import build_machine_card_preview

    sources = tuple(
        mapping(item=f"item-{i}", candidate=f"candidate-{i}", sense=f"sense-{i}") for i in range(12)
    )
    preview = build_machine_card_preview(sources, language="pt")
    assert len(preview.cards) == 10
    assert preview.available_cards == 12 and preview.omitted_cards == 2
    assert preview.source_mapping_count == 12
    assert preview == build_machine_card_preview(tuple(reversed(sources)), language="pt")


def test_preview_deduplicates_identical_mappings_and_combines_identical_sense_provenance():
    from multilang.services.qualification_machine_preview import build_machine_card_preview

    source = mapping()
    other = mapping(item="lexical-2", candidate="candidate-2")
    preview = build_machine_card_preview((other, source, source), language="pt")
    assert len(preview.cards) == 1
    assert preview.source_mapping_count == 2
    assert preview.cards[0].metadata.mappings == (source, other)


@pytest.mark.parametrize("kind", ["item", "candidate", "identity"])
def test_conflicting_duplicates_fail_even_beyond_preview_limit(kind):
    from multilang.services.qualification_machine_preview import build_machine_card_preview

    source = mapping()
    other = mapping(
        item=source.item_id if kind == "item" else "lexical-2",
        candidate=source.candidate_id if kind == "candidate" else "candidate-2",
        gloss="conflicting meaning",
    )
    with pytest.raises(ValueError, match="conflict"):
        build_machine_card_preview((source, other), language="pt", limit=1)


@pytest.mark.parametrize(
    "changes",
    [
        {"item_id": "another-item"},
        {"source_correction_proposed": True},
    ],
)
def test_preview_validates_mapping_identity(changes):
    from multilang.services.qualification_machine_preview import build_machine_card_preview

    source = mapping().model_copy(update=changes)
    with pytest.raises(ValueError, match="mapping"):
        build_machine_card_preview((source,), language="pt")


@pytest.mark.parametrize("verdict", ["rejected", "inconclusive"])
def test_preview_never_turns_unresolved_decisions_into_cards(verdict):
    from multilang.services.qualification_machine_preview import build_machine_card_preview

    source = mapping()
    decision = MachineLexicalDecision(
        item_id=source.item_id,
        item_sha256="c" * 64,
        decision=verdict,
        reason="Not resolved.",
    )
    with pytest.raises(ValueError, match="resolved"):
        build_machine_card_preview(
            (source.model_copy(update={"decision": decision}),), language="pt"
        )


def test_preview_rejects_remaining_uncertainty_in_an_accepted_decision():
    from multilang.services.qualification_machine_preview import build_machine_card_preview

    source = mapping()
    decision = source.decision.model_copy(update={"uncertainties": ("scope_unknown",)})
    with pytest.raises(ValueError, match="resolved"):
        build_machine_card_preview(
            (source.model_copy(update={"decision": decision}),), language="pt"
        )


def test_preview_rejects_unknown_language_and_language_drift():
    from multilang.services.qualification_machine_preview import (
        MachineCardPreview,
        build_machine_card_preview,
    )

    with pytest.raises(ValueError):
        build_machine_card_preview((mapping(),), language="xx")
    preview = build_machine_card_preview((mapping(),), language="pt")
    data = preview.model_dump(mode="json", exclude_computed_fields=True)
    data["language"] = "es"
    with pytest.raises(ValueError, match="language"):
        MachineCardPreview.model_validate(data)


def test_preview_roundtrip_rejects_invented_fields_content_and_authority():
    from multilang.services.qualification_machine_preview import (
        MachineCardPreview,
        build_machine_card_preview,
    )

    preview = build_machine_card_preview((mapping(),), language="pt")
    assert MachineCardPreview.model_validate_json(preview.model_dump_json()) == preview
    for change in (
        {"IPA": "invented"},
        {"Definitions": "A polished but unsupported definition."},
        {"sense": "house"},
    ):
        data = preview.model_dump(mode="json", exclude_computed_fields=True)
        data["cards"][0]["fields"].update(change)
        with pytest.raises(ValueError):
            MachineCardPreview.model_validate(data)
    for field in ("production_eligible", "exportable"):
        data = preview.model_dump(mode="json", exclude_computed_fields=True)
        data[field] = True
        with pytest.raises(ValueError):
            MachineCardPreview.model_validate(data)


def test_empty_preview_is_explicit_and_valid():
    from multilang.services.qualification_machine_preview import (
        build_machine_card_preview,
        render_machine_card_preview,
    )

    preview = build_machine_card_preview((), language="pt")
    assert preview.cards == () and preview.available_cards == 0
    assert preview.omitted_cards == 0
    assert "Nenhum cartão" in render_machine_card_preview(preview)


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


def test_renderer_escapes_all_untrusted_text_and_cannot_load_network_resources():
    from multilang.services.qualification_machine_preview import (
        build_machine_card_preview,
        render_machine_card_preview,
    )

    source = mapping(
        lemma='<img src="https://invalid.example/image" onerror="alert(1)">',
        sense="</pre><script>alert(2)</script>",
        gloss='<a href="javascript:alert(3)">meaning & use</a>',
    )
    preview = build_machine_card_preview((source,), language="pt")
    rendered = render_machine_card_preview(preview)
    parser = Tags()
    parser.feed(rendered)
    assert not {"script", "img", "iframe", "a", "link", "audio", "video", "form"}.intersection(
        tag for tag, _ in parser.elements
    )
    assert all(not any(name.startswith("on") for name in attrs) for _, attrs in parser.elements)
    csp = next(
        attrs["content"]
        for tag, attrs in parser.elements
        if tag == "meta" and attrs.get("http-equiv") == "Content-Security-Policy"
    )
    assert "default-src 'none'" in csp and "base-uri 'none'" in csp
    assert "&lt;img" in rendered and "&lt;script&gt;" in rendered
    assert "meaning &amp; use" in rendered
    assert "não exportável" in rendered
    assert "não é uma definição didática validada" in rendered
    assert "Pendências" in rendered and "Proveniência" in rendered
    assert "IPA" in rendered and "sentence_audio" in rendered


def test_renderer_revalidates_nested_contracts():
    from multilang.services.qualification_machine_preview import (
        build_machine_card_preview,
        render_machine_card_preview,
    )

    preview = build_machine_card_preview((mapping(),), language="pt")
    forged = preview.model_construct(
        **{
            **preview.model_dump(exclude_computed_fields=True),
            "cards": preview.cards,
            "exportable": True,
        }
    )
    with pytest.raises(ValueError):
        render_machine_card_preview(forged)


def test_preview_replay_rejects_candidate_conflicts_between_separate_cards():
    from multilang.services.qualification_machine_preview import (
        MachineCardPreview,
        build_machine_card_preview,
    )

    first = build_machine_card_preview((mapping(),), language="pt")
    second = build_machine_card_preview(
        (mapping(item="lexical-2", sense="different"),), language="pt"
    )
    payload = first.model_dump(mode="json", exclude_computed_fields=True)
    payload["cards"].append(
        second.model_dump(mode="json", exclude_computed_fields=True)["cards"][0]
    )
    payload["available_cards"] = payload["source_mapping_count"] = 2
    with pytest.raises(ValueError, match="conflict"):
        MachineCardPreview.model_validate(payload)


def test_preview_replay_checks_mapping_count_against_visible_provenance():
    from multilang.services.qualification_machine_preview import (
        MachineCardPreview,
        build_machine_card_preview,
    )

    preview = build_machine_card_preview(
        (mapping(), mapping(item="other", candidate="other")), language="pt"
    )
    payload = preview.model_dump(mode="json", exclude_computed_fields=True)
    payload["source_mapping_count"] = 1
    with pytest.raises(ValueError, match="count"):
        MachineCardPreview.model_validate(payload)
