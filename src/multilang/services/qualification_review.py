"""Immutable offline review packets, separate human drafts and receipt verification.

An operator receipt authenticates the declared reviewer and exact decisions. It
does not establish professional credentials or enable production capabilities.
"""

from __future__ import annotations

import base64
import hashlib
import html
import json
import os
import re
import unicodedata
from datetime import datetime
from decimal import Decimal
from importlib.resources import files
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated, Literal

from pydantic import Field, computed_field, field_validator, model_validator

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.language_profiles import Identifier, NativeContract, Sha256
from multilang.domain.lexical_identity import UnitDecimal, canonical_sha256
from multilang.services.native_evidence import EvidenceStore
from multilang.services.vocabulary_review import _plain_path, _read_bytes

_MAX_BYTES = 32 * 1024**2
_MAX_HTML_BYTES = 64 * 1024**2
_UPOS = frozenset(
    "ADJ ADP ADV AUX CCONJ DET INTJ NOUN NUM PART PRON PROPN PUNCT SCONJ SYM VERB X".split()
)
_RATINGS = frozenset(
    "frequency irregularity unpredictability ambiguity unexpected_pronunciation prerequisite learning_difficulty".split()
)
Text = Annotated[str, Field(min_length=1, max_length=4096)]
SmallText = Annotated[str, Field(min_length=1, max_length=512)]
FeatureText = Annotated[str, Field(min_length=1, max_length=64000)]
FeatureMap = Annotated[dict[Identifier, FeatureText], Field(max_length=64)]
Ratings = Annotated[dict[Identifier, UnitDecimal], Field(max_length=7)]
Nonnegative = Annotated[Decimal, Field(ge=0, le=10**18, allow_inf_nan=False)]
Decision = Literal["accepted", "corrected", "rejected", "inconclusive"]


def _nfc(value: str) -> str:
    if not unicodedata.is_normalized("NFC", value) or any(
        unicodedata.category(c) in {"Cs", "Co", "Cn"}
        or (unicodedata.category(c) == "Cc" and c not in "\r\n\t")
        for c in value
    ):
        raise ValueError("review text must be NFC without invalid Unicode")
    return value


def _ratings(value):
    if set(value) - _RATINGS:
        raise ValueError("unsupported review rating")
    return value


def _resolved_sense(value):
    if value is not None:
        _nfc(value)
        if value.casefold() in {"unknown", "unresolved", "none", "null", "?", "unk", "x"}:
            raise ValueError("explicit resolved sense required; use null for unknown senses")
    return value


class ReviewSource(NativeContract):
    source_id: Identifier
    source_sha256: Sha256
    record_id: Identifier
    document_id: Identifier | None = None
    sentence_id: Identifier | None = None
    excerpt: str = Field(default="", max_length=64000)

    _source_text = field_validator("excerpt")(_nfc)


class ReviewToken(NativeContract):
    start: int = Field(ge=0, strict=True)
    end: int = Field(gt=0, strict=True)
    text: SmallText
    lemma: SmallText
    pos: Identifier
    sense_id: Identifier | None = None
    features: FeatureMap = Field(default_factory=dict)

    _token_text = field_validator("text", "lemma")(_nfc)
    _sense = field_validator("sense_id")(_resolved_sense)

    @model_validator(mode="after")
    def valid_token(self):
        if self.end - self.start != len(self.text) or self.pos not in _UPOS:
            raise ValueError("invalid review token span or POS")
        for key, value in self.features.items():
            _nfc(key)
            _nfc(value)
        return self


def _spans(text: str, tokens: tuple[ReviewToken, ...]) -> None:
    previous = 0
    for token in tokens:
        if token.start < previous or text[token.start : token.end] != token.text:
            raise ValueError("review token span does not match original source")
        previous = token.end


class _ReviewItem(NativeContract):
    item_id: Identifier
    sources: tuple[ReviewSource, ...] = Field(min_length=1, max_length=128)

    @computed_field
    @property
    def item_sha256(self) -> str:
        return canonical_sha256(self.model_dump(mode="json", exclude_computed_fields=True))


class LexicalReviewItem(_ReviewItem):
    kind: Literal["lexical"] = "lexical"
    candidate_id: Identifier
    candidate_sha256: Sha256
    lemma: SmallText
    pos: Identifier
    glosses: tuple[Text, ...] = Field(default=(), max_length=128)
    source_sense_ids: tuple[Identifier, ...] = Field(default=(), max_length=128)
    proposed_sense_id: Identifier | None = None

    _lemma = field_validator("lemma")(_nfc)
    _sense = field_validator("proposed_sense_id")(_resolved_sense)


