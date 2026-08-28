"""CLI coverage for Korean frequency source retrieval commands."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

import multilang.cli as cli_module
from multilang.cli import create_app


runner = CliRunner()

_HASH = "a" * 64


def test_resolver_command_emits_content_free_retrieval_result(tmp_path: Path, monkeypatch) -> None:
    result_file = tmp_path / "retrieval-result.json"

    class FakeRetriever:
        def retrieve_to_directory(self, output_dir: Path):
            assert output_dir == tmp_path
            from multilang.domain.korean import KoreanFrequencyRetrievalResult

            output_dir.mkdir(exist_ok=True)
            result = KoreanFrequencyRetrievalResult(
                source_id="nikl-korean-learners-vocabulary",
                landing_url="https://www.korean.go.kr/front/etcData/etcDataView.do?mn_id=46&etc_seq=70",
                accepted_filename="한국어 학습용 어휘 목록.txt",
                landing_sha256=_HASH,
                attachment_url="https://www.korean.go.kr/front/etcData/etcDataFileDownload.do?etc_seq=70&file_seq=1",
                attachment_sha256="b" * 64,
                source_bytes_sha256="c" * 64,
                source_byte_count=100,
                retrieved_at="2026-08-28T00:00:00Z",
                text_encoding="utf-8",
                schema_version="nikl-frequency-retrieval-v1",
            )
            result_file.write_text(result.model_dump_json(), encoding="utf-8")
            return result, result_file

    monkeypatch.setattr(cli_module, "KoreanFrequencySourceRetriever", lambda: FakeRetriever())

    result = runner.invoke(create_app(), ["retrieve-korean-frequency-source", "--output-dir", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == [
        "retrieval_status=validated",
        "source_id=nikl-korean-learners-vocabulary",
        "accepted_filename=한국어 학습용 어휘 목록.txt",
        f"source_bytes_sha256={'c' * 64}",
        "source_byte_count=100",
        f"retrieval_result={result_file}",
    ]
    assert "https://" not in result.output
    assert str(Path.home()) not in result.output


def test_validate_retrieval_result_command_is_read_only(tmp_path: Path) -> None:
    from multilang.domain.korean import KoreanFrequencyRetrievalResult, raw_bytes_sha256

    result_path = tmp_path / "retrieval-result.json"
    source_path = tmp_path / "source.txt"
    source_bytes = "1\t학교\tNNG\tplace of learning\n".encode("utf-8")
    source_path.write_bytes(source_bytes)
    result = KoreanFrequencyRetrievalResult(
        source_id="nikl-korean-learners-vocabulary",
        landing_url="https://www.korean.go.kr/front/etcData/etcDataView.do?mn_id=46&etc_seq=70",
        accepted_filename="한국어 학습용 어휘 목록.txt",
        landing_sha256=_HASH,
        attachment_url="https://www.korean.go.kr/front/etcData/etcDataFileDownload.do?etc_seq=70&file_seq=1",
        attachment_sha256="b" * 64,
        source_bytes_sha256=raw_bytes_sha256(source_bytes),
        source_byte_count=len(source_bytes),
        retrieved_at="2026-08-28T00:00:00Z",
        text_encoding="utf-8",
        schema_version="nikl-frequency-retrieval-v1",
    )
    result_path.write_text(json.dumps(result.model_dump(mode="json"), ensure_ascii=False), encoding="utf-8")
    before = {path.name: path.stat().st_mtime_ns for path in (result_path, source_path)}

    command_result = runner.invoke(
        create_app(),
        [
            "validate-korean-source-retrieval-result",
            "--result-file",
            str(result_path),
            "--source-file",
            str(source_path),
        ],
    )

    assert command_result.exit_code == 0, command_result.output
    assert command_result.output.splitlines() == [
        "retrieval_result_status=valid",
        "source_id=nikl-korean-learners-vocabulary",
        "accepted_filename=한국어 학습용 어휘 목록.txt",
        f"source_byte_count={len(source_bytes)}",
    ]
    assert before == {path.name: path.stat().st_mtime_ns for path in (result_path, source_path)}


def test_retrieval_command_failures_are_content_free(tmp_path: Path, monkeypatch) -> None:
    class FakeRetriever:
        def retrieve_to_directory(self, output_dir: Path):
            raise ValueError(f"private path leaked: {tmp_path / 'secret.txt'}")

    monkeypatch.setattr(cli_module, "KoreanFrequencySourceRetriever", lambda: FakeRetriever())

    result = runner.invoke(create_app(), ["retrieve-korean-frequency-source", "--output-dir", str(tmp_path)])


    assert result.exit_code == 1
    assert result.output == "korean_frequency_source_error=operation_failed\n"
    assert str(tmp_path) not in result.output
