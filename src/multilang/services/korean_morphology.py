"""Lazy pinned Kiwi adapter with privacy-safe project-owned evidence."""

from __future__ import annotations

import math
import unicodedata
from collections import defaultdict
from collections.abc import Callable, Iterable
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as distribution_version
from threading import Lock
from typing import Final

from multilang.domain.korean import (
    KOREAN_LEXICAL_POS_TAGS,
    KOREAN_MORPHOLOGY_POLICY_VERSION,
    KoreanAnalysisAlternative,
    KoreanAnalyzerFingerprint,
    KoreanLexicalIdentity,
    KoreanMatchResult,
    KoreanMatchStatus,
    KoreanMorphemeEvidence,
    KoreanMorphologyResult,
    KoreanMorphologyStatus,
    KoreanReasonCode,
    KoreanSignatureItem,
    KoreanSurfaceSpan,
    KoreanTextError,
    KoreanWordAnalysis,
    canonicalize_korean,
)
from multilang.services.korean_pos import is_kiwi_punctuation

_ANALYZER_PACKAGE: Final = "kiwipiepy"
_MODEL_PACKAGE: Final = "kiwipiepy-model"
_EXPECTED_ANALYZER_VERSION: Final = "0.23.2"
_EXPECTED_MODEL_VERSION: Final = "0.23.0"
_PUNCTUATION_POS: Final = frozenset({"SF", "SP", "SS", "SSO", "SSC", "SE", "SO", "SW"})
_MAX_SURFACE_SPANS: Final = 16384

_ANALYSIS_OPTIONS: Final[dict[str, object]] = {
    "top_n": 2,
    "split_complex": False,
    "compatible_jamo": False,
    "normalize_coda": False,
    "z_coda": False,
    "typos": None,
    "oov_handling": "chr",
}

AnalyzerFactory = Callable[[], object]


class _ProjectionError(ValueError):
    """Internal content-free signal for malformed vendor output."""


def _installed_version(package: str, expected: str) -> str:
    try:
        return distribution_version(package)
    except PackageNotFoundError:
        return f"unavailable-{expected}"


def _default_analyzer_factory() -> object:
    from kiwipiepy import Kiwi

    return Kiwi(
        num_workers=1,
        model_type="cong",
        enabled_dialects="standard",
        integrate_allomorph=True,
    )


def _safe_base_pos(raw_pos: object) -> str:
    if not isinstance(raw_pos, str):
        raise _ProjectionError("malformed_pos")
    normalized = raw_pos.strip().upper()
    if not normalized or any(
        character not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
        for character in normalized
    ):
        raise _ProjectionError("malformed_pos")
    return normalized.partition("-")[0]


