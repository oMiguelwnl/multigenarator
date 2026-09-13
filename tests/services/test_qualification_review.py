"""Synthetic local review authority; no test approves real linguistic evidence."""

import hashlib
import json
from datetime import UTC, datetime, timedelta

import pytest


def api():
    from multilang.services import qualification_review

    return qualification_review


def packet(*, split="calibration", text="I went."):
    m = api()
    source = m.ReviewSource(
        source_id="synthetic",
        source_sha256="a" * 64,
        record_id="source-1",
        document_id="doc-1",
        sentence_id="sentence-1",
        excerpt=text,
    )
    return m.ReviewPacket(
        packet_id="fixture",
        language="en",
        split=split,
        profile_sha256="b" * 64,
        rubric_sha256="c" * 64,
        items=(
            m.LexicalReviewItem(
                item_id="lexical-1",
                sources=(source,),
                candidate_id="candidate-1",
                candidate_sha256="d" * 64,
                lemma="go",
                pos="VERB",
                glosses=("To move.",),
            ),
            m.FormReviewItem(
                item_id="form-1",
                sources=(source,),
                candidate_id="candidate-1",
                candidate_sha256="d" * 64,
                lemma="go",
                pos="VERB",
                text="went",
                features={"Tense": "Past"},
                measurements={"count": "2"},
                proposed_ratings={"frequency": "0.75"},
                missing_reasons=("sense_unresolved",),
            ),
            m.CaseReviewItem(
                item_id="case-1",
                sources=(source,),
                text=text,
                behavior_tags=("irregular",),
                proposal_tokens=(
                    m.ReviewToken(
                        start=2,
                        end=6,
                        text="went",
                        lemma="go",
                        pos="VERB",
                        features={"Tense": "Past"},
                    ),
                )
                if text == "I went."
                else (),
            ),
        ),
    )


def submission(p, *, reviewer="synthetic-reviewer", decisions=None):
    m = api()
    return m.HumanReviewSubmission(
        packet_sha256=p.packet_sha256,
        reviewer_id=reviewer,
        expertise_declaration="Synthetic test only",
        reviewed_at=datetime.now(UTC),
        decisions=decisions
        if decisions is not None
        else (
            m.FormDecision(
                item_id=p.items[1].item_id,
                item_sha256=p.items[1].item_sha256,
                decision="accepted",
                reason="Synthetic inclusion label",
                include=True,
                ratings={"irregularity": "1"},
            ),
        ),
    )


