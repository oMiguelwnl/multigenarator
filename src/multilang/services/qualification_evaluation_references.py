"""Reproducible dictionary references for a versioned offline evaluation.

There is no caller-defined exemption role. Only this producer's bounded lexical
projection is shareable; source examples and review/observation data are omitted.
It proves provenance, not the linguistic correctness of the dictionary.
"""

import json
from typing import Annotated, Literal

from pydantic import Field, computed_field, field_validator, model_validator

from multilang.domain.form_evidence import LEXICAL_UPOS
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.language_profiles import NativeContract, Sha256
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.qualification_pipeline import ArtifactReference
from multilang.services.qualification_review import _json, _nfc
from multilang.services.vocabulary_sources import (
    SourceLimits,
    _strings,
    _verified_lines,
    wiktextract_record_candidates,
)

Text = Annotated[str, Field(min_length=1, max_length=16000)]
Labels = Annotated[tuple[Text, ...], Field(max_length=4096)]


class DictionaryReferenceTerm(NativeContract):
    lemma: str = Field(min_length=1, max_length=512)
    pos: str

    _lemma_nfc = field_validator("lemma")(_nfc)

    @field_validator("pos")
    @classmethod
    def lexical_pos(cls, value):
        if value not in LEXICAL_UPOS:
            raise ValueError("reference term requires lexical UPOS")
        return value


class DictionaryReferenceInput(NativeContract):
    dictionary: ArtifactReference
    language: SupportedLanguage
    terms: tuple[DictionaryReferenceTerm, ...] = Field(min_length=1, max_length=256)
    limits: SourceLimits = Field(default_factory=SourceLimits)

    @model_validator(mode="after")
    def unique_terms(self):
        if len({(x.lemma, x.pos) for x in self.terms}) != len(self.terms):
            raise ValueError("duplicate dictionary reference term")
        return self


class ReferenceForm(NativeContract):
    form: Text
    tags: Labels = ()
    raw_tags: Labels = ()


class ReferenceSense(NativeContract):
    glosses: Labels
    raw_glosses: Labels = ()
    tags: Labels = ()
    topics: Labels = ()
    raw_tags: Labels = ()
    form_of: Labels = ()


class DictionaryReferenceRecord(NativeContract):
    lemma: str
    pos: str
    source_record_sha256: Sha256
    tags: Labels = ()
    forms: tuple[ReferenceForm, ...] = Field(default=(), max_length=4096)
    senses: tuple[ReferenceSense, ...] = Field(min_length=1, max_length=4096)

    @computed_field
    @property
    def record_sha256(self) -> str:
        return canonical_sha256(self.model_dump(mode="json", exclude_computed_fields=True))


class DictionaryReferenceRegistry(NativeContract):
    schema_version: Literal["dictionary-reference-registry-1"] = "dictionary-reference-registry-1"
    producer: Literal["wiktextract-reference-projection-1"] = "wiktextract-reference-projection-1"
    spec: DictionaryReferenceInput
    records: tuple[DictionaryReferenceRecord, ...] = Field(min_length=1, max_length=4096)
    production_eligible: Literal[False] = False

    @computed_field
    @property
    def registry_sha256(self) -> str:
        return canonical_sha256(self.model_dump(mode="json", exclude_computed_fields=True))


def reference_excerpt(record: DictionaryReferenceRecord) -> str:
    text = json.dumps(
        record.model_dump(mode="json"),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    if len(text) > 64000:
        raise ValueError("dictionary reference excerpt limit exceeded")
    return text


def prepare_dictionary_references(spec: DictionaryReferenceInput) -> DictionaryReferenceRegistry:
    spec = DictionaryReferenceInput.model_validate(spec.model_dump(mode="json"))
    targets = {(term.lemma, term.pos) for term in spec.terms}
    lemma_filter = {term.lemma.casefold() for term in spec.terms}
    records, found, output_bytes = {}, set(), 0
    for line in _verified_lines(spec.dictionary.path, spec.dictionary.sha256, spec.limits):
        if not line.strip():
            continue
        raw = _json(line.encode())
        candidates = list(
            wiktextract_record_candidates(
                raw, language=spec.language.value, lemma_filter=lemma_filter
            )
        )
        chosen = [(index, c) for index, c in candidates if (c.lemma, c.pos) in targets]
        if not chosen:
            continue
        first = chosen[0][1]
        found.add((first.lemma, first.pos))
        if first.source_record_sha256 in records:
            continue
        forms = tuple(
            ReferenceForm(
                form=f["form"],
                tags=_strings(f.get("tags", ())),
                raw_tags=_strings(f.get("raw_tags", ())),
            )
            for f in first.forms
            if isinstance(f.get("form"), str) and f["form"]
        )
        senses = []
        for index, candidate in chosen:
            raw_sense = raw["senses"][index]
            senses.append(
                ReferenceSense(
                    glosses=candidate.glosses,
                    raw_glosses=_strings(raw_sense.get("raw_glosses", ())),
                    tags=_strings(raw_sense.get("tags", ())),
                    topics=_strings(raw_sense.get("topics", ())),
                    raw_tags=_strings(raw_sense.get("raw_tags", ())),
                    form_of=candidate.form_of,
                )
            )
        record = DictionaryReferenceRecord(
            lemma=first.lemma,
            pos=first.pos,
            source_record_sha256=first.source_record_sha256,
            tags=_strings(raw.get("tags", ())),
            forms=forms,
            senses=tuple(senses),
        )
        output_bytes += len(reference_excerpt(record).encode())
        if output_bytes > spec.limits.max_output_bytes:
            raise ValueError("dictionary reference output byte limit exceeded")
        records[first.source_record_sha256] = record
        if len(records) > min(4096, spec.limits.max_unique_entries):
            raise ValueError("dictionary reference record limit exceeded")
    if targets - found:
        raise ValueError("dictionary reference term missing for exact language/lemma/POS")
    return DictionaryReferenceRegistry(
        spec=spec, records=tuple(records[k] for k in sorted(records))
    )


def verify_dictionary_references(
    registry: DictionaryReferenceRegistry,
) -> DictionaryReferenceRegistry:
    registry = DictionaryReferenceRegistry.model_validate(
        registry.model_dump(mode="json", exclude_computed_fields=True)
    )
    replay = prepare_dictionary_references(registry.spec)
    if replay != registry:
        raise ValueError("dictionary reference projection replay detected drift")
    return replay