class KiwiKoreanMorphologyService:
    """Construct one exact-config Kiwi lazily and project all vendor results."""

    def __init__(self, *, analyzer_factory: AnalyzerFactory | None = None) -> None:
        self._analyzer_factory = analyzer_factory or _default_analyzer_factory
        self._analyzer: object | None = None
        self._initialization_attempted = False
        self._initialization_failure: tuple[KoreanReasonCode, str] | None = None
        self._initialization_lock = Lock()
        self._fingerprint = KoreanAnalyzerFingerprint(
            analyzer_name="kiwi",
            analyzer_package_version=_installed_version(
                _ANALYZER_PACKAGE,
                _EXPECTED_ANALYZER_VERSION,
            ),
            model_package_version=_installed_version(
                _MODEL_PACKAGE,
                _EXPECTED_MODEL_VERSION,
            ),
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
            policy_version=KOREAN_MORPHOLOGY_POLICY_VERSION,
        )

    @property
    def fingerprint(self) -> KoreanAnalyzerFingerprint:
        return self._fingerprint

    def analyze(self, text: str) -> KoreanMorphologyResult:
        try:
            canonical_text = canonicalize_korean(text)
        except KoreanTextError as exc:
            return self._non_passing_result(
                status=KoreanMorphologyStatus.INVALID,
                reason_code=KoreanReasonCode.INVALID_TEXT,
                exception_class=type(exc).__name__,
            )

        analyzer = self._get_analyzer()
        if analyzer is None:
            assert self._initialization_failure is not None
            reason_code, exception_class = self._initialization_failure
            return self._non_passing_result(
                status=KoreanMorphologyStatus.UNAVAILABLE,
                reason_code=reason_code,
                exception_class=exception_class,
            )

        try:
            analyze_method = getattr(analyzer, "analyze")
            raw_results = analyze_method(canonical_text, **_ANALYSIS_OPTIONS)
        except Exception as exc:
            return self._non_passing_result(
                status=KoreanMorphologyStatus.UNAVAILABLE,
                reason_code=KoreanReasonCode.ANALYZER_RUNTIME_ERROR,
                exception_class=type(exc).__name__,
            )

        if isinstance(raw_results, (list, tuple)) and not raw_results:
            return self._non_passing_result(
                status=KoreanMorphologyStatus.UNAVAILABLE,
                reason_code=KoreanReasonCode.EMPTY_ANALYSIS,
            )

        try:
            alternatives = _project_alternatives(
                raw_results,
                canonical_text=canonical_text,
                expected_count=self.fingerprint.top_n,
            )
        except _ProjectionError:
            return self._non_passing_result(
                status=KoreanMorphologyStatus.UNAVAILABLE,
                reason_code=KoreanReasonCode.MALFORMED_ANALYSIS,
            )

        if any(alternative.has_oov for alternative in alternatives):
            return KoreanMorphologyResult(
                status=KoreanMorphologyStatus.OOV,
                analyzer_fingerprint=self.fingerprint,
                alternatives=alternatives,
                reason_code=KoreanReasonCode.OOV_TOKEN,
            )
        return KoreanMorphologyResult(
            status=KoreanMorphologyStatus.RESOLVED,
            analyzer_fingerprint=self.fingerprint,
            alternatives=alternatives,
            reason_code=KoreanReasonCode.ANALYSIS_RESOLVED,
        )

    def match_target(
        self,
        sentence_text: str,
        target: KoreanLexicalIdentity | None,
    ) -> KoreanMatchResult:
        validated_target = _validated_target(target)
        if validated_target is None:
            status = (
                KoreanMatchStatus.MISSING
                if target is None or not isinstance(target, KoreanLexicalIdentity)
                else KoreanMatchStatus.INVALID
            )
            reason_code = (
                KoreanReasonCode.MISSING_IDENTITY
                if status is KoreanMatchStatus.MISSING
                else KoreanReasonCode.INVALID_SIGNATURE
            )
            return self._match_result(status=status, reason_code=reason_code)

        if validated_target.analyzer_fingerprint != self.fingerprint:
            return self._match_result(
                status=KoreanMatchStatus.FINGERPRINT_MISMATCH,
                reason_code=KoreanReasonCode.FINGERPRINT_MISMATCH,
            )

        analysis = self.analyze(sentence_text)
        if analysis.status is KoreanMorphologyStatus.OOV:
            return self._match_result(
                status=KoreanMatchStatus.OOV,
                reason_code=KoreanReasonCode.OOV_TOKEN,
            )
        if analysis.status is KoreanMorphologyStatus.UNAVAILABLE:
            return self._match_result(
                status=KoreanMatchStatus.UNAVAILABLE,
                reason_code=analysis.reason_code,
            )
        if analysis.status is KoreanMorphologyStatus.INVALID:
            return self._match_result(
                status=KoreanMatchStatus.INVALID,
                reason_code=analysis.reason_code,
            )
        if analysis.status is KoreanMorphologyStatus.AMBIGUOUS:
            return self._match_result(
                status=KoreanMatchStatus.AMBIGUOUS,
                reason_code=KoreanReasonCode.ANALYSIS_DISAGREEMENT,
            )

        target_signature = validated_target.morpheme_signature
        decisions = tuple(
            any(
                word.lexical_signature == target_signature
                for word in alternative.words
            )
            for alternative in analysis.alternatives
        )
        if decisions == (True, True):
            return self._match_result(
                status=KoreanMatchStatus.MATCHED,
                reason_code=KoreanReasonCode.CONSENSUS_MATCH,
                alternative_matches=decisions,
            )
        if any(decisions):
            return self._match_result(
                status=KoreanMatchStatus.AMBIGUOUS,
                reason_code=KoreanReasonCode.ANALYSIS_DISAGREEMENT,
                alternative_matches=decisions,
            )
        return self._match_result(
            status=KoreanMatchStatus.MISMATCH,
            reason_code=KoreanReasonCode.NO_SIGNATURE_MATCH,
            alternative_matches=decisions,
        )

    def _get_analyzer(self) -> object | None:
        if self._initialization_attempted:
            return self._analyzer
        with self._initialization_lock:
            if self._initialization_attempted:
                return self._analyzer
            try:
                self._analyzer = self._analyzer_factory()
                if not callable(getattr(self._analyzer, "analyze", None)):
                    raise TypeError("analyzer_contract")
            except ImportError as exc:
                self._initialization_failure = (
                    KoreanReasonCode.ANALYZER_IMPORT_ERROR,
                    type(exc).__name__,
                )
            except Exception as exc:
                self._initialization_failure = (
                    KoreanReasonCode.ANALYZER_CONSTRUCTION_ERROR,
                    type(exc).__name__,
                )
            finally:
                self._initialization_attempted = True
        return self._analyzer

    def _non_passing_result(
        self,
        *,
        status: KoreanMorphologyStatus,
        reason_code: KoreanReasonCode,
        exception_class: str | None = None,
    ) -> KoreanMorphologyResult:
        return KoreanMorphologyResult(
            status=status,
            analyzer_fingerprint=self.fingerprint,
            alternatives=(),
            reason_code=reason_code,
            exception_class=exception_class,
        )

    def _match_result(
        self,
        *,
        status: KoreanMatchStatus,
        reason_code: KoreanReasonCode,
        alternative_matches: tuple[bool, ...] = (),
    ) -> KoreanMatchResult:
        return KoreanMatchResult(
            status=status,
            reason_code=reason_code,
            analyzer_fingerprint=self.fingerprint,
            alternative_matches=alternative_matches,
        )