class FormReviewItem(_ReviewItem):
    kind: Literal["form"] = "form"
    candidate_id: Identifier
    candidate_sha256: Sha256
    lemma: SmallText
    pos: Identifier
    text: SmallText
    features: FeatureMap = Field(default_factory=dict)
    canonical_sense_id: Identifier | None = None
    measurement_sha256: Sha256 | None = None
    evidence_source_keys: tuple[Sha256, ...] = Field(
        default=(), max_length=100000, exclude_if=lambda value: not value
    )
    measurements: dict[Identifier, Nonnegative] = Field(default_factory=dict, max_length=32)
    proposed_ratings: Ratings = Field(default_factory=dict)
    missing_reasons: tuple[Text, ...] = Field(default=(), max_length=64)

    _form_text = field_validator("lemma", "text")(_nfc)
    _supported_ratings = field_validator("proposed_ratings")(_ratings)
    _sense = field_validator("canonical_sense_id")(_resolved_sense)

    @field_validator("pos")
    @classmethod
    def upos_only(cls, value):
        if value not in _UPOS:
            raise ValueError("form proposals require a declared UPOS value")
        return value


class CaseReviewItem(_ReviewItem):
    kind: Literal["case"] = "case"
    text: str = Field(min_length=1, max_length=64000)
    proposal_tokens: tuple[ReviewToken, ...] = Field(default=(), max_length=4096)
    expected_match: bool | None = Field(default=None, strict=True)
    model_fingerprint: Sha256 | None = None
    behavior_tags: tuple[Identifier, ...] = Field(default=(), max_length=64)

    _case_text = field_validator("text")(_nfc)

    @model_validator(mode="after")
    def exact_spans(self):
        _spans(self.text, self.proposal_tokens)
        return self


ReviewItem = Annotated[
    LexicalReviewItem | FormReviewItem | CaseReviewItem, Field(discriminator="kind")
]


class ReviewPacket(NativeContract):
    schema_version: Literal[1] = 1
    packet_id: Identifier
    language: SupportedLanguage
    split: Literal["pilot", "calibration", "evaluation"]
    profile_sha256: Sha256
    rubric_sha256: Sha256
    items: tuple[ReviewItem, ...] = Field(min_length=1, max_length=5000)
    production_eligible: Literal[False] = False

    @model_validator(mode="after")
    def unique_items(self):
        if len({item.item_id for item in self.items}) != len(self.items):
            raise ValueError("duplicate review item identifier")
        return self

    @computed_field
    @property
    def packet_sha256(self) -> str:
        return canonical_sha256(self.model_dump(mode="json", exclude_computed_fields=True))


class _HumanDecision(NativeContract):
    item_id: Identifier
    item_sha256: Sha256
    decision: Decision
    reason: str = Field(min_length=1, max_length=4000)

    @field_validator("reason")
    @classmethod
    def explicit_reason(cls, value):
        if not value.strip():
            raise ValueError("a review decision needs a reason")
        return _nfc(value)


class LexicalDecision(_HumanDecision):
    kind: Literal["lexical"] = "lexical"
    corrected_lemma: SmallText | None = None
    corrected_pos: Identifier | None = None
    canonical_sense_id: Identifier | None = None
    _sense = field_validator("canonical_sense_id")(_resolved_sense)

    @model_validator(mode="after")
    def correction_shape(self):
        if self.decision in {"accepted", "corrected"} and not self.canonical_sense_id:
            raise ValueError("accepted lexical review requires an explicit sense")
        if self.decision == "corrected" and not (self.corrected_lemma and self.corrected_pos):
            raise ValueError("lexical correction requires lemma and POS")
        if self.decision != "corrected" and (self.corrected_lemma or self.corrected_pos):
            raise ValueError("only corrected decisions may replace lexical facts")
        if self.corrected_pos is not None and self.corrected_pos not in _UPOS - {"X"}:
            raise ValueError("corrected lexical POS must be resolved")
        if self.corrected_lemma is not None:
            _nfc(self.corrected_lemma)
        return self


class FormDecision(_HumanDecision):
    kind: Literal["form"] = "form"
    include: bool | None = Field(default=None, strict=True)
    ratings: Ratings = Field(default_factory=dict)
    canonical_sense_id: Identifier | None = None
    analysis_confidence: UnitDecimal | None = None

    _supported_ratings = field_validator("ratings")(_ratings)
    _sense = field_validator("canonical_sense_id")(_resolved_sense)

    @model_validator(mode="after")
    def definite_label(self):
        if self.decision in {"accepted", "corrected"} and self.include is None:
            raise ValueError("form review requires an explicit include/exclude label")
        if self.decision in {"rejected", "inconclusive"} and self.include is not None:
            raise ValueError("unresolved form decisions cannot provide calibration labels")
        return self