def write_json(path, value):
    path.write_text(value.model_dump_json(indent=2), encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def imported(tmp_path, p, s, **kwargs):
    m = api()
    pp, sp = tmp_path / "packet.json", tmp_path / "submission.json"
    return m.import_review(
        packet_path=pp,
        packet_sha256=write_json(pp, p),
        submission_path=sp,
        submission_sha256=write_json(sp, s),
        expected_reviewer="synthetic-reviewer",
        **kwargs,
    )


def test_partial_review_roundtrip_remains_an_explicit_draft(tmp_path):
    p = packet()
    result = imported(tmp_path, p, submission(p))
    assert result.status == "draft"
    assert result.pending_items == 2
    assert not result.production_eligible
    assert result.packet == p
    assert result.submission.decisions[0].include is True


def test_reviewed_analysis_confidence_is_optional_and_never_synthesized(tmp_path):
    p = packet()
    decision = submission(p).decisions[0]
    assert decision.analysis_confidence is None
    explicit = decision.model_copy(update={"analysis_confidence": "0.9"})
    result = imported(tmp_path, p, submission(p, decisions=(explicit,)))
    assert str(result.submission.decisions[0].analysis_confidence) == "0.9"
    assert result.authenticated is False


def test_export_writes_immutable_private_packet_and_safe_interactive_html(tmp_path):
    m = api()
    p = packet(
        split="evaluation", text="</script><img src=x onerror=alert(1)> café 한국어 __proto__"
    )
    destination = tmp_path / "review"
    manifest = m.export_review(p, destination)
    original = (destination / "packet.json").read_bytes()
    assert (
        m.load_review_packet(
            destination / "packet.json", expected_sha256=manifest.packet_file_sha256
        )
        == p
    )
    html = (destination / "review.html").read_text()
    assert "</script><img" not in html
    assert "connect-src 'none'" in html
    assert "textContent" in html
    assert "innerHTML" not in html
    assert 'id="resume"' in html and 'id="download"' in html
    assert (destination / "packet.json").stat().st_mode & 0o777 == 0o600
    with pytest.raises(ValueError, match="exists"):
        m.export_review(p, destination)
    assert (destination / "packet.json").read_bytes() == original


@pytest.mark.parametrize("change", ["packet", "item", "reviewer", "kind", "duplicate", "unknown"])
def test_review_binding_and_identity_fail_closed(tmp_path, change):
    m = api()
    p = packet()
    s = submission(p)
    data = s.model_dump(mode="json")
    if change == "packet":
        data["packet_sha256"] = "f" * 64
    elif change == "reviewer":
        data["reviewer_id"] = "other-reviewer"
    elif change == "duplicate":
        data["decisions"].append(data["decisions"][0])
    elif change == "item":
        data["decisions"][0]["item_sha256"] = "f" * 64
    elif change == "unknown":
        data["decisions"][0]["item_id"] = "missing"
    else:
        data["decisions"][0] = dict(
            kind="case",
            item_id=p.items[1].item_id,
            item_sha256=p.items[1].item_sha256,
            decision="inconclusive",
            reason="Wrong kind",
        )
    with pytest.raises(ValueError):
        imported(tmp_path, p, m.HumanReviewSubmission.model_validate(data))


def test_corrected_case_requires_exact_original_unicode_spans(tmp_path):
    m = api()
    p = packet()
    decision = m.CaseDecision(
        item_id=p.items[2].item_id,
        item_sha256=p.items[2].item_sha256,
        decision="corrected",
        reason="Explicit corrected analysis",
        expected_match=True,
        corrected_tokens=(
            m.ReviewToken(start=2, end=6, text="went", lemma="go", pos="VERB", sense_id="motion"),
        ),
    )
    assert imported(tmp_path, p, submission(p, decisions=(decision,))).status == "draft"
    bad = decision.model_copy(
        update={
            "corrected_tokens": (
                m.ReviewToken(start=1, end=5, text="went", lemma="go", pos="VERB"),
            )
        }
    )
    with pytest.raises(ValueError, match="span"):
        imported(tmp_path, p, submission(p, decisions=(bad,)))


def test_signed_review_requires_explicit_matching_signer_and_valid_purpose(tmp_path):
    from multilang.services.native_evidence import EvidenceStore, SignedEvidence

    m = api()
    p, root = packet(), tmp_path / "receipts"
    root.mkdir()
    s = submission(p)
    store = EvidenceStore(root, key=b"synthetic-test-key" * 4)
    for signer, purpose, expired, accepted in [
        ("synthetic-reviewer", "qualification-review", False, True),
        ("different-signer", "qualification-review", False, False),
        ("synthetic-reviewer", "vocabulary-form", False, False),
        ("synthetic-reviewer", "qualification-review", True, False),
    ]:
        receipt = SignedEvidence.sign(
            m.review_signing_payload(p, s),
            key=store.key,
            signer=signer,
            purpose=purpose,
            expires_at=datetime.now(UTC) + timedelta(days=-1 if expired else 1),
        )
        (root / f"{receipt.receipt_id}.json").write_text(receipt.model_dump_json())
        signed = s.model_copy(update={"receipt_id": receipt.receipt_id})
        if accepted:
            assert imported(tmp_path, p, signed, verifier=store).status == "authenticated"
        else:
            with pytest.raises(ValueError, match="receipt"):
                imported(tmp_path, p, signed, verifier=store)


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "-0.1", "1.1"])
def test_invalid_rating_rejected(bad):
    m = api()
    p = packet()
    with pytest.raises(ValueError):
        m.FormDecision(
            item_id="form-1",
            item_sha256=p.items[1].item_sha256,
            decision="accepted",
            reason="Invalid",
            include=True,
            ratings={"frequency": bad},
        )


def test_extra_fields_unknown_criteria_timezone_and_overlapping_tokens_rejected():
    p = packet()
    with pytest.raises(ValueError):
        p.model_copy(update={"production_eligible": True})
    with pytest.raises(ValueError):
        submission(p).model_copy(update={"reviewed_at": datetime(2026, 9, 13)})
    with pytest.raises(ValueError):
        p.items[1].model_copy(update={"proposed_ratings": {"__proto__": "0.5"}})
    with pytest.raises(ValueError, match="span"):
        p.items[2].model_copy(update={"proposal_tokens": p.items[2].proposal_tokens * 2})


