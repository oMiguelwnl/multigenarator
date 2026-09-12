import csv
import hashlib
import json


def test_catalog_covers_all_modern_languages_and_never_implies_approval():
    from multilang.services.vocabulary_preparation import source_catalog

    entries = source_catalog()
    assert len(entries) == 22
    assert {entry["language"] for entry in entries} == {
        "pt",
        "es",
        "en",
        "fr",
        "de",
        "it",
        "pl",
        "tr",
        "ro",
        "ru",
        "nl",
        "ko",
        "da",
        "nb",
        "sv",
        "fi",
        "hu",
        "cs",
        "hr",
        "el",
        "ja",
        "zh",
    }
    assert all(not e["corpus"]["redistribution_approved"] for e in entries)


def test_legacy_audit_distinguishes_word_rows_from_resolved_identities(tmp_path):
    from multilang.services.vocabulary_preparation import audit_legacy_frequency

    path = tmp_path / "en" / "curated-v1.csv"
    path.parent.mkdir()
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["display_form", "lemma", "part_of_speech"])
        writer.writeheader()
        writer.writerow({"display_form": "went", "lemma": "went", "part_of_speech": "unknown"})
    result = audit_legacy_frequency(tmp_path, "en")
    assert result["row_count"] == 1
    assert result["unknown_pos_count"] == 1
    assert result["resolved_identity_count"] == 0
    assert not result["production_eligible"]


def test_preparation_writes_reviewable_candidates_without_production_claim(tmp_path):
    from multilang.services.vocabulary_preparation import prepare_vocabulary

    dictionary = tmp_path / "lexicon.jsonl"
    dictionary.write_text(
        json.dumps(
            {
                "word": "go",
                "lang_code": "en",
                "pos": "verb",
                "senses": [{"glosses": ["To move from one place to another."]}],
                "forms": [{"form": "went", "tags": ["past"]}],
            }
        )
        + "\n"
    )
    output = tmp_path / "prepared"
    result = prepare_vocabulary(
        language="en",
        dictionary=dictionary,
        dictionary_sha256=hashlib.sha256(dictionary.read_bytes()).hexdigest(),
        output=output,
    )
    assert result["lexical_candidate_count"] == 1
    assert result["resolved_identity_count"] == 0
    assert result["production_eligible"] is False
    assert "independent_sense_review" in result["blockers"]
    row = json.loads((output / "candidates.jsonl").read_text())
    assert row["forms"][0]["form"] == "went"
    assert (output / "manifest.json").is_file()
    assert (output / "review.jsonl").is_file()


def test_preparation_rejects_overwriting_existing_artifacts(tmp_path):
    import pytest

    from multilang.services.vocabulary_preparation import prepare_vocabulary

    dictionary = tmp_path / "dictionary.jsonl"
    dictionary.write_text("")
    output = tmp_path / "prepared"
    output.mkdir()
    (output / "keep.txt").write_text("user data")
    with pytest.raises(ValueError, match="empty"):
        prepare_vocabulary(
            language="en",
            dictionary=dictionary,
            dictionary_sha256=hashlib.sha256(b"").hexdigest(),
            output=output,
        )
    assert (output / "keep.txt").read_text() == "user data"


def test_native_vocabulary_audit_is_available_before_production_activation(tmp_path):
    from typer.testing import CliRunner

    from multilang.native_cli import create_native_app
    from multilang.settings import Settings

    app = create_native_app(settings=Settings(roadmap_4_enabled=False))
    result = CliRunner().invoke(app, ["vocabulary", "sources", "--language", "en"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["language"] == "en"


def test_preparation_bounds_aggregate_derived_output_and_leaves_no_partial_dataset(tmp_path):
    import pytest

    from multilang.services.vocabulary_preparation import prepare_vocabulary
    from multilang.services.vocabulary_sources import SourceLimits

    dictionary = tmp_path / "dictionary.jsonl"
    dictionary.write_text(
        json.dumps(
            {
                "word": "go",
                "lang_code": "en",
                "pos": "verb",
                "senses": [{"glosses": ["To move."]} for _ in range(30)],
            }
        )
        + "\n"
    )
    output = tmp_path / "prepared"
    with pytest.raises(ValueError, match="output.*limit"):
        prepare_vocabulary(
            language="en",
            dictionary=dictionary,
            dictionary_sha256=hashlib.sha256(dictionary.read_bytes()).hexdigest(),
            output=output,
            limits=SourceLimits(max_output_bytes=1500),
        )
    assert not output.exists()


def test_cli_can_prepare_review_template_and_compile_pending_evidence_without_activation(tmp_path):
    from typer.testing import CliRunner

    from multilang.native_cli import create_native_app
    from multilang.services.language_profiles import LanguageProfileRegistry
    from multilang.settings import Settings

    dictionary = tmp_path / "dictionary.jsonl"
    dictionary.write_text(
        json.dumps(
            {"word": "go", "lang_code": "en", "pos": "verb", "senses": [{"glosses": ["To move."]}]}
        )
        + "\n"
    )
    runner = CliRunner()
    app = create_native_app(settings=Settings(_env_file=None, roadmap_4_enabled=False))
    prepared = tmp_path / "prepared"
    outcome = runner.invoke(
        app,
        [
            "vocabulary",
            "prepare",
            "en",
            str(dictionary),
            hashlib.sha256(dictionary.read_bytes()).hexdigest(),
            str(prepared),
        ],
    )
    assert outcome.exit_code == 0, outcome.output
    review = tmp_path / "review.json"
    outcome = runner.invoke(
        app, ["vocabulary", "review-template", str(prepared), "fixture", "1", str(review)]
    )
    assert outcome.exit_code == 0, outcome.output
    data = json.loads(review.read_text())
    assert data["senses"][0]["decision"] == "pending"
    assert data["senses"][0]["stable_sense_id"] is None
    profile = (
        LanguageProfileRegistry()
        .get("en")
        .model_copy(
            update={
                "source_ids": ("fixture",),
                "analyzer_id": "contextual-morphology",
                "analyzer_version": "1",
            }
        )
    )
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(profile.model_dump_json())
    output = tmp_path / "compiled"
    outcome = runner.invoke(
        app,
        [
            "vocabulary",
            "compile-review",
            str(prepared),
            str(review),
            hashlib.sha256(review.read_bytes()).hexdigest(),
            str(profile_path),
            str(output),
        ],
    )
    assert outcome.exit_code == 0, outcome.output
    bundle = json.loads((output / "bundle.json").read_text())
    assert not bundle["production_eligible"]
    assert bundle["identities"] == []
    assert len(bundle["quarantine"]) == 1


def test_cli_errors_do_not_echo_input_content(tmp_path):
    from typer.testing import CliRunner

    from multilang.native_cli import create_native_app
    from multilang.settings import Settings

    path = tmp_path / "private.jsonl"
    path.write_text("private-input-do-not-log")
    result = CliRunner().invoke(
        create_native_app(settings=Settings(_env_file=None)),
        [
            "vocabulary",
            "prepare",
            "en",
            str(path),
            hashlib.sha256(path.read_bytes()).hexdigest(),
            str(tmp_path / "output"),
        ],
    )
    assert result.exit_code == 1
    assert "Operation rejected" in result.output
    assert "private-input-do-not-log" not in result.output