class CaseDecision(_HumanDecision):
    kind: Literal["case"] = "case"
    corrected_tokens: tuple[ReviewToken, ...] | None = Field(default=None, max_length=4096)
    expected_match: bool | None = Field(default=None, strict=True)

    @model_validator(mode="after")
    def correction_shape(self):
        if self.decision in {"accepted", "corrected"} and self.expected_match is None:
            raise ValueError("case review requires an explicit expected matching result")
        if self.decision == "corrected" and self.corrected_tokens is None:
            raise ValueError("case correction requires explicit tokens")
        if self.decision != "corrected" and self.corrected_tokens is not None:
            raise ValueError("only corrected decisions may replace case tokens")
        if self.corrected_tokens is not None and any(t.pos == "X" for t in self.corrected_tokens):
            raise ValueError("corrected case POS must be resolved")
        return self


HumanDecision = Annotated[
    LexicalDecision | FormDecision | CaseDecision, Field(discriminator="kind")
]


class HumanReviewSubmission(NativeContract):
    schema_version: Literal[1] = 1
    packet_sha256: Sha256
    reviewer_id: Identifier
    expertise_declaration: str = Field(min_length=1, max_length=2000)
    reviewed_at: datetime
    decisions: tuple[HumanDecision, ...] = Field(default=(), max_length=5000)
    receipt_id: Sha256 | None = None

    @model_validator(mode="after")
    def valid_submission(self):
        if self.reviewed_at.tzinfo is None or self.reviewed_at.utcoffset() is None:
            raise ValueError("review time requires an explicit timezone")
        if not self.expertise_declaration.strip():
            raise ValueError("explicit reviewer expertise declaration required")
        if len({d.item_id for d in self.decisions}) != len(self.decisions):
            raise ValueError("duplicate human decision")
        return self


class ValidatedReview(NativeContract):
    packet: ReviewPacket
    submission: HumanReviewSubmission
    status: Literal["draft", "authenticated"]
    production_eligible: Literal[False] = False

    @computed_field
    @property
    def authenticated(self) -> bool:
        return self.status == "authenticated"

    @computed_field
    @property
    def pending_items(self) -> int:
        return len(self.packet.items) - len(self.submission.decisions)


class ReviewExportManifest(NativeContract):
    schema_version: Literal[1] = 1
    packet_sha256: Sha256
    packet_file_sha256: Sha256
    html_sha256: Sha256
    item_count: int
    production_eligible: Literal[False] = False


def _json(data: bytes):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def invalid_constant(_value):
        raise ValueError("non-finite JSON value")

    return json.loads(data, object_pairs_hook=unique_pairs, parse_constant=invalid_constant)


def load_review_packet(path: Path, *, expected_sha256: str) -> ReviewPacket:
    return ReviewPacket.model_validate(_json(_read_bytes(path, expected_sha256, limit=_MAX_BYTES)))


def _bound_decisions(packet: ReviewPacket, submission: HumanReviewSubmission) -> None:
    if packet.packet_sha256 != submission.packet_sha256:
        raise ValueError("review packet checksum mismatch")
    items = {item.item_id: item for item in packet.items}
    for decision in submission.decisions:
        item = items.get(decision.item_id)
        if item is None or item.item_sha256 != decision.item_sha256 or item.kind != decision.kind:
            raise ValueError("human decision is not bound to the original review item")
        if isinstance(decision, CaseDecision):
            tokens = (
                decision.corrected_tokens
                if decision.corrected_tokens is not None
                else item.proposal_tokens
            )
            _spans(item.text, tokens)
            if decision.decision in {"accepted", "corrected"}:
                if any(token.pos == "X" for token in tokens):
                    raise ValueError("accepted case contains unresolved POS")
                if decision.expected_match and not tokens:
                    raise ValueError("positive matching review requires explicit tokens")
        if (
            isinstance(decision, LexicalDecision)
            and decision.decision == "accepted"
            and item.pos not in _UPOS - {"X"}
        ):
            raise ValueError("accepted lexical POS is unresolved")


