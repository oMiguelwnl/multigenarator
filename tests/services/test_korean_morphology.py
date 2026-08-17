"""Real-library goldens and fail-closed tests for Korean morphology."""

from __future__ import annotations

from importlib import import_module, util
import os
import subprocess
import sys
from types import ModuleType
import unicodedata

import pytest


_OOV_TEXT = "알리오올리오가 진짜 맛있는 집"
_ANALYZE_OPTIONS: dict[str, object] = {
    "top_n": 2,
    "split_complex": False,
    "compatible_jamo": False,
    "normalize_coda": False,
    "z_coda": False,
    "typos": None,
    "oov_handling": "chr",
}


def _service_module() -> ModuleType:
    assert util.find_spec("multilang.services.korean_morphology") is not None, (
        "the Korean morphology adapter module must exist"
    )
    return import_module("multilang.services.korean_morphology")


def _real_kiwi() -> object:
    from kiwipiepy import Kiwi

    return Kiwi(
        num_workers=1,
        model_type="cong",
        enabled_dialects="standard",
        integrate_allomorph=True,
    )


def _signature_pairs(word: object) -> tuple[tuple[str, str], ...]:
    return tuple((item.form, item.pos) for item in word.lexical_signature)


def test_importing_adapter_does_not_import_or_construct_kiwi() -> None:
    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "utf-8"
    script = (
        "import sys; "
        "import multilang.services.korean_morphology; "
        "assert 'kiwipiepy' not in sys.modules"
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )

    assert result.returncode == 0, result.stderr


def test_fingerprint_records_every_locked_constructor_and_analysis_option() -> None:
    api = _service_module()

    def forbidden_factory() -> object:
        raise AssertionError("fingerprint access must remain lazy")

    service = api.KiwiKoreanMorphologyService(analyzer_factory=forbidden_factory)

    assert service.fingerprint.model_dump() == {
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
        "policy_version": "kiwi-top2-consensus-v1",
    }


def test_repeated_analysis_calls_construct_one_real_analyzer_lazily() -> None:
    api = _service_module()
    construction_count = 0

    def counted_factory() -> object:
        nonlocal construction_count
        construction_count += 1
        return _real_kiwi()

    service = api.KiwiKoreanMorphologyService(analyzer_factory=counted_factory)
    assert construction_count == 0

    first = service.analyze("학교에서")
    second = service.analyze("공부해요")

    assert first.status.value == "resolved"
    assert second.status.value == "resolved"
    assert construction_count == 1


def test_real_kiwi_projects_noun_particle_and_compound_eojeol_evidence() -> None:
    api = _service_module()
    service = api.KiwiKoreanMorphologyService(analyzer_factory=_real_kiwi)

    noun_result = service.analyze("학교에서")
    compound_result = service.analyze("공부해요")

    assert noun_result.status.value == "resolved"
    assert compound_result.status.value == "resolved"
    for alternative in noun_result.alternatives:
        assert _signature_pairs(alternative.words[0]) == (("학교", "NNG"),)
        assert [item.raw_pos for item in alternative.words[0].morphemes] in (
            ["NNG", "JKB"],
            ["NNG", "JKB", "JKB"],
        )
    for alternative in compound_result.alternatives:
        assert alternative.words[0].word_position == 0
        assert _signature_pairs(alternative.words[0]) == (
            ("공부", "NNG"),
            ("하", "XSV"),
        )
        assert alternative.words[0].surface_form == "공부해요"


def test_real_kiwi_projects_nfc_and_nfd_inputs_identically() -> None:
    api = _service_module()
    kiwi = _real_kiwi()
    service = api.KiwiKoreanMorphologyService(analyzer_factory=lambda: kiwi)
    nfc = "학교에서"
    nfd = unicodedata.normalize("NFD", nfc)

    nfc_result = service.analyze(nfc)
    nfd_result = service.analyze(nfd)

    assert nfc_result == nfd_result


