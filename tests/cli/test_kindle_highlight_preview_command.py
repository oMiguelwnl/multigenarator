from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from multilang.cli import create_app
from multilang.domain.korean import (
    KoreanAnalyzerFingerprint,
    KoreanLexicalIdentity,
    KoreanSignatureItem,
)


runner = CliRunner()
FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "kindle_highlights"


def _korean_identity() -> KoreanLexicalIdentity:
    return KoreanLexicalIdentity(
        submitted_form=None,
        canonical_nfc="물은",
        lemma="물",
        part_of_speech="NNG",
        sense_id="fixture:water:1",
        register="standard",
        morpheme_signature=(KoreanSignatureItem(form="물", pos="NNG"),),
        analyzer_fingerprint=KoreanAnalyzerFingerprint(
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
        ),
        status="resolved",
    )


def _write_korean_fixture(path: Path, private_text: str) -> None:
    path.write_text(
        "==========\nSynthetic Learner Reader\n"
        "- Your Highlight at location 7\n\n"
        f"{private_text}\n",
        encoding="utf-8",
    )


class _CountingKoreanResolver:
    def __init__(self, *, unavailable: bool = False) -> None:
        self.unavailable = unavailable
        self.calls: list[str] = []

    def resolve_korean_highlight_text(self, text: str) -> tuple[object, ...]:
        self.calls.append(text)
        if self.unavailable:
            return ()
        return (SimpleNamespace(identity=_korean_identity(), word_position=0),)


class _InjectedRuntimeService:
    def __init__(self, grounding_service: object) -> None:
        self.grounding_service = grounding_service


def test_preview_kindle_highlights_prints_stable_count_lines() -> None:
    app = create_app()

    result = runner.invoke(
        app,
        [
            "preview-kindle-highlights",
            "--language",
            "es",
            "--input-file",
            str(FIXTURE_DIR / "local_export.html"),
        ],
    )

    assert result.exit_code == 0
    lines = result.output.strip().splitlines()
    assert lines[0] == "imported_highlights=3"
    assert lines[1].startswith("extracted_candidates=")
    assert lines[2] == "rejected_highlights=0"
    assert lines[3].startswith("duplicate_candidates=")
    assert lines[4].startswith("planned_cards=")


def test_preview_kindle_highlights_applies_planned_card_limit() -> None:
    app = create_app()

    result = runner.invoke(
        app,
        [
            "preview-kindle-highlights",
            "--language",
            "pt",
            "--input-file",
            str(FIXTURE_DIR / "local_export.txt"),
            "--planned-card-limit",
            "2",
        ],
    )

    assert result.exit_code == 0
    assert "planned_cards=2" in result.output


def test_preview_kindle_highlights_has_privacy_safe_errors(tmp_path: Path) -> None:
    private_path = tmp_path / "Private Book - Secret Author.pdf"
    private_path.write_text("minha frase privada", encoding="utf-8")
    app = create_app()

    result = runner.invoke(
        app,
        [
            "preview-kindle-highlights",
            "--language",
            "pt",
            "--input-file",
            str(private_path),
        ],
    )

    assert result.exit_code == 1
    assert "unsupported_format" in result.output
    assert str(private_path) not in result.output
    assert "minha frase privada" not in result.output


def test_generate_source_kindle_highlights_remains_blocked() -> None:
    app = create_app()

    result = runner.invoke(app, ["generate", "--language", "es", "--source", "kindle-highlights"])

    assert result.exit_code != 0
    assert "--source must be one of: frequency, word-list, highlights" in result.output


def test_korean_preview_reuses_injected_runtime_grounding_resolver_without_second_adapter(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import multilang.cli as cli_module

    private_text = "물은 비밀 문장입니다"
    private_path = tmp_path / "Private Korean Reader.txt"
    _write_korean_fixture(private_path, private_text)
    resolver = _CountingKoreanResolver()

    def forbidden_adapter() -> object:
        raise AssertionError("a second Korean morphology adapter was constructed")

    monkeypatch.setattr(
        cli_module,
        "KiwiKoreanMorphologyService",
        forbidden_adapter,
        raising=False,
    )
    app = create_app(service=_InjectedRuntimeService(resolver))

    result = runner.invoke(
        app,
        [
            "preview-kindle-highlights",
            "--language",
            "ko",
            "--input-file",
            str(private_path),
        ],
    )

    assert result.exit_code == 0
    assert resolver.calls == [private_text]
    assert result.output.strip().splitlines() == [
        "imported_highlights=1",
        "extracted_candidates=1",
        "rejected_highlights=0",
        "duplicate_candidates=0",
        "planned_cards=1",
    ]
    assert private_text not in result.output
    assert str(private_path) not in result.output


def test_korean_preview_fails_closed_with_content_free_error(
    tmp_path: Path,
) -> None:
    private_text = "비밀 원문 prompt instruction"
    private_path = tmp_path / "Secret Korean Reader.txt"
    _write_korean_fixture(private_path, private_text)
    resolver = _CountingKoreanResolver(unavailable=True)
    app = create_app(service=_InjectedRuntimeService(resolver))

    result = runner.invoke(
        app,
        [
            "preview-kindle-highlights",
            "--language",
            "ko",
            "--input-file",
            str(private_path),
        ],
    )

    assert result.exit_code == 1
    assert result.output.strip() == (
        "korean_highlight_preview_error=korean_resolution_unavailable"
    )
    assert resolver.calls == [private_text]
    assert private_text not in result.output
    assert str(private_path) not in result.output
