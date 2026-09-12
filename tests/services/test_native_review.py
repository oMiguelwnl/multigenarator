import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.services.native_evidence import EvidenceStore
from multilang.services.native_review import NativeReviewService


def test_native_review_requires_signed_receipt_before_any_data_change(tmp_path):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            service = NativeReviewService(session, EvidenceStore(tmp_path, key=None))
            with pytest.raises(ValueError, match="signed evidence"):
                service.approve(
                    {"kind": "content", "version_id": "unknown", "receipt_sha256": "a" * 64},
                    actor="linguist",
                )
            assert not session.new
    finally:
        engine.dispose()
