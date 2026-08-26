"""Contracts for canonical Korean text, morphology evidence, and identity."""

from __future__ import annotations

from importlib import import_module, util
from types import ModuleType
import unicodedata

import pytest
from pydantic import ValidationError


def _korean() -> ModuleType:
    assert util.find_spec("multilang.domain.korean") is not None, (
        "the Korean domain contract module must exist"
    )
    return import_module("multilang.domain.korean")


def _fingerprint(api: ModuleType, **overrides: object) -> object:
    values: dict[str, object] = {
        "analyzer_name": "kiwi",
        "analyzer_package_version": "0.23.2",
        "model_package_version": "0.23.0",
        "model_type": "cong",
        "enabled_dialects": "standard",
        "num_workers": 1,
        "integrate_allomorph": True,
        "top_n": 2,
        "split_complex": False,
        "compatible_jamo": False,
        "normalize_coda": False,
        "z_coda": False,
        "typos": None,
        "oov_handling": "chr",
        "policy_version": api.KOREAN_MORPHOLOGY_POLICY_VERSION,
    }
    values.update(overrides)
    return api.KoreanAnalyzerFingerprint(**values)


def _identity_values(api: ModuleType, **overrides: object) -> dict[str, object]:
    submitted = unicodedata.normalize("NFD", "학교")
    values: dict[str, object] = {
        "submitted_form": submitted,
        "canonical_nfc": "학교",
        "lemma": "학교",
        "part_of_speech": "NNG",
        "sense_id": "reviewed:school:1",
        "register": "standard",
        "morpheme_signature": (
            api.KoreanSignatureItem(form="학교", pos="NNG"),
        ),
        "analyzer_fingerprint": _fingerprint(api),
        "status": "resolved",
    }
    values.update(overrides)
    return values


def test_korean_constants_separate_canonical_code_from_provider_locale() -> None:
    api = _korean()

    assert api.KOREAN_LANGUAGE_CODE == "ko"
    assert api.KOREAN_PROVIDER_LOCALE == "ko-KR"
    assert api.KOREAN_MORPHOLOGY_POLICY_VERSION
    assert api.KOREAN_FOUNDATION_DEFAULT_SOURCE == "current-candidate"
    assert api.KOREAN_FOUNDATION_HISTORY_SOURCE == "v1-history"


def test_nfd_and_nfc_share_canonical_value_key_while_submission_is_preserved() -> None:
    api = _korean()
    nfc = "학교"
    nfd = unicodedata.normalize("NFD", nfc)

    assert nfd != nfc
    assert api.canonicalize_korean(nfd) == nfc
    assert api.canonicalize_korean(nfc) == nfc
    assert api.korean_lexical_key(
        lemma=nfd,
        part_of_speech="NNG",
        sense_id="reviewed:school:1",
    ) == api.korean_lexical_key(
        lemma=nfc,
        part_of_speech="NNG",
        sense_id="reviewed:school:1",
    )

    identity = api.KoreanLexicalIdentity(**_identity_values(api))
    assert identity.submitted_form == nfd
    assert identity.canonical_nfc == nfc


@pytest.mark.parametrize("forbidden", ["ㄱ", "ﾡ", "학교ㄱ", "학교ﾡ"])
def test_compatibility_and_halfwidth_hangul_are_rejected_without_repair(
    forbidden: str,
) -> None:
    api = _korean()

    with pytest.raises(api.KoreanTextError) as exc_info:
        api.canonicalize_korean(forbidden)

    assert str(exc_info.value) == "Korean text contains forbidden compatibility Hangul"
    assert forbidden not in str(exc_info.value)


def test_lexical_key_is_separated_by_part_of_speech_and_source_sense() -> None:
    api = _korean()
    noun = api.korean_lexical_key(
        lemma="배우",
        part_of_speech="NNG",
        sense_id="reviewed:actor:1",
    )
    predicate = api.korean_lexical_key(
        lemma="배우",
        part_of_speech="VV",
        sense_id="reviewed:learn:1",
    )
    second_noun_sense = api.korean_lexical_key(
        lemma="배우",
        part_of_speech="NNG",
        sense_id="reviewed:actor:2",
    )

    assert len({noun, predicate, second_noun_sense}) == 3
    assert noun.startswith("ko:")


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("lemma", ""),
        ("lemma", "unknown"),
        ("part_of_speech", ""),
        ("part_of_speech", "UNKNOWN"),
        ("sense_id", ""),
        ("sense_id", "unresolved"),
        ("register", ""),
        ("morpheme_signature", ()),
        ("canonical_nfc", unicodedata.normalize("NFD", "학교")),
        ("status", "ambiguous"),
    ],
)
def test_resolved_identity_rejects_incomplete_or_noncanonical_fields(
    field: str,
    invalid_value: object,
) -> None:
    api = _korean()

    with pytest.raises(ValidationError):
        api.KoreanLexicalIdentity(
            **_identity_values(api, **{field: invalid_value})
        )


