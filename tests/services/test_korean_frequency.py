"""Strict Korean frequency source and bundle contract tests."""

from __future__ import annotations

import json
import importlib.util
from pathlib import Path

import pytest


_HASH_A = "a" * 64
_HASH_B = "b" * 64
_HASH_C = "c" * 64
_HASH_D = "d" * 64
_HASH_E = "e" * 64
_HASH_F = "f" * 64
_HASH_1 = "1" * 64
_HASH_2 = "2" * 64


def _fingerprint():
    from multilang.domain.korean import KoreanAnalyzerFingerprint

    return KoreanAnalyzerFingerprint(
        analyzer_name="kiwi",
        analyzer_package_version="0.23.2",
        model_package_version="0.23.0",
        model_type="cong",
        enabled_dialects="standard",
        num_workers=1,
        integrate_allomorph=True,
        top_n=2,
        split_complex=False,
        compatible_jamo=False,
        normalize_coda=False,
        z_coda=False,
        typos=None,
        oov_handling="chr",
        policy_version="kiwi-top2-consensus-v1",
    )


def _identity(*, lemma: str = "학교", pos: str = "NNG", sense_id: str = "nikl:1"):
    from multilang.domain.korean import KoreanLexicalIdentity, KoreanSignatureItem

    return KoreanLexicalIdentity(
        submitted_form=lemma,
        canonical_nfc=lemma,
        lemma=lemma,
        part_of_speech=pos,
        sense_id=sense_id,
        register="standard",
        morpheme_signature=(KoreanSignatureItem(form=lemma.removesuffix("다") or lemma, pos=pos),),
        analyzer_fingerprint=_fingerprint(),
        status="resolved",
    )


def _entry(**overrides):
    from multilang.domain.korean import KoreanFrequencyEntry

    values = {
        "language": "ko",
        "version": "nikl-ko-learners-v1",
        "level": 1,
        "final_rank": 1,
        "source_rank": 1,
        "source_provenance": "nikl-korean-learners-vocabulary",
        "source_version": "2003-06-04.revised-2019-05-30",
        "license_decision": "approved-local-use",
        "storage_disposition": "private-local-only",
        "curation_decision": "accepted",
        "curation_flags": ("source_rank_preserved", "modernity_review_required"),
        "grounding_confidence": "source-backed",
        "bundle_sha256": _HASH_A,
        "retrieval_sha256": _HASH_B,
        "analyzer_fingerprint": _fingerprint(),
        "lexical_identity": _identity(),
    }
    values.update(overrides)
    return KoreanFrequencyEntry(**values)


def test_contract_canonical_json_hash_is_stable_and_content_based() -> None:
    from multilang.domain.korean import canonical_json_sha256

    left = {"b": [2, {"x": "학교"}], "a": 1}
    right = {"a": 1, "b": [2, {"x": "학교"}]}

    assert canonical_json_sha256(left) == canonical_json_sha256(right)
    assert canonical_json_sha256(left) != canonical_json_sha256({"a": 1, "b": [2, {"x": "학교들"}]})


def test_retrieval_contract_separates_landing_attachment_and_source_bytes() -> None:
    from multilang.domain.korean import KoreanFrequencyRetrievalResult

    result = KoreanFrequencyRetrievalResult(
        source_id="nikl-korean-learners-vocabulary",
        landing_url="https://www.korean.go.kr/front/etcData/etcDataView.do?mn_id=46&etc_seq=70",
        accepted_filename="한국어 학습용 어휘 목록.txt",
        landing_sha256=_HASH_A,
        attachment_url="https://www.korean.go.kr/front/etcData/etcDataFileDownload.do?etc_seq=70&file_seq=1",
        attachment_sha256=_HASH_B,
        source_bytes_sha256=_HASH_C,
        source_byte_count=12345,
        retrieved_at="2026-08-28T00:00:00Z",
        text_encoding="utf-8",
        schema_version="nikl-frequency-retrieval-v1",
    )

    assert result.accepted_filename == "한국어 학습용 어휘 목록.txt"
    assert result.grants_transform_power is False

    with pytest.raises(ValueError):
        KoreanFrequencyRetrievalResult(
            **(result.model_dump() | {"accepted_filename": "한국어 학습용 어휘 목록.xls"})
        )

    with pytest.raises(ValueError):
        KoreanFrequencyRetrievalResult(
            **(result.model_dump() | {"landing_url": "https://evil.example/front/etcData/etcDataView.do?mn_id=46&etc_seq=70"})
        )


