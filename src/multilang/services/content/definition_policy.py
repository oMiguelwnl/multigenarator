"""One selected sense, one learner definition; formatting cannot certify meaning."""

import re
import unicodedata
from hashlib import sha256
from typing import TYPE_CHECKING

from multilang.domain.definitions import DefinitionEvidence
from multilang.services.part_of_speech import canonical_part_of_speech_label
from multilang.services.text_field_remediation import _is_learner_safe_definition

if TYPE_CHECKING:
    from multilang.services.lexical_lookup import LexicalRecord

DEFINITION_POLICY_VERSION = "definition-single-sense-v2"
_ACTIVE = re.compile(r"<|>|\{\{|\[(?:sound|anki):|(?:javascript|vbscript|data)\s*:", re.I)
_LABEL = re.compile(r"^([a-z][a-z ]{1,30}): (\S.*)$")


def definition_prompt_rules() -> list[str]:
    return [
        f"Definition policy: {DEFINITION_POLICY_VERSION}",
        "- Define exactly ONE selected source sense per card. Never merge unrelated senses or select a sense by list order.",
        "- Format the definition as '[part of speech]: [meaning]' on one plain-text line, at most 500 characters.",
        "- Keep the part-of-speech label in canonical English; write the meaning in the requested definition/explanation language.",
        "- Use simple learner-friendly vocabulary. Prefer a short phrase; avoid circular definitions that merely repeat the study word.",
        "- Preserve the supplied source meaning, part of speech and sense. Opaque sense identifiers alone are not meaning evidence.",
        "- Do not include HTML, lists, multiple senses, example sentences, pronunciation, or grammatical inflection notes in the definition.",
        "- Define function words by their actual function, not as letters or acronyms.",
        "- The example sentence must use the target with exactly the meaning expressed in the definition.",
        "- Style examples (English meanings only when English is requested): 'noun: a building where people live'; 'verb: to move quickly on foot'; 'adjective: having a low temperature'; 'preposition: toward the inside of something'.",
        "- Example with Portuguese meaning: 'noun: uma construção onde as pessoas moram'.",
    ]


def select_source_meaning(record: "LexicalRecord") -> tuple[str, str | None]:
    """Only source-authored sense mappings can disambiguate multiple meanings."""
    if record.definition_senses:
        selected = {
            entry.model_dump_json(): entry
            for entry in record.definition_senses
            if entry.sense_id == record.sense_id
        }
        if len(selected) != 1:
            raise ValueError("source sense is missing or ambiguous")
        entry = next(iter(selected.values()))
        return entry.meaning, entry.language
    meanings = tuple(dict.fromkeys(value.strip() for value in record.definitions if value.strip()))
    if len(meanings) != 1:
        raise ValueError("missing or ambiguous source meaning")
    return meanings[0], record.definition_language


def resolve_definition_evidence(identity, lookup) -> DefinitionEvidence:
    """Resolve a local source record against the persisted identity, never user text."""
    expected_pos = canonical_part_of_speech_label(identity.part_of_speech)
    if expected_pos is None:
        raise ValueError("definition evidence requires a resolved part of speech")
    records = lookup.lookup_candidates(
        language_code=identity.language.value, term=identity.normalized_lemma
    )
    matches = {}
    for record in records:
        if (
            record.lemma != identity.normalized_lemma
            or record.source != identity.source_id
            or record.source_version != identity.source_version
            or record.source_sha256 != identity.source_sha256
            or canonical_part_of_speech_label(record.part_of_speech) != expected_pos
            or record.sense_id != identity.sense_id
        ):
            continue
        matches[record.model_dump_json()] = record
    if len(matches) != 1:
        raise ValueError("definition evidence is missing or ambiguous for the canonical identity")
    serialized, record = next(iter(matches.items()))
    meaning, language = select_source_meaning(record)
    if language is None:
        raise ValueError("definition evidence requires the source meaning language")
    validate_definition(
        f"{expected_pos}: {meaning}",
        lemma=record.lemma,
        display_form=record.display_form,
        part_of_speech=expected_pos,
    )
    return DefinitionEvidence(
        lemma=record.lemma,
        source_language=identity.language.value,
        part_of_speech=expected_pos,
        sense_id=identity.sense_id,
        meaning=meaning,
        language=language,
        source=record.source,
        source_version=identity.source_version,
        source_sha256=identity.source_sha256,
        lexical_record_sha256=sha256(serialized.encode()).hexdigest(),
    )


def validate_definition(
    value: str, *, lemma: str, display_form: str, part_of_speech: str | None = None
) -> str:
    """Reject structural defects without rewriting source text or claiming truth."""
    if (
        not isinstance(value, str)
        or len(value) > 500
        or _ACTIVE.search(value)
        or len(value.splitlines()) != 1
        or any(
            unicodedata.category(char).startswith("C") or unicodedata.category(char) in {"Zl", "Zp"}
            for char in value
        )
    ):
        raise ValueError("definition must be bounded plain text on one line")
    match = _LABEL.fullmatch(value)
    if match is None:
        raise ValueError("definition must use '[part of speech]: [meaning]'")
    label, meaning = match.groups()
    if not any(char.isalnum() for char in meaning):
        raise ValueError("definition must contain a substantive meaning")
    canonical = canonical_part_of_speech_label(label)
    expected = canonical_part_of_speech_label(part_of_speech)
    if (canonical != label and label != "term") or (expected and expected != label):
        raise ValueError("definition part of speech differs from source")
    if not _is_learner_safe_definition(value):
        raise ValueError("definition must explain meaning, not a placeholder or inflection")

    def normalized(text: str) -> str:
        return unicodedata.normalize("NFC", text).casefold().strip(" .")

    circular_body = re.sub(
        r"^(?:to|a|an|the|um|uma|o|os|as|un|una|el|la|le|les|der|die|das|ein|eine)\s+",
        "",
        normalized(meaning),
    )
    if {normalized(meaning), circular_body} & {normalized(lemma), normalized(display_form)}:
        raise ValueError("circular definition repeats the study word")
    return value
