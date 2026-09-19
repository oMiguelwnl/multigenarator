"""Korean completion shared smoke helper regression."""

import multilang.cli as cli_module


def test_generated_local_smoke_index_is_usable_as_english_evidence(tmp_path) -> None:
    from multilang.domain.jobs import SupportedLanguage
    from multilang.domain.lexicon import GroundingStatus
    from multilang.services.lexical_grounding import LexicalGroundingService
    from multilang.services.lexical_lookup import LexicalLookup
    from multilang.services.word_list_parser import ParsedWordListItem

    cli_module._write_local_smoke_assets(tmp_path)
    service = LexicalGroundingService(LexicalLookup(tmp_path / "lexicon"))
    candidate = service.ground_word_list_item(
        language=SupportedLanguage.EN,
        item=ParsedWordListItem(line_number=1, submitted_form="harbor", display_form="harbor", item_key="harbor"),
    )

    assert candidate.grounding_status == GroundingStatus.GROUNDED
    assert candidate.definition_language == "en"
