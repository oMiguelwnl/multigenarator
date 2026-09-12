"""Durable private learning operations using the existing native transaction boundary."""

import re
from collections import defaultdict
from collections.abc import Iterable
from itertools import islice
from pathlib import Path

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError

from multilang.db.native_models import (
    AuditLog,
    LegacyIdentityAlias,
    LexicalIdentityRecord,
    UserStateRecord,
)
from multilang.domain.anki_semantics import SemanticCard
from multilang.domain.events import DomainEvent, canonical_hash
from multilang.domain.learning import (
    AdaptivePolicy,
    AdaptiveQueueResult,
    HistoryAlias,
    HistoryImport,
    HistoryLimits,
    LearnerState,
)
from multilang.repositories.native_repository import NativeRepository
from multilang.services.adaptive_queue import (
    build_adaptive_queue,
    override_priority,
    reset_adaptation,
    revoke_history,
)
from multilang.services.anki_history import read_anki_history
from multilang.services.legacy_identity_adapter import LegacyAliasCandidate
from multilang.services.native_evidence import EvidenceStore


class NativeLearningService:
    """Flush state, audit and outbox atomically; callers own commit/rollback.

    The facade supplies the authenticated owner. No request payload can choose a
    second namespace. Missing state has revision zero; all writes require CAS.
    """

    STATE_KEY = "native-learning"

    def __init__(
        self, repository: NativeRepository, *, evidence_store: EvidenceStore | None = None
    ):
        self.repository = repository
        self.session = repository.session
        self.evidence_store = evidence_store

    @staticmethod
    def _namespace(owner_id: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_.@-]{1,128}", owner_id):
            raise ValueError("learning owner must be an authenticated bounded identifier")
        return f"user:{owner_id}"

    def _entity(self, owner_id: str) -> str:
        return canonical_hash({"owner": owner_id, "key": self.STATE_KEY})

    def get_state(self, *, owner_id: str) -> LearnerState:
        namespace = self._namespace(owner_id)
        row = self.session.get(UserStateRecord, (owner_id, self.STATE_KEY), populate_existing=True)
        if row is None:
            return LearnerState(namespace=namespace, revision=0)
        state = LearnerState.model_validate(row.payload)
        if state.namespace != namespace or state.revision != row.revision:
            raise ValueError("stored learner namespace or revision integrity failed")
        return state

    def _current(self, owner_id: str, expected_revision: int) -> LearnerState:
        if not isinstance(expected_revision, int) or expected_revision < 0:
            raise ValueError("expected learner revision must be nonnegative")
        state = self.get_state(owner_id=owner_id)
        if state.revision != expected_revision:
            raise ValueError("learner revision conflict")
        return state

    def _next_revision(self, owner_id: str, current: int) -> int:
        previous = (
            self.session.scalar(
                select(func.max(AuditLog.revision)).where(
                    AuditLog.entity_id == self._entity(owner_id)
                )
            )
            or 0
        )
        return max(current, int(previous)) + 1

    def _save(
        self,
        owner_id: str,
        before: LearnerState,
        state: LearnerState,
        *,
        event_type: str,
        reason: str,
    ) -> LearnerState:
        namespace = self._namespace(owner_id)
        if state.namespace != namespace:
            raise ValueError("learner state belongs to another owner")
        revision = self._next_revision(owner_id, before.revision)
        after = LearnerState.model_validate(state.model_dump(mode="json") | {"revision": revision})
        payload = after.model_dump(mode="json")
        if (
            len(after.history) > 100
            or sum(len(item.states) for item in after.history) > 200000
            or len(after.known_card_ids) > 200000
            or len(after.reading_card_ids) > 200000
        ):
            raise ValueError("stored learner state exceeds bounded capacity")
        event = DomainEvent(
            event_type=event_type,
            entity_id=self._entity(owner_id),
            revision=revision,
            actor="user:" + canonical_hash(owner_id)[:32],
            reason=reason,
            before_sha256=canonical_hash(before.model_dump(mode="json")),
            after_sha256=canonical_hash(payload),
        )
        if before.revision == 0:
            try:
                with self.session.begin_nested():
                    self.session.add(
                        UserStateRecord(
                            owner_id=owner_id,
                            key=self.STATE_KEY,
                            revision=revision,
                            payload=payload,
                        )
                    )
                    self.session.flush()
            except IntegrityError as exc:
                raise ValueError("learner revision conflict") from exc
        else:
            result = self.session.execute(
                update(UserStateRecord)
                .where(
                    UserStateRecord.owner_id == owner_id,
                    UserStateRecord.key == self.STATE_KEY,
                    UserStateRecord.revision == before.revision,
                )
                .values(revision=revision, payload=payload)
            )
            if result.rowcount != 1:
                raise ValueError("learner revision conflict")
        self.repository.record_event(event)
        return after

    def register_aliases(
        self, *, aliases: Iterable[HistoryAlias], receipt_sha256: str, actor: str
    ) -> int:
        items = tuple(islice(aliases, 100001))
        if not items or len(items) > 100000:
            raise ValueError("history alias count limit")
        items = tuple(HistoryAlias.model_validate(alias.model_dump()) for alias in items)
        signed_payload = {
            "aliases": [alias.model_dump(exclude={"evidence_sha256"}) for alias in items],
            "reviewer": actor,
        }
        if self.evidence_store is None or not self.evidence_store.verify(
            receipt_sha256, signed_payload, purpose="anki-history-alias"
        ):
            raise ValueError("independent signed history alias evidence is required")
        # Share the adapter's parent lock order so concurrent identity/history
        # composition cannot overwrite the other independently verified payload.
        parent_ids = sorted({alias.parent_lexical_identity_id for alias in items})
        for start in range(0, len(parent_ids), 500):
            self.session.execute(
                select(LexicalIdentityRecord.id)
                .where(LexicalIdentityRecord.id.in_(parent_ids[start : start + 500]))
                .order_by(LexicalIdentityRecord.id)
                .with_for_update()
            ).all()
        groups = defaultdict(list)
        seen = set()
        for alias in items:
            key = (alias.note_guid, alias.template_ordinal, alias.model_id)
            if key in seen or alias.evidence_sha256 != receipt_sha256:
                raise ValueError("ambiguous history alias or evidence mismatch")
            if self.repository.get_identity(alias.parent_lexical_identity_id) is None:
                raise ValueError("history alias references unknown lexical identity")
            seen.add(key)
            groups[alias.note_guid].append(alias)
        pending = []
        extensions = []
        for guid, group in groups.items():
            if len({alias.parent_lexical_identity_id for alias in group}) != 1:
                raise ValueError("history alias note must map to one lexical family")
            payload = {"history_aliases": [alias.model_dump(mode="json") for alias in group]}
            previous = self.session.get(
                LegacyIdentityAlias, guid, populate_existing=True, with_for_update=True
            )
            if previous is not None:
                previous_history = previous.payload.get("history_aliases")
                if previous.identity_id != group[0].parent_lexical_identity_id or (
                    previous_history is not None
                    and (
                        previous.evidence_sha256 != receipt_sha256
                        or previous_history != payload["history_aliases"]
                    )
                ):
                    raise ValueError(
                        "existing legacy alias is immutable; conflicting history evidence"
                    )
                identity_payload = previous.payload.get("identity_alias")
                if identity_payload is not None:
                    identity = LegacyAliasCandidate.model_validate(identity_payload)
                    if (
                        identity.legacy_guid != guid
                        or identity.identity_ids != (previous.identity_id,)
                        or identity.evidence_sha256 is None
                        or (
                            previous_history is None
                            and previous.evidence_sha256 != identity.evidence_sha256
                        )
                        or not self.evidence_store.verify(
                            identity.evidence_sha256,
                            identity.model_dump(mode="json", exclude={"evidence_sha256"}),
                            purpose="legacy-identity-alias",
                        )
                    ):
                        raise ValueError("stored identity alias evidence integrity mismatch")
                elif previous_history is None:
                    raise ValueError("stored identity alias evidence is required")
                extensions.append((previous, dict(previous.payload) | payload))
            else:
                pending.append(
                    LegacyIdentityAlias(
                        legacy_guid=guid,
                        identity_id=group[0].parent_lexical_identity_id,
                        evidence_sha256=receipt_sha256,
                        payload=payload,
                    )
                )
        for previous, payload in extensions:
            previous.payload = payload
            # The identity proof remains in identity_alias; this column binds the
            # independently reviewed semantic-card history when both are present.
            previous.evidence_sha256 = receipt_sha256
        self.session.add_all(pending)
        self.repository.record_event(
            DomainEvent(
                event_type="LearnerAliasesRegistered",
                entity_id=canonical_hash(sorted(groups)),
                revision=1,
                actor=actor,
                reason="independent_alias_review",
                after_sha256=canonical_hash(signed_payload),
            )
        )
        return len(items)

    def _aliases(
        self, alias_guids: tuple[str, ...] | None, limits: HistoryLimits
    ) -> tuple[HistoryAlias, ...]:
        statement = (
            select(LegacyIdentityAlias)
            .order_by(LegacyIdentityAlias.legacy_guid)
            .limit(limits.max_cards + 1)
        )
        if alias_guids is not None:
            if len(alias_guids) > limits.max_cards or any(
                not value or len(value) > 128 for value in alias_guids
            ):
                raise ValueError("history alias selector limit")
            statement = statement.where(LegacyIdentityAlias.legacy_guid.in_(alias_guids))
        result = []
        for count, row in enumerate(self.session.scalars(statement), start=1):
            if count > limits.max_cards:
                raise ValueError("history alias registry limit; select explicit aliases")
            # Identity-only legacy aliases do not prove a semantic card/ordinal.
            rows = row.payload.get("history_aliases", ())
            for payload in rows:
                alias = HistoryAlias.model_validate(payload)
                if (
                    alias.note_guid != row.legacy_guid
                    or alias.parent_lexical_identity_id != row.identity_id
                    or alias.evidence_sha256 != row.evidence_sha256
                ):
                    raise ValueError("stored history alias evidence integrity mismatch")
                result.append(alias)
                if len(result) > limits.max_cards:
                    raise ValueError("history alias count limit")
        return tuple(result)

    def import_history(
        self,
        *,
        owner_id: str,
        path: Path,
        expected_revision: int,
        alias_guids: tuple[str, ...] | None = None,
        limits: HistoryLimits | None = None,
    ) -> HistoryImport:
        before = self._current(owner_id, expected_revision)
        limits = HistoryLimits.model_validate((limits or HistoryLimits()).model_dump())
        imported = read_anki_history(
            path,
            aliases=self._aliases(alias_guids, limits),
            namespace=before.namespace,
            limits=limits,
        )
        existing = next(
            (item for item in before.history if item.import_id == imported.import_id), None
        )
        if existing is not None:
            if existing != imported:
                raise ValueError("history import identity integrity mismatch")
            return existing
        state = LearnerState.model_validate(
            before.model_dump(mode="json") | {"history": (*before.history, imported)}
        )
        self._save(
            owner_id,
            before,
            state,
            event_type="LearnerHistoryImported",
            reason="explicit_history_import",
        )
        return imported

    def _ids(self, card_ids: Iterable[str]) -> tuple[str, ...]:
        values = tuple(islice(card_ids, 200001))
        if len(values) > 200000 or any(
            not isinstance(value, str) or not value or len(value) > 255 for value in values
        ):
            raise ValueError("learner card identifier limit")
        return tuple(sorted(set(values)))

    def set_known(
        self, *, owner_id: str, card_ids: Iterable[str], expected_revision: int
    ) -> LearnerState:
        before = self._current(owner_id, expected_revision)
        state = LearnerState.model_validate(
            before.model_dump(mode="json") | {"known_card_ids": self._ids(card_ids)}
        )
        return self._save(
            owner_id, before, state, event_type="LearnerStateUpdated", reason="explicit_known_cards"
        )

    def set_reading(
        self, *, owner_id: str, card_ids: Iterable[str], expected_revision: int
    ) -> LearnerState:
        before = self._current(owner_id, expected_revision)
        state = LearnerState.model_validate(
            before.model_dump(mode="json") | {"reading_card_ids": self._ids(card_ids)}
        )
        return self._save(
            owner_id,
            before,
            state,
            event_type="LearnerStateUpdated",
            reason="explicit_reading_cards",
        )

    def set_expansion(
        self, *, owner_id: str, enabled: bool, expected_revision: int
    ) -> LearnerState:
        before = self._current(owner_id, expected_revision)
        state = LearnerState.model_validate(
            before.model_dump(mode="json") | {"expansion_enabled": enabled}
        )
        return self._save(
            owner_id, before, state, event_type="LearnerStateUpdated", reason="expansion_opt_in"
        )

    def override(
        self, *, owner_id: str, card_id: str, priority: int | None, expected_revision: int
    ) -> LearnerState:
        before = self._current(owner_id, expected_revision)
        self._ids((card_id,))
        return self._save(
            owner_id,
            before,
            override_priority(before, card_id=card_id, priority=priority),
            event_type="LearnerStateUpdated",
            reason="explicit_priority_override",
        )

    def reset(self, *, owner_id: str, expected_revision: int) -> LearnerState:
        before = self._current(owner_id, expected_revision)
        return self._save(
            owner_id,
            before,
            reset_adaptation(before),
            event_type="LearnerStateUpdated",
            reason="adaptation_reset",
        )

    def revoke_history(
        self, *, owner_id: str, import_id: str, expected_revision: int
    ) -> LearnerState:
        before = self._current(owner_id, expected_revision)
        return self._save(
            owner_id,
            before,
            revoke_history(before, import_id),
            event_type="LearnerHistoryRevoked",
            reason="history_consent_revoked",
        )

    def delete(self, *, owner_id: str, expected_revision: int) -> None:
        before = self._current(owner_id, expected_revision)
        if before.revision == 0:
            return
        result = self.session.execute(
            delete(UserStateRecord).where(
                UserStateRecord.owner_id == owner_id,
                UserStateRecord.key == self.STATE_KEY,
                UserStateRecord.revision == expected_revision,
            )
        )
        if result.rowcount != 1:
            raise ValueError("learner revision conflict")
        self.repository.record_event(
            DomainEvent(
                event_type="LearnerStateDeleted",
                entity_id=self._entity(owner_id),
                revision=self._next_revision(owner_id, before.revision),
                actor="user:" + canonical_hash(owner_id)[:32],
                reason="learner_consent_revoked",
                before_sha256=canonical_hash(before.model_dump(mode="json")),
                after_sha256=canonical_hash({}),
            )
        )

    def queue(
        self, *, owner_id: str, cards: Iterable[SemanticCard], policy: AdaptivePolicy | None = None
    ) -> AdaptiveQueueResult:
        policy = AdaptivePolicy.model_validate((policy or AdaptivePolicy()).model_dump())
        items = tuple(islice(cards, policy.max_cards + 1))
        return build_adaptive_queue(
            cards=items, learner_state=self.get_state(owner_id=owner_id), policy=policy
        )