def test_build_result_requires_retrieval_binding_and_no_activation_power() -> None:
    from multilang.domain.korean import KoreanFrequencyBuildResult, KoreanFrequencyBuildPolicy

    policy = KoreanFrequencyBuildPolicy(
        source_id="nikl-korean-learners-vocabulary",
        source_version="2003-06-04.revised-2019-05-30",
        allowed_use="local-generation",
        redistribution="not-approved",
        attribution_required=True,
        storage_disposition="private-local-only",
        retrieval_sha256=_HASH_B,
        source_bytes_sha256=_HASH_C,
        analyzer_fingerprint=_fingerprint(),
    )
    result = KoreanFrequencyBuildResult(
        policy=policy,
        retrieval_sha256=_HASH_B,
        source_bytes_sha256=_HASH_C,
        accepted_count=3000,
        rejection_count=2965,
        level_counts={1: 1000, 2: 1000, 3: 1000},
        inventory_sha256=_HASH_D,
        rejection_sha256=_HASH_E,
        report_sha256=_HASH_F,
        bundle_sha256=_HASH_A,
        active=False,
    )

    assert result.total_source_dispositions == 5965
    assert result.grants_runtime_activation is False

    with pytest.raises(ValueError):
        KoreanFrequencyBuildResult(**(result.model_dump(mode="python") | {"source_bytes_sha256": _HASH_D}))

    with pytest.raises(ValueError):
        KoreanFrequencyBuildResult(**(result.model_dump(mode="python") | {"active": True}))


def test_identity_contract_rejects_unresolved_pos_sense_and_function_morphemes() -> None:
    assert _entry().lexical_identity.lexical_key.startswith("ko:")

    with pytest.raises(ValueError):
        _entry(lexical_identity=_identity(pos="JKS", sense_id="nikl:particle"))

    with pytest.raises(ValueError):
        _entry(lexical_identity=_identity(sense_id="unknown"))

    with pytest.raises(ValueError):
        _entry(analyzer_fingerprint=_fingerprint().model_copy(update={"analyzer_package_version": "0.23.1"}))


def test_accounting_requires_3000_unique_identities_and_2965_rejections() -> None:
    from multilang.domain.korean import validate_korean_frequency_accounting

    entries = tuple(
        _entry(
            final_rank=rank,
            source_rank=rank,
            level=((rank - 1) // 1000) + 1,
            lexical_identity=_identity(
                lemma=f"어휘{rank}",
                pos="NNG",
                sense_id=f"nikl:{rank}",
            ),
        )
        for rank in range(1, 3001)
    )
    result = validate_korean_frequency_accounting(
        entries,
        source_candidate_count=5965,
        rejection_count=2965,
    )

    assert result == {1: 1000, 2: 1000, 3: 1000}

    duplicate = list(entries)
    duplicate[1] = duplicate[1].model_copy(update={"lexical_identity": duplicate[0].lexical_identity})
    with pytest.raises(ValueError):
        validate_korean_frequency_accounting(tuple(duplicate), source_candidate_count=5965, rejection_count=2965)

    with pytest.raises(ValueError):
        validate_korean_frequency_accounting(entries[:-1], source_candidate_count=5965, rejection_count=2966)


def test_authority_separation_blocks_synthetic_as_production_and_extra_fields() -> None:
    from multilang.domain.korean import KoreanFrequencyBundleManifest, KoreanFrequencyBundleMember

    member = KoreanFrequencyBundleMember(
        relative_path="curated-v1.csv",
        sha256=_HASH_1,
        byte_count=100,
        row_count=3000,
        kind="curated-inventory",
    )
    manifest = KoreanFrequencyBundleManifest(
        schema_version="korean-frequency-bundle-v1",
        language="ko",
        version="nikl-ko-learners-v1",
        source_id="nikl-korean-learners-vocabulary",
        source_version="2003-06-04.revised-2019-05-30",
        license_decision="approved-local-use",
        storage_disposition="private-local-only",
        synthetic=False,
        analyzer_fingerprint=_fingerprint(),
        members=(member,),
        inventory_sha256=_HASH_1,
        rejection_sha256=_HASH_2,
        report_sha256=_HASH_A,
        bundle_sha256=_HASH_B,
        level_counts={1: 1000, 2: 1000, 3: 1000},
        entry_count=3000,
        rejection_count=2965,
    )

    assert manifest.production_eligible is False

    with pytest.raises(ValueError):
        KoreanFrequencyBundleManifest(**(manifest.model_dump(mode="python") | {"synthetic": True, "storage_disposition": "repository-redistributable"}))

    payload = manifest.model_dump(mode="python") | {"private_path": "/home/user/source.txt"}
    with pytest.raises(ValueError):
        KoreanFrequencyBundleManifest(**payload)

    serialized = json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False)
    assert "/home" not in serialized


class _FakeResponse:
    def __init__(self, payload: bytes, *, headers: dict[str, str] | None = None, url: str | None = None) -> None:
        self._payload = payload
        self.headers = headers or {}
        self.url = url

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, limit: int = -1) -> bytes:
        if limit < 0:
            return self._payload
        chunk, self._payload = self._payload[:limit], self._payload[limit:]
        return chunk

    def geturl(self) -> str:
        return self.url or ""


