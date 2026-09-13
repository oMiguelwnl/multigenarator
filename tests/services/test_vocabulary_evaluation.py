import hashlib
import json

import pytest

from multilang.services.contextual_morphology import (
    ContextualAnalysis,
    ContextualToken,
    sentence_hash,
)


def corpus(tmp_path):
    path = tmp_path / "sample.conllu"
    path.write_text(
        "# sent_id = one\n# text = I went home.\n"
        "1\tI\tI\tPRON\t_\t_\t2\tnsubj\t_\t_\n"
        "2\twent\tgo\tVERB\t_\tTense=Past\t0\troot\t_\t_\n"
        "3\thome\thome\tADV\t_\t_\t2\tadvmod\t_\tSpaceAfter=No\n"
        "4\t.\t.\tPUNCT\t_\t_\t2\tpunct\t_\t_\n\n"
    )
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


class Analyzer:
    def __init__(self, *, wrong=False, unavailable=False):
        self.wrong, self.unavailable = wrong, unavailable

    def analyze(self, language, text):
        values = dict(
            language=language, sentence_sha256=sentence_hash(text), model_fingerprint="a" * 64
        )
        if self.unavailable:
            return ContextualAnalysis(**values, status="unavailable", reason="missing")
        tokens = tuple(
            ContextualToken(
                text=word,
                lemma=lemma,
                pos=pos,
                start=start,
                end=end,
                sentence_sha256=sentence_hash(text),
                model_fingerprint="a" * 64,
                features=features,
            )
            for word, lemma, pos, start, end, features in [
                ("I", "I", "PRON", 0, 1, ()),
                ("went", "went" if self.wrong else "go", "VERB", 2, 6, (("Tense", "Past"),)),
                ("home", "home", "ADV", 7, 11, ()),
                (".", ".", "PUNCT", 11, 12, ()),
            ]
        )
        return ContextualAnalysis(
            **values, status="complete", tokens=tokens, reason="morphology_only"
        )


def test_held_out_evaluation_reports_accuracy_without_qualification(tmp_path):
    from multilang.services.vocabulary_evaluation import evaluate_corpus

    path, digest = corpus(tmp_path)
    result = evaluate_corpus(
        language="en",
        corpus=path,
        corpus_sha256=digest,
        output=tmp_path / "evaluation",
        analyzer=Analyzer(),
        max_sentences=2,
    )
    assert result["sample_sentence_count"] == 1
    assert result["metrics"]["lemma_accuracy"] == 1.0
    assert result["metrics"]["exact_span_recall"] == 1.0
    assert result["qualification"] is False
    assert result["target_false_accept_rate"] is None
    observation = json.loads((tmp_path / "evaluation/observations.jsonl").read_text())
    assert observation["analysis"]["tokens"][1]["lemma"] == "go"
    assert observation["reference"]["source_sha256"] == digest


def test_wrong_complete_analysis_is_counted_as_error(tmp_path):
    from multilang.services.vocabulary_evaluation import evaluate_corpus

    path, digest = corpus(tmp_path)
    result = evaluate_corpus(
        language="en",
        corpus=path,
        corpus_sha256=digest,
        output=tmp_path / "evaluation",
        analyzer=Analyzer(wrong=True),
    )
    assert result["metrics"]["lemma_accuracy"] == 0.75
    assert result["false_complete_sentence_count"] == 1


def test_missing_models_do_not_disappear_from_denominators(tmp_path):
    from multilang.services.vocabulary_evaluation import evaluate_corpus

    path, digest = corpus(tmp_path)
    result = evaluate_corpus(
        language="en",
        corpus=path,
        corpus_sha256=digest,
        output=tmp_path / "evaluation",
        analyzer=Analyzer(unavailable=True),
    )
    assert result["analysis_statuses"] == {"unavailable": 1}
    assert result["metrics"]["lemma_accuracy"] == 0
    assert result["metrics"]["exact_span_recall"] == 0