def test_resolved_identity_rejects_incomplete_analyzer_fingerprint() -> None:
    api = _korean()
    incomplete = _fingerprint(api).model_dump()
    incomplete.pop("oov_handling")

    with pytest.raises(ValidationError):
        api.KoreanLexicalIdentity(
            **_identity_values(api, analyzer_fingerprint=incomplete)
        )


def test_signature_and_analysis_models_retain_safe_ordered_evidence() -> None:
    api = _korean()
    morphemes = (
        api.KoreanMorphemeEvidence(
            form="공부",
            lemma="공부",
            pos="NNG",
            raw_pos="NNG",
            oov=False,
        ),
        api.KoreanMorphemeEvidence(
            form="하",
            lemma="하다",
            pos="XSV",
            raw_pos="XSV",
            oov=False,
        ),
    )
    signature = (
        api.KoreanSignatureItem(form="공부", pos="NNG"),
        api.KoreanSignatureItem(form="하", pos="XSV"),
    )
    word = api.KoreanWordAnalysis(
        surface_form="공부해요",
        word_position=0,
        morphemes=morphemes,
        lexical_signature=signature,
    )
    alternative = api.KoreanAnalysisAlternative(
        rank=1,
        score=-12.5,
        words=(word,),
        has_oov=False,
    )

    assert word.lexical_signature == signature
    assert [item.pos for item in word.morphemes] == ["NNG", "XSV"]
    assert alternative.words[0].word_position == 0
    with pytest.raises(ValidationError):
        word.word_position = 1


def test_analysis_and_match_outcomes_are_explicit_and_fail_closed() -> None:
    api = _korean()
    fingerprint = _fingerprint(api)
    unavailable = api.KoreanMorphologyResult(
        status="unavailable",
        analyzer_fingerprint=fingerprint,
        alternatives=(),
        reason_code="analyzer_runtime_error",
        exception_class="RuntimeError",
    )
    match = api.KoreanMatchResult(
        status="unavailable",
        reason_code="analyzer_runtime_error",
        analyzer_fingerprint=fingerprint,
    )

    assert unavailable.status.value == "unavailable"
    assert unavailable.exception_class == "RuntimeError"
    assert match.status.value == "unavailable"
    assert match.matched is False


def test_signature_items_reject_noncanonical_forms_and_nonlexical_pos() -> None:
    api = _korean()

    with pytest.raises(ValidationError):
        api.KoreanSignatureItem(
            form=unicodedata.normalize("NFD", "학교"),
            pos="NNG",
        )
    with pytest.raises(ValidationError):
        api.KoreanSignatureItem(form="에서", pos="JKB")


def _foundation_values(api: ModuleType) -> dict[str, dict[str, object]]:
    return {
        "concept": {
            "id": "orthography.vowel.a",
            "domain": "orthography",
            "prerequisite_ids": ("orthography.jamo",),
            "sequence": 2,
        },
        "curriculum": {
            "target_concept_id": "orthography.vowel.a",
            "prerequisite_concept_ids": ("orthography.jamo",),
            "observed_concept_ids": (
                "orthography.jamo",
                "orthography.vowel.a",
            ),
            "unknown_concept_ids": ("orthography.vowel.a",),
            "policy": "strict",
        },
        "pronunciation": {
            "canonical_spelling": "국물",
            "normative_pronunciation": "[궁물]",
            "surface_pronunciation": "[궁물]",
            "ipa": "[kuŋmul]",
            "phonological_rule_ids": ("phonology.nasalization.velar",),
            "review_status": "needs_review",
        },
        "jamo_mapping": {
            "display_glyph": "ㄱ",
            "canonical_jamo": "ᄀ",
            "jamo_position": "initial",
            "unicode_name": "HANGUL CHOSEONG KIYEOK",
            "source_version": "unicode-17.0",
            "source_hash": "a" * 64,
            "review_status": "needs_review",
        },
    }


