from __future__ import annotations

from pathlib import Path

import pytest

from multilang.domain.korean import (
    KoreanAnalyzerFingerprint,
    KoreanLexicalIdentity,
    KoreanSignatureItem,
)
from multilang.domain.jobs import SupportedLanguage
from multilang.services.highlight_candidate_extraction import extract_highlight_candidates
from multilang.services.highlight_import_preview import build_highlight_import_preview
from multilang.services.kindle_highlight_parser import parse_kindle_highlight_export
from multilang.services.lexical_grounding import KoreanResolvedLexeme


FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "kindle_highlights"


def test_build_highlight_import_preview_combines_parser_and_candidate_counts() -> None:
    preview = build_highlight_import_preview(
        FIXTURE_DIR / "local_export.html",
        language=SupportedLanguage.ES,
    )

    assert preview.imported_highlights == 3
    assert preview.extracted_candidates > 0
    assert preview.rejected_highlights == 0
    assert preview.duplicate_candidates >= 0
    assert preview.planned_cards == preview.extracted_candidates


def test_build_highlight_import_preview_applies_planned_card_limit() -> None:
    preview = build_highlight_import_preview(
        FIXTURE_DIR / "local_export.txt",
        language=SupportedLanguage.PT,
        planned_card_limit=2,
    )

    assert preview.extracted_candidates > 2
    assert preview.planned_cards == 2


def test_build_highlight_import_preview_omits_private_text_and_paths_from_errors(tmp_path: Path) -> None:
    private_path = tmp_path / "Private Book - Secret Author.pdf"
    private_text = "Minha frase privada nunca deve aparecer"
    private_path.write_text(private_text, encoding="utf-8")

    with pytest.raises(ValueError) as exc_info:
        build_highlight_import_preview(private_path, language=SupportedLanguage.PT)

    message = str(exc_info.value)
    assert private_text not in message
    assert str(private_path) not in message
    assert "unsupported_format" in message


def _korean_identity(*, surface_form: str, lemma: str, sense_id: str) -> KoreanLexicalIdentity:
    return KoreanLexicalIdentity(
        submitted_form=None,
        canonical_nfc=surface_form,
        lemma=lemma,
        part_of_speech="NNG",
        sense_id=sense_id,
        register="standard",
        morpheme_signature=(KoreanSignatureItem(form=lemma, pos="NNG"),),
        analyzer_fingerprint=KoreanAnalyzerFingerprint(
            analyzer_name="kiwi",
            analyzer_package_version="0.23.2",
            model_package_version="0.23.0",
            model_type="cong",
            enabled_dialects="standard",
            num_workers=1,
            integrate_allomorph=True,
            top_n=2,
            split_complex=False,
            compatible_jamo=False,
            normalize_coda=False,
            z_coda=False,
            typos=None,
            oov_handling="chr",
            policy_version="kiwi-top2-consensus-v1",
        ),
        status="resolved",
    )


class _PreviewKoreanResolver:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def resolve_korean_highlight_text(
        self,
        text: str,
    ) -> tuple[KoreanResolvedLexeme, ...]:
        self.calls.append(text)
        return (
            KoreanResolvedLexeme(
                surface_form="물은",
                identity=_korean_identity(
                    surface_form="물은",
                    lemma="물",
                    sense_id="fixture:water:1",
                ),
                word_position=0,
            ),
            KoreanResolvedLexeme(
                surface_form="학교에서",
                identity=_korean_identity(
                    surface_form="학교에서",
                    lemma="학교",
                    sense_id="fixture:school:1",
                ),
                word_position=1,
            ),
        )


class _UnavailablePreviewKoreanResolver:
    def resolve_korean_highlight_text(
        self,
        text: str,
    ) -> tuple[KoreanResolvedLexeme, ...]:
        raise RuntimeError("C:/private/book.txt raw excerpt vendor dump traceback prompt")


def _write_korean_kindle_fixture(path: Path, text: str) -> None:
    path.write_text(
        "==========\nSynthetic Learner Reader\n- Your Highlight at location 7\n\n"
        f"{text}\n",
        encoding="utf-8",
    )


def test_korean_preview_passes_same_resolver_and_matches_extraction_counts(
    tmp_path: Path,
) -> None:
    private_text = "물은 학교에서 보여요"
    path = tmp_path / "Private Korean Book.txt"
    _write_korean_kindle_fixture(path, private_text)
    resolver = _PreviewKoreanResolver()

    preview = build_highlight_import_preview(
        path,
        language=SupportedLanguage.KO,
        korean_resolver=resolver,
    )
    parsed = parse_kindle_highlight_export(path)
    direct_resolver = _PreviewKoreanResolver()
    extraction = extract_highlight_candidates(
        parsed.highlights,
        language=SupportedLanguage.KO,
        korean_resolver=direct_resolver,
    )

    assert preview.imported_highlights == 1
    assert preview.extracted_candidates == len(extraction.candidates) == 2
    assert preview.planned_cards == 2
    assert resolver.calls == [private_text]
    serialized = preview.model_dump_json()
    assert private_text not in serialized
    assert str(path) not in serialized


def test_korean_preview_unavailable_resolution_returns_content_free_counts(
    tmp_path: Path,
) -> None:
    private_text = "비밀 원문 prompt instruction"
    path = tmp_path / "Secret Reader.txt"
    _write_korean_kindle_fixture(path, private_text)

    preview = build_highlight_import_preview(
        path,
        language=SupportedLanguage.KO,
        korean_resolver=_UnavailablePreviewKoreanResolver(),
    )
    serialized = preview.model_dump_json()

    assert preview.imported_highlights == 1
    assert preview.extracted_candidates == 0
    assert preview.planned_cards == 0
    assert private_text not in serialized
    assert str(path) not in serialized
    assert "vendor dump" not in serialized
    assert "traceback" not in serialized
