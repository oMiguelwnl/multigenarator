import hashlib
import importlib
import json

import pytest
from pydantic import ValidationError

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.vocabulary_preparation import prepare_vocabulary, source_catalog


def api():
    return importlib.import_module("multilang.services.qualification_pipeline")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def request(tmp_path, **changes):
    module = api()
    source = tmp_path / "source.jsonl"
    if not source.exists():
        rows = [
            {
                "lang_code": "pt",
                "word": "correr",
                "pos": "verb",
                "forms": [{"form": "corri", "tags": ["past"]}],
                "senses": [{"glosses": ["run"]}, {"glosses": ["flow"]}],
            },
            {"lang_code": "pt", "word": "casa", "pos": "noun", "senses": [{"glosses": ["house"]}]},
        ]
        source.write_text("".join(json.dumps(row) + "\n" for row in rows))
        prepare_vocabulary(
            language="pt",
            dictionary=source,
            dictionary_sha256=sha(source),
            output=tmp_path / "prepared",
        )
    values = dict(
        language="pt",
        prepared_inputs=[
            {
                "directory": tmp_path / "prepared",
                "manifest_sha256": sha(tmp_path / "prepared/manifest.json"),
            }
        ],
        seed_words=("correr", "casa"),
        seed_provenance={
            "requested_language": "pt",
            "effective_language": "pt",
            "source": "explicit",
            "source_version": "demo-1",
            "raw_seed_words": ("correr", "casa"),
            "selection_reason": "Synthetic explicit demonstration seeds.",
        },
        profile_sha256="a" * 64,
        rubric_sha256="b" * 64,
        headword_count=2,
        case_count=1,
    )
    values.update(changes)
    return module.QualificationPipelineRequest.model_validate(values)


def test_source_backed_pipeline_is_local_preserves_originals_and_resumes(tmp_path, monkeypatch):
    inputs = request(tmp_path)
    before = {p.name: sha(p) for p in (tmp_path / "prepared").iterdir()}

    def forbidden(*args, **kwargs):
        pytest.fail("local pipeline attempted model or network access")

    monkeypatch.setattr("httpx.Client", forbidden)
    monkeypatch.setattr(
        "multilang.services.contextual_morphology.LocalContextualMorphologyService", forbidden
    )
    output = tmp_path / "result"
    result = api().run_qualification_pipeline(inputs, output)
    assert result["status"] == "prepared"
    assert result["production_eligible"] is False
    assert result["provider_calls_executed"] == result["model_calls_executed"] == 0
    assert result["pilot"]["headword_count"] == 2
    assert result["pilot"]["lexical_candidate_count"] == 3
    assert (output / "pilot/review/lexical-001/packet.json").is_file()
    assert result == api().run_qualification_pipeline(inputs, output)
    assert before == {p.name: sha(p) for p in (tmp_path / "prepared").iterdir()}


@pytest.mark.parametrize("target", ["source", "output", "extra", "request"])
def test_resume_rejects_changed_inputs_outputs_or_configuration(tmp_path, target):
    inputs = request(tmp_path)
    output = tmp_path / "result"
    api().run_qualification_pipeline(inputs, output)
    if target == "source":
        (tmp_path / "prepared/candidates.jsonl").write_text("{}\n")
    elif target == "output":
        (output / "pilot/review/lexical-001/packet.json").write_text("{}")
    elif target == "extra":
        (output / "unexpected.json").write_text("{}")
    else:
        inputs = inputs.model_copy(update={"headword_count": 1})
    with pytest.raises(ValueError, match="checksum|inventory|request"):
        api().run_qualification_pipeline(inputs, output)


def test_seed_provenance_normalization_and_language_are_explicit(tmp_path):
    base = request(tmp_path).model_dump()
    base["seed_words"] = ("café",)
    base["seed_provenance"]["raw_seed_words"] = ("cafe\u0301",)
    normalized = api().QualificationPipelineRequest.model_validate(base)
    assert normalized.seed_provenance.raw_seed_words == ("cafe\u0301",)
    bad = normalized.model_dump()
    bad["seed_words"] = ("cafe\u0301",)
    with pytest.raises(ValidationError, match="NFC"):
        api().QualificationPipelineRequest.model_validate(bad)
    bad = normalized.model_dump()
    bad["seed_provenance"]["requested_language"] = "en"
    with pytest.raises(ValidationError, match="language"):
        api().QualificationPipelineRequest.model_validate(bad)


def test_every_modern_catalog_language_has_typed_configuration(tmp_path):
    base = request(tmp_path).model_dump()
    for entry in source_catalog():
        language = entry["language"]
        values = {
            **base,
            "language": language,
            "seed_provenance": {
                **base["seed_provenance"],
                "requested_language": language,
                "effective_language": "sh" if language == "hr" else language,
            },
        }
        assert api().QualificationPipelineRequest.model_validate(values).language.value == language
    with pytest.raises(ValidationError, match="Latin|modern"):
        api().QualificationPipelineRequest.model_validate({**base, "language": "la"})