def test_real_kiwi_oov_token_evidence_marks_analysis_non_passing() -> None:
    api = _service_module()
    kiwi = _real_kiwi()

    raw_alternatives = kiwi.analyze(_OOV_TEXT, **_ANALYZE_OPTIONS)
    assert len(raw_alternatives) == 2
    assert all(
        any(
            token.form == "알리오올리오" and token.oov is True
            for token in tokens
        )
        for tokens, _score in raw_alternatives
    )

    result = api.KiwiKoreanMorphologyService(
        analyzer_factory=lambda: kiwi
    ).analyze(_OOV_TEXT)

    assert result.status.value == "oov"
    assert result.reason_code.value == "oov_token"
    assert result.passing is False
    assert len(result.alternatives) == 2
    assert all(alternative.has_oov for alternative in result.alternatives)


class _RuntimeFailureAnalyzer:
    def analyze(self, text: str, **kwargs: object) -> list[object]:
        raise OSError("C:/private/learner.txt secret token dump")


class _EmptyAnalyzer:
    def analyze(self, text: str, **kwargs: object) -> list[object]:
        return []


class _MalformedAnalyzer:
    def analyze(self, text: str, **kwargs: object) -> list[object]:
        return [(object(), "not-a-score")]


@pytest.mark.parametrize(
    ("factory", "reason_code", "exception_class"),
    [
        (
            lambda: (_ for _ in ()).throw(ImportError("secret import path")),
            "analyzer_import_error",
            "ImportError",
        ),
        (
            lambda: (_ for _ in ()).throw(RuntimeError("secret model path")),
            "analyzer_construction_error",
            "RuntimeError",
        ),
        (lambda: _RuntimeFailureAnalyzer(), "analyzer_runtime_error", "OSError"),
        (lambda: _EmptyAnalyzer(), "empty_analysis", None),
        (lambda: _MalformedAnalyzer(), "malformed_analysis", None),
    ],
)
def test_import_model_runtime_and_malformed_failures_are_typed_and_content_free(
    factory: object,
    reason_code: str,
    exception_class: str | None,
) -> None:
    api = _service_module()
    source_text = "비밀학습자텍스트"
    service = api.KiwiKoreanMorphologyService(analyzer_factory=factory)

    result = service.analyze(source_text)
    serialized = result.model_dump_json()

    assert result.status.value == "unavailable"
    assert result.passing is False
    assert result.reason_code.value == reason_code
    assert result.exception_class == exception_class
    assert source_text not in serialized
    assert "private" not in serialized
    assert "secret" not in serialized
    assert "token dump" not in serialized


def test_forbidden_korean_text_returns_invalid_without_constructing_analyzer() -> None:
    api = _service_module()
    construction_count = 0

    def counted_factory() -> object:
        nonlocal construction_count
        construction_count += 1
        return _real_kiwi()

    result = api.KiwiKoreanMorphologyService(
        analyzer_factory=counted_factory
    ).analyze("학교ㄱ")

    assert result.status.value == "invalid"
    assert result.reason_code.value == "invalid_text"
    assert result.passing is False
    assert construction_count == 0
    assert "학교" not in result.model_dump_json()


def _target_identity(
    service: object,
    *,
    lemma: str,
    part_of_speech: str,
    signature: tuple[tuple[str, str], ...],
    sense_id: str,
    submitted_form: str | None = None,
    fingerprint: object | None = None,
) -> object:
    korean = import_module("multilang.domain.korean")
    canonical_form = korean.canonicalize_korean(submitted_form or lemma)
    return korean.KoreanLexicalIdentity(
        submitted_form=submitted_form,
        canonical_nfc=canonical_form,
        lemma=korean.canonicalize_korean(lemma),
        part_of_speech=part_of_speech,
        sense_id=sense_id,
        register="standard",
        morpheme_signature=tuple(
            korean.KoreanSignatureItem(form=form, pos=pos)
            for form, pos in signature
        ),
        analyzer_fingerprint=fingerprint or service.fingerprint,
        status="resolved",
    )