def test_foundation_contracts_are_exported_frozen_and_forbid_extras() -> None:
    api = _korean()
    expected_exports = {
        "KoreanConcept",
        "KoreanCurriculumEvidence",
        "KoreanPedagogicalJamoMapping",
        "KoreanPronunciationEvidence",
        "KoreanReviewStatus",
    }

    assert expected_exports <= set(api.__all__)
    assert {status.value for status in api.KoreanReviewStatus} == {
        "needs_review",
        "approved",
        "rejected",
    }

    values = _foundation_values(api)
    contracts = (
        api.KoreanConcept(**values["concept"]),
        api.KoreanCurriculumEvidence(**values["curriculum"]),
        api.KoreanPronunciationEvidence(**values["pronunciation"]),
        api.KoreanPedagogicalJamoMapping(**values["jamo_mapping"]),
    )
    for contract in contracts:
        field_name = next(iter(type(contract).model_fields))
        with pytest.raises(ValidationError):
            setattr(contract, field_name, getattr(contract, field_name))

    with pytest.raises(ValidationError):
        api.KoreanConcept(**values["concept"], unexpected=True)


@pytest.mark.parametrize("domain", ["orthography", "phonology", "grammar", "lexicon"])
def test_concept_contract_preserves_the_complete_spec_domain_enum(domain: str) -> None:
    api = _korean()
    values = _foundation_values(api)["concept"] | {"domain": domain}

    assert api.KoreanConcept(**values).domain == domain


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("id", ""),
        ("id", "unknown"),
        ("id", "x" * 129),
        ("domain", "media"),
        ("prerequisite_ids", ("orthography.jamo", "orthography.jamo")),
        ("prerequisite_ids", ("orthography.vowel.a",)),
        ("sequence", 0),
    ],
)
def test_concept_contract_rejects_unresolved_duplicate_or_unbounded_values(
    field: str,
    invalid_value: object,
) -> None:
    api = _korean()
    values = _foundation_values(api)["concept"] | {field: invalid_value}

    with pytest.raises(ValidationError):
        api.KoreanConcept(**values)


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("target_concept_id", "unresolved"),
        (
            "prerequisite_concept_ids",
            ("orthography.jamo", "orthography.jamo"),
        ),
        (
            "observed_concept_ids",
            ("orthography.jamo", "orthography.vowel.a", "orthography.vowel.a"),
        ),
        ("unknown_concept_ids", ("orthography.vowel.a", "orthography.vowel.a")),
        ("observed_concept_ids", ("orthography.jamo",)),
        ("policy", "best_effort"),
    ],
)
def test_curriculum_evidence_rejects_unsafe_or_false_local_evidence(
    field: str,
    invalid_value: object,
) -> None:
    api = _korean()
    values = _foundation_values(api)["curriculum"] | {field: invalid_value}

    with pytest.raises(ValidationError):
        api.KoreanCurriculumEvidence(**values)


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("canonical_spelling", ""),
        ("canonical_spelling", unicodedata.normalize("NFD", "국물")),
        ("normative_pronunciation", "unknown"),
        ("surface_pronunciation", "ﾡ"),
        ("ipa", "x" * 513),
        (
            "phonological_rule_ids",
            ("phonology.nasalization.velar", "phonology.nasalization.velar"),
        ),
        ("review_status", "auto_approved"),
    ],
)
def test_pronunciation_evidence_keeps_forms_separate_and_fails_closed(
    field: str,
    invalid_value: object,
) -> None:
    api = _korean()
    values = _foundation_values(api)["pronunciation"] | {field: invalid_value}

    with pytest.raises(ValidationError):
        api.KoreanPronunciationEvidence(**values)


def test_pedagogical_jamo_mapping_is_explicitly_positional() -> None:
    api = _korean()
    values = _foundation_values(api)["jamo_mapping"]

    initial = api.KoreanPedagogicalJamoMapping(**values)
    final = api.KoreanPedagogicalJamoMapping(
        **(
            values
            | {
                "canonical_jamo": "ᆨ",
                "jamo_position": "final",
                "unicode_name": "HANGUL JONGSEONG KIYEOK",
            }
        )
    )

    assert initial.display_glyph == final.display_glyph == "ㄱ"
    assert initial.canonical_jamo == "ᄀ"
    assert final.canonical_jamo == "ᆨ"
    with pytest.raises(api.KoreanTextError):
        api.canonicalize_korean(initial.display_glyph)


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("display_glyph", "ᄀ"),
        ("display_glyph", "ﾡ"),
        ("display_glyph", "ㄱㄴ"),
        ("canonical_jamo", "ㄱ"),
        ("canonical_jamo", "ﾡ"),
        ("canonical_jamo", "ᆨ"),
        ("jamo_position", "onset"),
        ("unicode_name", "HANGUL JONGSEONG KIYEOK"),
        ("source_version", "unknown"),
        ("source_hash", "a" * 63),
        ("source_hash", "A" * 64),
        ("review_status", "verified"),
    ],
)
def test_pedagogical_jamo_mapping_rejects_spoofed_or_malformed_identity(
    field: str,
    invalid_value: object,
) -> None:
    api = _korean()
    values = _foundation_values(api)["jamo_mapping"] | {field: invalid_value}

    with pytest.raises(ValidationError):
        api.KoreanPedagogicalJamoMapping(**values)