def review_signing_payload(packet: ReviewPacket, submission: HumanReviewSubmission) -> dict:
    packet = ReviewPacket.model_validate(packet.model_dump(mode="json"))
    submission = HumanReviewSubmission.model_validate(submission.model_dump(mode="json"))
    _bound_decisions(packet, submission)
    return {
        "schema_version": 1,
        "packet_sha256": packet.packet_sha256,
        "language": packet.language.value,
        "split": packet.split,
        "profile_sha256": packet.profile_sha256,
        "rubric_sha256": packet.rubric_sha256,
        "submission": submission.model_dump(mode="json", exclude={"receipt_id"}),
    }


def validate_review(
    packet: ReviewPacket,
    submission: HumanReviewSubmission,
    *,
    expected_reviewer: str,
    verifier: EvidenceStore | None = None,
) -> ValidatedReview:
    """Reauthenticate originals at every trust boundary; never trust a status flag."""
    packet = ReviewPacket.model_validate(packet.model_dump(mode="json"))
    submission = HumanReviewSubmission.model_validate(submission.model_dump(mode="json"))
    payload = review_signing_payload(packet, submission)
    if submission.reviewer_id != expected_reviewer:
        raise ValueError("reviewer does not match the expected identity")
    status = "draft"
    if submission.receipt_id is not None:
        if verifier is None:
            raise ValueError("review receipt cannot be verified without an evidence store")
        try:
            receipt = verifier.load(submission.receipt_id)
            valid = receipt.signer == expected_reviewer and verifier.verify(
                submission.receipt_id, payload, purpose="qualification-review"
            )
        except (ValueError, OSError):
            valid = False
        if valid is not True:
            raise ValueError("review receipt does not authenticate the expected reviewer")
        status = "authenticated"
    return ValidatedReview(packet=packet, submission=submission, status=status)


def import_review(
    *,
    packet_path: Path,
    packet_sha256: str,
    submission_path: Path,
    submission_sha256: str,
    expected_reviewer: str,
    verifier: EvidenceStore | None = None,
) -> ValidatedReview:
    packet = load_review_packet(packet_path, expected_sha256=packet_sha256)
    submission = HumanReviewSubmission.model_validate(
        _json(_read_bytes(submission_path, submission_sha256, limit=_MAX_BYTES))
    )
    return validate_review(
        packet, submission, expected_reviewer=expected_reviewer, verifier=verifier
    )


def _safe_json(data: dict) -> str:
    return (
        json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def export_review(packet: ReviewPacket, output: Path) -> ReviewExportManifest:
    packet = ReviewPacket.model_validate(packet.model_dump(mode="json"))
    output = _plain_path(output)
    if output.exists():
        raise ValueError("review output already exists")
    packet_bytes = packet.model_dump_json(indent=2).encode("utf-8") + b"\n"
    if len(packet_bytes) > _MAX_BYTES:
        raise ValueError("review packet byte limit exceeded")
    resources = files("multilang.resources").joinpath("qualification_review")
    script = resources.joinpath("review.js").read_text(encoding="utf-8")
    style = resources.joinpath("review.css").read_text(encoding="utf-8")
    script_hash = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
    style_hash = base64.b64encode(hashlib.sha256(style.encode()).digest()).decode()
    csp = f"default-src 'none'; script-src 'sha256-{script_hash}'; style-src 'sha256-{style_hash}'; connect-src 'none'; img-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"
    page = resources.joinpath("review.html").read_text(encoding="utf-8")
    substitutions = {
        "CSP": html.escape(csp, quote=True).replace("&#x27;", "'"),
        "STYLE": style,
        "PACKET": _safe_json(packet.model_dump(mode="json")),
        "SCRIPT": script,
    }
    # One pass: source strings containing template markers remain literal data.
    page = re.sub(r"\{\{(CSP|STYLE|PACKET|SCRIPT)\}\}", lambda match: substitutions[match[1]], page)
    page_bytes = page.encode("utf-8")
    if len(page_bytes) > _MAX_HTML_BYTES:
        raise ValueError("review HTML byte limit exceeded")
    manifest = ReviewExportManifest(
        packet_sha256=packet.packet_sha256,
        packet_file_sha256=hashlib.sha256(packet_bytes).hexdigest(),
        html_sha256=hashlib.sha256(page_bytes).hexdigest(),
        item_count=len(packet.items),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".qualification-review-", dir=output.parent) as directory:
        staging = Path(directory) / "review"
        staging.mkdir(mode=0o700)
        for name, data in (
            ("packet.json", packet_bytes),
            ("review.html", page_bytes),
            ("manifest.json", (manifest.model_dump_json(indent=2) + "\n").encode()),
        ):
            path = staging / name
            path.write_bytes(data)
            path.chmod(0o600)
        if output.exists():
            raise ValueError("review output created concurrently")
        os.rename(staging, output)
    return manifest
