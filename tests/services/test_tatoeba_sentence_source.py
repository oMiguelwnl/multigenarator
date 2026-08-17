"""Tests for deterministic Tatoeba fallback sentence selection."""

from __future__ import annotations

from dataclasses import dataclass

from multilang.services.tatoeba_sentence_source import TatoebaCandidateRow, TatoebaSentenceSource


@dataclass
class FakeCandidateProvider:
    rows: list[TatoebaCandidateRow]
    calls: int = 0

    def search_candidates(
        self,
        *,
        display_form: str,
        lemma: str,
        target_language: str,
        translation_target_language: str,
    ) -> list[TatoebaCandidateRow]:
        self.calls += 1
        return list(self.rows)


def build_row(
    *,
    sentence: str,
    translations: list[str] | None = None,
    base: int = 0,
    is_direct_translation: bool = True,
) -> TatoebaCandidateRow:
    return TatoebaCandidateRow(
        sentence_id=1,
        sentence_text=sentence,
        target_language="es",
        translation_language="en",
        linked_translations=translations or ["I wash myself before sleep."],
        base=base,
        is_direct_translation=is_direct_translation,
    )


def test_reflexive_target_prefers_reflexive_mid_length_declarative_candidate() -> None:
    source = TatoebaSentenceSource(
        candidate_provider=FakeCandidateProvider(
            rows=[
                build_row(sentence="¿Lavar ahora?"),
                build_row(sentence="Lavar ropa."),
                build_row(sentence="Yo me lavo antes de dormir."),
            ]
        )
    )

    result = source.select_sentence(
        display_form="lavarse",
        lemma="lavar",
        target_language="es",
        translation_target_language="en",
    )

    assert result is not None
    assert result.sentence == "Yo me lavo antes de dormir."
    assert result.provenance["source"] == "tatoeba"


def test_returns_no_sentence_when_no_candidate_survives_filters() -> None:
    source = TatoebaSentenceSource(
        candidate_provider=FakeCandidateProvider(
            rows=[
                build_row(sentence="Wash!", translations=["Lave!"], base=0),
                build_row(sentence="What about wash?", translations=["E lavar?"], base=1),
                build_row(sentence="Wash", translations=[]),
            ]
        )
    )

    result = source.select_sentence(
        display_form="wash",
        lemma="wash",
        target_language="en",
        translation_target_language="pt",
    )

    assert result is None


def test_korean_returns_no_fallback_before_candidate_provider_access() -> None:
    provider = FakeCandidateProvider(rows=[])
    source = TatoebaSentenceSource(candidate_provider=provider)

    result = source.select_sentence(
        display_form="먹었어요",
        lemma="먹다",
        target_language="ko",
        translation_target_language="pt",
    )

    assert result is None
    assert provider.calls == 0