def _validated_target(
    target: KoreanLexicalIdentity | None,
) -> KoreanLexicalIdentity | None:
    if not isinstance(target, KoreanLexicalIdentity):
        return None
    try:
        return KoreanLexicalIdentity.model_validate(target.model_dump(mode="python"))
    except ValueError:
        return None


def _project_alternatives(
    raw_results: object,
    *,
    canonical_text: str,
    expected_count: int,
) -> tuple[KoreanAnalysisAlternative, ...]:
    if not isinstance(raw_results, (list, tuple)) or len(raw_results) != expected_count:
        raise _ProjectionError("malformed_alternative_count")

    alternatives: list[KoreanAnalysisAlternative] = []
    for rank, raw_alternative in enumerate(raw_results, start=1):
        if not isinstance(raw_alternative, (list, tuple)) or len(raw_alternative) != 2:
            raise _ProjectionError("malformed_alternative")
        raw_tokens, raw_score = raw_alternative
        if isinstance(raw_score, bool) or not isinstance(raw_score, (int, float)):
            raise _ProjectionError("malformed_score")
        score = float(raw_score)
        if not math.isfinite(score):
            raise _ProjectionError("malformed_score")
        if not isinstance(raw_tokens, Iterable) or isinstance(raw_tokens, (str, bytes)):
            raise _ProjectionError("malformed_tokens")
        tokens = tuple(raw_tokens)
        if not tokens:
            raise _ProjectionError("empty_tokens")
        alternatives.append(
            _project_alternative(
                tokens,
                score=score,
                rank=rank,
                canonical_text=canonical_text,
            )
        )
    return tuple(alternatives)


def _project_alternative(
    tokens: tuple[object, ...],
    *,
    score: float,
    rank: int,
    canonical_text: str,
) -> KoreanAnalysisAlternative:
    groups: dict[tuple[int, int], list[tuple[KoreanMorphemeEvidence, int, int]]] = defaultdict(list)

    for token in tokens:
        form = getattr(token, "form", None)
        lemma = getattr(token, "lemma", None)
        raw_pos = getattr(token, "tag", None)
        word_position = getattr(token, "word_position", None)
        sentence_position = getattr(token, "sent_position", None)
        oov = getattr(token, "oov", None)
        start = getattr(token, "start", None)
        length = getattr(token, "len", None)
        if (
            not isinstance(form, str)
            or not isinstance(lemma, str)
            or type(word_position) is not int
            or word_position < 0
            or type(sentence_position) is not int
            or sentence_position < 0
            or not isinstance(oov, bool)
            or type(start) is not int
            or type(length) is not int
            or start < 0
            or length < 0
            or start + length > len(canonical_text)
        ):
            raise _ProjectionError("malformed_token")
        normalized_raw_pos = str(raw_pos).strip().upper()
        base_pos = _safe_base_pos(normalized_raw_pos)
        try:
            evidence = KoreanMorphemeEvidence(
                form=canonicalize_korean(form),
                lemma=canonicalize_korean(lemma),
                pos=base_pos,
                raw_pos=normalized_raw_pos,
                oov=oov,
            )
        except (KoreanTextError, ValueError) as exc:
            raise _ProjectionError("malformed_token") from exc
        groups[(sentence_position, word_position)].append((evidence, start, start + length))

    words: list[KoreanWordAnalysis] = []
    surface_spans: list[KoreanSurfaceSpan] = []
    bounded_groups = sorted(
        ((*_source_bounds(group), key, group) for key, group in groups.items()),
        key=lambda item: item[0],
    )
    previous_end = 0
    for word_position, (surface_start, surface_end, _key, group) in enumerate(bounded_groups):
        remaining_spans = _MAX_SURFACE_SPANS - len(surface_spans)
        if remaining_spans <= 0:
            raise _ProjectionError("surface_span_limit")
        if surface_start < previous_end:
            raise _ProjectionError("overlapping_word_groups")
        previous_end = surface_end
        morphemes = tuple(item for item, _start, _end in group)
        surface_spans.extend(
            _project_surface_spans(
                group,
                word_position=word_position,
                canonical_text=canonical_text,
                max_spans=remaining_spans,
            )
        )
        signature = tuple(
            KoreanSignatureItem(form=item.form, pos=item.pos)
            for item in morphemes
            if item.pos in KOREAN_LEXICAL_POS_TAGS
        )
        if not signature:
            continue
        try:
            words.append(
                KoreanWordAnalysis(
                    surface_form=canonical_text[surface_start:surface_end],
                    word_position=word_position,
                    morphemes=morphemes,
                    lexical_signature=signature,
                )
            )
        except ValueError as exc:
            raise _ProjectionError("malformed_word") from exc

    if not words:
        raise _ProjectionError("missing_lexical_words")
    observed_oov = any(bool(getattr(token, "oov", False)) for token in tokens)
    projected_oov = any(
        morpheme.oov
        for word in surface_spans
        for morpheme in word.morphemes
    )
    if observed_oov != projected_oov:
        raise _ProjectionError("unprojected_oov")
    try:
        return KoreanAnalysisAlternative(
            rank=rank,
            score=score,
            words=tuple(words),
            has_oov=projected_oov,
            surface_spans=tuple(surface_spans),
        )
    except ValueError as exc:
        raise _ProjectionError("malformed_alternative") from exc