def test_wrong_tense_is_a_false_complete_sentence(tmp_path):
    from multilang.services.vocabulary_evaluation import evaluate_corpus

    class WrongTense(Analyzer):
        def analyze(self, language, text):
            result = super().analyze(language, text)
            tokens = list(result.tokens)
            tokens[1] = tokens[1].model_copy(update={"features": (("Tense", "Pres"),)})
            return result.model_copy(update={"tokens": tuple(tokens)})

    path, digest = corpus(tmp_path)
    result = evaluate_corpus(
        language="en",
        corpus=path,
        corpus_sha256=digest,
        output=tmp_path / "evaluation",
        analyzer=WrongTense(),
    )
    assert result["metrics"]["lemma_accuracy"] == 1
    assert result["metrics"]["annotated_features_accuracy"] == 0
    assert result["false_complete_sentence_count"] == 1


def test_training_split_cannot_be_reported_as_held_out_and_output_is_immutable(tmp_path):
    from multilang.services.vocabulary_evaluation import evaluate_corpus

    path, digest = corpus(tmp_path)
    with pytest.raises(ValueError, match="test"):
        evaluate_corpus(
            language="en",
            corpus=path,
            corpus_sha256=digest,
            split="train",
            output=tmp_path / "evaluation",
            analyzer=Analyzer(),
        )
    (tmp_path / "evaluation").mkdir()
    with pytest.raises(ValueError, match="exists"):
        evaluate_corpus(
            language="en",
            corpus=path,
            corpus_sha256=digest,
            output=tmp_path / "evaluation",
            analyzer=Analyzer(),
        )


@pytest.mark.parametrize("language", ["ko", "ja"])
def test_native_annotation_inventory_is_not_reported_as_ud_accuracy(tmp_path, language):
    from multilang.services.vocabulary_evaluation import evaluate_corpus

    path, digest = corpus(tmp_path)
    result = evaluate_corpus(
        language=language,
        corpus=path,
        corpus_sha256=digest,
        output=tmp_path / "evaluation",
        analyzer=Analyzer(),
    )
    assert result["metrics"]["lemma_accuracy"] is None
    assert result["metrics"]["pos_accuracy"] is None
    assert result["metrics"]["annotated_features_accuracy"] is None
    assert result["metrics"]["exact_span_recall"] == 1
    assert result["counts"]["lemma_eligible_tokens"] == 4
    assert result["raw_annotation_metrics"]["lemma_accuracy"] == 1
    assert result["metric_compatibility"]["lemma_accuracy"]["comparable"] is False
    assert result["metric_compatibility"]["lemma_accuracy"]["reason"]
    assert result["false_complete_sentence_count"] is None
    assert result["qualification"] is False


def test_stanza_annotation_comparability_remains_explicit(tmp_path):
    from multilang.services.vocabulary_evaluation import evaluate_corpus

    path, digest = corpus(tmp_path)
    result = evaluate_corpus(
        language="en",
        corpus=path,
        corpus_sha256=digest,
        output=tmp_path / "evaluation",
        analyzer=Analyzer(wrong=True),
    )
    assert result["evaluator_version"] == "3"
    assert result["metric_compatibility"]["lemma_accuracy"]["comparable"] is True
    assert result["metrics"]["lemma_accuracy"] == 0.75
    assert result["false_complete_sentence_count"] == 1


def test_evaluation_output_budget_covers_observations_and_publishes_nothing_on_failure(tmp_path):
    from multilang.services.vocabulary_evaluation import evaluate_corpus
    from multilang.services.vocabulary_sources import SourceLimits

    path, digest = corpus(tmp_path)
    with pytest.raises(ValueError, match="output byte limit"):
        evaluate_corpus(
            language="en",
            corpus=path,
            corpus_sha256=digest,
            output=tmp_path / "evaluation",
            analyzer=Analyzer(),
            limits=SourceLimits(max_output_bytes=100),
        )
    assert not (tmp_path / "evaluation").exists()
