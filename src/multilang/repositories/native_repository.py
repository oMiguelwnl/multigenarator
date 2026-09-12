"""Transactional persistence for core, generated and user data.

Methods flush but never commit. The application owns the transaction, including
all audit and outbox rows. Versions are immutable; only explicit heads move.
"""

import unicodedata
from copy import deepcopy

from pydantic import BaseModel
from sqlalchemy import delete, exists, func, or_, select, update
from sqlalchemy.orm import Session

from multilang.db.native_models import (
    AudioVersionRecord,
    AuditLog,
    ContentVersionRecord,
    DatasetFormMembership,
    DatasetHeadRecord,
    DatasetMembershipRecord,
    DatasetVersionRecord,
    DeckEditionRecord,
    DomainEventRecord,
    LanguageProfileRecord,
    LexicalIdentityRecord,
    LexicalIdentityRevision,
    SurfaceFormRecord,
    SurfaceFormRevision,
    UserStateRecord,
)
from multilang.domain.datasets import DatasetManifest
from multilang.domain.events import DomainEvent, canonical_hash


def model_payload(model: BaseModel) -> dict:
    """Store constructor fields, not computed properties that cannot round-trip."""
    return model.model_dump(mode="json", include=set(type(model).model_fields))


def _namespace_owner(namespace: str, owner_id: str) -> None:
    if namespace not in {"core", "expansion", "custom", "highlight", "foundation"}:
        raise ValueError("unsupported content namespace")
    if (namespace in {"custom", "highlight"}) != bool(owner_id):
        raise ValueError("private namespaces require owner; shared namespaces forbid owner")