def test_foundation_validation_errors_hide_submitted_content() -> None:
    api = _korean()
    marker = "private-source-content-should-not-appear"
    values = _foundation_values(api)["concept"] | {"id": marker + "!"}

    with pytest.raises(ValidationError) as exc_info:
        api.KoreanConcept(**values)

    assert marker not in str(exc_info.value)


def test_all_modern_hangul_syllables_compose_and_decompose_exhaustively() -> None:
    api = _korean()
    syllables: set[str] = set()

    for initial_index in range(19):
        initial = chr(0x1100 + initial_index)
        for medial_index in range(21):
            medial = chr(0x1161 + medial_index)
            for final_index in range(28):
                final = None if final_index == 0 else chr(0x11A7 + final_index)
                syllable = api.compose_modern_hangul(initial, medial, final)

                assert len(syllable) == 1
                assert unicodedata.is_normalized("NFC", syllable)
                assert api.decompose_modern_hangul(syllable) == (
                    initial,
                    medial,
                    final,
                )
                syllables.add(syllable)

    assert len(syllables) == 11_172
    assert min(map(ord, syllables)) == 0xAC00
    assert max(map(ord, syllables)) == 0xD7A3
    assert api.compose_modern_hangul("ᄀ", "ᅡ") == "가"
    assert api.compose_modern_hangul("ᄒ", "ᅵ", "ᇂ") == "힣"


@pytest.mark.parametrize(
    ("initial", "medial", "final"),
    [
        ("ㄱ", "ᅡ", None),
        ("ﾡ", "ᅡ", None),
        ("ᄓ", "ᅡ", None),
        ("ᄀᄂ", "ᅡ", None),
        ("A", "ᅡ", None),
        ("ᄀ", "ㅏ", None),
        ("ᄀ", "ￂ", None),
        ("ᄀ", "ᅶ", None),
        ("ᄀ", "ᅡᅥ", None),
        ("ᄀ", "A", None),
        ("ᄀ", "ᅡ", "ㄱ"),
        ("ᄀ", "ᅡ", "ﾡ"),
        ("ᄀ", "ᅡ", "ᆧ"),
        ("ᄀ", "ᅡ", "ᇃ"),
        ("ᄀ", "ᅡ", "ᆨᆫ"),
        ("ᄀ", "ᅡ", ""),
    ],
)
def test_modern_hangul_composition_rejects_nonmodern_or_wrong_shape_inputs(
    initial: str,
    medial: str,
    final: str | None,
) -> None:
    api = _korean()

    with pytest.raises(api.KoreanTextError) as exc_info:
        api.compose_modern_hangul(initial, medial, final)

    error = str(exc_info.value)
    assert error in {
        "Hangul initial must be one modern conjoining Jamo",
        "Hangul medial must be one modern conjoining Jamo",
        "Hangul final must be one modern conjoining Jamo",
    }
    assert initial not in error
    assert medial not in error
    if final:
        assert final not in error


@pytest.mark.parametrize(
    "invalid",
    ["", "가나", "A", "ㄱ", "ﾡ", "ᄀ", "가", "\uABFF", "\uD7A4"],
)
def test_modern_hangul_decomposition_rejects_non_syllable_inputs(
    invalid: str,
) -> None:
    api = _korean()

    with pytest.raises(api.KoreanTextError) as exc_info:
        api.decompose_modern_hangul(invalid)

    assert str(exc_info.value) == "value must be one precomposed modern Hangul syllable"
    if invalid:
        assert invalid not in str(exc_info.value)


def test_nfd_syllable_requires_the_explicit_canonical_boundary() -> None:
    api = _korean()
    nfd = unicodedata.normalize("NFD", "각")
    mapping = api.KoreanPedagogicalJamoMapping(
        **_foundation_values(api)["jamo_mapping"]
    )

    assert nfd == "각"
    with pytest.raises(api.KoreanTextError):
        api.decompose_modern_hangul(nfd)

    canonical = api.canonicalize_korean(nfd)
    assert canonical == "각"
    assert api.decompose_modern_hangul(canonical) == ("ᄀ", "ᅡ", "ᆨ")
    assert mapping.display_glyph == "ㄱ"
