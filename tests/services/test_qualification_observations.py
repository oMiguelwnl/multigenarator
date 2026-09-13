import hashlib
from datetime import UTC, datetime

import pytest

from multilang.services.contextual_morphology import (
    ContextualAnalysis,
    ContextualBlockedSpan,
    ContextualToken,
    sentence_hash,
)


def _document(path, text="We read.\n\nThey read."):
    from multilang.services.qualification_corpora import SourceDocument

    doc = SourceDocument(
        language="en",
        project="wikipedia",
        source_id="wikimedia:en.wikipedia.org",
        document_id="en.wikipedia.org:1",
        page_id=1,
        revision_id="5",
        title="Reading",
        source_url="https://en.wikipedia.org/w/index.php?oldid=5",
        text_register="encyclopedic",
        published_at=datetime.now(UTC),
        acquired_at=datetime.now(UTC),
        raw_sha256="a" * 64,
        revision_raw_sha256="b" * 64,
        publication_raw_sha256="c" * 64,
        text=text,
        text_sha256=hashlib.sha256(text.encode()).hexdigest(),
        license_id="unresolved",
        license_url="https://example.org/license",
        license_evidence_sha256="d" * 64,
        attribution="test-only source",
    )
    path.write_text(doc.model_dump_json() + "\n")
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Analyzer:
    def analyze(self, language, text):
        prefix, verb = text.split(" ")
        base = dict(sentence_sha256=sentence_hash(text), model_fingerprint="e" * 64)
        return ContextualAnalysis(
            language=language,
            status="complete",
            reason="synthetic test",
            **base,
            tokens=(
                ContextualToken(
                    text=prefix, lemma=prefix.lower(), pos="PRON", start=0, end=len(prefix), **base
                ),
                ContextualToken(
                    text="read",
                    lemma="read",
                    pos="VERB",
                    start=len(prefix) + 1,
                    end=len(prefix) + 5,
                    **base,
                ),
                ContextualToken(
                    text=".", lemma=".", pos="PUNCT", start=len(text) - 1, end=len(text), **base
                ),
            ),
        )


def test_observer_preserves_document_boundaries_and_unresolved_senses(tmp_path):
    from multilang.services.qualification_observations import observe_document_corpus

    path = tmp_path / "documents.jsonl"
    digest = _document(path)
    result = observe_document_corpus(path, digest, Analyzer())
    assert result.context.token_count == 4
    assert len(result.context.documents) == 1
    assert result.coverage.source_document_count == 1
    assert result.coverage.analyzed_unit_count == 2
    assert len(result.occurrences) == 4
    assert len({o.document_id for o in result.occurrences}) == 1
    assert all(o.sense_id is None for o in result.occurrences)
    assert len({o.sentence_id for o in result.occurrences}) == 2
    assert result.analyses[1].document_start == 10
    assert result.analyses[1].text == "They read."
    assert result.production_eligible is False


def test_blocked_spans_are_retained_and_excluded_from_denominator(tmp_path):
    from multilang.services.qualification_observations import observe_document_corpus

    class BlockedAnalyzer:
        def analyze(self, language, text):
            base = dict(sentence_sha256=sentence_hash(text), model_fingerprint="e" * 64)
            return ContextualAnalysis(
                language=language,
                status="inconclusive",
                reason="blocked",
                **base,
                tokens=(
                    ContextualToken(text="read", lemma="read", pos="VERB", start=3, end=7, **base),
                ),
                blocked_spans=(
                    ContextualBlockedSpan(
                        text="We", start=0, end=2, reason="unknown_lexical_token", **base
                    ),
                ),
            )

    path = tmp_path / "documents.jsonl"
    digest = _document(path, "We read")
    result = observe_document_corpus(path, digest, BlockedAnalyzer())
    assert result.context.token_count == 1
    assert result.coverage.blocked_nonspace_characters == 2
    assert result.coverage.unaccounted_nonspace_characters == 0
    assert len(result.analyses[0].analysis.blocked_spans) == 1