class NativeRepository:
    def __init__(self, session: Session):
        self.session = session

    def record_event(self, event: DomainEvent) -> None:
        if self.session.get(DomainEventRecord, event.event_id) is not None:
            return
        self.session.add(
            DomainEventRecord(
                id=event.event_id, event_type=event.event_type, payload=model_payload(event)
            )
        )
        self.session.add(
            AuditLog(
                id=event.event_id,
                entity_id=event.entity_id,
                action=event.event_type,
                actor=event.actor,
                reason=event.reason,
                revision=event.revision,
                before_sha256=event.before_sha256,
                after_sha256=event.after_sha256,
                created_at=event.occurred_at,
            )
        )
        self.session.flush()

    def put_profile(self, profile: BaseModel, *, actor: str = "system") -> dict:
        from multilang.domain.language_profiles import LanguageProfile

        profile = LanguageProfile.model_validate(profile.model_dump(mode="json"))
        payload = model_payload(profile)
        code = payload["language"]
        version = payload["version"]
        key = f"{code}:{version}"
        digest = canonical_hash(payload)
        row = self.session.get(LanguageProfileRecord, key)
        if row is not None and row.content_sha256 != digest:
            raise ValueError("language profile version is immutable")
        if row is None:
            self.session.add(
                LanguageProfileRecord(
                    id=key, language=code, version=version, content_sha256=digest, payload=payload
                )
            )
            self.session.flush()
            self.record_event(
                DomainEvent(
                    event_type="LanguageProfileRegistered",
                    entity_id=key,
                    revision=1,
                    actor=actor,
                    reason="profile_registration",
                    after_sha256=digest,
                )
            )
        return payload

    def put_identity(
        self, identity: BaseModel, *, actor: str, reason: str, expected_revision: int | None = None
    ) -> dict:
        from multilang.domain.lexical_identity import LexicalIdentity

        identity = LexicalIdentity.model_validate(identity.model_dump(mode="json"))
        payload = model_payload(identity)
        key = identity.lexical_identity_id
        digest = canonical_hash(payload)
        row = self.session.get(LexicalIdentityRecord, key)
        if row is not None:
            if expected_revision is not None and row.revision != expected_revision:
                raise ValueError("lexical revision conflict")
            if row.content_sha256 == digest:
                return self.get_identity(key)
            if expected_revision is None:
                raise ValueError("updating an identity requires expected_revision")
            old_hash, revision = row.content_sha256, row.revision + 1
            result = self.session.execute(
                update(LexicalIdentityRecord)
                .where(
                    LexicalIdentityRecord.id == key,
                    LexicalIdentityRecord.revision == expected_revision,
                )
                .values(revision=revision, content_sha256=digest, payload=payload)
            )
            if result.rowcount != 1:
                raise ValueError("lexical revision conflict")
            event_type = "LexicalIdentityUpdated"
        else:
            if expected_revision not in {None, 0}:
                raise ValueError("lexical revision conflict")
            revision, old_hash, event_type = 1, None, "LexicalIdentityCreated"
            self.session.add(
                LexicalIdentityRecord(
                    id=key,
                    language=payload["language"],
                    normalized_lemma=payload["normalized_lemma"],
                    part_of_speech=payload["part_of_speech"],
                    sense_id=payload["sense_id"],
                    revision=revision,
                    content_sha256=digest,
                    payload=payload,
                )
            )
            self.session.flush()
        self.session.add(
            LexicalIdentityRevision(
                identity_id=key, revision=revision, content_sha256=digest, payload=payload
            )
        )
        self.record_event(
            DomainEvent(
                event_type=event_type,
                entity_id=key,
                revision=revision,
                actor=actor,
                reason=reason,
                before_sha256=old_hash,
                after_sha256=digest,
            )
        )
        return self.get_identity(key)

    def get_identity(self, identity_id: str) -> dict | None:
        row = self.session.get(LexicalIdentityRecord, identity_id)
        if row is None:
            return None
        return {
            **deepcopy(row.payload),
            "lexical_identity_id": row.id,
            "revision": row.revision,
            "content_sha256": row.content_sha256,
        }

    def identity_history(self, identity_id: str) -> list[dict]:
        return [
            {
                "revision": row.revision,
                "content_sha256": row.content_sha256,
                "payload": deepcopy(row.payload),
            }
            for row in self.session.scalars(
                select(LexicalIdentityRevision)
                .where(LexicalIdentityRevision.identity_id == identity_id)
                .order_by(LexicalIdentityRevision.revision)
            )
        ]

    def put_form(
        self,
        form: BaseModel,
        *,
        identity_id: str,
        analysis_id: str,
        text: str,
        actor: str = "system",
        expected_revision: int | None = None,
    ) -> None:
        from multilang.domain.lexical_identity import SurfaceForm

        form = SurfaceForm.model_validate(form.model_dump(mode="json"))
        if (identity_id, analysis_id, text) != (
            form.lexical_identity_id,
            form.analysis.morphological_analysis_id,
            form.text,
        ):
            raise ValueError(
                "surface form arguments do not match its parent/analysis/text contract"
            )
        if self.session.get(LexicalIdentityRecord, identity_id) is None:
            raise ValueError("unknown parent identity")
        payload = model_payload(form)
        key = form.surface_form_id
        digest = canonical_hash(payload)
        row = self.session.get(SurfaceFormRecord, key)
        if row is not None and row.content_sha256 == digest:
            return
        old_hash = row.content_sha256 if row else None
        revision = row.revision + 1 if row else 1
        if row is not None:
            if expected_revision != row.revision:
                raise ValueError("surface form update requires current expected_revision")
            result = self.session.execute(
                update(SurfaceFormRecord)
                .where(SurfaceFormRecord.id == key, SurfaceFormRecord.revision == expected_revision)
                .values(revision=revision, content_sha256=digest, payload=payload)
            )
            if result.rowcount != 1:
                raise ValueError("surface form revision conflict")
        if row is None:
            self.session.add(
                SurfaceFormRecord(
                    id=key,
                    identity_id=identity_id,
                    analysis_id=analysis_id,
                    normalized_text=unicodedata.normalize("NFC", text).casefold(),
                    content_sha256=digest,
                    payload=payload,
                    revision=1,
                )
            )
            self.session.flush()
        self.session.add(
            SurfaceFormRevision(
                form_id=key, revision=revision, content_sha256=digest, payload=payload
            )
        )
        self.record_event(
            DomainEvent(
                event_type="SurfaceFormUpdated",
                entity_id=key,
                revision=revision,
                actor=actor,
                reason="source_form",
                before_sha256=old_hash,
                after_sha256=digest,
            )
        )

    def clone_dataset_version(
        self, source_dataset_id: str, manifest: DatasetManifest, *, actor: str, reason: str
    ) -> dict:
        """Approve/relabel an existing snapshot without reading mutable projections."""
        source = self.get_dataset(source_dataset_id, owner_id=manifest.owner_id)
        if source is None:
            raise ValueError("unknown source dataset")
        original = DatasetManifest.model_validate(source)
        fields = (
            "language",
            "kind",
            "namespace",
            "owner_id",
            "source_id",
            "source_sha256",
            "policy_version",
            "members",
        )
        if any(getattr(original, field) != getattr(manifest, field) for field in fields):
            raise ValueError("dataset approval cannot change source or inventory")
        self.dataset_identities(source_dataset_id, owner_id=manifest.owner_id)
        self.dataset_forms(source_dataset_id, owner_id=manifest.owner_id)
        return self.save_dataset(
            manifest, actor=actor, reason=reason, _source_dataset_id=source_dataset_id
        )

    def save_dataset(
        self,
        manifest: DatasetManifest,
        *,
        actor: str,
        reason: str,
        _source_dataset_id: str | None = None,
    ) -> dict:
        if self.session.get(DatasetVersionRecord, manifest.dataset_id) is not None:
            return self.get_dataset(manifest.dataset_id, owner_id=manifest.owner_id)
        previous = self.session.scalar(
            select(DatasetVersionRecord).where(
                DatasetVersionRecord.language == manifest.language.value,
                DatasetVersionRecord.kind == manifest.kind,
                DatasetVersionRecord.namespace == manifest.namespace,
                DatasetVersionRecord.owner_id == manifest.owner_id,
                DatasetVersionRecord.version == manifest.version,
            )
        )
        if previous is not None:
            raise ValueError("dataset version already exists with different input")
        # One lookup for the entire inventory; avoid 3000 individual database queries.
        ids = [member.identity_id for member in manifest.members]
        parents = {
            row.id: row
            for row in self.session.scalars(
                select(LexicalIdentityRecord).where(LexicalIdentityRecord.id.in_(ids))
            )
        }
        pinned_members = (
            {
                row.identity_id: row
                for row in self.session.scalars(
                    select(DatasetMembershipRecord).where(
                        DatasetMembershipRecord.dataset_id == _source_dataset_id
                    )
                )
            }
            if _source_dataset_id
            else {}
        )
        for member in manifest.members:
            parent = parents.get(member.identity_id)
            if parent is None or parent.language != manifest.language.value:
                raise ValueError("dataset member missing or language mismatch")
            if member.identity_sha256 is not None and member.identity_sha256 != (
                pinned_members[member.identity_id].identity_sha256
                if _source_dataset_id
                else parent.content_sha256
            ):
                raise ValueError("dataset identity evidence drift")
        self.session.add(
            DatasetVersionRecord(
                id=manifest.dataset_id,
                language=manifest.language.value,
                kind=manifest.kind,
                namespace=manifest.namespace,
                owner_id=manifest.owner_id,
                version=manifest.version,
                payload=model_payload(manifest),
            )
        )
        self.session.flush()
        self.session.add_all(
            [
                DatasetMembershipRecord(
                    dataset_id=manifest.dataset_id,
                    identity_id=member.identity_id,
                    rank=member.rank,
                    identity_sha256=(
                        pinned_members[member.identity_id].identity_sha256
                        if _source_dataset_id
                        else parents[member.identity_id].content_sha256
                    ),
                )
                for member in manifest.members
            ]
        )
        forms = (
            self.session.scalars(
                select(DatasetFormMembership).where(
                    DatasetFormMembership.dataset_id == _source_dataset_id
                )
            )
            if _source_dataset_id
            else self.session.scalars(
                select(SurfaceFormRecord).where(SurfaceFormRecord.identity_id.in_(ids))
            )
        )
        self.session.add_all(
            [
                DatasetFormMembership(
                    dataset_id=manifest.dataset_id,
                    form_id=form.form_id if _source_dataset_id else form.id,
                    content_sha256=form.content_sha256,
                )
                for form in forms
            ]
        )
        self.record_event(
            DomainEvent(
                event_type="DatasetImported",
                entity_id=manifest.dataset_id,
                revision=1,
                actor=actor,
                reason=reason,
                after_sha256=manifest.dataset_id,
            )
        )
        return self.get_dataset(manifest.dataset_id, owner_id=manifest.owner_id)

    def get_dataset(self, dataset_id: str, *, owner_id: str = "") -> dict | None:
        row = self.session.get(DatasetVersionRecord, dataset_id)
        if row is None or row.owner_id != owner_id:
            return None
        return {**deepcopy(row.payload), "dataset_id": row.id}

    def dataset_identities(self, dataset_id: str, *, owner_id: str = "") -> list:
        """Resolve the exact immutable revisions captured by the dataset."""
        if self.get_dataset(dataset_id, owner_id=owner_id) is None:
            raise ValueError("unknown dataset")
        from multilang.domain.lexical_identity import LexicalIdentity

        rows = self.session.execute(
            select(LexicalIdentityRevision.payload)
            .join(
                DatasetMembershipRecord,
                (DatasetMembershipRecord.identity_id == LexicalIdentityRevision.identity_id)
                & (
                    DatasetMembershipRecord.identity_sha256
                    == LexicalIdentityRevision.content_sha256
                ),
            )
            .where(DatasetMembershipRecord.dataset_id == dataset_id)
            .order_by(DatasetMembershipRecord.rank)
        )
        identities = {}
        for (payload,) in rows:
            identity = LexicalIdentity.model_validate(payload)
            identities[identity.lexical_identity_id] = identity
        expected = self.session.scalars(
            select(DatasetMembershipRecord).where(DatasetMembershipRecord.dataset_id == dataset_id)
        ).all()
        if len(identities) != len(expected):
            raise ValueError("dataset identity revision missing or corrupted")
        return list(identities.values())

    def dataset_forms(self, dataset_id: str, *, owner_id: str = "") -> list:
        if self.get_dataset(dataset_id, owner_id=owner_id) is None:
            raise ValueError("unknown dataset")
        from multilang.domain.lexical_identity import SurfaceForm

        rows = self.session.execute(
            select(SurfaceFormRevision.payload)
            .join(
                DatasetFormMembership,
                (DatasetFormMembership.form_id == SurfaceFormRevision.form_id)
                & (DatasetFormMembership.content_sha256 == SurfaceFormRevision.content_sha256),
            )
            .where(DatasetFormMembership.dataset_id == dataset_id)
            .order_by(DatasetFormMembership.form_id)
        )
        forms = {}
        for (payload,) in rows:
            form = SurfaceForm.model_validate(payload)
            forms[form.surface_form_id] = form
        expected = self.session.scalar(
            select(func.count())
            .select_from(DatasetFormMembership)
            .where(DatasetFormMembership.dataset_id == dataset_id)
        )
        if len(forms) != expected:
            raise ValueError("dataset form revision missing or corrupted")
        return list(forms.values())

    def list_datasets(self, *, owner_id: str = "", limit: int = 100) -> list[dict]:
        if not 1 <= limit <= 500:
            raise ValueError("dataset limit must be 1..500")
        return [
            {
                "dataset_id": row.id,
                "language": row.language,
                "kind": row.kind,
                "namespace": row.namespace,
                "version": row.version,
                "member_count": len(row.payload["members"]),
            }
            for row in self.session.scalars(
                select(DatasetVersionRecord)
                .where(DatasetVersionRecord.owner_id == owner_id)
                .order_by(DatasetVersionRecord.language, DatasetVersionRecord.version)
                .limit(limit)
            )
        ]

    @staticmethod
    def _channel(language: str, kind: str, namespace: str, owner_id: str) -> str:
        return canonical_hash([language, kind, namespace, owner_id])

    def active_dataset(
        self, *, language: str, kind: str, namespace: str, owner_id: str = ""
    ) -> dict | None:
        row = self.session.get(
            DatasetHeadRecord, self._channel(language, kind, namespace, owner_id)
        )
        return None if row is None else self.get_dataset(row.dataset_id, owner_id=owner_id)

    def activate_dataset(
        self,
        dataset_id: str,
        *,
        actor: str,
        reason: str,
        production: bool = True,
        owner_id: str = "",
        expected_head: str | None = None,
    ) -> None:
        data = self.get_dataset(dataset_id, owner_id=owner_id)
        if data is None:
            raise ValueError("unknown dataset")
        manifest = DatasetManifest.model_validate(
            {k: v for k, v in data.items() if k != "dataset_id"}
        )
        if production:
            manifest.require_production()
        channel = self._channel(
            manifest.language.value, manifest.kind, manifest.namespace, manifest.owner_id
        )
        row = self.session.get(DatasetHeadRecord, channel)
        if row is not None and row.dataset_id == dataset_id:
            return
        if expected_head is not None and (row is None or row.dataset_id != expected_head):
            raise ValueError("dataset head conflict")
        before, revision = (row.dataset_id, row.revision + 1) if row else (None, 1)
        if row:
            result = self.session.execute(
                update(DatasetHeadRecord)
                .where(
                    DatasetHeadRecord.channel == channel, DatasetHeadRecord.revision == revision - 1
                )
                .values(dataset_id=dataset_id, revision=revision)
            )
            if result.rowcount != 1:
                raise ValueError("dataset head conflict")
        else:
            self.session.add(
                DatasetHeadRecord(channel=channel, dataset_id=dataset_id, revision=revision)
            )
        self.record_event(
            DomainEvent(
                event_type="DatasetActivated",
                entity_id=channel,
                revision=revision,
                actor=actor,
                reason=reason,
                before_sha256=before,
                after_sha256=dataset_id,
            )
        )

    def compare_datasets(self, before_id: str, after_id: str, *, owner_id: str = "") -> dict:
        before, after = (
            self.get_dataset(before_id, owner_id=owner_id),
            self.get_dataset(after_id, owner_id=owner_id),
        )
        if before is None or after is None:
            raise ValueError("unknown dataset")
        if any(before[key] != after[key] for key in ("language", "kind", "namespace", "owner_id")):
            raise ValueError("cannot compare unrelated dataset channels")
        old = {item["identity_id"]: item for item in before["members"]}
        new = {item["identity_id"]: item for item in after["members"]}
        return {
            "added": sorted(new.keys() - old.keys()),
            "removed": sorted(old.keys() - new.keys()),
            "changed": sorted(key for key in new.keys() & old.keys() if old[key] != new[key]),
        }

    def save_content(
        self,
        *,
        version_id: str,
        identity_id: str,
        namespace: str,
        owner_id: str,
        edition_id: str,
        payload: dict,
        search_text: str,
        actor: str,
    ) -> dict:
        _namespace_owner(namespace, owner_id)
        if self.session.get(LexicalIdentityRecord, identity_id) is None:
            raise ValueError("unknown identity")
        digest = canonical_hash(payload)
        row = self.session.get(ContentVersionRecord, version_id)
        if row is not None:
            if (
                row.content_sha256,
                row.owner_id,
                row.namespace,
                row.identity_id,
                row.edition_id,
            ) != (digest, owner_id, namespace, identity_id, edition_id):
                raise ValueError("content version is immutable")
            return deepcopy(row.payload)
        self.session.add(
            ContentVersionRecord(
                id=version_id,
                identity_id=identity_id,
                namespace=namespace,
                owner_id=owner_id,
                edition_id=edition_id,
                content_sha256=digest,
                search_text=search_text,
                payload=deepcopy(payload),
            )
        )
        self.record_event(
            DomainEvent(
                event_type="ContentGenerated",
                entity_id=version_id,
                revision=1,
                actor=actor,
                reason="enrichment",
                after_sha256=digest,
            )
        )
        return deepcopy(payload)

    def save_audio(
        self,
        *,
        version_id: str,
        signature_sha256: str,
        namespace: str,
        owner_id: str,
        payload: dict,
        actor: str,
    ) -> dict:
        _namespace_owner(namespace, owner_id)
        digest = canonical_hash(payload)
        row = self.session.get(AudioVersionRecord, version_id)
        if row is not None:
            if (row.content_sha256, row.namespace, row.owner_id, row.signature_sha256) != (
                digest,
                namespace,
                owner_id,
                signature_sha256,
            ):
                raise ValueError("audio version is immutable")
            return deepcopy(row.payload)
        self.session.add(
            AudioVersionRecord(
                id=version_id,
                signature_sha256=signature_sha256,
                namespace=namespace,
                owner_id=owner_id,
                content_sha256=digest,
                payload=deepcopy(payload),
            )
        )
        self.record_event(
            DomainEvent(
                event_type="AudioGenerated",
                entity_id=version_id,
                revision=1,
                actor=actor,
                reason="synthesis",
                after_sha256=digest,
            )
        )
        return deepcopy(payload)

    def find_audio(self, signature_sha256: str, *, owner_id: str = "") -> list[dict]:
        return [
            deepcopy(row.payload)
            for row in self.session.scalars(
                select(AudioVersionRecord).where(
                    AudioVersionRecord.signature_sha256 == signature_sha256,
                    AudioVersionRecord.owner_id == owner_id,
                )
            )
        ]

    def freeze_edition(self, edition, *, actor: str, verifier) -> dict:
        from multilang.domain.editions import DeckEdition

        edition = DeckEdition.model_validate(edition.model_dump(mode="json"))
        self.edition_cards(edition, production=True)
        if verifier is None or not verifier(edition):
            raise ValueError("edition freeze requires independently verified evidence")
        previous = self.session.get(DeckEditionRecord, edition.edition_id)
        if previous is not None:
            if previous.bundle_sha256 != edition.bundle_sha256:
                raise ValueError("canonical edition is immutable; create a new edition")
            return deepcopy(previous.payload)
        self.session.add(
            DeckEditionRecord(
                id=edition.edition_id,
                dataset_id=edition.dataset_id,
                bundle_sha256=edition.bundle_sha256,
                payload=model_payload(edition),
            )
        )
        self.record_event(
            DomainEvent(
                event_type="EditionFrozen",
                entity_id=edition.edition_id,
                revision=1,
                actor=actor,
                reason="independent_review",
                after_sha256=edition.bundle_sha256,
            )
        )
        return model_payload(edition)

    def get_edition(self, edition_id: str):
        from multilang.domain.editions import DeckEdition

        row = self.session.get(DeckEditionRecord, edition_id)
        if row is None:
            raise ValueError("unknown canonical edition")
        edition = DeckEdition.model_validate(row.payload)
        if edition.bundle_sha256 != row.bundle_sha256:
            raise ValueError("canonical edition integrity failed")
        return edition

    def edition_cards(self, edition, *, production: bool = True):
        from multilang.domain.anki_semantics import SemanticCard
        from multilang.domain.audio_version import AudioVersion
        from multilang.domain.content import ContentVersion
        from multilang.services.native_audio import reusable_audio_version
        from multilang.services.native_validation import ContentValidator
        from multilang.services.semantic_anki import project_cards

        dataset = self.get_dataset(edition.dataset_id)
        if dataset is None:
            raise ValueError("unknown edition dataset")
        manifest = DatasetManifest.model_validate(dataset)
        if production:
            manifest.require_production()
            if manifest.kind != "ranking" or edition.important_form_policy is None:
                raise ValueError(
                    "production edition needs corpus ranking and important-form policy"
                )
        forms = self.dataset_forms(edition.dataset_id)
        selected = (
            edition.important_form_policy.select(forms) if edition.important_form_policy else ()
        )
        pinned_identities = self.dataset_identities(edition.dataset_id)
        grounding_hashes = {
            identity.lexical_identity_id: canonical_hash(model_payload(identity))
            for identity in pinned_identities
        }
        cards = project_cards(
            identities=pinned_identities,
            approved_forms=selected,
            ranks={member.identity_id: member.rank for member in manifest.members},
            deck_edition_id=edition.edition_id,
            inventory=manifest.namespace,
            optional_roles=edition.optional_roles,
        )
        bindings = {binding.card_id: binding for binding in edition.bindings}
        if set(bindings) != {card.card_id for card in cards}:
            raise ValueError(
                "edition bindings must cover all headwords, approved forms and optional roles"
            )
        content_ids = [item.content_version_id for item in edition.bindings]
        audio_ids = [
            key
            for item in edition.bindings
            for key in (item.word_audio_version_id, item.sentence_audio_version_id)
        ]
        contents = {
            row.id: row
            for row in self.session.scalars(
                select(ContentVersionRecord).where(ContentVersionRecord.id.in_(content_ids))
            )
        }
        audios = {
            row.id: row
            for row in self.session.scalars(
                select(AudioVersionRecord).where(AudioVersionRecord.id.in_(audio_ids))
            )
        }
        results = []
        for card in cards:
            binding = bindings[card.card_id]
            content_row = contents.get(binding.content_version_id)
            word_row, sentence_row = (
                audios.get(binding.word_audio_version_id),
                audios.get(binding.sentence_audio_version_id),
            )
            if not content_row or not word_row or not sentence_row:
                raise ValueError("edition references missing content/audio version")
            if any(row.owner_id for row in (content_row, word_row, sentence_row)):
                raise ValueError("private data cannot enter a shared canonical edition")
            content = ContentVersion.model_validate(content_row.payload)
            if (
                content.request.grounding_sha256
                != grounding_hashes[card.parent_lexical_identity_id]
            ):
                raise ValueError(
                    "content grounding differs from the edition's pinned source revision"
                )
            ContentValidator().validate(content, require_review=production).require_valid()
            word, sentence = (
                AudioVersion.model_validate(word_row.payload),
                AudioVersion.model_validate(sentence_row.payload),
            )
            if (
                content.version_id != content_row.id
                or word.version_id != word_row.id
                or sentence.version_id != sentence_row.id
            ):
                raise ValueError("edition version hash drift")
            if production and any(
                version.review_status != "approved" for version in (content, word, sentence)
            ):
                raise ValueError("all edition content/audio requires independent approval")
            for audio in (word, sentence):
                if not reusable_audio_version(audio.signature, audio, namespace="core"):
                    raise ValueError("edition audio integrity failed")
            results.append(
                SemanticCard.model_validate(
                    card.model_dump(mode="json")
                    | {"content": content, "word_audio": word, "sentence_audio": sentence}
                )
            )
        return tuple(results)

    def save_user_state(self, *, owner_id: str, key: str, payload: dict) -> None:
        if not owner_id or not key or len(owner_id) > 128 or len(key) > 128:
            raise ValueError("owner/key is required and bounded")
        canonical_hash(payload)
        row = self.session.get(UserStateRecord, (owner_id, key))
        if row:
            row.revision += 1
            row.payload = deepcopy(payload)
        else:
            self.session.add(
                UserStateRecord(owner_id=owner_id, key=key, revision=1, payload=deepcopy(payload))
            )
        self.session.flush()

    def get_user_state(self, *, owner_id: str, key: str) -> dict | None:
        row = self.session.get(UserStateRecord, (owner_id, key))
        return deepcopy(row.payload) if row else None

    def delete_user_data(self, *, owner_id: str, actor: str) -> None:
        if not owner_id:
            raise ValueError("cannot delete shared data")
        has_data = any(
            self.session.scalar(
                select(func.count()).select_from(model).where(model.owner_id == owner_id)
            )
            for model in (
                UserStateRecord,
                ContentVersionRecord,
                AudioVersionRecord,
                DatasetVersionRecord,
            )
        )
        if not has_data:
            return
        digest = canonical_hash(["user", owner_id])
        revision = (
            int(
                self.session.scalar(
                    select(func.max(AuditLog.revision)).where(
                        AuditLog.entity_id == digest, AuditLog.action == "UserDataDeleted"
                    )
                )
                or 0
            )
            + 1
        )
        for model in (UserStateRecord, ContentVersionRecord, AudioVersionRecord):
            self.session.execute(delete(model).where(model.owner_id == owner_id))
        private_ids = select(DatasetVersionRecord.id).where(
            DatasetVersionRecord.owner_id == owner_id
        )
        self.session.execute(
            delete(DatasetHeadRecord).where(DatasetHeadRecord.dataset_id.in_(private_ids))
        )
        self.session.execute(
            delete(DatasetMembershipRecord).where(
                DatasetMembershipRecord.dataset_id.in_(private_ids)
            )
        )
        self.session.execute(
            delete(DatasetFormMembership).where(DatasetFormMembership.dataset_id.in_(private_ids))
        )
        self.session.execute(
            delete(DatasetVersionRecord).where(DatasetVersionRecord.owner_id == owner_id)
        )
        self.record_event(
            DomainEvent(
                event_type="UserDataDeleted",
                entity_id=digest,
                revision=revision,
                actor=actor,
                reason="consent_revoked",
                after_sha256=canonical_hash([]),
            )
        )

    def search(
        self,
        query: str,
        *,
        language: str | None = None,
        limit: int = 50,
        owner_id: str | None = None,
        min_rank: int | None = None,
        max_rank: int | None = None,
    ) -> list[dict]:
        if not 1 <= limit <= 500 or len(query) > 512:
            raise ValueError("search query/limit exceeded")
        normalized = unicodedata.normalize("NFC", query.strip()).casefold()
        # Literal wildcard escaping is essential for a query like '%'.
        pattern = (
            "%" + normalized.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        )
        form_match = exists(
            select(SurfaceFormRecord.id).where(
                SurfaceFormRecord.identity_id == LexicalIdentityRecord.id,
                SurfaceFormRecord.normalized_text.ilike(pattern, escape="\\"),
            )
        )
        meaning_match = exists(
            select(ContentVersionRecord.id).where(
                ContentVersionRecord.identity_id == LexicalIdentityRecord.id,
                ContentVersionRecord.owner_id.in_(["", owner_id] if owner_id else [""]),
                ContentVersionRecord.search_text.ilike(pattern, escape="\\"),
            )
        )
        statement = select(LexicalIdentityRecord).where(
            or_(
                LexicalIdentityRecord.normalized_lemma.ilike(pattern, escape="\\"),
                LexicalIdentityRecord.sense_id.ilike(pattern, escape="\\"),
                form_match,
                meaning_match,
            )
        )
        if language is not None:
            statement = statement.where(LexicalIdentityRecord.language == language)
        if min_rank is not None or max_rank is not None:
            rank_match = (
                select(DatasetMembershipRecord.identity_id)
                .join(
                    DatasetHeadRecord,
                    DatasetHeadRecord.dataset_id == DatasetMembershipRecord.dataset_id,
                )
                .join(
                    DatasetVersionRecord,
                    DatasetVersionRecord.id == DatasetMembershipRecord.dataset_id,
                )
                .where(
                    DatasetMembershipRecord.identity_id == LexicalIdentityRecord.id,
                    DatasetVersionRecord.owner_id == "",
                    DatasetVersionRecord.namespace.in_(("core", "expansion")),
                )
            )
            if min_rank is not None:
                rank_match = rank_match.where(DatasetMembershipRecord.rank >= min_rank)
            if max_rank is not None:
                rank_match = rank_match.where(DatasetMembershipRecord.rank <= max_rank)
            statement = statement.where(exists(rank_match))
        rows = self.session.scalars(
            statement.order_by(
                LexicalIdentityRecord.language,
                LexicalIdentityRecord.normalized_lemma,
                LexicalIdentityRecord.id,
            ).limit(limit)
        )
        return [
            {
                "lexical_identity_id": row.id,
                "language": row.language,
                "normalized_lemma": row.normalized_lemma,
                "part_of_speech": row.part_of_speech,
                "sense_id": row.sense_id,
                "revision": row.revision,
            }
            for row in rows
        ]