def test_resolver_derives_exact_attachment_from_official_landing_response() -> None:
    from multilang.services.korean_frequency import resolve_nikl_frequency_attachment_url

    html = """
    <html><body>
      <a href="/front/etcData/etcDataFileDownload.do?etc_seq=70&file_seq=1">한국어 학습용 어휘 목록.txt</a>
    </body></html>
    """.encode()

    result = resolve_nikl_frequency_attachment_url(html)

    assert result == "https://www.korean.go.kr/front/etcData/etcDataFileDownload.do?etc_seq=70&file_seq=1"


def test_attachment_resolution_rejects_ambiguous_or_unofficial_targets() -> None:
    from multilang.services.korean_frequency import resolve_nikl_frequency_attachment_url

    ambiguous = b"""
    <a href="/front/etcData/etcDataFileDownload.do?etc_seq=70&file_seq=1">\xed\x95\x9c\xea\xb5\xad\xec\x96\xb4 \xed\x95\x99\xec\x8a\xb5\xec\x9a\xa9 \xec\x96\xb4\xed\x9c\x98 \xeb\xaa\xa9\xeb\xa1\x9d.txt</a>
    <a href="/front/etcData/etcDataFileDownload.do?etc_seq=70&file_seq=2">\xed\x95\x9c\xea\xb5\xad\xec\x96\xb4 \xed\x95\x99\xec\x8a\xb5\xec\x9a\xa9 \xec\x96\xb4\xed\x9c\x98 \xeb\xaa\xa9\xeb\xa1\x9d.txt</a>
    """
    unofficial = b"<a href='https://evil.example/download.txt'>\xed\x95\x9c\xea\xb5\xad\xec\x96\xb4 \xed\x95\x99\xec\x8a\xb5\xec\x9a\xa9 \xec\x96\xb4\xed\x9c\x98 \xeb\xaa\xa9\xeb\xa1\x9d.txt</a>"

    for html in (ambiguous, unofficial):
        with pytest.raises(ValueError):
            resolve_nikl_frequency_attachment_url(html)


def test_bounded_retrieval_installs_valid_txt_and_result_after_validation(tmp_path: Path) -> None:
    from multilang.services.korean_frequency import KoreanFrequencySourceRetriever

    landing = b"<a href='/front/etcData/etcDataFileDownload.do?etc_seq=70&file_seq=1'>\xed\x95\x9c\xea\xb5\xad\xec\x96\xb4 \xed\x95\x99\xec\x8a\xb5\xec\x9a\xa9 \xec\x96\xb4\xed\x9c\x98 \xeb\xaa\xa9\xeb\xa1\x9d.txt</a>"
    source = "1\t학교\tNNG\tplace of learning\n2\t가다\tVV\tto go\n".encode("utf-8")
    calls: list[str] = []

    def fake_urlopen(request: object, timeout: int):
        url = getattr(request, "full_url", str(request))
        calls.append(url)
        if "etcDataView" in url:
            return _FakeResponse(landing, headers={"Content-Type": "text/html; charset=utf-8"}, url=url)
        return _FakeResponse(
            source,
            headers={
                "Content-Type": "text/plain; charset=utf-8",
                "Content-Disposition": "attachment; filename*=UTF-8''%ED%95%9C%EA%B5%AD%EC%96%B4%20%ED%95%99%EC%8A%B5%EC%9A%A9%20%EC%96%B4%ED%9C%98%20%EB%AA%A9%EB%A1%9D.txt",
            },
            url=url,
        )

    result, result_path = KoreanFrequencySourceRetriever(urlopen=fake_urlopen).retrieve_to_directory(tmp_path)

    assert calls == [
        "https://www.korean.go.kr/front/etcData/etcDataView.do?mn_id=46&etc_seq=70",
        "https://www.korean.go.kr/front/etcData/etcDataFileDownload.do?etc_seq=70&file_seq=1",
    ]
    assert result.source_byte_count == len(source)
    assert result_path.name == "retrieval-result.json"
    assert (tmp_path / "source.txt").read_bytes() == source