@pytest.mark.parametrize(
    ("lemma", "part_of_speech", "signature", "sentence"),
    [
        ("먹다", "VV", (("먹", "VV"),), "밥을 먹었어요"),
        ("듣다", "VV", (("듣", "VV"),), "음악을 들어요"),
        ("예쁘다", "VA", (("예쁘", "VA"),), "꽃이 예뻐요"),
    ],
)
def test_real_kiwi_consensus_matches_regular_irregular_and_adjectival_predicates(
    lemma: str,
    part_of_speech: str,
    signature: tuple[tuple[str, str], ...],
    sentence: str,
) -> None:
    api = _service_module()
    service = api.KiwiKoreanMorphologyService()
    target = _target_identity(
        service,
        lemma=lemma,
        part_of_speech=part_of_speech,
        signature=signature,
        sense_id=f"reviewed:{part_of_speech}:{lemma}",
    )

    result = service.match_target(sentence, target)

    assert result.status.value == "matched"
    assert result.matched is True
    assert result.alternative_matches == (True, True)


def test_real_kiwi_compound_signature_requires_one_complete_eojeol() -> None:
    api = _service_module()
    service = api.KiwiKoreanMorphologyService()
    target = _target_identity(
        service,
        lemma="공부하다",
        part_of_speech="VV",
        signature=(("공부", "NNG"), ("하", "XSV")),
        sense_id="reviewed:study:1",
    )

    same_eojeol = service.match_target("매일 한국어를 공부해요", target)
    split_eojeol = service.match_target("공부 하세요", target)

    assert same_eojeol.status.value == "matched"
    assert same_eojeol.alternative_matches == (True, True)
    assert split_eojeol.status.value == "mismatch"
    assert split_eojeol.alternative_matches == (False, False)


def test_real_kiwi_noun_and_predicate_homographs_never_cross_match() -> None:
    api = _service_module()
    service = api.KiwiKoreanMorphologyService()
    noun = _target_identity(
        service,
        lemma="배우",
        part_of_speech="NNG",
        signature=(("배우", "NNG"),),
        sense_id="reviewed:actor:1",
    )
    predicate = _target_identity(
        service,
        lemma="배우다",
        part_of_speech="VV",
        signature=(("배우", "VV"),),
        sense_id="reviewed:learn:1",
    )

    assert service.match_target("그 배우가 연기해요", noun).matched is True
    assert service.match_target("저는 한국어를 배워요", predicate).matched is True
    assert service.match_target("그 배우가 연기해요", predicate).matched is False
    assert service.match_target("저는 한국어를 배워요", noun).matched is False


def test_real_kiwi_nfd_sentence_and_target_match_the_same_compound_signature() -> None:
    api = _service_module()
    service = api.KiwiKoreanMorphologyService()
    submitted_nfd = unicodedata.normalize("NFD", "공부하다")
    target = _target_identity(
        service,
        lemma="공부하다",
        part_of_speech="VV",
        signature=(("공부", "NNG"), ("하", "XSV")),
        sense_id="reviewed:study:1",
        submitted_form=submitted_nfd,
    )
    sentence = unicodedata.normalize("NFD", "매일 한국어를 공부해요")

    result = service.match_target(sentence, target)

    assert target.submitted_form == submitted_nfd
    assert result.status.value == "matched"
    assert result.alternative_matches == (True, True)


def test_real_kiwi_one_of_two_matching_analyses_is_ambiguous() -> None:
    api = _service_module()
    service = api.KiwiKoreanMorphologyService()
    target = _target_identity(
        service,
        lemma="걷다",
        part_of_speech="VV",
        signature=(("걷", "VV"),),
        sense_id="reviewed:walk:1",
    )

    result = service.match_target("걸어요", target)

    assert result.status.value == "ambiguous"
    assert result.matched is False
    assert sorted(result.alternative_matches) == [False, True]