def observation(tmp_path):
    from multilang.services.contextual_morphology import sentence_hash
    from multilang.services.qualification_observations import CorpusObservationResult

    text = "corri"
    token = dict(
        text=text,
        lemma="correr",
        pos="VERB",
        start=0,
        end=5,
        features=(),
        sentence_sha256=sentence_hash(text),
        model_fingerprint="c" * 64,
    )
    occurrence = dict(
        language="pt",
        split="calibration",
        source_sha256="d" * 64,
        document_id=None,
        sentence_id="sentence-1",
        sentence=text,
        start=0,
        end=5,
        text=text,
        lemma="correr",
        pos="VERB",
        features={},
    )
    result = CorpusObservationResult.model_validate(
        dict(
            source_sha256="d" * 64,
            language="pt",
            split="calibration",
            context=dict(
                language="pt",
                split="calibration",
                source_sha256s=["d" * 64],
                token_count=1,
                documents=[],
                sampling_description="Synthetic grammar fixture",
            ),
            occurrences=[occurrence],
            analyses=[
                dict(
                    source_sha256="d" * 64,
                    document_id="source-" + "d" * 64,
                    sentence_id="sentence-1",
                    text=text,
                    analysis=dict(
                        language="pt",
                        sentence_sha256=sentence_hash(text),
                        status="complete",
                        tokens=[token],
                        model_fingerprint="c" * 64,
                        reason="test-fixture",
                    ),
                )
            ],
            skipped_units=[],
            coverage=dict(
                source_document_count=None,
                measured_document_count=None,
                document_boundaries_known=False,
                source_unit_count=1,
                analyzed_unit_count=1,
                source_nonspace_characters=5,
                aligned_nonspace_characters=5,
                blocked_nonspace_characters=0,
                unaccounted_nonspace_characters=0,
                measured_lexical_tokens=1,
                excluded_nonlexical_tokens=0,
                statuses={"complete": 1},
            ),
            model_fingerprints=["c" * 64],
            sampling_description="Synthetic grammar fixture",
            source_scope="UD-train-grammar-only",
        )
    )
    path = tmp_path / "explicit-observation.json"
    path.write_text(result.model_dump_json())
    return path


def test_observations_are_explicit_and_never_regenerated_or_conflated(tmp_path):
    path = observation(tmp_path)
    (tmp_path / "newer-observations.json").write_text("not selected")
    inputs = request(tmp_path, observation={"path": path, "sha256": sha(path)})
    result = api().run_qualification_pipeline(inputs, tmp_path / "result")
    assert result["pilot"]["measurement_count"] == 1
    evidence = json.loads((tmp_path / "result/source-evidence.json").read_text())
    assert evidence["observation"]["source_scope"] == "UD-train-grammar-only"
    assert evidence["observation"]["coverage"]["document_boundaries_known"] is False
    measured = json.loads((tmp_path / "result/pilot/measurements.json").read_text())
    assert measured["measurements"][0]["dispersion"] is None


@pytest.mark.parametrize("corruption", ["language", "count", "span"])
def test_inconsistent_observation_is_rejected_before_output(tmp_path, corruption):
    path = observation(tmp_path)
    raw = json.loads(path.read_text())
    if corruption == "language":
        raw["language"] = "en"
    elif corruption == "count":
        raw["context"]["token_count"] = 2
    else:
        raw["analyses"][0]["text"] = "casa!"
    path.write_text(json.dumps(raw))
    inputs = request(tmp_path, observation={"path": path, "sha256": sha(path)})
    with pytest.raises(ValueError, match="observation"):
        api().run_qualification_pipeline(inputs, tmp_path / "result")
    assert not (tmp_path / "result").exists()


def test_category_helper_preserves_exact_record_hashes_and_rejects_replacement(tmp_path):
    request(tmp_path)
    path = tmp_path / "source.jsonl"
    output = tmp_path / "categories.json"
    reference = api().prepare_source_categories(path, sha(path), output, language="pt")
    expected = {
        canonical_sha256(json.loads(line)): json.loads(line)["pos"]
        for line in path.read_text().splitlines()
    }
    assert json.loads(output.read_text()) == expected
    assert reference.sha256 == sha(output)
    with pytest.raises(ValueError, match="exists"):
        api().prepare_source_categories(path, sha(path), output, language="pt")


@pytest.mark.parametrize("corruption", ["documents", "coverage", "fingerprints"])
def test_observation_metadata_cannot_fabricate_measurement_coverage(tmp_path, corruption):
    path = observation(tmp_path)
    raw = json.loads(path.read_text())
    if corruption == "documents":
        raw["context"]["documents"] = [
            {
                "source_sha256": "d" * 64,
                "document_id": "invented-document",
                "text_sha256": "e" * 64,
                "token_count": 1,
            }
        ]
    elif corruption == "coverage":
        raw["coverage"]["aligned_nonspace_characters"] = 4
    else:
        raw["model_fingerprints"] = ["f" * 64]
    path.write_text(json.dumps(raw))
    inputs = request(tmp_path, observation={"path": path, "sha256": sha(path)})
    with pytest.raises(ValueError, match="observation"):
        api().run_qualification_pipeline(inputs, tmp_path / "result")


def test_failures_do_not_publish_partial_output(tmp_path, monkeypatch):
    inputs = request(tmp_path)

    def interrupted(**kwargs):
        kwargs["output"].mkdir()
        (kwargs["output"] / "partial.json").write_text("{}")
        raise RuntimeError("simulated interruption")

    monkeypatch.setattr(api(), "prepare_qualification_pilot", interrupted)
    with pytest.raises(RuntimeError, match="interruption"):
        api().run_qualification_pipeline(inputs, tmp_path / "result")
    assert not (tmp_path / "result").exists()