def _source_bounds(
    group: list[tuple[KoreanMorphemeEvidence, int, int]],
) -> tuple[int, int]:
    """Allow overlapping/zero-width morphology, never an invented source range."""
    positive = sorted((start, end) for _item, start, end in group if start < end)
    if not positive:
        raise _ProjectionError("empty_source_group")
    lower, upper = positive[0]
    for start, end in positive[1:]:
        if start > upper:
            raise _ProjectionError("uncovered_group_source")
        upper = max(upper, end)
    if any(not lower <= start <= upper for _item, start, end in group if start == end):
        raise _ProjectionError("unanchored_zero_width_morpheme")
    return lower, upper


def _project_surface_spans(
    group: list[tuple[KoreanMorphemeEvidence, int, int]],
    *,
    word_position: int,
    canonical_text: str,
    max_spans: int = _MAX_SURFACE_SPANS,
) -> tuple[KoreanSurfaceSpan, ...]:
    """Separate only exact, non-overlapping vendor punctuation boundaries."""
    # Kiwi's lexical spans may overlap or arrive out of source order. A single
    # ordered sweep finds overlaps without rescanning the group per punctuation.
    positive = sorted(
        (start, end, index)
        for index, (_item, start, end) in enumerate(group)
        if start < end
    )
    overlapping: set[int] = set()
    previous_end = 0
    for position, (start, end, index) in enumerate(positive):
        if start < previous_end or (
            position + 1 < len(positive) and positive[position + 1][0] < end
        ):
            overlapping.add(index)
        previous_end = max(previous_end, end)
    spans: list[KoreanSurfaceSpan] = []
    run: list[tuple[KoreanMorphemeEvidence, int, int]] = []

    def retain(items: list[tuple[KoreanMorphemeEvidence, int, int]]) -> None:
        if not items:
            return
        if len(spans) >= max_spans:
            raise _ProjectionError("surface_span_limit")
        start, end = _source_bounds(items)
        try:
            spans.append(
                KoreanSurfaceSpan(
                    surface_form=canonical_text[start:end],
                    start=start,
                    end=end,
                    word_position=word_position,
                    morphemes=tuple(item for item, _start, _end in items),
                )
            )
        except ValueError as exc:
            raise _ProjectionError("malformed_surface_span") from exc

    for index, (item, start, end) in enumerate(group):
        punctuation = False
        if item.pos in _PUNCTUATION_POS:
            source = canonical_text[start:end]
            if not source or source != item.form:
                raise _ProjectionError("unproven_punctuation_span")
            punctuation = is_kiwi_punctuation(item.pos, source)
            if not punctuation and item.pos != "SW" and any(
                not unicodedata.category(character).startswith("S") for character in source
            ):
                raise _ProjectionError("unproven_punctuation_category")
        if punctuation:
            if index in overlapping:
                raise _ProjectionError("overlapping_punctuation_span")
            retain(run)
            run = []
            retain([(item, start, end)])
        else:
            run.append((item, start, end))
    retain(run)
    return tuple(spans)


__all__ = ["KiwiKoreanMorphologyService"]
