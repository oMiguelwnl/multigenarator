"""Reproducible local staging for all modern languages, with explicit review gaps."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import unicodedata
from collections import Counter
from importlib.resources import files
from pathlib import Path
from tempfile import TemporaryDirectory

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.vocabulary_sources import SourceLimits, read_conllu, read_wiktextract


def source_catalog(language: str | None = None):
    resource = files("multilang").joinpath("resources/vocabulary_sources.json")
    catalog = json.loads(resource.read_text(encoding="utf-8"))["languages"]
    expected = {item.value for item in SupportedLanguage if item.value != "la"}
    if len(catalog) != len(expected) or {item["language"] for item in catalog} != expected:
        raise ValueError("source catalog language coverage is inconsistent")
    if language is None:
        return catalog
    for entry in catalog:
        if entry["language"] == language:
            return entry
    raise ValueError("unsupported modern language; Latin uses the isolated pipeline")


def audit_legacy_frequency(root: Path, language: str) -> dict:
    source_catalog(language)
    path = Path(root) / language / "curated-v1.csv"
    result = {
        "language": language,
        "row_count": 0,
        "unknown_pos_count": 0,
        "lemma_equals_display_count": 0,
        "resolved_identity_count": 0,
        "production_eligible": False,
        "source_missing": not path.is_file(),
    }
    if not path.is_file():
        return result
    if path.is_symlink() or path.stat().st_size > 64 * 1024**2:
        raise ValueError("legacy source file is outside bounds")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open(encoding="utf-8", newline="") as handle:
        rows = csv.DictReader(handle)
        for row in rows:
            result["row_count"] += 1
            if result["row_count"] > 100_000:
                raise ValueError("legacy source record limit exceeded")
            result["unknown_pos_count"] += row.get("part_of_speech", "").casefold() in {
                "",
                "unknown",
                "x",
                "none",
                "unresolved",
            }
            result["lemma_equals_display_count"] += row.get("lemma") == row.get("display_form")
    result["source_sha256"] = digest
    result["reason"] = "legacy rows do not establish reviewed lemma/POS/sense identities"
    return result


class _OutputBudget:
    def __init__(self, limit: int):
        self.limit, self.written = limit, 0

    def write(self, handle, text: str) -> None:
        self.written += len(text.encode("utf-8"))
        if self.written > self.limit:
            raise ValueError("preparation output byte limit exceeded")
        handle.write(text)

    def dump(self, path: Path, value) -> None:
        with path.open("w", encoding="utf-8") as handle:
            for chunk in json.JSONEncoder(ensure_ascii=False, sort_keys=True, indent=2).iterencode(
                value
            ):
                self.write(handle, chunk)
            self.write(handle, "\n")


def _file_hash(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def prepare_vocabulary(
    *,
    language: str,
    dictionary: Path,
    dictionary_sha256: str,
    output: Path,
    corpus: Path | None = None,
    corpus_sha256: str | None = None,
    corpus_split: str = "test",
    lemmas: set[str] | None = None,
    dictionary_format: str = "wiktextract",
    glosses: Path | None = None,
    glosses_sha256: str | None = None,
    limits: SourceLimits | None = None,
) -> dict:
    catalog = source_catalog(language)
    limits = limits or SourceLimits()
    budget = _OutputBudget(limits.max_output_bytes)
    output = Path(output).absolute()
    if any(path.is_symlink() for path in (output, *output.parents)):
        raise ValueError("preparation output must not traverse symlinks")
    if output.exists():
        raise ValueError("preparation requires a new empty output path")
    if corpus_split not in {"test", "train", "reference"}:
        raise ValueError("corpus split must be declared")
    if (corpus is None) != (corpus_sha256 is None):
        raise ValueError("corpus path and checksum must be supplied together")
    source_diagnostics: list[dict] = []
    if dictionary_format == "wiktextract":
        if glosses is not None or glosses_sha256 is not None:
            raise ValueError("Wiktextract does not accept a separate gloss source")
        source = read_wiktextract(
            dictionary,
            language=language,
            expected_sha256=dictionary_sha256,
            lemmas=lemmas,
            limits=limits,
        )
    elif dictionary_format == "jmdict":
        from multilang.services.japanese_sources import read_jmdict

        if language != "ja" or glosses is not None or glosses_sha256 is not None:
            raise ValueError("JMdict requires Japanese and its embedded English glosses")
        source = read_jmdict(dictionary, expected_sha256=dictionary_sha256,
                             lemmas=lemmas, limits=limits, diagnostics=source_diagnostics)
    elif dictionary_format == "croatian-wordnet":
        from multilang.services.wordnet_sources import read_croatian_wordnet

        if language != "hr" or glosses is None or glosses_sha256 is None:
            raise ValueError("Croatian WordNet requires Croatian and verified gloss data")
        source = read_croatian_wordnet(
            dictionary,
            expected_sha256=dictionary_sha256,
            glosses=glosses,
            glosses_sha256=glosses_sha256,
            lemmas=lemmas,
            limits=limits,
        )
    else:
        raise ValueError("unknown dictionary format")
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".vocabulary-", dir=output.parent) as temporary:
        staging = Path(temporary) / "dataset"
        staging.mkdir()
        count, senses, inflections = 0, 0, 0
        unknown_pos, duplicates = 0, 0
        seen: set[str] = set()
        lemmas_seen: set[str] = set()
        with (
            (staging / "candidates.jsonl").open("w", encoding="utf-8") as candidates,
            (staging / "review.jsonl").open("w", encoding="utf-8") as review,
        ):
            for candidate in source:
                if candidate.candidate_id in seen:
                    duplicates += 1
                    continue
                seen.add(candidate.candidate_id)
                count += 1
                senses += candidate.kind == "lexeme"
                inflections += candidate.kind == "inflection"
                unknown_pos += candidate.pos == "X"
                lemmas_seen.add(candidate.lemma)
                if count > min(limits.max_records, limits.max_unique_entries):
                    raise ValueError("candidate record limit exceeded")
                budget.write(candidates, candidate.model_dump_json() + "\n")
                budget.write(
                    review,
                    json.dumps(
                        {
                            "candidate_id": candidate.candidate_id,
                            "lemma": candidate.lemma,
                            "pos": candidate.pos,
                            "glosses": candidate.glosses,
                            "kind": candidate.kind,
                            "stable_sense_id": None,
                            "decision": "pending",
                            "reviewer": None,
                            "evidence_sha256": None,
                        },
                        ensure_ascii=False,
                    )
                    + "\n",
                )
        sentence_count = token_count = unaligned = 0
        documents: set[str] = set()
        lemma_counts: Counter = Counter()
        if corpus is not None:
            with (staging / "reference-corpus.jsonl").open("w", encoding="utf-8") as handle:
                for sentence in read_conllu(
                    corpus, language=language, expected_sha256=corpus_sha256, limits=limits
                ):
                    sentence_count += 1
                    documents.add(sentence.document_id)
                    for token in sentence.tokens:
                        token_count += 1
                        unaligned += token.start is None
                        if token.lemma and token.pos:
                            lemma_counts[(token.lemma, token.pos)] += 1
                        if len(lemma_counts) > limits.max_unique_entries:
                            raise ValueError("corpus vocabulary limit exceeded")
                    if sentence_count > limits.max_unique_entries:
                        raise ValueError("corpus sentence limit exceeded")
                    budget.write(handle, sentence.model_dump_json() + "\n")
            budget.dump(
                staging / "corpus-observed-counts.json",
                [
                    {"lemma": lemma, "pos": pos, "observed_count": observed}
                    for (lemma, pos), observed in sorted(lemma_counts.items())
                ],
            )
        blockers = [
            "independent_sense_review",
            "source_redistribution_review",
            "language_evaluation",
            "balanced_frequency_corpora",
            "important_form_policy",
            "reviewed_content_and_audio",
            "anki_client_acceptance",
        ]
        if senses < 3000:
            blockers.insert(0, "insufficient_lexical_candidates")
        if unknown_pos:
            blockers.insert(0, "unresolved_part_of_speech")
        result = {
            "schema_version": 1,
            "language": language,
            "status": "candidate_only",
            "production_eligible": False,
            "lexical_candidate_count": senses,
            "inflection_candidate_count": inflections,
            "distinct_word_count": len(lemmas_seen),
            "duplicate_records_removed": duplicates,
            "unresolved_pos_count": unknown_pos,
            "resolved_identity_count": 0,
            "approved_important_form_count": 0,
            "target_core_identity_count": 3000,
            "blockers": blockers,
            "dictionary_sha256": dictionary_sha256,
            "dictionary_format": dictionary_format,
            "glosses_sha256": glosses_sha256,
            "candidate_filter": {
                "policy": "nfc-casefold-selection-only-v1",
                "sha256": canonical_sha256(
                    sorted({unicodedata.normalize("NFC", word).casefold() for word in lemmas})
                )
                if lemmas is not None
                else None,
            },
            "source_catalog_sha256": canonical_sha256(catalog),
            "corpus": {
                "sha256": corpus_sha256,
                "split": corpus_split,
                "sentence_count": sentence_count,
                "token_count": token_count,
                "document_count": len(documents),
                "unaligned_token_count": unaligned,
                "canonical_ranking_input": False,
            },
            "workload": {
                "approved_core_cards": 0,
                "headword_target": 3000,
                "important_form_cards": None,
                "provider_calls_executed": 0,
                "cost_estimate_available": False,
            },
        }
        budget.dump(staging / "sources.json", catalog)
        if dictionary_format == "jmdict":
            budget.dump(staging / "source-diagnostics.json", source_diagnostics)
            result["source_diagnostic_count"] = len(source_diagnostics)
            if source_diagnostics:
                result["blockers"].append("quarantined_source_restrictions")
        result["files"] = {
            path.name: _file_hash(path) for path in sorted(staging.iterdir()) if path.is_file()
        }
        result["preparation_sha256"] = canonical_sha256(result)
        budget.dump(staging / "manifest.json", result)
        if output.exists():
            raise ValueError("output was created concurrently; refusing replacement")
        os.rename(staging, output)
    return result