def test_bounded_retrieval_cleans_only_quarantine_temp_on_attachment_failure(tmp_path: Path) -> None:
    from multilang.services.korean_frequency import KoreanFrequencySourceRetriever

    keep = tmp_path / "keep.txt"
    keep.write_text("keep", encoding="utf-8")
    landing = b"<a href='/front/etcData/etcDataFileDownload.do?etc_seq=70&file_seq=1'>\xed\x95\x9c\xea\xb5\xad\xec\x96\xb4 \xed\x95\x99\xec\x8a\xb5\xec\x9a\xa9 \xec\x96\xb4\xed\x9c\x98 \xeb\xaa\xa9\xeb\xa1\x9d.txt</a>"

    def fake_urlopen(request: object, timeout: int):
        url = getattr(request, "full_url", str(request))
        if "etcDataView" in url:
            return _FakeResponse(landing, url=url)
        return _FakeResponse(b"not a tabular source", headers={"Content-Type": "text/plain; charset=utf-8"}, url=url)

    with pytest.raises(ValueError):
        KoreanFrequencySourceRetriever(urlopen=fake_urlopen).retrieve_to_directory(tmp_path)

    assert keep.read_text(encoding="utf-8") == "keep"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["keep.txt"]


def test_retrieval_result_validation_recomputes_source_bytes_read_only(tmp_path: Path) -> None:
    from multilang.domain.korean import KoreanFrequencyRetrievalResult, raw_bytes_sha256
    from multilang.services.korean_frequency import validate_korean_source_retrieval_result

    source = "1\t학교\tNNG\tplace of learning\n".encode("utf-8")
    source_path = tmp_path / "source.txt"
    result_path = tmp_path / "retrieval-result.json"
    source_path.write_bytes(source)
    result = KoreanFrequencyRetrievalResult(
        source_id="nikl-korean-learners-vocabulary",
        landing_url="https://www.korean.go.kr/front/etcData/etcDataView.do?mn_id=46&etc_seq=70",
        accepted_filename="한국어 학습용 어휘 목록.txt",
        landing_sha256=_HASH_A,
        attachment_url="https://www.korean.go.kr/front/etcData/etcDataFileDownload.do?etc_seq=70&file_seq=1",
        attachment_sha256=_HASH_B,
        source_bytes_sha256=raw_bytes_sha256(source),
        source_byte_count=len(source),
        retrieved_at="2026-08-28T00:00:00Z",
        text_encoding="utf-8",
        schema_version="nikl-frequency-retrieval-v1",
    )
    result_path.write_text(result.model_dump_json(), encoding="utf-8")
    mtimes = (result_path.stat().st_mtime_ns, source_path.stat().st_mtime_ns)

    validated = validate_korean_source_retrieval_result(result_path, source_file=source_path)

    assert validated == result
    assert mtimes == (result_path.stat().st_mtime_ns, source_path.stat().st_mtime_ns)

    source_path.write_text("tampered\n", encoding="utf-8")
    with pytest.raises(ValueError):
        validate_korean_source_retrieval_result(result_path, source_file=source_path)


def _write_minimal_valid_build_tree(tmp_path: Path) -> tuple[Path, Path]:
    fixture_path = Path(__file__).resolve().parents[1] / "scripts" / "test_build_frequency_assets.py"
    fixture_spec = importlib.util.spec_from_file_location("test_build_frequency_assets", fixture_path)
    assert fixture_spec is not None and fixture_spec.loader is not None
    fixture_module = importlib.util.module_from_spec(fixture_spec)
    fixture_spec.loader.exec_module(fixture_module)
    module_path = Path(__file__).resolve().parents[2] / "scripts" / "build_frequency_assets.py"
    spec = importlib.util.spec_from_file_location("build_frequency_assets", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    build_korean_frequency_assets = module.build_korean_frequency_assets

    target_root = tmp_path / "bundles"
    inputs = fixture_module._fixture_inputs(tmp_path)
    result = build_korean_frequency_assets(**inputs, target_root=target_root)
    return target_root / "fixture-v1", target_root / "fixture-v1" / "build-result.json"


def test_build_validator_recomputes_manifest_member_hashes_and_root(
    tmp_path: Path,
) -> None:
    from multilang.services.korean_frequency import validate_korean_source_build_result

    bundle_dir, result_file = _write_minimal_valid_build_tree(tmp_path)

    result = validate_korean_source_build_result(result_file, bundle_dir=bundle_dir)

    assert result.active is False
    assert result.bundle_sha256

    (bundle_dir / "curated-inventory.jsonl").write_text("tampered\n", encoding="utf-8")
    with pytest.raises(ValueError):
        validate_korean_source_build_result(result_file, bundle_dir=bundle_dir)


def test_inactive_exact_existing_build_validation_is_read_only(tmp_path: Path) -> None:
    from multilang.services.korean_frequency import validate_korean_source_build_result

    bundle_dir, result_file = _write_minimal_valid_build_tree(tmp_path)
    before = {path.name: path.stat().st_mtime_ns for path in bundle_dir.iterdir()}

    result = validate_korean_source_build_result(result_file, bundle_dir=bundle_dir)

    assert result.grants_runtime_activation is False
    assert before == {path.name: path.stat().st_mtime_ns for path in bundle_dir.iterdir()}
