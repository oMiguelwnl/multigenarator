"""Offline preparation is accessible before the gated production runtime is enabled."""

import json
from functools import wraps
from pathlib import Path
from typing import Annotated

import typer

from multilang.services.language_models import model_status, prepare_model
from multilang.services.vocabulary_preparation import (
    audit_legacy_frequency,
    prepare_vocabulary,
    source_catalog,
)
from multilang.settings import Settings


def _print(value):
    typer.echo(json.dumps(value, ensure_ascii=False, default=str))


def _guard(function):
    @wraps(function)
    def guarded(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as exc:
            typer.echo(
                f"Operation rejected ({type(exc).__name__}); validate inputs and evidence.",
                err=True,
            )
            raise typer.Exit(1) from None

    return guarded


def create_vocabulary_app(*, settings: Settings | None = None) -> typer.Typer:
    cli = typer.Typer(
        help="Prepare and evaluate real lexical sources locally.",
        pretty_exceptions_show_locals=False,
    )

    def configuration():
        return settings or Settings()

    def load_profile(path):
        from multilang.domain.language_profiles import LanguageProfile
        from multilang.services.vocabulary_review import _read_bytes

        return LanguageProfile.model_validate_json(_read_bytes(path, limit=1024**2))

    @cli.command("sources")
    @_guard
    def sources(language: str | None = None):
        _print(source_catalog(language))

    @cli.command("audit")
    @_guard
    def audit(language: str | None = None, assets: Path = Path("assets/frequency")):
        codes = [language] if language else [item["language"] for item in source_catalog()]
        _print([audit_legacy_frequency(assets, code) for code in codes])

    @cli.command("models")
    @_guard
    def models(language: str | None = None, root: Path = Path(".multilang/models/stanza-1.10.0")):
        codes = [language] if language else [item["language"] for item in source_catalog()]
        _print([model_status(code, root) for code in codes])

    @cli.command("prepare-model")
    @_guard
    def model(language: str, root: Path = Path(".multilang/models/stanza-1.10.0")):
        _print(prepare_model(language, root))

    @cli.command("acquire")
    @_guard
    def acquire(
        language: str,
        kind: str,
        root: Path = Path(".multilang/sources"),
        index: Annotated[int, typer.Option(min=0)] = 0,
        max_bytes: Annotated[int, typer.Option(min=1, max=8 * 1024**3)] = 4 * 1024**3,
    ):
        from multilang.services.vocabulary_acquisition import acquire_source

        _print(acquire_source(language, kind, root, index=index, max_bytes=max_bytes))

    @cli.command("split-dictionary")
    @_guard
    def split(
        dictionary: Path,
        dictionary_sha256: str,
        output: Path,
        seed_words: Annotated[int, typer.Option(min=3000, max=100000)] = 30000,
    ):
        from wordfreq import top_n_list

        from multilang.services.vocabulary_acquisition import split_wiktextract

        filters = {
            item["language"]: set(top_n_list(item["language"], seed_words))
            for item in source_catalog()
        }
        _print(split_wiktextract(dictionary, dictionary_sha256, output, filters))

    @cli.command("prepare")
    @_guard
    def prepare(
        language: str,
        dictionary: Path,
        dictionary_sha256: str,
        output: Path,
        corpus: Path | None = None,
        corpus_sha256: str | None = None,
        corpus_split: str = "test",
        dictionary_format: str = "wiktextract",
        glosses: Path | None = None,
        glosses_sha256: str | None = None,
        seed_words: Annotated[int | None, typer.Option(min=1, max=100000)] = None,
        max_bytes: Annotated[int, typer.Option(min=1)] = 512 * 1024**2,
    ):
        from multilang.services.vocabulary_sources import SourceLimits

        lemmas = None
        if seed_words is not None:
            from wordfreq import top_n_list

            lemmas = set(top_n_list(language, seed_words))

        _print(
            prepare_vocabulary(
                language=language,
                dictionary=dictionary,
                dictionary_sha256=dictionary_sha256,
                output=output,
                corpus=corpus,
                corpus_sha256=corpus_sha256,
                corpus_split=corpus_split,
                dictionary_format=dictionary_format,
                glosses=glosses,
                glosses_sha256=glosses_sha256,
                lemmas=lemmas,
                limits=SourceLimits(max_bytes=max_bytes),
            )
        )

    @cli.command("evaluate")
    @_guard
    def evaluate(
        language: str,
        corpus: Path,
        corpus_sha256: str,
        output: Path,
        model_root: Path = Path(".multilang/models/stanza-1.10.0"),
        max_sentences: Annotated[int, typer.Option(min=1, max=5000)] = 200,
    ):
        from multilang.services.contextual_morphology import LocalContextualMorphologyService
        from multilang.services.vocabulary_evaluation import evaluate_corpus

        _print(
            evaluate_corpus(
                language=language,
                corpus=corpus,
                corpus_sha256=corpus_sha256,
                output=output,
                analyzer=LocalContextualMorphologyService(model_root=model_root),
                max_sentences=max_sentences,
            )
        )

    @cli.command("analyze")
    @_guard
    def analyze(language: str, text_file: Path):
        from multilang.services.contextual_morphology import LocalContextualMorphologyService
        from multilang.services.vocabulary_review import _read_bytes

        text = _read_bytes(text_file, limit=64000).decode("utf-8").rstrip("\r\n")
        _print(
            LocalContextualMorphologyService(model_root=configuration().native_language_models_dir)
            .analyze(language, text)
            .model_dump(mode="json")
        )

    @cli.command("review-template")
    @_guard
    def review_template(preparation: Path, source_id: str, source_version: str, output: Path):
        from multilang.services.vocabulary_review import _plain_path, create_pending_review

        result = create_pending_review(
            preparation, source_id=source_id, source_version=source_version
        )
        with _plain_path(output).open("x", encoding="utf-8") as handle:
            handle.write(result.model_dump_json(indent=2) + "\n")
        _print(
            {
                "output": str(output),
                "pending_senses": len(result.senses),
                "production_eligible": False,
            }
        )

    @cli.command("compile-review")
    @_guard
    def compile_review(
        preparation: Path, decisions: Path, decisions_sha256: str, profile: Path, output: Path
    ):
        from multilang.native_runtime import _evidence_store
        from multilang.services.vocabulary_review import compile_reviewed_vocabulary

        bundle = compile_reviewed_vocabulary(
            preparation_dir=preparation,
            decisions_path=decisions,
            decisions_sha256=decisions_sha256,
            profile=load_profile(profile),
            verifier=_evidence_store(configuration()),
            output=output,
        )
        _print(
            {
                "bundle_sha256": bundle.bundle_sha256,
                "workload": bundle.workload,
                "production_eligible": False,
                "output": str(output),
            }
        )

    @cli.command("review-payloads")
    @_guard
    def review_payloads(decisions: Path, decisions_sha256: str, profile: Path):
        from multilang.services.vocabulary_review import (
            VocabularyReview,
            _read_bytes,
            decision_payload,
            policy_payload,
        )

        review = VocabularyReview.model_validate_json(_read_bytes(decisions, decisions_sha256))
        selected_profile = load_profile(profile)
        payloads = [
            {"purpose": purpose, "payload": decision_payload(review, decision, selected_profile)}
            for purpose, choices in [
                ("vocabulary-sense", review.senses),
                ("vocabulary-form", review.forms),
                ("vocabulary-form-aggregation", review.aggregations),
            ]
            for decision in choices
            if decision.decision == "accepted"
        ]
        if review.important_form_policy is not None:
            payloads.append(
                {
                    "purpose": "vocabulary-form-policy",
                    "payload": policy_payload(review, selected_profile),
                }
            )
        contextual = [
            {
                "purpose": "contextual-sense-binding",
                "payload": decision.binding.model_dump(
                    mode="json", exclude={"review_receipt_sha256"}
                ),
            }
            for decision in review.forms
            if decision.binding is not None
        ]
        _print(
            {
                "contextual_payloads": contextual,
                "unsigned_payloads": payloads,
                "signing_order": [
                    "contextual_bindings",
                    "important_form_policy",
                    "senses",
                    "forms",
                    "aggregations",
                ],
                "production_eligible": False,
            }
        )

    return cli
