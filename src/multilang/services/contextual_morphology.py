"""Local contextual morphology and an explicit, reviewed sense-binding gate.

Models supply morphology only. They cannot mint lexical identities or senses.
Offsets address the unchanged NFC input in Unicode characters, never bytes.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from collections.abc import Mapping
from pathlib import Path
from threading import RLock
from types import MappingProxyType
from typing import Literal, Protocol

from pydantic import Field, model_validator

from multilang.domain.content import ContentRequest, FrozenContentModel, TargetMatchEvidence
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.japanese_pos import unidic_to_upos
from multilang.services.korean_pos import is_kiwi_punctuation, kiwi_to_upos
from multilang.services.language_models import load_stanza_pipeline, model_spec, model_status

_UPOS = frozenset(
    "ADJ ADP ADV AUX CCONJ DET INTJ NOUN NUM PART PRON PROPN PUNCT SCONJ SYM VERB X".split()
)
_ANALYZER_VERSION = "contextual-morphology-4"
_MAX_TOKENS = 16384


def sentence_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def contextual_model_fingerprint(status: Mapping[str, object]) -> str:
    """Bind model metadata to the current interpretation of its predictions."""
    return canonical_sha256({**status, "policy": _ANALYZER_VERSION})


def _text(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > 64000
        or not unicodedata.is_normalized("NFC", value)
        or any(
            unicodedata.category(c) in {"Cs", "Co", "Cn", "Cf"}
            or (unicodedata.category(c) == "Cc" and c not in "\n\r\t")
            for c in value
        )
    ):
        raise ValueError("invalid Unicode or non-NFC text")
    return value


class ContextualToken(FrozenContentModel):
    text: str = Field(min_length=1, max_length=64000)
    lemma: str = Field(min_length=1, max_length=4096)
    pos: str = Field(min_length=1, max_length=128)
    features: tuple[tuple[str, str], ...] = ()
    start: int = Field(ge=0, strict=True)
    end: int = Field(gt=0, strict=True)
    sentence_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    model_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def valid_morphology(self):
        for value in (self.text, self.lemma, self.pos):
            _text(value)
        if self.end <= self.start or self.end - self.start != len(self.text):
            raise ValueError("invalid token span")
        if self.pos not in _UPOS:
            raise ValueError("unsupported universal POS")
        if len({key for key, _ in self.features}) != len(self.features):
            raise ValueError("duplicate morphology feature")
        for key, value in self.features:
            _text(key)
            _text(value)
        return self

    @property
    def analysis_id(self) -> str:
        return canonical_sha256(self.model_dump(mode="json"))


class ContextualConstituent(FrozenContentModel):
    """Vendor evidence inside a blocked surface, without invented child spans."""

    text: str = Field(min_length=1, max_length=4096)
    lemma: str | None = Field(default=None, min_length=1, max_length=4096)
    pos: str | None = Field(default=None, min_length=1, max_length=128)
    features: tuple[tuple[str, str], ...] = Field(default=(), max_length=128)

    @model_validator(mode="after")
    def valid_evidence(self):
        for value in (self.text, self.lemma, self.pos):
            if value is not None:
                _text(value)
        if len({key for key, _ in self.features}) != len(self.features):
            raise ValueError("duplicate constituent feature")
        for key, value in self.features:
            _text(key)
            _text(value)
        return self


class ContextualBlockedSpan(FrozenContentModel):
    text: str = Field(min_length=1, max_length=64000)
    start: int = Field(ge=0, strict=True)
    end: int = Field(gt=0, strict=True)
    sentence_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    model_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    reason: Literal[
        "unaligned_multiword_expansion",
        "unresolved_morphology",
        "unknown_lexical_token",
        "compound_lexical_projection",
        "missing_vendor_span",
    ]
    constituents: tuple[ContextualConstituent, ...] = Field(default=(), max_length=128)

    @model_validator(mode="after")
    def valid_surface(self):
        _text(self.text)
        if self.end <= self.start or self.end - self.start != len(self.text):
            raise ValueError("invalid blocked surface span")
        return self


class ContextualAnalysis(FrozenContentModel):
    language: str
    status: Literal["complete", "inconclusive", "invalid", "unavailable", "unsupported"]
    sentence_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    model_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    tokens: tuple[ContextualToken, ...] = Field(default=(), max_length=_MAX_TOKENS)
    blocked_spans: tuple[ContextualBlockedSpan, ...] = Field(default=(), max_length=_MAX_TOKENS)
    reason: str
    analyzer_version: str = "contextual-morphology-1"

    @model_validator(mode="after")
    def valid_tokens(self):
        if self.status == "complete" and (not self.tokens or self.blocked_spans):
            raise ValueError("complete analysis requires tokens without blockers")
        if len(self.tokens) + len(self.blocked_spans) > _MAX_TOKENS:
            raise ValueError("contextual span limit")
        previous = 0
        for group in (self.tokens, self.blocked_spans):
            if any(a.start >= b.start for a, b in zip(group, group[1:])):
                raise ValueError("contextual spans must be ordered")
        for token in sorted((*self.tokens, *self.blocked_spans), key=lambda row: row.start):
            if (
                token.start < previous
                or token.sentence_sha256 != self.sentence_sha256
                or token.model_fingerprint != self.model_fingerprint
            ):
                raise ValueError("inconsistent contextual token")
            previous = token.end
        return self


class ContextualAnalyzer(Protocol):
    def analyze(self, language: str, text: str) -> ContextualAnalysis: ...


def _features(value: object) -> tuple[tuple[str, str], ...]:
    if value in (None, "_", ""):
        return ()
    if not isinstance(value, str):
        raise ValueError("malformed features")
    fields = tuple(tuple(item.split("=", 1)) for item in value.split("|"))
    if any(len(field) != 2 or not all(field) for field in fields):
        raise ValueError("malformed features")
    return tuple(sorted(fields))


def _complete_features(language, surface, pos, features):
    # Russian UD defines NumForm=Digit for numerals written with digits.
    # This source property needs no inferred lemma, case, gender or sense.
    # https://universaldependencies.org/ru/feat/NumForm.html
    if (
        language == "ru"
        and pos in {"NUM", "ADJ"}
        and surface.isdecimal()
        and not any(key == "NumForm" for key, _ in features)
    ):
        return tuple(sorted((*features, ("NumForm", "Digit"))))
    return features


def _exact_span(text, start, end, surface):
    if (
        type(start) is not int
        or type(end) is not int
        or not isinstance(surface, str)
        or not surface
        or start < 0
        or end <= start
        or end > len(text)
        or text[start:end] != surface
    ):
        raise ValueError("unproven vendor surface span")


def _resolved_row(row):
    """Validate morphology before retaining a row as usable lexical evidence."""
    ContextualToken(**row, sentence_sha256="0" * 64, model_fingerprint="0" * 64)
    return row["pos"] != "X"


def _blocked(surface, start, end, reason, constituents=()):
    return dict(text=surface, start=start, end=end, reason=reason, constituents=constituents)


class LocalContextualMorphologyService:
    """Serialize vendor calls, verify local models, and never implicitly download.

    Non-NFC input is rejected instead of silently changing source offsets. The
    caller may explicitly normalize a source before creating its source hash.
    """

    def __init__(
        self,
        *,
        model_root: Path,
        model_profiles: Mapping[str, str] | None = None,
        threads: int = 1,
    ) -> None:
        if type(threads) is not int or not 1 <= threads <= 8:
            raise ValueError("CPU model threads must be between 1 and 8")
        profiles = dict(model_profiles or {})
        if len(profiles) > 22:
            raise ValueError("too many language model profiles")
        for language, profile in profiles.items():
            spec = model_spec(language)
            if profile not in ("fast", "balanced", "accurate"):
                raise ValueError("unsupported language model profile")
            if spec.backend != "stanza" and profile != "fast":
                raise ValueError("native analyzer only supports the fast profile")
        self.model_root = Path(model_root)
        self.model_profiles = MappingProxyType(profiles)
        self.threads = threads
        self._pipelines: dict[tuple[str, str], object] = {}
        self._lock = RLock()

    def analyze(self, language: str, text: str) -> ContextualAnalysis:
        empty = "0" * 64
        try:
            _text(text)
        except ValueError:
            return ContextualAnalysis(
                language=str(language),
                status="invalid",
                sentence_sha256=empty,
                model_fingerprint=empty,
                reason="invalid_unicode_or_non_nfc",
                analyzer_version=_ANALYZER_VERSION,
            )
        source = sentence_hash(text)
        try:
            spec = model_spec(language)
        except ValueError:
            return ContextualAnalysis(
                language=str(language),
                status="unsupported",
                sentence_sha256=source,
                model_fingerprint=empty,
                reason="unsupported_language",
                analyzer_version=_ANALYZER_VERSION,
            )
        fingerprint = empty
        with self._lock:
            try:
                selected = self.model_profiles.get(language, "fast")
                profile_kwargs = {"profile": selected} if selected != "fast" else {}
                status = model_status(language, self.model_root, **profile_kwargs)
                if not status.get("available"):
                    raise RuntimeError("model unavailable")
                fingerprint = contextual_model_fingerprint(status)
                key = (language, fingerprint)
                if key not in self._pipelines:
                    if spec.backend == "stanza":
                        pipeline = load_stanza_pipeline(
                            language,
                            self.model_root,
                            **profile_kwargs,
                            **({"threads": self.threads} if self.threads != 1 else {}),
                        )
                    elif spec.backend == "kiwi":
                        from multilang.services.korean_morphology import KiwiKoreanMorphologyService

                        pipeline = KiwiKoreanMorphologyService()
                    else:
                        from multilang.services.japanese_analysis import japanese_tagger

                        pipeline = japanese_tagger()
                    self._pipelines[key] = pipeline
                pipeline = self._pipelines[key]
            except Exception:
                return ContextualAnalysis(
                    language=language,
                    status="unavailable",
                    sentence_sha256=source,
                    model_fingerprint=fingerprint,
                    reason="model_missing_or_drifted",
                    analyzer_version=_ANALYZER_VERSION,
                )
            try:
                if spec.backend == "stanza":
                    rows, blocked, complete = self._stanza(pipeline, text, language=language)
                elif spec.backend == "kiwi":
                    rows, blocked, complete = self._kiwi(pipeline, text)
                else:
                    rows, blocked, complete = self._fugashi(pipeline, text)
                tokens = tuple(
                    ContextualToken(**row, sentence_sha256=source, model_fingerprint=fingerprint)
                    for row in rows
                )
                blockers = [
                    ContextualBlockedSpan(
                        **row, sentence_sha256=source, model_fingerprint=fingerprint
                    )
                    for row in blocked
                ]

                def retain_gap(start, end):
                    # This is the exact unobserved source interval, not an
                    # inferred token, lemma, sense, or morphological constituent.
                    while start < end and text[start].isspace():
                        start += 1
                    while end > start and text[end - 1].isspace():
                        end -= 1
                    if start < end:
                        blockers.append(
                            ContextualBlockedSpan(
                                text=text[start:end],
                                start=start,
                                end=end,
                                reason="missing_vendor_span",
                                sentence_sha256=source,
                                model_fingerprint=fingerprint,
                            )
                        )

                previous = 0
                for token in sorted((*tokens, *blockers), key=lambda row: row.start):
                    if token.start < previous or text[token.start : token.end] != token.text:
                        raise ValueError("inexact or missing source span")
                    retain_gap(previous, token.start)
                    previous = token.end
                retain_gap(previous, len(text))
                if not tokens or blockers or any(t.pos == "X" for t in tokens):
                    complete = False
                return ContextualAnalysis(
                    language=language,
                    status="complete" if complete else "inconclusive",
                    tokens=tokens,
                    blocked_spans=tuple(sorted(blockers, key=lambda row: row.start)),
                    sentence_sha256=source,
                    model_fingerprint=fingerprint,
                    reason=(
                        "morphology_only"
                        if complete
                        else "blocked_source_spans"
                        if blockers
                        else "ambiguous_or_incomplete_analysis"
                    ),
                    analyzer_version=_ANALYZER_VERSION,
                )
            except Exception:
                return ContextualAnalysis(
                    language=language,
                    status="inconclusive",
                    sentence_sha256=source,
                    model_fingerprint=fingerprint,
                    reason="malformed_or_unaligned_analysis",
                    analyzer_version=_ANALYZER_VERSION,
                )

    @staticmethod
    def _stanza(pipeline, text, *, language=None):
        document = pipeline(text)
        rows, blocked, total_words = [], [], 0
        for sentence in document.sentences:
            for token in sentence.tokens:
                _exact_span(text, token.start_char, token.end_char, token.text)
                if not 1 <= len(token.words) <= 128:
                    raise ValueError("invalid constituent count")
                total_words += len(token.words)
                if total_words > _MAX_TOKENS:
                    raise ValueError("token limit")
                constituents = tuple(
                    ContextualConstituent(
                        text=word.text,
                        lemma=word.lemma,
                        pos=word.upos,
                        features=_features(word.feats),
                    )
                    for word in token.words
                )
                candidate_rows, cursor, aligned = [], token.start_char, True
                for word in token.words:
                    start = (
                        token.start_char
                        if len(token.words) == 1
                        else getattr(word, "start_char", None)
                    )
                    end = (
                        token.end_char if len(token.words) == 1 else getattr(word, "end_char", None)
                    )
                    try:
                        _exact_span(text, start, end, word.text)
                        if start != cursor or end > token.end_char:
                            raise ValueError("non-partitioning child span")
                    except ValueError:
                        aligned = False
                        break
                    cursor = end
                    candidate_rows.append(
                        dict(
                            text=word.text,
                            lemma=word.lemma,
                            pos=word.upos,
                            features=_complete_features(
                                language, word.text, word.upos, _features(word.feats)
                            ),
                            start=start,
                            end=end,
                        )
                    )
                if not aligned or cursor != token.end_char:
                    blocked.append(
                        _blocked(
                            token.text,
                            token.start_char,
                            token.end_char,
                            "unaligned_multiword_expansion"
                            if len(token.words) > 1
                            else "unresolved_morphology",
                            constituents,
                        )
                    )
                    continue
                try:
                    resolved = all(_resolved_row(row) for row in candidate_rows)
                except ValueError:
                    resolved = False
                if resolved:
                    rows.extend(candidate_rows)
                else:
                    blocked.append(
                        _blocked(
                            token.text,
                            token.start_char,
                            token.end_char,
                            "unresolved_morphology",
                            constituents,
                        )
                    )
        return rows, blocked, not blocked

    @staticmethod
    def _fugashi(pipeline, text):
        rows, blocked, position = [], [], 0
        for token in pipeline(text):
            whitespace = token.white_space
            if not isinstance(whitespace, str) or whitespace.strip():
                raise ValueError("invalid vendor whitespace")
            if text[position : position + len(whitespace)] != whitespace:
                raise ValueError("inexact vendor whitespace")
            position += len(whitespace)
            _exact_span(text, position, position + len(token.surface), token.surface)
            feature = token.feature
            pos = unidic_to_upos(feature.pos1, feature.pos2, feature.lemma)
            features = tuple(
                (name, getattr(feature, name))
                for name in feature._fields
                if getattr(feature, name) not in (None, "", "*")
            )
            punctuation = feature.pos1 in {"記号", "補助記号"} and all(
                unicodedata.category(c).startswith("P") for c in token.surface
            )
            # A dictionary's missing punctuation lemma does not make a lexical
            # guess necessary. Lexical unknowns never use this narrow exception.
            row = dict(
                text=token.surface,
                lemma=token.surface if punctuation else feature.lemma,
                pos="PUNCT" if punctuation else pos,
                features=features,
                start=position,
                end=position + len(token.surface),
            )
            try:
                resolved = _resolved_row(row) and (not token.is_unk or punctuation)
            except ValueError:
                resolved = False
            if resolved:
                rows.append(row)
            else:
                blocked.append(
                    _blocked(
                        token.surface,
                        position,
                        position + len(token.surface),
                        "unknown_lexical_token" if token.is_unk else "unresolved_morphology",
                        (
                            ContextualConstituent(
                                text=token.surface,
                                lemma=feature.lemma,
                                pos=feature.pos1,
                                features=features,
                            ),
                        ),
                    )
                )
            position += len(token.surface)
            if len(rows) + len(blocked) > _MAX_TOKENS:
                raise ValueError("token limit")
        return rows, blocked, not blocked

    @staticmethod
    def _kiwi(pipeline, text):
        from multilang.domain.korean import KOREAN_LEXICAL_POS_TAGS, KoreanMorphologyStatus

        result = pipeline.analyze(text)
        if not result.passing and result.status != KoreanMorphologyStatus.OOV:
            raise ValueError("Kiwi unavailable or incomplete")
        alternatives = result.alternatives
        if not alternatives or any(not getattr(item, "surface_spans", ()) for item in alternatives):
            raise ValueError("Kiwi analysis requires proven surface spans")
        complete = result.passing and all(
            item.surface_spans == alternatives[0].surface_spans for item in alternatives[1:]
        )
        unknown_spans = []
        for alternative in alternatives:
            if len(alternative.surface_spans) > _MAX_TOKENS:
                raise ValueError("token limit")
            for span in alternative.surface_spans:
                if not 1 <= len(span.morphemes) <= 128:
                    raise ValueError("invalid constituent count")
                if any(m.oov for m in span.morphemes):
                    _exact_span(text, span.start, span.end, span.surface_form)
                    unknown_spans.append((span.start, span.end))
        unknown_spans.sort()
        unknown_index = 0
        rows, blocked = [], []
        for word in alternatives[0].surface_spans:
            # Check before both branches: compound groups continue early and
            # must not allocate unbounded constituent/blocker projections.
            if len(rows) + len(blocked) >= _MAX_TOKENS:
                raise ValueError("token limit")
            if not 1 <= len(word.morphemes) <= 128:
                raise ValueError("invalid constituent count")
            _exact_span(text, word.start, word.end, word.surface_form)
            constituents = tuple(
                ContextualConstituent(text=m.form, lemma=m.lemma, pos=m.raw_pos)
                for m in word.morphemes
            )
            lexical = [item for item in word.morphemes if item.pos in KOREAN_LEXICAL_POS_TAGS]
            punctuation = len(word.morphemes) == 1 and (
                word.morphemes[0].form == word.surface_form
                and is_kiwi_punctuation(word.morphemes[0].pos, word.surface_form)
            )
            # A standalone number/postposition can use its exact native lemma.
            # This does not add a lexical head or collapse a multi-morpheme group.
            singleton = (
                word.morphemes[0]
                if len(word.morphemes) == 1
                and word.morphemes[0].form == word.surface_form
                and kiwi_to_upos(word.morphemes[0].pos) != "X"
                else None
            )
            resolved = lexical[0] if len(lexical) == 1 else singleton
            # Top-2 OOV evidence must not disappear when rank 1 recognizes the
            # same source. Retain the proven rank-1 span as a blocked parent.
            while (
                unknown_index < len(unknown_spans) and unknown_spans[unknown_index][1] <= word.start
            ):
                unknown_index += 1
            oov = unknown_index < len(unknown_spans) and unknown_spans[unknown_index][0] < word.end
            if oov or (resolved is None and not punctuation):
                blocked.append(
                    _blocked(
                        word.surface_form,
                        word.start,
                        word.end,
                        "unknown_lexical_token"
                        if oov
                        else (
                            "compound_lexical_projection" if lexical else "unresolved_morphology"
                        ),
                        constituents,
                    )
                )
                continue
            row = dict(
                text=word.surface_form,
                lemma=word.surface_form if punctuation else resolved.lemma,
                pos="PUNCT" if punctuation else kiwi_to_upos(resolved.pos),
                features=(
                    (
                        "Morphemes",
                        json.dumps(
                            [m.model_dump(mode="json") for m in word.morphemes],
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        ),
                    ),
                ),
                start=word.start,
                end=word.end,
            )
            if _resolved_row(row):
                rows.append(row)
            else:
                blocked.append(
                    _blocked(
                        word.surface_form,
                        word.start,
                        word.end,
                        "unresolved_morphology",
                        constituents,
                    )
                )
            if len(rows) + len(blocked) > _MAX_TOKENS:
                raise ValueError("token limit")
        return rows, blocked, complete and not blocked


class ReviewedSenseBinding(FrozenContentModel):
    """Trusted caller supplies persisted source/review evidence, never model guesses.

    Receipt authenticity and reviewer authorization belong to the repository's
    review store. This value binds that evidence to one exact contextual token.
    """

    language: str = Field(min_length=2, max_length=8)
    sentence_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    start: int = Field(ge=0, strict=True)
    end: int = Field(gt=0, strict=True)
    token_analysis_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    lexical_identity_id: str = Field(min_length=1, max_length=255)
    sense_id: str = Field(min_length=1, max_length=255)
    morphological_analysis_id: str | None = Field(default=None, min_length=1, max_length=255)
    concept_id: str = Field(min_length=1, max_length=255)
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reviewer: str = Field(min_length=1, max_length=255)
    review_receipt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def valid_review(self):
        if self.end <= self.start or not self.reviewer.strip():
            raise ValueError("invalid reviewed binding")
        return self


class ContextualTargetMatcher:
    """Callable NativeContentService matcher; complete reviewed context required."""

    def __init__(self, *, analyzer: ContextualAnalyzer, bindings: tuple[ReviewedSenseBinding, ...]):
        self.analyzer = analyzer
        self.bindings = tuple(ReviewedSenseBinding.model_validate(b.model_dump()) for b in bindings)

    def __call__(self, request: ContentRequest, sentence: str) -> TargetMatchEvidence:
        request = ContentRequest.model_validate(request.model_dump())
        result = self.analyzer.analyze(request.language, sentence)
        result = ContextualAnalysis.model_validate(result.model_dump())
        observed, targets, used = [], [], []
        complete = result.status == "complete" and result.language == request.language
        if complete:
            complete = result.sentence_sha256 == sentence_hash(sentence)
            previous = 0
            for token in result.tokens:
                if (
                    token.start < previous
                    or token.end > len(sentence)
                    or sentence[previous : token.start].strip()
                    or sentence[token.start : token.end] != token.text
                    or token.pos == "X"
                ):
                    complete = False
                    break
                previous = token.end
            if sentence[previous:].strip():
                complete = False
        for token in result.tokens if complete else ():
            if sentence[token.start : token.end] != token.text:
                complete = False
                break
            if token.pos in {"PUNCT", "SYM"}:
                continue
            if request.language == "ko" and request.i_plus_one_mode == "strict":
                # A grouped lexical binding cannot attest separately to its
                # particle/ending concepts. Keep the existing Korean authority
                # for that curriculum until a constituent-complete binding exists.
                try:
                    morphemes = json.loads(dict(token.features).get("Morphemes", "[]"))
                except (TypeError, ValueError):
                    morphemes = None
                if not isinstance(morphemes, list) or len(morphemes) != 1:
                    complete = False
                    break
            matches = [
                b
                for b in self.bindings
                if b.language == request.language
                and b.sentence_sha256 == result.sentence_sha256
                and b.start == token.start
                and b.end == token.end
                and b.token_analysis_id == token.analysis_id
            ]
            if len(matches) != 1:
                complete = False
                break
            binding = matches[0]
            observed.append(binding.concept_id)
            used.append(binding.model_dump(mode="json"))
            if (
                binding.lexical_identity_id == request.lexical_identity_id
                and binding.sense_id == request.sense_id
                and binding.morphological_analysis_id == request.morphological_analysis_id
                and binding.concept_id == request.target_concept_id
                and token.text == request.display_text
                and token.lemma == request.lemma
            ):
                targets.append((token.start, token.end))
        matched = complete and len(targets) == 1
        return TargetMatchEvidence(
            lexical_identity_id=request.lexical_identity_id,
            sense_id=request.sense_id,
            morphological_analysis_id=request.morphological_analysis_id,
            target_concept_id=request.target_concept_id,
            matched=matched,
            observed_concept_ids=tuple(sorted(set(observed))) if matched else (),
            analyzer_version=result.analyzer_version,
            target_span=targets[0] if matched else None,
            evidence_sha256=canonical_sha256(
                {
                    "analysis": result.model_dump(mode="json"),
                    "bindings": used,
                    "request": request.model_dump(mode="json"),
                    "matched": matched,
                }
            ),
        )