def test_packet_and_submission_files_are_bounded_and_never_follow_symlinks(tmp_path):
    m = api()
    p, path = packet(), tmp_path / "original.json"
    digest = write_json(path, p)
    link = tmp_path / "link.json"
    link.symlink_to(path)
    with pytest.raises(ValueError, match="symlink"):
        m.load_review_packet(link, expected_sha256=digest)
    with pytest.raises(ValueError, match="checksum"):
        m.load_review_packet(path, expected_sha256="f" * 64)
    with pytest.raises(ValueError):
        m.ReviewPacket.model_validate({**p.model_dump(mode="json"), "unexpected": 1})


def test_duplicate_json_keys_are_not_silently_reinterpreted(tmp_path):
    m = api()
    path = tmp_path / "duplicate.json"
    path.write_text('{"schema_version": 1, "schema_version": 2}')
    with pytest.raises(ValueError, match="duplicate"):
        m.load_review_packet(path, expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def test_source_template_markers_cannot_replace_embedded_data(tmp_path):
    p = packet(text="{{SCRIPT}} {{STYLE}} {{CSP}} {{PACKET}}")
    api().export_review(p, tmp_path / "review")
    page = (tmp_path / "review" / "review.html").read_text()
    data = page.split('<script id="packet" type="application/json">', 1)[1].split("</script>", 1)[0]
    assert json.loads(data)["items"][2]["text"] == p.items[2].text


def test_packet_byte_limit_applies_before_parsing(tmp_path, monkeypatch):
    m = api()
    path = tmp_path / "too-large.json"
    digest = write_json(path, packet())
    monkeypatch.setattr(m, "_MAX_BYTES", 32)
    with pytest.raises(ValueError, match="bounded"):
        m.load_review_packet(path, expected_sha256=digest)


@pytest.mark.parametrize("sense", ["unknown", "UNRESOLVED", "none", "null", "?", "unk", "X"])
def test_sense_placeholders_cannot_become_reviewed_canonical_senses(sense):
    m = api()
    p = packet()
    for choice in (
        lambda: p.items[0].model_copy(update={"proposed_sense_id": sense}),
        lambda: p.items[1].model_copy(update={"canonical_sense_id": sense}),
        lambda: p.items[2].proposal_tokens[0].model_copy(update={"sense_id": sense}),
        lambda: submission(p).decisions[0].model_copy(update={"canonical_sense_id": sense}),
        lambda: m.LexicalDecision(
            item_id=p.items[0].item_id,
            item_sha256=p.items[0].item_sha256,
            decision="accepted",
            reason="Invalid placeholder",
            canonical_sense_id=sense,
        ),
    ):
        with pytest.raises(ValueError, match="resolved sense"):
            choice()


def test_form_proposal_pos_is_upos_and_unknown_values_remain_explicit():
    p = packet()
    for pos in ("X", "PUNCT", "SYM", "NOUN", "VERB"):
        assert p.items[1].model_copy(update={"pos": pos}).pos == pos
    with pytest.raises(ValueError, match="UPOS"):
        p.items[1].model_copy(update={"pos": "MADEUP"})


def test_native_morpheme_feature_is_preserved_beyond_short_identifier_limits(tmp_path):
    p = packet()
    native_feature = json.dumps(
        [{"form": "학교", "pos": "NNG", "evidence": "a" * 1200}], ensure_ascii=False
    )
    form = p.items[1].model_copy(update={"features": {"Morphemes": native_feature}})
    updated = p.model_copy(update={"items": (p.items[0], form, p.items[2])})
    path = tmp_path / "packet.json"
    digest = write_json(path, updated)
    loaded = api().load_review_packet(path, expected_sha256=digest)
    assert loaded.items[1].features["Morphemes"] == native_feature
    with pytest.raises(ValueError):
        form.model_copy(update={"features": {"Morphemes": "a" * 64001}})


def test_full_measurement_source_keys_are_immutable_and_not_editable_decisions():
    m = api()
    p = packet()
    assert "evidence_source_keys" not in p.items[1].model_dump(mode="json")
    item = p.items[1].model_copy(update={"evidence_source_keys": ("a" * 64, "b" * 64)})
    assert item.evidence_source_keys == ("a" * 64, "b" * 64)
    assert item.item_sha256 != p.items[1].item_sha256
    with pytest.raises(ValueError):
        m.FormDecision.model_validate(
            {
                **submission(p).decisions[0].model_dump(mode="json"),
                "evidence_source_keys": ["a" * 64],
            }
        )
