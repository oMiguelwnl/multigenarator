"""Tests for cached lexical lookup."""

from __future__ import annotations

import json
from pathlib import Path
import unicodedata

import pytest

from multilang.services.lexical_lookup import LexicalLookup, LexicalRecord, normalize_lexical_key


def test_has_index_reports_missing_and_present_language_index(tmp_path: Path) -> None:
    lookup = LexicalLookup(data_dir=tmp_path)

    assert lookup.has_index(language_code="pt") is False

    _write_fixture_index(tmp_path, language_code="pt", rows={"lavar": _record("lavar")})

    assert lookup.has_index(language_code="pt") is True


def test_lookup_reads_fixture_index(tmp_path: Path) -> None:
    lookup = LexicalLookup(data_dir=tmp_path)
    index_path = _write_fixture_index(
        tmp_path,
        language_code="pt",
        rows={
            "lavar-se": _record(
                "lavar-se",
                definitions=["to wash oneself"],
                ipa=None,
            )
        },
    )

    record = lookup.lookup(language_code="pt", term="  LAVAR-SE  ")

    assert index_path.exists()
    assert record is not None
    assert record.lemma == "lavar-se"
    assert record.display_form == "lavar-se"
    assert record.definitions == ["to wash oneself"]
    assert record.ipa is None
    assert record.source == "manual"


def test_normalize_lexical_key_converges_canonical_equivalents() -> None:
    nfc = "학교"
    nfd = unicodedata.normalize("NFD", nfc)

    assert normalize_lexical_key(f"  {nfc}  ") == normalize_lexical_key(nfd)
    assert unicodedata.is_normalized("NFC", normalize_lexical_key(nfd))


def test_lookup_candidates_returns_ordered_source_backed_senses(tmp_path: Path) -> None:
    noun = _record(
        "배우",
        lemma="배우",
        part_of_speech="NNG",
        sense_id="fixture-actor-1",
        register="neutral",
        source="reviewed-fixture",
    )
    verb = _record(
        "배우다",
        lemma="배우다",
        part_of_speech="VV",
        sense_id="fixture-learn-1",
        register="neutral",
        source="reviewed-fixture",
    )
    _write_fixture_index(
        tmp_path,
        language_code="ko",
        rows={"배우": [noun, verb]},
    )
    lookup = LexicalLookup(data_dir=tmp_path)

    candidates = lookup.lookup_candidates(language_code="ko", term=" 배우 ")

    assert candidates == (
        LexicalRecord.model_validate(noun),
        LexicalRecord.model_validate(verb),
    )
    assert lookup.lookup(language_code="ko", term="배우") == candidates[0]


def test_korean_lookup_rejects_record_without_source_backed_sense(tmp_path: Path) -> None:
    _write_fixture_index(
        tmp_path,
        language_code="ko",
        rows={"학교": _record("학교", part_of_speech="NNG", source="reviewed-fixture")},
    )
    lookup = LexicalLookup(data_dir=tmp_path)

    with pytest.raises(ValueError, match="source-backed POS and sense_id"):
        lookup.lookup_candidates(language_code="ko", term="학교")


def test_iter_candidates_is_deterministic_and_deduplicates_only_complete_aliases(
    tmp_path: Path,
) -> None:
    nfc_school = "학교"
    nfd_school = unicodedata.normalize("NFD", nfc_school)
    actor = _record(
        "배우",
        lemma="배우",
        part_of_speech="NNG",
        sense_id="fixture-actor-1",
        register="neutral",
        source="reviewed-fixture",
    )
    formal_actor = _record(
        "배우",
        lemma="배우",
        part_of_speech="NNG",
        sense_id="fixture-actor-1",
        register="formal",
        source="reviewed-fixture",
    )
    school = _record(
        nfc_school,
        lemma=nfc_school,
        part_of_speech="NNG",
        sense_id="fixture-school-1",
        register="neutral",
        source="reviewed-fixture",
    )
    school_alias = _record(
        nfd_school,
        lemma=nfd_school,
        part_of_speech="NNG",
        sense_id="fixture-school-1",
        register="neutral",
        source="reviewed-fixture",
    )
    learn = _record(
        "배우다",
        lemma="배우다",
        part_of_speech="VV",
        sense_id="fixture-learn-1",
        register="neutral",
        source="reviewed-fixture",
    )
    _write_fixture_index(
        tmp_path,
        language_code="ko",
        rows={
            nfd_school: school_alias,
            "배우": [actor, formal_actor, learn],
            nfc_school: school,
        },
    )
    lookup = LexicalLookup(data_dir=tmp_path)

    candidates = lookup.iter_candidates(language_code="ko")

    assert [record.sense_id for record in candidates] == [
        "fixture-actor-1",
        "fixture-actor-1",
        "fixture-learn-1",
        "fixture-school-1",
    ]
    assert [record.register for record in candidates] == [
        "neutral",
        "formal",
        "neutral",
        "neutral",
    ]
    assert candidates[-1].lemma == nfc_school


def test_legacy_single_record_index_keeps_lookup_and_inventory_compatibility(
    tmp_path: Path,
) -> None:
    legacy = _record("lavar")
    _write_fixture_index(tmp_path, language_code="pt", rows={"lavar": legacy})
    lookup = LexicalLookup(data_dir=tmp_path)

    assert lookup.lookup(language_code="pt", term="LAVAR") == LexicalRecord.model_validate(legacy)
    assert lookup.lookup_candidates(language_code="pt", term="LAVAR") == (
        LexicalRecord.model_validate(legacy),
    )
    assert lookup.iter_candidates(language_code="pt") == (LexicalRecord.model_validate(legacy),)


def _record(
    term: str,
    *,
    lemma: str | None = None,
    definitions: list[str] | None = None,
    ipa: str | None = "/term/",
    part_of_speech: str | None = None,
    sense_id: str | None = None,
    register: str | None = None,
    source: str = "manual",
) -> dict[str, object]:
    return {
        "term": term,
        "display_form": term,
        "lemma": lemma or term,
        "definitions": definitions or [f"definition for {term}"],
        "part_of_speech": part_of_speech,
        "sense_id": sense_id,
        "register": register,
        "ipa": ipa,
        "source": source,
    }


def _write_fixture_index(
    tmp_path: Path,
    *,
    language_code: str,
    rows: dict[str, dict[str, object] | list[dict[str, object]]],
) -> Path:
    index_path = tmp_path / language_code / "lexical-index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
    return index_path
