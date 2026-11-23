"""Preview one local upload using the generation pipeline's source readers."""

import re
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated, Literal

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel

from multilang.domain.highlights import HighlightInputMode
from multilang.domain.jobs import SupportedLanguage
from multilang.services.highlight_candidate_extraction import extract_highlight_candidates
from multilang.services.kindle_highlight_parser import parse_kindle_highlight_export
from multilang.services.word_list_parser import parse_word_list

router = APIRouter()
MAX_SOURCE_BYTES = 5_000_000
SAMPLE_SIZE = 40


class SourcePreview(BaseModel):
    candidate_count: int
    highlight_count: int = 0
    duplicates: int
    ignored: int
    items: list[str]
    excerpts: list[str]


def _korean_resolver():
    from multilang.services.korean_morphology import KiwiKoreanMorphologyService
    from multilang.services.lexical_grounding import LexicalGroundingService
    from multilang.services.lexical_lookup import LexicalLookup
    from multilang.settings import Settings

    return LexicalGroundingService(
        lookup=LexicalLookup(data_dir=Settings().lexicon_data_dir),
        korean_morphology=KiwiKoreanMorphologyService(),
    )


def _preview_highlights(
    path: Path, language: SupportedLanguage, mode: HighlightInputMode
) -> SourcePreview:
    korean = language is SupportedLanguage.KO
    if korean and mode is HighlightInputMode.VOCABULARY:
        raise HTTPException(422, "Para coreano, selecione o modo de trechos de leitura.")
    if mode is HighlightInputMode.TEXT and language in {SupportedLanguage.LA, SupportedLanguage.ZH}:
        raise HTTPException(422, "Neste idioma, use destaques de palavras ou expressões.")
    parsed = parse_kindle_highlight_export(path)
    if not parsed.highlights:
        raise HTTPException(422, "Nenhum destaque reconhecido. Confira a exportação do Kindle.")
    result = extract_highlight_candidates(
        parsed.highlights,
        language=language,
        input_mode=mode,
        korean_resolver=_korean_resolver() if korean else None,
    )
    if korean and result.errors:
        raise HTTPException(422, "A análise morfológica não resolveu os destaques em coreano.")
    if not result.candidates:
        raise HTTPException(422, "Nenhuma palavra reconhecida. Confira o idioma e o modo escolhido.")
    return SourcePreview(
        candidate_count=len(result.candidates),
        highlight_count=len(parsed.highlights),
        duplicates=result.duplicate_count,
        ignored=len(parsed.rejected) + result.rejected_token_count,
        items=[] if korean else [item.display_form[:256] for item in result.candidates[:SAMPLE_SIZE]],
        excerpts=[] if korean else [item.text[:300] for item in parsed.highlights[:5]],
    )


@router.post("/studio-api/sources/preview")
def preview_source(
    content: Annotated[bytes, Body(media_type="application/octet-stream")],
    kind: Literal["word-list", "highlights"],
    language: SupportedLanguage,
    extension: Literal["txt", "html", "htm"],
    mode: HighlightInputMode = HighlightInputMode.TEXT,
) -> SourcePreview:
    if len(content) > MAX_SOURCE_BYTES:
        raise HTTPException(413, "O arquivo excede o limite de 5 MB.")
    if kind == "word-list" and extension != "txt":
        raise HTTPException(422, "Para uma lista de palavras, selecione um arquivo TXT.")
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(422, "Salve o arquivo como texto UTF-8.") from None
    if not decoded.strip() or re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", decoded):
        raise HTTPException(422, "Selecione um arquivo de texto com conteúdo válido.")
    with NamedTemporaryFile(suffix=f".{extension}", delete_on_close=False) as source:
        source.write(content)
        source.close()
        path = Path(source.name)
        try:
            if kind == "highlights":
                return _preview_highlights(path, language, mode)
            words = parse_word_list(path)
        except (ValueError, AssertionError):
            raise HTTPException(422, "O leitor não reconheceu o conteúdo. Confira o arquivo.") from None
    if not words.items:
        raise HTTPException(422, "Nenhuma palavra reconhecida na lista.")
    duplicates = sum(warning.code == "duplicate_item" for warning in words.warnings)
    return SourcePreview(
        candidate_count=len(words.items),
        duplicates=duplicates,
        ignored=len(words.warnings) - duplicates,
        items=[item.display_form[:256] for item in words.items[:SAMPLE_SIZE]],
        excerpts=[],
    )
