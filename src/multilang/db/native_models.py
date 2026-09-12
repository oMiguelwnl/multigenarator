"""Additive native tables on the existing Multilang SQLAlchemy metadata.

Tables are tagged so legacy startup cannot silently provision native persistence.
The Alembic revision is the production schema authority.
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from multilang.db.base import Base


class LanguageProfileRecord(Base):
    __tablename__ = "language_profiles"
    __table_args__ = (UniqueConstraint("language", "version"), {"info": {"native": True}})
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    language: Mapped[str] = mapped_column(String(8), index=True)
    version: Mapped[str] = mapped_column(String(64))
    content_sha256: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON)


class LexicalIdentityRecord(Base):
    __tablename__ = "lexical_identities"
    __table_args__ = (
        Index("ix_native_lexical_lookup", "language", "normalized_lemma"),
        {"info": {"native": True}},
    )
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    language: Mapped[str] = mapped_column(String(8))
    normalized_lemma: Mapped[str] = mapped_column(String(512))
    part_of_speech: Mapped[str] = mapped_column(String(64))
    sense_id: Mapped[str] = mapped_column(String(255))
    revision: Mapped[int] = mapped_column(Integer)
    content_sha256: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON)


class LexicalIdentityRevision(Base):
    __tablename__ = "lexical_identity_revisions"
    __table_args__ = {"info": {"native": True}}
    identity_id: Mapped[str] = mapped_column(ForeignKey("lexical_identities.id"), primary_key=True)
    revision: Mapped[int] = mapped_column(Integer, primary_key=True)
    content_sha256: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SurfaceFormRecord(Base):
    __tablename__ = "surface_forms"
    __table_args__ = {"info": {"native": True}}
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    identity_id: Mapped[str] = mapped_column(ForeignKey("lexical_identities.id"), index=True)
    analysis_id: Mapped[str] = mapped_column(String(128))
    normalized_text: Mapped[str] = mapped_column(String(512), index=True)
    content_sha256: Mapped[str] = mapped_column(String(64))
    revision: Mapped[int] = mapped_column(Integer, default=1)
    payload: Mapped[dict] = mapped_column(JSON)


class SurfaceFormRevision(Base):
    __tablename__ = "surface_form_revisions"
    __table_args__ = {"info": {"native": True}}
    form_id: Mapped[str] = mapped_column(ForeignKey("surface_forms.id"), primary_key=True)
    revision: Mapped[int] = mapped_column(Integer, primary_key=True)
    content_sha256: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON)


class DatasetVersionRecord(Base):
    __tablename__ = "dataset_versions"
    __table_args__ = (
        UniqueConstraint("language", "kind", "namespace", "owner_id", "version"),
        {"info": {"native": True}},
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    language: Mapped[str] = mapped_column(String(8), index=True)
    kind: Mapped[str] = mapped_column(String(32))
    namespace: Mapped[str] = mapped_column(String(32))
    owner_id: Mapped[str] = mapped_column(String(128), default="")
    version: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DatasetMembershipRecord(Base):
    __tablename__ = "dataset_memberships"
    __table_args__ = (UniqueConstraint("dataset_id", "rank"), {"info": {"native": True}})
    dataset_id: Mapped[str] = mapped_column(
        ForeignKey("dataset_versions.id", ondelete="CASCADE"), primary_key=True
    )
    identity_id: Mapped[str] = mapped_column(ForeignKey("lexical_identities.id"), primary_key=True)
    rank: Mapped[int] = mapped_column(Integer)
    identity_sha256: Mapped[str] = mapped_column(String(64))


class DatasetHeadRecord(Base):
    __tablename__ = "dataset_heads"
    __table_args__ = {"info": {"native": True}}
    channel: Mapped[str] = mapped_column(String(255), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("dataset_versions.id"))
    revision: Mapped[int] = mapped_column(Integer)


class DatasetFormMembership(Base):
    __tablename__ = "dataset_form_memberships"
    __table_args__ = {"info": {"native": True}}
    dataset_id: Mapped[str] = mapped_column(
        ForeignKey("dataset_versions.id", ondelete="CASCADE"), primary_key=True
    )
    form_id: Mapped[str] = mapped_column(ForeignKey("surface_forms.id"), primary_key=True)
    content_sha256: Mapped[str] = mapped_column(String(64))


class ContentVersionRecord(Base):
    __tablename__ = "content_versions"
    __table_args__ = (
        Index("ix_content_owner_identity", "owner_id", "identity_id"),
        {"info": {"native": True}},
    )
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    identity_id: Mapped[str] = mapped_column(ForeignKey("lexical_identities.id"))
    namespace: Mapped[str] = mapped_column(String(32))
    owner_id: Mapped[str] = mapped_column(String(128), default="")
    edition_id: Mapped[str] = mapped_column(String(128), index=True)
    content_sha256: Mapped[str] = mapped_column(String(64))
    search_text: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSON)


class DeckEditionRecord(Base):
    __tablename__ = "deck_editions"
    __table_args__ = {"info": {"native": True}}
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("dataset_versions.id"), index=True)
    bundle_sha256: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON)


class AudioVersionRecord(Base):
    __tablename__ = "audio_versions"
    __table_args__ = {"info": {"native": True}}
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    signature_sha256: Mapped[str] = mapped_column(String(64), index=True)
    namespace: Mapped[str] = mapped_column(String(32))
    owner_id: Mapped[str] = mapped_column(String(128), default="")
    content_sha256: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON)


class UserStateRecord(Base):
    __tablename__ = "user_state"
    __table_args__ = {"info": {"native": True}}
    owner_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    revision: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(JSON)


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = {"info": {"native": True}}
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    entity_id: Mapped[str] = mapped_column(String(255), index=True)
    action: Mapped[str] = mapped_column(String(64))
    actor: Mapped[str] = mapped_column(String(128))
    reason: Mapped[str] = mapped_column(String(128))
    revision: Mapped[int] = mapped_column(Integer)
    before_sha256: Mapped[str | None] = mapped_column(String(64))
    after_sha256: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DomainEventRecord(Base):
    __tablename__ = "domain_events"
    __table_args__ = {"info": {"native": True}}
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, index=True
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0)


class LegacyIdentityAlias(Base):
    __tablename__ = "legacy_identity_aliases"
    __table_args__ = {"info": {"native": True}}
    legacy_guid: Mapped[str] = mapped_column(String(128), primary_key=True)
    identity_id: Mapped[str] = mapped_column(ForeignKey("lexical_identities.id"), index=True)
    evidence_sha256: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON)


class MigrationJournalRecord(Base):
    __tablename__ = "migration_journal"
    __table_args__ = {"info": {"native": True}}
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_sha256: Mapped[str] = mapped_column(String(64))
    target_sha256: Mapped[str] = mapped_column(String(64))
    backup_sha256: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    payload: Mapped[dict] = mapped_column(JSON)
