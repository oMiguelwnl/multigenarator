"""Contract tests for canonical Korean language support."""

from __future__ import annotations

import importlib.util
from importlib import import_module
from importlib.metadata import version as distribution_version
from pathlib import Path
import sys
import tomllib
from types import ModuleType

import multilang.settings as settings_module
import pytest
from multilang.domain.exporting import ExportCardIdentity, ExportCardRow
from multilang.domain.jobs import GenerationRequest, SupportedLanguage
from multilang.domain.korean import KOREAN_LANGUAGE_CODE, KOREAN_PROVIDER_LOCALE
from multilang.domain.lexicon import policy_for_language
from multilang.services.audio_voice_registry import (
    VoiceSelectionError,
    get_voice_registry,
    select_voice,
)
from multilang.services.export_anki_package import build_multilang_note
from multilang.services.input_fingerprint import build_run_key
from multilang.services.tatoeba_sentence_source import TatoebaSentenceSource


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_SCAN_ROOTS = (PROJECT_ROOT / "src", PROJECT_ROOT / "scripts")
ALLOWED_KOREAN_PROVIDER_LOCALE_LITERALS: frozenset[tuple[str, str]] = frozenset(
    {
        (
            "src/multilang/domain/korean.py",
            'KOREAN_PROVIDER_LOCALE: Final = "ko-KR"',
        )
    }
)


def _load_frequency_asset_builder() -> ModuleType:
    module_path = PROJECT_ROOT / "scripts" / "build_frequency_assets.py"
    spec = importlib.util.spec_from_file_location(
        "korean_frequency_asset_builder",
        module_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


build_frequency_assets = _load_frequency_asset_builder()


def _production_korean_provider_locale_literals() -> tuple[tuple[str, str], ...]:
    occurrences: list[tuple[str, str]] = []
    for root in PRODUCTION_SCAN_ROOTS:
        for path in sorted(root.rglob("*.py")):
            relative_path = path.relative_to(PROJECT_ROOT).as_posix()
            for line in path.read_text(encoding="utf-8").splitlines():
                if "ko-KR" in line:
                    occurrences.append((relative_path, line.strip()))
    return tuple(occurrences)


def _generic_korean_row(source_type: str) -> ExportCardRow:
    return ExportCardRow(
        identity=ExportCardIdentity(
            language=SupportedLanguage.KO,
            source_type=source_type,
            job_id=f"ko-{source_type}-contract",
            item_key=f"ko-{source_type}-item",
            lemma_key="ko:contract-identity",
            sort_index=1,
        ),
        word="공부하다",
        front_of_card="공부하다",
        definitions="verbo: estudar",
        example_sentence="저는 도서관에서 매일 한국어를 공부해요.",
        translation="Eu estudo coreano todos os dias na biblioteca.",
        word_audio=f"[sound:ko-{source_type}-word.mp3]",
        sentence_audio=f"[sound:ko-{source_type}-sentence.mp3]",
    )


def test_kiwi_analyzer_and_model_are_exact_direct_runtime_dependencies() -> None:
    project = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]
    dependencies = project["dependencies"]

    assert project["requires-python"] == ">=3.12"
    assert dependencies.count("kiwipiepy==0.23.2") == 1
    assert dependencies.count("kiwipiepy-model==0.23.0") == 1

    kiwipiepy = import_module("kiwipiepy")
    kiwipiepy_model = import_module("kiwipiepy_model")

    assert distribution_version("kiwipiepy") == "0.23.2"
    assert distribution_version("kiwipiepy-model") == "0.23.0"
    assert kiwipiepy.__version__ == "0.23.2"
    assert kiwipiepy_model.__version__ == "0.23.0"


def test_production_uses_ko_kr_only_at_the_explicit_locale_constant() -> None:
    occurrences = _production_korean_provider_locale_literals()

    assert occurrences
    assert set(occurrences) == ALLOWED_KOREAN_PROVIDER_LOCALE_LITERALS
    assert KOREAN_PROVIDER_LOCALE == "ko-KR"


