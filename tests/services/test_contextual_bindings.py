from datetime import UTC, datetime, timedelta

import pytest

from multilang.services.contextual_morphology import ReviewedSenseBinding
from multilang.services.native_evidence import EvidenceStore, SignedEvidence


def binding():
    return ReviewedSenseBinding(
        language="en",
        sentence_sha256="a" * 64,
        start=0,
        end=4,
        token_analysis_id="b" * 64,
        lexical_identity_id="lex:go",
        sense_id="movement",
        concept_id="concept:go",
        source_sha256="c" * 64,
        reviewer="fixture-reviewer",
        review_receipt_sha256="d" * 64,
    )


def sign(store, payload, purpose):
    receipt = SignedEvidence.sign(
        payload,
        key=store.key,
        signer="fixture-reviewer",
        purpose=purpose,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    store.root.mkdir(parents=True, exist_ok=True)
    (store.root / f"{receipt.receipt_id}.json").write_text(receipt.model_dump_json())
    return receipt.receipt_id


def signed_set(tmp_path, namespace="core"):
    from multilang.services.contextual_bindings import ContextualBindingSet

    evidence = EvidenceStore(
        tmp_path / "evidence", key=b"test-only-key-never-a-production-approval"
    )
    original = binding()
    receipt = sign(
        evidence,
        original.model_dump(mode="json", exclude={"review_receipt_sha256"}),
        "contextual-sense-binding",
    )
    original = original.model_copy(update={"review_receipt_sha256": receipt})
    values = dict(
        namespace=namespace,
        language="en",
        profile_version="1",
        bindings=(original,),
        receipt_sha256="e" * 64,
    )
    draft = ContextualBindingSet(**values)
    values["receipt_sha256"] = sign(
        evidence,
        draft.model_dump(mode="json", exclude={"receipt_sha256"}),
        "contextual-binding-set",
    )
    return ContextualBindingSet(**values), evidence


def test_binding_store_checks_signatures_and_preserves_namespace(tmp_path):
    from multilang.services.contextual_bindings import ReviewedBindingStore

    item, evidence = signed_set(tmp_path, "user:alice")
    store = ReviewedBindingStore(tmp_path / "bindings", verifier=evidence.verify)
    store.put(item)
    assert store.load("user:alice", "en", "a" * 64, "1") == item.bindings
    assert store.load("core", "en", "a" * 64, "1") == ()
    assert store.load("user:bob", "en", "a" * 64, "1") == ()
    assert store.load("user:alice", "en", "a" * 64, "2") == ()


def test_unsigned_or_reassigned_bindings_cannot_enter_store(tmp_path):
    from multilang.services.contextual_bindings import ReviewedBindingStore

    item, evidence = signed_set(tmp_path, "user:alice")
    store = ReviewedBindingStore(tmp_path / "bindings", verifier=evidence.verify)
    with pytest.raises(ValueError, match="signature"):
        store.put(item.model_copy(update={"namespace": "core"}))
    with pytest.raises(ValueError, match="signature"):
        store.put(item.model_copy(update={"receipt_sha256": "0" * 64}))


def test_binding_store_rejects_path_escape_and_symlinks(tmp_path):
    from multilang.services.contextual_bindings import ReviewedBindingStore

    item, evidence = signed_set(tmp_path)
    root = tmp_path / "bindings"
    root.symlink_to(tmp_path / "evidence", target_is_directory=True)
    store = ReviewedBindingStore(root, verifier=evidence.verify)
    with pytest.raises(ValueError, match="symlink"):
        store.put(item)
    with pytest.raises(ValueError):
        store.load("core", "en", "../outside", "1")


def test_runtime_registers_separate_local_matchers_without_downloading_models(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from multilang.native_runtime import build_native_facade
    from multilang.settings import Settings

    engine = create_engine("sqlite://")
    with Session(engine) as session:
        first = build_native_facade(
            session,
            Settings(
                _env_file=None,
                native_language_models_dir=tmp_path / "models-one",
                native_contextual_bindings_dir=tmp_path / "bindings-one",
            ),
        )
        second = build_native_facade(
            session,
            Settings(
                _env_file=None,
                native_language_models_dir=tmp_path / "models-two",
                native_contextual_bindings_dir=tmp_path / "bindings-two",
            ),
        )
        a = first.plugins.get("analyzer", "contextual-morphology-target", "1")
        b = second.plugins.get("analyzer", "contextual-morphology-target", "1")
        assert a is not b
        assert a.store.root == tmp_path / "bindings-one"
        assert b.store.root == tmp_path / "bindings-two"
        assert not (tmp_path / "models-one").exists()
    engine.dispose()


def test_runtime_rejects_another_owners_binding_before_persistence(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from multilang.native_runtime import build_native_facade
    from multilang.settings import Settings

    item, evidence = signed_set(tmp_path, "user:alice")
    engine = create_engine("sqlite://")
    with Session(engine) as session:
        facade = build_native_facade(
            session,
            Settings(
                _env_file=None,
                roadmap_4_enabled=True,
                native_contextual_bindings_dir=tmp_path / "bindings",
                native_evidence_dir=evidence.root,
                native_evidence_signing_key=evidence.key.decode(),
            ),
        )
        with pytest.raises(ValueError, match="owner"):
            facade.import_contextual_bindings(item.model_dump(mode="json"), actor="bob")
    assert not (tmp_path / "bindings").exists()
    engine.dispose()