def test_unavailable_model_yields_no_fake_nonzero_denominator(tmp_path):
    from multilang.services.qualification_observations import observe_document_corpus

    class Unavailable:
        def analyze(self, language, text):
            return ContextualAnalysis(
                language=language,
                status="unavailable",
                reason="missing",
                sentence_sha256=sentence_hash(text),
                model_fingerprint="e" * 64,
            )

    path = tmp_path / "documents.jsonl"
    digest = _document(path)
    result = observe_document_corpus(path, digest, Unavailable())
    assert result.context is None
    assert result.occurrences == ()
    assert result.coverage.unaccounted_nonspace_characters > 0
    assert result.coverage.source_document_count == 1


@pytest.mark.parametrize("status", ["invalid", "unavailable", "unsupported"])
def test_nonobserving_status_cannot_supply_tokens_to_measurement(tmp_path, status):
    from multilang.services.qualification_observations import observe_document_corpus

    class ContradictoryAnalyzer(Analyzer):
        def analyze(self, language, text):
            return super().analyze(language, text).model_copy(update={"status": status})

    path = tmp_path / "documents.jsonl"
    digest = _document(path, "We read.")
    with pytest.raises(ValueError, match="status"):
        observe_document_corpus(path, digest, ContradictoryAnalyzer())


def test_corpus_split_cannot_be_changed_at_observation(tmp_path):
    from multilang.services.qualification_observations import observe_document_corpus

    path = tmp_path / "documents.jsonl"
    digest = _document(path)
    with pytest.raises(ValueError, match="split"):
        observe_document_corpus(path, digest, Analyzer(), split="evaluation")


def test_wrong_analysis_source_never_enters_measurement(tmp_path):
    from multilang.services.qualification_observations import observe_document_corpus

    class Wrong(Analyzer):
        def analyze(self, language, text):
            return super().analyze("pt", text)

    path = tmp_path / "documents.jsonl"
    digest = _document(path)
    with pytest.raises(ValueError, match="source"):
        observe_document_corpus(path, digest, Wrong())


def test_units_above_explicit_limit_are_skipped_without_truncation(tmp_path):
    from multilang.services.qualification_observations import (
        ObservationLimits,
        observe_document_corpus,
    )

    path = tmp_path / "documents.jsonl"
    digest = _document(path)
    result = observe_document_corpus(
        path, digest, Analyzer(), limits=ObservationLimits(max_unit_characters=5)
    )
    assert result.context is None
    assert len(result.skipped_units) == 2
    assert result.skipped_units[0].reason == "unit_character_limit"