def test_three_mode_job_keys_policy_and_generic_tags_use_only_canonical_ko() -> None:
    policy = policy_for_language(SupportedLanguage.KO)

    assert KOREAN_LANGUAGE_CODE == SupportedLanguage.KO.value == "ko"
    assert policy.definition_language == "pt"
    assert policy.translation_target_language == "pt"
    assert not (PROJECT_ROOT / "assets" / "frequency" / "ko").exists()

    for source_type in ("frequency", "word-list", "kindle-highlights"):
        request = GenerationRequest(
            language=SupportedLanguage.KO,
            source_type=source_type,
        )
        run_key = build_run_key(request, requested_item_keys=("공부하다",))
        row = _generic_korean_row(source_type)
        note = build_multilang_note(row)

        assert run_key.startswith(f"ko:{source_type}:")
        assert note.tags.count("ko") == 1
        assert "ko-KR" not in note.tags
        assert row.identity.language.value == "ko"
        assert row.ordered_field_mapping()["Image"] == ""


def test_korean_identity_is_canonical_and_separate_from_frequency_asset_approval() -> None:
    approved_languages = getattr(
        settings_module,
        "APPROVED_FREQUENCY_ASSET_LANGUAGES",
        None,
    )

    assert SupportedLanguage.KO.value == "ko"
    assert settings_module.DEFAULT_SUPPORTED_LANGUAGES.count("ko") == 1
    assert approved_languages is not None
    assert "ko" not in approved_languages
    assert "ko-KR" not in settings_module.DEFAULT_SUPPORTED_LANGUAGES


def test_korean_has_no_guessed_voice_or_tatoeba_fallback() -> None:
    class CountingCandidateProvider:
        calls = 0

        def search_candidates(self, **kwargs: object) -> list[object]:
            self.calls += 1
            return []

    assert SupportedLanguage.KO not in get_voice_registry()
    with pytest.raises(VoiceSelectionError):
        select_voice(SupportedLanguage.KO)

    provider = CountingCandidateProvider()
    source = TatoebaSentenceSource(candidate_provider=provider)
    assert (
        source.select_sentence(
            display_form="학교에서",
            lemma="학교",
            target_language="ko",
            translation_target_language="pt",
        )
        is None
    )
    assert provider.calls == 0


def test_frequency_asset_all_operations_use_only_approved_languages(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    build_calls: list[str] = []
    check_calls: list[str] = []

    monkeypatch.setattr(
        build_frequency_assets,
        "_build_language_asset",
        lambda *, code, **kwargs: build_calls.append(code),
    )
    monkeypatch.setattr(
        build_frequency_assets,
        "load_curated_frequency_entries",
        lambda language, **kwargs: check_calls.append(language.value),
    )

    build_frequency_assets.build_assets(
        assets_dir=tmp_path / "build",
        version="v1",
    )
    build_frequency_assets.check_assets(
        assets_dir=tmp_path / "check",
        version="v1",
    )

    approved_languages = list(settings_module.APPROVED_FREQUENCY_ASSET_LANGUAGES)
    assert build_calls == approved_languages
    assert check_calls == approved_languages
    assert "ko" not in build_calls
    assert "ko" not in check_calls


@pytest.mark.parametrize("operation", ["build", "check"])
def test_explicit_korean_frequency_asset_operation_fails_before_side_effects(
    operation: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    side_effects: list[str] = []

    def fail_on_side_effect(*args: object, **kwargs: object) -> None:
        side_effects.append("called")
        raise AssertionError("Korean frequency gate ran after a side effect")

    monkeypatch.setattr(Path, "mkdir", fail_on_side_effect)
    monkeypatch.setattr(build_frequency_assets, "iter_wordlist", fail_on_side_effect)
    monkeypatch.setattr(build_frequency_assets, "_write_csv", fail_on_side_effect)
    monkeypatch.setattr(
        build_frequency_assets,
        "load_curated_frequency_entries",
        fail_on_side_effect,
    )

    assets_dir = tmp_path / "blocked-frequency"
    asset_operation = (
        build_frequency_assets.build_assets
        if operation == "build"
        else build_frequency_assets.check_assets
    )

    with pytest.raises(RuntimeError) as exc_info:
        asset_operation(
            assets_dir=assets_dir,
            version="v1",
            language_code="ko",
        )

    assert str(exc_info.value) == (
        "Korean frequency assets require approved source, attribution, and "
        "redistribution terms before build or check operations"
    )
    assert side_effects == []
    assert not assets_dir.exists()
