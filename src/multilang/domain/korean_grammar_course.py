"""Authored Korean lessons: content is distinct from production approval."""

from __future__ import annotations

import unicodedata
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from multilang.domain.korean_grammar import (
    KOREAN_GRAMMAR_CATEGORIES,
    korean_grammar_canonical_json_sha256,
)

EntryId = Annotated[str, StringConstraints(pattern=r"^g(?:[0-9]|1[0-3])\.[a-z0-9-]+$", max_length=96)]
Text = Annotated[str, StringConstraints(min_length=1, max_length=2048)]
SourceId = Literal["sejong-curriculum", "krdict"]


class _CourseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, hide_input_in_errors=True, serialize_by_alias=True
    )

    @field_validator("*")
    @classmethod
    def canonical_safe_text(cls, value):
        for item in value if isinstance(value, tuple) else (value,):
            if not isinstance(item, str):
                continue
            if item != unicodedata.normalize("NFC", item) or item != item.strip():
                raise ValueError("course_text_must_be_canonical")
            if any(unicodedata.category(c) in {"Cc", "Cf", "Cs"} for c in item):
                raise ValueError("course_text_contains_control_characters")
            if any(marker in item.lower() for marker in ("<", ">", "[sound:", "javascript:")):
                raise ValueError("course_text_contains_markup")
        if isinstance(value, tuple) and all(isinstance(item, str) for item in value) and len(set(value)) != len(value):
            raise ValueError("course_list_contains_duplicates")
        return value


class KoreanGrammarLesson(_CourseModel):
    """One original explanation with explicit, reviewable teaching dependencies."""

    entry_id: EntryId
    category_id: str
    form: Text
    function: Text
    attachment_rule: Text
    usage_register: Text = Field(alias="register")
    example_sentence: Text
    portuguese_translation: Text
    spoken_sample: Text
    prerequisite_ids: tuple[EntryId, ...] = Field(max_length=128)
    lexical_lemmas: tuple[Text, ...] = Field(min_length=1, max_length=32)
    source_ids: tuple[SourceId, ...] = Field(min_length=1, max_length=2)
    notes: str = Field(max_length=4096)
    target_surfaces: tuple[Text, ...] = Field(min_length=1, max_length=16)

    @model_validator(mode="after")
    def consistent_target(self) -> Self:
        # The existing export schema stores the rule and essential usage notes
        # together. Reject an unexportable lesson at authoring time; never trim.
        if len(self.attachment_rule + (" Nota: " + self.notes if self.notes else "")) > 2048:
            raise ValueError("compiled_grammar_rule_exceeds_limit")
        if self.category_id not in KOREAN_GRAMMAR_CATEGORIES:
            raise ValueError("unknown_grammar_category")
        if self.entry_id.partition(".")[0].upper() != self.category_id:
            raise ValueError("grammar_id_category_mismatch")
        if self.entry_id in self.prerequisite_ids:
            raise ValueError("grammar_self_dependency")
        for text in (self.form, self.example_sentence, self.spoken_sample):
            if not any("가" <= c <= "힣" for c in text):
                raise ValueError("korean_lesson_requires_hangul")
        # Editorial anchors only; substring presence does NOT prove morphology or i+1.
        if not all(surface in self.example_sentence for surface in self.target_surfaces):
            raise ValueError("editorial_target_missing_from_example")
        return self

    @property
    def content_sha256(self) -> str:
        return korean_grammar_canonical_json_sha256(self)


class KoreanGrammarCourse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_version: Literal["korean-grammar-course-v1"] = "korean-grammar-course-v1"
    language: Literal["ko"] = "ko"
    translation_language: Literal["pt-BR"] = "pt-BR"
    cards: tuple[KoreanGrammarLesson, ...] = Field(min_length=14, max_length=256)

    @model_validator(mode="after")
    def ordered_complete_inventory(self) -> Self:
        seen: set[str] = set()
        previous_category = -1
        for card in self.cards:
            if card.entry_id in seen:
                raise ValueError("duplicate_grammar_entry")
            if not set(card.prerequisite_ids) <= seen:
                raise ValueError("unknown_or_forward_grammar_dependency")
            category = int(card.category_id[1:])
            if category < previous_category:
                raise ValueError("unordered_grammar_category")
            previous_category = category
            seen.add(card.entry_id)
        if {card.category_id for card in self.cards} != set(KOREAN_GRAMMAR_CATEGORIES):
            raise ValueError("incomplete_grammar_categories")
        return self

    @property
    def content_sha256(self) -> str:
        return korean_grammar_canonical_json_sha256(self)

    def prerequisite_closure(self, entry_id: str) -> tuple[str, ...]:
        by_id = {card.entry_id: card for card in self.cards}
        pending = list(by_id[entry_id].prerequisite_ids)
        ancestors: set[str] = set()
        while pending:
            predecessor = pending.pop()
            if predecessor not in ancestors:
                ancestors.add(predecessor)
                pending.extend(by_id[predecessor].prerequisite_ids)
        return tuple(card.entry_id for card in self.cards if card.entry_id in ancestors)


Digest = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class KoreanGrammarLexicalSupportEntry(_CourseModel):
    entry_id: str = Field(pattern=r"^lex\.[a-z0-9-]+$", max_length=96)
    lemma: Text
    source_form: Text
    source_pos: Literal["명", "대", "동", "형", "부", "관", "보", "의"]
    source_entry_sha256: Digest
    meaning_pt: Text
    teaching_mode: Literal["lexical", "construction"]
    introduced_by: EntryId | None
    usage_note_pt: Text
    used_by: tuple[EntryId, ...] = Field(min_length=1, max_length=256)

    @model_validator(mode="after")
    def explicit_teaching_owner(self) -> Self:
        if (self.teaching_mode == "construction") != (self.introduced_by is not None):
            raise ValueError("construction_requires_teaching_owner")
        return self


class KoreanGrammarLexicalSupport(_CourseModel):
    schema_version: Literal["korean-grammar-lexical-support-v1"]
    course_sha256: Digest
    source_id: Literal["nikl-korean-learners-vocabulary"]
    source_version: Literal["2003-06-04.revised-2019-05-30"]
    source_sha256: Literal["3b49681f05d6a7490c13da2a2847e433effdf65da409fd295792d6ee33685064"]
    entries: tuple[KoreanGrammarLexicalSupportEntry, ...] = Field(min_length=1, max_length=256)


class KoreanGrammarObservationUncertainty(_CourseModel):
    form: Text
    reason: Text


class KoreanGrammarObservation(_CourseModel):
    entry_id: EntryId
    observed_grammar_ids: tuple[EntryId, ...] = Field(min_length=1, max_length=256)
    rationale_pt: Text
    unresolved: tuple[KoreanGrammarObservationUncertainty, ...] = Field(max_length=32)


class KoreanGrammarObservations(_CourseModel):
    schema_version: Literal["korean-grammar-observations-v1"]
    course_sha256: Digest
    observation_scope: Literal["example-and-spoken-sample"]
    entries: tuple[KoreanGrammarObservation, ...] = Field(min_length=14, max_length=256)


class KoreanGrammarCourseSupport(_CourseModel):
    lexical: KoreanGrammarLexicalSupport
    observations: KoreanGrammarObservations
