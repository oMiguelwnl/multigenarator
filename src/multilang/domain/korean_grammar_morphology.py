"""Hash-bound contextual claims over unchanged, native Korean analyses.

These are review candidates, not approval receipts and not analyzer consensus.
References address projected morphemes within exact vendor surface spans.
"""

from __future__ import annotations

import unicodedata
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from multilang.domain.korean import KoreanMorphologyResult
from multilang.domain.korean_grammar_course import Digest, EntryId

Rationale = Annotated[str, StringConstraints(min_length=20, max_length=4096)]
SentenceField = Literal["example_sentence", "spoken_sample"]


class _ClaimModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    @field_validator("*")
    @classmethod
    def canonical_strings(cls, value):
        if isinstance(value, str) and (
            not unicodedata.is_normalized("NFC", value)
            or any(unicodedata.category(c) in {"Cc", "Cf", "Cs"} for c in value)
        ):
            raise ValueError("noncanonical_morphology_claim")
        return value


class GrammarMorphemeReference(_ClaimModel):
    span_index: int = Field(ge=0, le=16383, strict=True)
    morpheme_index: int = Field(ge=0, le=127, strict=True)


class GrammarNativeAnalysisRecord(_ClaimModel):
    entry_id: EntryId
    field: SentenceField
    text_sha256: Digest
    analysis: KoreanMorphologyResult


class GrammarRejectedAlternative(_ClaimModel):
    rank: int = Field(ge=1, le=2, strict=True)
    alternative_sha256: Digest
    rationale_pt: Rationale


class GrammarLexicalMorphologyClaim(_ClaimModel):
    support_entry_id: str = Field(pattern=r"^lex\.[a-z0-9-]+$", max_length=96)
    source_entry_sha256: Digest
    morpheme_refs: tuple[GrammarMorphemeReference, ...] = Field(min_length=1, max_length=32)
    mapping_kind: Literal["exact_lemma", "compound_lemma", "contextual_pos"]
    rationale_pt: Rationale


class GrammarConstructionMorphologyClaim(_ClaimModel):
    grammar_id: EntryId
    morpheme_refs: tuple[GrammarMorphemeReference, ...] = Field(min_length=1, max_length=256)
    evidence_kind: Literal[
        "morpheme", "construction", "morphophonology", "clause_structure", "metalinguistic"
    ]
    rationale_pt: Rationale


class GrammarSentenceMorphologyClaims(_ClaimModel):
    entry_id: EntryId
    field: SentenceField
    text_sha256: Digest
    analysis_sha256: Digest
    selected_rank: int = Field(ge=1, le=2, strict=True)
    selection_rationale_pt: Rationale
    rejected_alternatives: tuple[GrammarRejectedAlternative, ...] = Field(min_length=1, max_length=1)
    lexical_claims: tuple[GrammarLexicalMorphologyClaim, ...] = Field(min_length=1, max_length=256)
    grammar_claims: tuple[GrammarConstructionMorphologyClaim, ...] = Field(min_length=1, max_length=128)


class KoreanGrammarMorphologyManifest(_ClaimModel):
    schema_version: Literal["korean-grammar-morphology-claims-v1"]
    course_sha256: Digest
    support_sha256: Digest
    analyzer_fingerprint_sha256: Digest
    records: tuple[GrammarSentenceMorphologyClaims, ...] = Field(min_length=1, max_length=512)
