import hashlib
import json

from typer.testing import CliRunner

from multilang.vocabulary_cli import create_vocabulary_app


def test_local_commands_are_exposed_before_production_enablement():
    result = CliRunner().invoke(create_vocabulary_app(), ["qualification", "--help"])
    assert result.exit_code == 0, result.output
    for command in (
        "measure",
        "workload",
        "export-review",
        "import-review",
        "calibrate",
        "evaluate",
        "prepare-pilot",
    ):
        assert command in result.output


def test_workload_cli_runs_service_and_refuses_wrong_hash_or_overwrite(tmp_path):
    request = tmp_path / "request.json"
    request.write_text(json.dumps({"headwords": 100, "observed_forms": 12}))
    digest = hashlib.sha256(request.read_bytes()).hexdigest()
    output = tmp_path / "output.json"
    app = create_vocabulary_app()
    args = ["qualification", "workload", str(request), digest, str(output)]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    data = json.loads(output.read_text())
    assert data["headword_candidates"] == 100
    assert data["expected_cost"] is None
    assert data["provider_calls_executed"] == 0
    assert CliRunner().invoke(app, args).exit_code == 1
    args[3] = "f" * 64
    assert CliRunner().invoke(app, args).exit_code == 1


def test_measure_cli_preserves_real_counts_and_rejects_unknown_request_fields(tmp_path):
    request = tmp_path / "request.json"
    request.write_text(
        json.dumps(
            {
                "context": {
                    "language": "en",
                    "split": "calibration",
                    "source_sha256s": ["a" * 64],
                    "token_count": 100,
                },
                "occurrences": [
                    {
                        "language": "en",
                        "split": "calibration",
                        "source_sha256": "a" * 64,
                        "sentence_id": "s1",
                        "sentence": "We went.",
                        "start": 3,
                        "end": 7,
                        "text": "went",
                        "lemma": "go",
                        "pos": "VERB",
                    }
                ],
            }
        )
    )
    digest = hashlib.sha256(request.read_bytes()).hexdigest()
    output = tmp_path / "output.json"
    result = CliRunner().invoke(
        create_vocabulary_app(), ["qualification", "measure", str(request), digest, str(output)]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(output.read_text())
    assert data["measurements"][0]["observed_count"] == 1
    assert data["measurements"][0]["sense_id"] is None


def test_corpus_cli_preserves_frozen_discovery_and_checks_hash_before_acquisition(
    tmp_path, monkeypatch
):
    from types import SimpleNamespace

    from multilang.services import qualification_corpora as corpus

    selection = corpus.PageSelection(
        language="pt", project="wikipedia", page_ids=(7,),
        selection_policy="bounded-recent-new-pages-v1", continuation_available=False,
        raw_response=json.dumps({"query": {"recentchanges": [{"pageid": 7, "ns": 0}]}}),
        acquired_at="2026-09-13T12:00:00Z",
    )
    calls = []

    def discover(language, project, **kwargs):
        calls.append((language, project, kwargs))
        return selection

    def acquire(language, project, page_ids, output, **kwargs):
        calls.append((language, project, tuple(page_ids), kwargs["selection"]))
        return SimpleNamespace(model_dump=lambda **_: {"production_eligible": False})

    monkeypatch.setattr(corpus, "discover_wikimedia_pages", discover)
    monkeypatch.setattr(corpus, "acquire_wikimedia_documents", acquire)
    app = create_vocabulary_app()
    frozen = tmp_path / "selection.json"
    result = CliRunner().invoke(app, ["qualification", "discover-corpus", "pt", "wikipedia",
        str(frozen), "--strategy", "recent-new-pages", "--limit", "5"])
    assert result.exit_code == 0, result.output
    assert calls == [("pt", "wikipedia", {"limit": 5, "strategy": "recent-new-pages"})]
    digest = hashlib.sha256(frozen.read_bytes()).hexdigest()
    args = ["qualification", "acquire-corpus", "pt", "wikipedia", str(tmp_path / "corpus"),
        "--page-id", "7", "--selection", str(frozen), "--selection-sha256", digest]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert calls[-1] == ("pt", "wikipedia", (7,), selection)
    args[-1] = "0" * 64
    assert CliRunner().invoke(app, args).exit_code == 1
    assert len(calls) == 2
    assert CliRunner().invoke(app, args[:-2]).exit_code == 1
    assert len(calls) == 2
