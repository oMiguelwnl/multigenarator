"""Reviewed teaching content for lexical prerequisites in a grammar bundle."""

from pydantic import Field, field_validator, model_validator

from multilang.domain.korean_grammar import (
    KoreanGrammarAIEvidenceBinding,
    KoreanGrammarMediaBinding,
    _FrozenGrammarModel,
    _identifier,
    _safe_text,
    _sha256_text,
    grammar_content_hash,
    korean_grammar_canonical_json_sha256,
)


def bootstrap_candidate_sha256(value) -> str:
    payload = value.model_dump(mode="json") if hasattr(value, "model_dump") else dict(value)
    for field in ("content_hash", "review_binding", "word_media_binding", "sentence_media_binding"):
        payload.pop(field, None)
    return korean_grammar_canonical_json_sha256(payload)


class KoreanGrammarBootstrapCard(_FrozenGrammarModel):
    """Sidecar content; metadata alone never becomes an exported study card."""

    entry_id: str = Field(min_length=1, max_length=128)
    bootstrap_sha256: str = Field(min_length=64, max_length=64)
    definitions: str = Field(min_length=1, max_length=2048)
    ipa: str = Field(default="", max_length=2048)
    example_sentence: str = Field(min_length=1, max_length=2048)
    portuguese_translation: str = Field(min_length=1, max_length=2048)
    review_binding: KoreanGrammarAIEvidenceBinding
    word_media_binding: KoreanGrammarMediaBinding
    sentence_media_binding: KoreanGrammarMediaBinding
    content_hash: str = Field(min_length=64, max_length=64)

    @field_validator("entry_id")
    @classmethod
    def bounded_identifier(cls, value):
        return _identifier(value, field_name="entry_id")

    @field_validator("bootstrap_sha256", "content_hash")
    @classmethod
    def valid_hash(cls, value):
        return _sha256_text(value, field_name="bootstrap hash")

    @field_validator("definitions", "ipa", "example_sentence", "portuguese_translation")
    @classmethod
    def safe_text(cls, value, info):
        if info.field_name == "ipa" and value == "":
            return value
        return _safe_text(value, field_name=info.field_name, require_hangul=info.field_name == "example_sentence")

    @model_validator(mode="after")
    def reviewed_current_content(self):
        if self.content_hash != grammar_content_hash(self):
            raise ValueError("bootstrap teaching content hash drift")
        review = self.review_binding
        if (review.content_hash != grammar_content_hash(review)
                or review.candidate_sha256 != bootstrap_candidate_sha256(self)
                or review.consensus_status != "ai_review_passed"
                or review.deterministic_validator_result != "passed"):
            raise ValueError("bootstrap requires current linguistic review")
        media = (self.word_media_binding, self.sentence_media_binding)
        if review.media_sha256 != korean_grammar_canonical_json_sha256([item.content_hash for item in media]):
            raise ValueError("bootstrap media review binding drift")
        for binding in media:
            if (binding.content_hash != grammar_content_hash(binding)
                    or binding.integrity_status != "passed"
                    or binding.acoustic_review_status not in {"ai_acoustic_review_passed", "automated_integrity_passed"}):
                raise ValueError("bootstrap requires reviewed media")
        return self