def test_training_adapter_rejects_test_receipt_and_keeps_grammar_scope(tmp_path):
    from multilang.services.qualification_observations import observe_training_corpus
    from multilang.services.vocabulary_preparation import source_catalog

    path = tmp_path / "training.conllu"
    path.write_text(
        "# newdoc id = real-doc\n# sent_id = 1\n# text = We read.\n"
        "1\tWe\twe\tPRON\t_\t_\t2\tnsubj\t_\t_\n"
        "2\tread\tread\tVERB\t_\t_\t0\troot\t_\tSpaceAfter=No\n"
        "3\t.\t.\tPUNCT\t_\t_\t2\tpunct\t_\t_\n\n"
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    catalog = source_catalog("en")["corpus"]
    receipt = dict(
        kind="corpus-test",
        language="en",
        sha256=digest,
        source_id=catalog["source_id"],
        source_url=catalog["train_urls"][0],
    )
    with pytest.raises(ValueError, match="training"):
        observe_training_corpus(path, digest, "en", Analyzer(), acquisition_receipt=receipt)
    receipt["kind"] = "corpus-train"
    result = observe_training_corpus(path, digest, "en", Analyzer(), acquisition_receipt=receipt)
    assert result.source_scope == "UD-train-grammar-only"
    assert result.split == "calibration"
    assert result.context.token_count == 2
    assert result.context.documents[0].document_id == "real-doc"
    assert "grammar-only" in result.sampling_description


def test_output_limit_is_enforced_for_original_analyses_and_occurrences(tmp_path):
    from multilang.services.qualification_observations import (
        ObservationLimits,
        observe_document_corpus,
    )

    path = tmp_path / "documents.jsonl"
    digest = _document(path)
    with pytest.raises(ValueError, match="output byte limit"):
        observe_document_corpus(
            path, digest, Analyzer(), limits=ObservationLimits(max_output_bytes=100)
        )


def test_corpus_unit_limit_prevents_analyzer_calls(tmp_path):
    from multilang.services.qualification_observations import (
        ObservationLimits,
        observe_document_corpus,
    )

    class Never:
        def analyze(self, *args):
            pytest.fail("oversized corpus reached analyzer")

    path = tmp_path / "documents.jsonl"
    digest = _document(path)
    with pytest.raises(ValueError, match="source unit limit"):
        observe_document_corpus(path, digest, Never(), limits=ObservationLimits(max_source_units=1))


def test_duplicate_training_documents_share_content_hash_despite_different_sentence_ids(tmp_path):
    from multilang.services.qualification_observations import observe_training_corpus
    from multilang.services.vocabulary_preparation import source_catalog

    path = tmp_path / "training.conllu"
    tokens = (
        "1\tWe\twe\tPRON\t_\t_\t2\tnsubj\t_\t_\n"
        "2\tread\tread\tVERB\t_\t_\t0\troot\t_\tSpaceAfter=No\n"
        "3\t.\t.\tPUNCT\t_\t_\t2\tpunct\t_\t_\n\n"
    )
    path.write_text(
        "".join(
            f"# newdoc id = doc{n}\n# sent_id = sentence{n}\n# text = We read.\n" + tokens
            for n in (1, 2)
        )
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    catalog = source_catalog("en")["corpus"]
    receipt = dict(
        kind="corpus-train",
        language="en",
        sha256=digest,
        source_id=catalog["source_id"],
        source_url=catalog["train_urls"][0],
    )
    result = observe_training_corpus(path, digest, "en", Analyzer(), acquisition_receipt=receipt)
    assert len(result.context.documents) == 2
    assert len({d.text_sha256 for d in result.context.documents}) == 1


@pytest.mark.parametrize("later_explicit_document", [False, True])
def test_missing_training_document_boundaries_never_become_dispersion(
    tmp_path, later_explicit_document
):
    from multilang.services.form_evidence import measure_form_evidence
    from multilang.services.qualification_observations import observe_training_corpus
    from multilang.services.vocabulary_preparation import source_catalog

    path = tmp_path / "training.conllu"
    tokens = (
        "1\tWe\twe\tPRON\t_\t_\t2\tnsubj\t_\t_\n"
        "2\tread\tread\tVERB\t_\t_\t0\troot\t_\tSpaceAfter=No\n"
        "3\t.\t.\tPUNCT\t_\t_\t2\tpunct\t_\t_\n\n"
    )
    path.write_text(
        "# sent_id = first\n# text = We read.\n"
        + tokens
        + (
            "# newdoc id = explicit\n# sent_id = second\n# text = We read.\n" + tokens
            if later_explicit_document
            else ""
        )
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    catalog = source_catalog("en")["corpus"]
    receipt = dict(
        kind="corpus-train",
        language="en",
        sha256=digest,
        source_id=catalog["source_id"],
        source_url=catalog["train_urls"][0],
    )
    result = observe_training_corpus(path, digest, "en", Analyzer(), acquisition_receipt=receipt)
    assert result.context.documents == ()
    assert all(item.document_id is None for item in result.occurrences)
    assert result.analyses[0].document_id == f"source-{digest}"
    assert result.coverage.document_boundaries_known is False
    assert result.coverage.source_document_count is None
    assert result.coverage.measured_document_count is None
    report = measure_form_evidence(result.context, result.occurrences)
    assert report.effective_document_count is None
    assert report.effective_token_count == 2 * (1 + later_explicit_document)
    assert all(
        item.document_count is None and item.dispersion is None for item in report.measurements
    )