def test_real_kiwi_oov_token_evidence_blocks_match() -> None:
    api = _service_module()
    kiwi = _real_kiwi()
    raw_alternatives = kiwi.analyze(_OOV_TEXT, **_ANALYZE_OPTIONS)
    assert all(
        any(
            token.form == "알리오올리오" and token.oov is True
            for token in tokens
        )
        and any(token.form == "집" and token.tag == "NNG" for token in tokens)
        for tokens, _score in raw_alternatives
    )
    service = api.KiwiKoreanMorphologyService(analyzer_factory=lambda: kiwi)
    target = _target_identity(
        service,
        lemma="집",
        part_of_speech="NNG",
        signature=(("집", "NNG"),),
        sense_id="reviewed:house:1",
    )

    result = service.match_target(_OOV_TEXT, target)

    assert result.status.value == "oov"
    assert result.reason_code.value == "oov_token"
    assert result.matched is False
    assert result.alternative_matches == ()


def test_fingerprint_mismatch_blocks_match_without_constructing_kiwi() -> None:
    api = _service_module()
    korean = import_module("multilang.domain.korean")
    construction_count = 0

    def counted_factory() -> object:
        nonlocal construction_count
        construction_count += 1
        return _real_kiwi()

    service = api.KiwiKoreanMorphologyService(analyzer_factory=counted_factory)
    fingerprint_values = service.fingerprint.model_dump()
    fingerprint_values["analyzer_package_version"] = "0.23.1"
    target = _target_identity(
        service,
        lemma="먹다",
        part_of_speech="VV",
        signature=(("먹", "VV"),),
        sense_id="reviewed:eat:1",
        fingerprint=korean.KoreanAnalyzerFingerprint(**fingerprint_values),
    )

    result = service.match_target("밥을 먹었어요", target)

    assert result.status.value == "fingerprint-mismatch"
    assert result.matched is False
    assert construction_count == 0


def test_missing_and_malformed_identity_never_reach_analysis() -> None:
    api = _service_module()
    construction_count = 0

    def counted_factory() -> object:
        nonlocal construction_count
        construction_count += 1
        return _real_kiwi()

    service = api.KiwiKoreanMorphologyService(analyzer_factory=counted_factory)
    valid_target = _target_identity(
        service,
        lemma="먹다",
        part_of_speech="VV",
        signature=(("먹", "VV"),),
        sense_id="reviewed:eat:1",
    )
    malformed_target = valid_target.model_copy(
        update={"morpheme_signature": ()}
    )

    missing = service.match_target("밥을 먹었어요", None)
    malformed = service.match_target("밥을 먹었어요", malformed_target)

    assert missing.status.value == "missing"
    assert malformed.status.value == "invalid"
    assert missing.matched is False
    assert malformed.matched is False
    assert construction_count == 0


def test_unavailable_analysis_never_falls_through_to_matching() -> None:
    api = _service_module()
    service = api.KiwiKoreanMorphologyService(
        analyzer_factory=lambda: _RuntimeFailureAnalyzer()
    )
    target = _target_identity(
        service,
        lemma="먹다",
        part_of_speech="VV",
        signature=(("먹", "VV"),),
        sense_id="reviewed:eat:1",
    )

    result = service.match_target("밥을 먹었어요", target)

    assert result.status.value == "unavailable"
    assert result.reason_code.value == "analyzer_runtime_error"
    assert result.matched is False
    assert "private" not in result.model_dump_json()


def test_real_kiwi_python312_smoke_projects_and_matches_compound_predicate() -> None:
    api = _service_module()
    service = api.KiwiKoreanMorphologyService()
    target = _target_identity(
        service,
        lemma="공부하다",
        part_of_speech="VV",
        signature=(("공부", "NNG"), ("하", "XSV")),
        sense_id="reviewed:study:1",
    )

    analysis = service.analyze("매일 한국어를 공부해요")
    match = service.match_target("매일 한국어를 공부해요", target)

    assert analysis.status.value == "resolved"
    assert all(
        any(
            _signature_pairs(word) == (("공부", "NNG"), ("하", "XSV"))
            for word in alternative.words
        )
        for alternative in analysis.alternatives
    )
    assert match.status.value == "matched"
    assert match.alternative_matches == (True, True)
