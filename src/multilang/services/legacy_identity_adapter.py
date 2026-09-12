"""Explicit one-to-one GUID preservation; identity aliases never infer card history.

The caller supplies independently verified mapping evidence and owns the outer
transaction. Dry runs classify every old GUID, and unresolved merges prevent the
whole batch from writing. No method opens or modifies an Anki collection.
"""

from collections import Counter
from collections.abc import Callable, Iterable
from typing import Literal

from pydantic import Field, computed_field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from multilang.db.native_models import LegacyIdentityAlias, LexicalIdentityRecord
from multilang.domain.events import DomainEvent, canonical_hash
from multilang.domain.language_profiles import NativeContract, Sha256
from multilang.repositories.native_repository import NativeRepository


class LegacyAliasCandidate(NativeContract):
    legacy_guid: str = Field(min_length=1, max_length=128, pattern=r"^[^\s\x00-\x1f\x7f]+$")
    identity_ids: tuple[str, ...] = Field(default=(), max_length=100)
    evidence_sha256: Sha256 | None = None


class LegacyAliasDecision(NativeContract):
    candidate: LegacyAliasCandidate
    classification: Literal[
        "resolved_one_to_one",
        "unresolved",
        "ambiguous",
        "merge_requires_resolution",
        "existing_conflict",
        "unverified_evidence",
        "missing_target",
    ]
    identity_sha256: Sha256 | None = None
    existing_payload_sha256: Sha256 | None = None


class LegacyAliasPreview(NativeContract):
    decisions: tuple[LegacyAliasDecision, ...]

    @computed_field
    @property
    def unresolved_count(self) -> int:
        return sum(item.classification != "resolved_one_to_one" for item in self.decisions)

    @computed_field
    @property
    def ready(self) -> bool:
        return bool(self.decisions) and self.unresolved_count == 0

    @property
    def confirmation_sha256(self) -> str:
        return canonical_hash(self.model_dump(mode="json"))


class LegacyIdentityAdapter:
    def __init__(
        self,
        session: Session,
        *,
        evidence_verifier: Callable[[LegacyAliasCandidate], bool],
        max_aliases: int = 10000,
    ):
        if not 1 <= max_aliases <= 100000:
            raise ValueError("alias count limit is invalid")
        self.session = session
        self.evidence_verifier = evidence_verifier
        self.max_aliases = max_aliases

    def preview(self, candidates: Iterable[LegacyAliasCandidate]) -> LegacyAliasPreview:
        inputs = []
        for item in candidates:
            if len(inputs) >= self.max_aliases:
                raise ValueError("alias count limit exceeded")
            inputs.append(LegacyAliasCandidate.model_validate(item.model_dump(mode="json")))
        if len({item.legacy_guid for item in inputs}) != len(inputs):
            raise ValueError("duplicate legacy GUID requires explicit resolution")
        counts = Counter(item.identity_ids[0] for item in inputs if len(item.identity_ids) == 1)
        identities = {}
        aliases = {}
        aliases_by_identity = {}
        guids = sorted(item.legacy_guid for item in inputs)
        target_ids = sorted(counts)
        for start in range(0, max(len(guids), len(target_ids)), 500):
            subset = target_ids[start : start + 500]
            for row in self.session.scalars(
                select(LexicalIdentityRecord)
                .where(LexicalIdentityRecord.id.in_(subset))
                .execution_options(populate_existing=True)
            ):
                identities[row.id] = row
            for row in self.session.scalars(
                select(LegacyIdentityAlias)
                .where(
                    or_(
                        LegacyIdentityAlias.legacy_guid.in_(guids[start : start + 500]),
                        LegacyIdentityAlias.identity_id.in_(subset),
                    )
                )
                .execution_options(populate_existing=True)
            ):
                aliases[row.legacy_guid] = row
                aliases_by_identity.setdefault(row.identity_id, set()).add(row.legacy_guid)
        decisions = []
        for item in sorted(inputs, key=lambda candidate: candidate.legacy_guid):
            classification = "resolved_one_to_one"
            identity_hash = None
            existing = aliases.get(item.legacy_guid)
            if not item.identity_ids:
                classification = "unresolved"
            elif len(item.identity_ids) != 1:
                classification = "ambiguous"
            elif counts[item.identity_ids[0]] > 1:
                classification = "merge_requires_resolution"
            else:
                identity_id = item.identity_ids[0]
                target = identities.get(identity_id)
                other = aliases_by_identity.get(identity_id, set()) - {item.legacy_guid}
                stored_mapping = existing.payload.get("identity_alias") if existing else None
                if existing is not None and (
                    existing.identity_id != identity_id
                    or (
                        stored_mapping is not None
                        and stored_mapping != item.model_dump(mode="json")
                    )
                    or (
                        "history_aliases" not in existing.payload
                        and existing.evidence_sha256 != item.evidence_sha256
                    )
                ):
                    classification = "existing_conflict"
                elif target is None:
                    classification = "missing_target"
                elif other:
                    classification = "merge_requires_resolution"
                elif item.evidence_sha256 is None or self.evidence_verifier(item) is not True:
                    classification = "unverified_evidence"
                else:
                    identity_hash = target.content_sha256
            decisions.append(
                LegacyAliasDecision(
                    candidate=item,
                    classification=classification,
                    identity_sha256=identity_hash,
                    existing_payload_sha256=canonical_hash(existing.payload) if existing else None,
                )
            )
        return LegacyAliasPreview(decisions=tuple(decisions))

    def apply(self, preview: LegacyAliasPreview, *, confirmation_sha256: str, actor: str) -> dict:
        preview = LegacyAliasPreview.model_validate(preview.model_dump(mode="json"))
        if confirmation_sha256 != preview.confirmation_sha256:
            raise ValueError("alias confirmation mismatch")
        if not preview.ready:
            raise ValueError("unresolved identity aliases block migration")
        candidates = tuple(item.candidate for item in preview.decisions)
        with self.session.begin_nested():
            # Lock parents in a fixed order before checking one-to-one conflicts.
            targets = sorted(item.identity_ids[0] for item in candidates)
            for start in range(0, len(targets), 500):
                self.session.execute(
                    select(LexicalIdentityRecord.id)
                    .where(LexicalIdentityRecord.id.in_(targets[start : start + 500]))
                    .order_by(LexicalIdentityRecord.id)
                    .with_for_update()
                ).all()
            current = self.preview(candidates)
            if current != preview:
                raise ValueError("alias mapping or evidence drift requires a new preview")
            for candidate in candidates:
                row = self.session.get(LegacyIdentityAlias, candidate.legacy_guid)
                mapping = candidate.model_dump(mode="json")
                if row is None:
                    row = LegacyIdentityAlias(
                        legacy_guid=candidate.legacy_guid,
                        identity_id=candidate.identity_ids[0],
                        evidence_sha256=candidate.evidence_sha256,
                        payload={"identity_alias": mapping},
                    )
                    self.session.add(row)
                elif row.payload.get("identity_alias") == mapping:
                    continue
                else:
                    row.payload = {**row.payload, "identity_alias": mapping}
                self.session.flush()
                NativeRepository(self.session).record_event(
                    DomainEvent(
                        event_type="LearnerAliasesRegistered",
                        entity_id=candidate.legacy_guid,
                        actor=actor,
                        reason="legacy_identity_alias",
                        revision=1,
                        after_sha256=canonical_hash(mapping),
                    )
                )
        return {"status": "completed", "preserved_guids": [item.legacy_guid for item in candidates]}
