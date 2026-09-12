"""Local contextual morphology and an explicit, reviewed sense-binding gate.

Models supply morphology only. They cannot mint lexical identities or senses.
Offsets address the unchanged NFC input in Unicode characters, never bytes.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from pathlib import Path
from threading import RLock
from typing import Literal, Protocol

from pydantic import Field, model_validator

from multilang.domain.content import ContentRequest, FrozenContentModel, TargetMatchEvidence
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.language_models import load_stanza_pipeline, model_spec, model_status

_UPOS = frozenset(
    "ADJ ADP ADV AUX CCONJ DET INTJ NOUN NUM PART PRON PROPN PUNCT SCONJ SYM VERB X".split()
)
_JAPANESE_POS = {
    "名詞": "NOUN",
    "代名詞": "PRON",
    "動詞": "VERB",
    "形容詞": "ADJ",
    "形状詞": "ADJ",
    "副詞": "ADV",
    "助詞": "PART",
    "助動詞": "AUX",
    "連体詞": "DET",
    "接続詞": "CCONJ",
    "感動詞": "INTJ",
    "補助記号": "PUNCT",
    "記号": "SYM",
}
_KOREAN_POS = {
    "NNG": "NOUN",
    "NNP": "PROPN",
    "NNB": "NOUN",
    "NR": "NUM",
    "NP": "PRON",
    "VV": "VERB",
    "VA": "ADJ",
    "VX": "AUX",
    "VCP": "AUX",
    "VCN": "ADJ",
    "MM": "DET",
    "MAG": "ADV",
    "MAJ": "CCONJ",
    "IC": "INTJ",
}


def sentence_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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


class ContextualAnalysis(FrozenContentModel):
    language: str
    status: Literal["complete", "inconclusive", "invalid", "unavailable", "unsupported"]
    sentence_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    model_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    tokens: tuple[ContextualToken, ...] = ()
    reason: str
    analyzer_version: str = "contextual-morphology-1"

    @model_validator(mode="after")
    def valid_tokens(self):
        if self.status == "complete" and not self.tokens:
            raise ValueError("complete analysis requires tokens")
        previous = 0
        for token in self.tokens:
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


class LocalContextualMorphologyService:
    """Serialize vendor calls, verify local models, and never implicitly download.

    Non-NFC input is rejected instead of silently changing source offsets. The
    caller may explicitly normalize a source before creating its source hash.
    """

    def __init__(self, *, model_root: Path) -> None:
        self.model_root = Path(model_root)
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
            )
        fingerprint = empty
        with self._lock:
            try:
                status = model_status(language, self.model_root)
                if not status.get("available"):
                    raise RuntimeError("model unavailable")
                fingerprint = canonical_sha256({"policy": "contextual-morphology-1", **status})
                key = (language, fingerprint)
                if key not in self._pipelines:
                    if spec.backend == "stanza":
                        pipeline = load_stanza_pipeline(language, self.model_root)
                    elif spec.backend == "kiwi":
                        from multilang.services.korean_morphology import KiwiKoreanMorphologyService

                        pipeline = KiwiKoreanMorphologyService()
                    else:
                        import unidic_lite
                        from fugashi import Tagger

                        pipeline = Tagger(f'-d "{unidic_lite.DICDIR}"')
                    self._pipelines[key] = pipeline
                pipeline = self._pipelines[key]
            except Exception:
                return ContextualAnalysis(
                    language=language,
                    status="unavailable",
                    sentence_sha256=source,
                    model_fingerprint=fingerprint,
                    reason="model_missing_or_drifted",
                )
            try:
                if spec.backend == "stanza":
                    rows, complete = self._stanza(pipeline, text)
                elif spec.backend == "kiwi":
                    rows, complete = self._kiwi(pipeline, text)
                else:
                    rows, complete = self._fugashi(pipeline, text)
                tokens = tuple(
                    ContextualToken(**row, sentence_sha256=source, model_fingerprint=fingerprint)
                    for row in rows
                )
                previous = 0
                for token in tokens:
                    if (
                        token.start < previous
                        or text[token.start : token.end] != token.text
                        or text[previous : token.start].strip()
                    ):
                        raise ValueError("inexact or missing source span")
                    previous = token.end
                if not tokens or text[previous:].strip() or any(t.pos == "X" for t in tokens):
                    complete = False
                return ContextualAnalysis(
                    language=language,
                    status="complete" if complete else "inconclusive",
                    tokens=tokens,
                    sentence_sha256=source,
                    model_fingerprint=fingerprint,
                    reason="morphology_only" if complete else "ambiguous_or_incomplete_analysis",
                )
            except Exception:
                return ContextualAnalysis(
                    language=language,
                    status="inconclusive",
                    sentence_sha256=source,
                    model_fingerprint=fingerprint,
                    reason="malformed_or_unaligned_analysis",
                )

    @staticmethod
    def _stanza(pipeline, text):
        document = pipeline(text)
        rows = []
        for sentence in document.sentences:
            for token in sentence.tokens:
                # Expanded words often lack exact original surface offsets. Never
                # guess a contraction's subspans from normalized word spellings.
                if len(token.words) != 1:
                    raise ValueError("unaligned multiword expansion")
                word = token.words[0]
                if word.text != token.text:
                    raise ValueError("word/token surface disagreement")
                rows.append(
                    dict(
                        text=token.text,
                        lemma=word.lemma,
                        pos=word.upos,
                        features=_features(word.feats),
                        start=token.start_char,
                        end=token.end_char,
                    )
                )
                if len(rows) > 16384:
                    raise ValueError("token limit")
        return rows, True

    @staticmethod
    def _fugashi(pipeline, text):
        rows, position, complete = [], 0, True
        for token in pipeline(text):
            whitespace = token.white_space
            if not isinstance(whitespace, str) or whitespace.strip():
                raise ValueError("invalid vendor whitespace")
            if text[position : position + len(whitespace)] != whitespace:
                raise ValueError("inexact vendor whitespace")
            position += len(whitespace)
            feature = token.feature
            pos = _JAPANESE_POS.get(feature.pos1, "X")
            if feature.pos1 == "名詞" and feature.pos2 == "固有名詞":
                pos = "PROPN"
            elif feature.pos1 == "名詞" and feature.pos2 == "数詞":
                pos = "NUM"
            features = tuple(
                (name, getattr(feature, name))
                for name in feature._fields
                if getattr(feature, name) not in ("", "*")
            )
            rows.append(
                dict(
                    text=token.surface,
                    lemma=feature.lemma,
                    pos=pos,
                    features=features,
                    start=position,
                    end=position + len(token.surface),
                )
            )
            position += len(token.surface)
            if token.is_unk:
                complete = False
            if len(rows) > 16384:
                raise ValueError("token limit")
        return rows, complete

    @staticmethod
    def _kiwi(pipeline, text):
        from multilang.domain.korean import KOREAN_LEXICAL_POS_TAGS

        result = pipeline.analyze(text)
        if not result.passing:
            raise ValueError("Kiwi unavailable or incomplete")
        alternatives = result.alternatives
        complete = all(item.words == alternatives[0].words for item in alternatives[1:])
        rows, position = [], 0
        for word in alternatives[0].words:
            # Existing Kiwi projection already validates raw vendor spans. Its
            # exact grouped surface is aligned sequentially; no substring search,
            # suffix splitting, lemma matching or whitespace-derived identity.
            while position < len(text) and text[position].isspace():
                position += 1
            if text[position : position + len(word.surface_form)] != word.surface_form:
                raise ValueError("unprojected Kiwi source text")
            lexical = [item for item in word.morphemes if item.pos in KOREAN_LEXICAL_POS_TAGS]
            if len(lexical) != 1:
                raise ValueError("compound lexical identity requires explicit projection")
            rows.append(
                dict(
                    text=word.surface_form,
                    lemma=lexical[0].lemma,
                    pos=_KOREAN_POS.get(lexical[0].pos, "X"),
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
                    start=position,
                    end=position + len(word.surface_form),
                )
            )
            position += len(word.surface_form)
        return rows, complete


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
